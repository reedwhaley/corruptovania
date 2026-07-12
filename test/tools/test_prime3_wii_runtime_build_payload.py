from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_build_module():
    module_path = Path(__file__).resolve().parents[2].joinpath("tools", "prime3_wii_runtime", "build_payload.py")
    spec = importlib.util.spec_from_file_location("prime3_wii_runtime_build_payload", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_prime3_runtime_payload_reproducible(tmp_path: Path) -> None:
    module = _load_build_module()
    if not Path(r"C:\devkitPro\devkitPPC\bin\powerpc-eabi-gcc.exe").is_file():
        pytest.skip("devkitPPC is not available in this environment")

    first_dir = tmp_path.joinpath("first")
    second_dir = tmp_path.joinpath("second")
    first_manifest = module.build_prime3_runtime_payload(first_dir)
    second_manifest = module.build_prime3_runtime_payload(second_dir)

    assert first_dir.joinpath("payload.bin").read_bytes() == second_dir.joinpath("payload.bin").read_bytes()
    assert first_dir.joinpath("payload.elf").read_bytes() == second_dir.joinpath("payload.elf").read_bytes()
    assert first_dir.joinpath("payload.json").read_text(encoding="utf-8") == second_dir.joinpath(
        "payload.json"
    ).read_text(encoding="utf-8")
    assert first_manifest.payload_sha256 == second_manifest.payload_sha256
