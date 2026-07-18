from __future__ import annotations

import argparse
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
    build_production_runtime_payload,
    load_validated_production_runtime_assets,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and validate the production Prime 3 CP3W runtime assets.")
    parser.add_argument("--output-dir", type=Path, default=Path(PRODUCTION_RUNTIME_ASSET_DIR))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_production_runtime_payload(args.output_dir)
    assets = load_validated_production_runtime_assets(args.output_dir, require_elf=True)
    print(f"DEVKITPRO={os.environ.get('DEVKITPRO', '')}")
    print(f"DEVKITPPC={os.environ.get('DEVKITPPC', '')}")
    print(f"payload.elf sha256={assets.elf_sha256}")
    print(f"payload.bin sha256={assets.payload_sha256}")
    print(f"payload.json sha256={assets.manifest_sha256}")
    print(f"mode={assets.manifest.relocated_runtime.transport.mode}")
    print(f"udp_port={assets.manifest.relocated_runtime.transport.udp_port}")
    print("validation=passed")


if __name__ == "__main__":
    main()
