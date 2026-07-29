"""Decode an S13D record copied from a Wii memory image."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--offset", type=lambda value: int(value, 0), required=True)
    args = parser.parse_args()
    data = args.image.read_bytes()[args.offset : args.offset + 0x94]
    words = struct.unpack(">11I7I5I", data[:0x5C])
    if words[0] != 0x53313344:
        raise SystemExit(f"expected S13D, got 0x{words[0]:08X}")
    print("magic=S13D")
    names = (
        "phase_before", "phase_after", "submit_result", "callback_invoked", "callback_result",
        "pending_operation", "callback_generation", "userdata_valid", "ip_fd", "socket_fd",
    )
    for name, value in zip(names, words[1:11], strict=True):
        print(f"{name}=0x{value:08X} signed={struct.unpack('>i', struct.pack('>I', value))[0]}")
    print("r3_r9=" + " ".join(f"0x{value:08X}" for value in words[11:18]))
    print("vectors=" + " ".join(f"0x{value:08X}" for value in words[18:23]))
    print("request=" + data[0x5C:0x84].hex(" "))
    print("payload=" + data[0x84:0x94].hex(" "))


if __name__ == "__main__":
    main()
