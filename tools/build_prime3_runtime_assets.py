from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    _repository_root = Path(__file__).resolve().parents[1]
    _repository_root_str = os.fspath(_repository_root)
    if _repository_root_str not in sys.path:
        sys.path.insert(0, _repository_root_str)

from randovania.games.prime3.exporter.hardware_runtime import (
    PRODUCTION_RUNTIME_ASSET_DIR,
)
from randovania.games.prime3.exporter.runtime_payload import PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE
from randovania.games.prime3.exporter.runtime_toolchain import resolve_prime3_runtime_toolchain
from tools.prime3_wii_runtime.build_payload import build_prime3_runtime_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and validate the canonical Prime 3 TCP runtime asset.")
    parser.add_argument("--output-dir", type=Path, default=Path(PRODUCTION_RUNTIME_ASSET_DIR))
    parser.add_argument(
        "--devkitppc",
        type=Path,
        help="Path to the devkitPPC root. DEVKITPRO is derived from its parent.",
    )
    return parser.parse_args()


def _toolchain_environment(devkitppc: Path | None) -> dict[str, str]:
    environment = dict(os.environ)
    if devkitppc is not None:
        environment["DEVKITPPC"] = os.fspath(devkitppc)
        environment["DEVKITPRO"] = os.fspath(devkitppc.parent)
    return environment


def build_canonical_tcp_assets(output_dir: Path, *, devkitppc: Path | None = None) -> None:
    toolchain = resolve_prime3_runtime_toolchain(_toolchain_environment(devkitppc))
    print(f"compiler={toolchain.compiler_path}")
    print(f"assembler={toolchain.compiler_path}")
    print(f"linker={toolchain.linker_path}")
    print(f"objcopy={toolchain.objcopy_path}")
    manifest = build_prime3_runtime_payload(
        output_dir,
        payload_mode=PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
        devkitppc_path=devkitppc,
    )
    transport = manifest.relocated_runtime.transport if manifest.relocated_runtime is not None else None
    if transport is None or transport.transport_kind != "tcp":
        raise RuntimeError("Canonical Prime 3 runtime build did not produce TCP transport metadata.")
    print(f"output_dir={output_dir}")
    print(f"payload.elf sha256={_sha256(output_dir.joinpath('payload.elf'))}")
    print(f"payload.bin sha256={manifest.payload_sha256}")
    print(f"payload.json sha256={_sha256(output_dir.joinpath('payload.json'))}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    args = parse_args()
    build_canonical_tcp_assets(args.output_dir, devkitppc=args.devkitppc)
    print("validation=passed")


if __name__ == "__main__":
    main()
