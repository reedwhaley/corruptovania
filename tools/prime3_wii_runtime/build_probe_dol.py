from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    _repository_root = Path(__file__).resolve().parents[2]
    _repository_root_str = os.fspath(_repository_root)
    if _repository_root_str not in sys.path:
        sys.path.insert(0, _repository_root_str)

from randovania.games.prime3.exporter.probe_delivery import build_unhooked_probe_dol
from randovania.games.prime3.exporter.runtime_payload import Prime3RuntimePayloadManifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-dol", type=Path, required=True)
    parser.add_argument("--output-dol", type=Path, required=True)
    parser.add_argument("--payload-bin", type=Path, required=True)
    parser.add_argument("--payload-manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = Prime3RuntimePayloadManifest.from_json_text(args.payload_manifest.read_text(encoding="utf-8"))
    result = build_unhooked_probe_dol(
        args.original_dol.read_bytes(),
        args.payload_bin.read_bytes(),
        manifest,
    )
    args.output_dol.parent.mkdir(parents=True, exist_ok=True)
    args.output_dol.write_bytes(result.probe_dol_bytes)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result.probe_section.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
