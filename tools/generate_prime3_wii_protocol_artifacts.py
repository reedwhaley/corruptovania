from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from randovania.game_connection.executor.prime3_wii_protocol_artifacts import (
    protocol_manifest_json,
    protocol_vectors_json,
)


def _write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Prime 3 Wii protocol manifest and vector artifacts.")
    parser.add_argument("--manifest-out", type=Path, help="Optional JSON output path for the protocol manifest.")
    parser.add_argument("--vectors-out", type=Path, help="Optional JSON output path for protocol test vectors.")
    args = parser.parse_args()

    manifest_json = protocol_manifest_json()
    vectors_json = protocol_vectors_json()

    if args.manifest_out is not None:
        _write_text(args.manifest_out, manifest_json)
    else:
        print(manifest_json, end="")

    if args.vectors_out is not None:
        _write_text(args.vectors_out, vectors_json)
    elif args.manifest_out is not None:
        print(vectors_json, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
