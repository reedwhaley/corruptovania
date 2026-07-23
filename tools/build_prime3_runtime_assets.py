from __future__ import annotations

import argparse
import ipaddress
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    _repository_root = Path(__file__).resolve().parents[1]
    _repository_root_str = os.fspath(_repository_root)
    if _repository_root_str not in sys.path:
        sys.path.insert(0, _repository_root_str)

from randovania.games.prime3.exporter.hardware_runtime import (
    HARDWARE_RUNTIME_MODES,
    PRODUCTION_RUNTIME_ASSET_DIR,
    Prime3HardwareRuntimeMode,
    build_hardware_runtime_payload,
    load_validated_hardware_runtime_assets,
    runtime_asset_directory,
)
from tools.prime3_wii_runtime.build_payload import DEFAULT_NATIVE_BEACON_IPV4, DEFAULT_NATIVE_BEACON_PORT


def _parse_ipv4(value: str) -> int:
    return int(ipaddress.IPv4Address(value))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and validate selectable Prime 3 CP3W hardware runtime assets.")
    parser.add_argument("--output-dir", type=Path, default=Path(PRODUCTION_RUNTIME_ASSET_DIR))
    parser.add_argument(
        "--mode",
        type=Prime3HardwareRuntimeMode,
        choices=HARDWARE_RUNTIME_MODES,
        action="append",
        help="Build only this mode; repeat for multiple modes. The default builds all hardware modes.",
    )
    parser.add_argument(
        "--native-beacon-ipv4",
        type=_parse_ipv4,
        default=DEFAULT_NATIVE_BEACON_IPV4,
        metavar="ADDRESS",
        help="Development IPv4 destination for the native bootstrap beacon.",
    )
    parser.add_argument(
        "--native-beacon-port",
        type=int,
        default=DEFAULT_NATIVE_BEACON_PORT,
        metavar="PORT",
        help="Development UDP destination port for the native bootstrap beacon.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"DEVKITPRO={os.environ.get('DEVKITPRO', '')}")
    print(f"DEVKITPPC={os.environ.get('DEVKITPPC', '')}")
    modes = tuple(args.mode) if args.mode else HARDWARE_RUNTIME_MODES
    for runtime_mode in modes:
        asset_dir = runtime_asset_directory(args.output_dir, runtime_mode)
        build_hardware_runtime_payload(
            asset_dir,
            runtime_mode,
            native_beacon_ipv4=args.native_beacon_ipv4,
            native_beacon_port=args.native_beacon_port,
        )
        assets = load_validated_hardware_runtime_assets(asset_dir, runtime_mode, require_elf=True)
        assert assets.manifest.relocated_runtime is not None
        transport = assets.manifest.relocated_runtime.transport
        assert transport is not None
        print(f"[{runtime_mode.value}] output_dir={asset_dir}")
        print(f"[{runtime_mode.value}] payload.elf sha256={assets.elf_sha256}")
        print(f"[{runtime_mode.value}] payload.bin sha256={assets.payload_sha256}")
        print(f"[{runtime_mode.value}] payload.json sha256={assets.manifest_sha256}")
        print(f"[{runtime_mode.value}] udp_port={transport.udp_port}")
    print("validation=passed")


if __name__ == "__main__":
    main()
