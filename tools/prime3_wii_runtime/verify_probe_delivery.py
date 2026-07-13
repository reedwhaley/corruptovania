from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    _repository_root = Path(__file__).resolve().parents[2]
    _repository_root_str = os.fspath(_repository_root)
    if _repository_root_str not in sys.path:
        sys.path.insert(0, _repository_root_str)

from randovania.games.prime3.exporter.probe_delivery import verify_probe_delivery


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-dol", type=Path, required=True)
    parser.add_argument("--probe-dol", type=Path, required=True)
    parser.add_argument("--extracted-final-dol", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--payload-bin", type=Path, required=True)
    parser.add_argument("--payload-manifest", type=Path, required=True)
    parser.add_argument("--payload-address")
    parser.add_argument("--halt-at-entry", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = verify_probe_delivery(
        original_dol_path=args.original_dol,
        probe_dol_path=args.probe_dol,
        extracted_final_dol_path=args.extracted_final_dol,
        payload_bin_path=args.payload_bin,
        payload_manifest_path=args.payload_manifest,
        payload_virtual_address=None if args.payload_address is None else int(args.payload_address, 0),
        halt_at_entry=args.halt_at_entry,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report.to_json_text(), encoding="utf-8")


if __name__ == "__main__":
    main()
