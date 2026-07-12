from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from randovania.games.prime3.exporter.runtime_payload import load_prime3_runtime_payload_artifact

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT.joinpath("tools", "prime3_wii_runtime", "build_payload.py")
BUILD_OUTPUT_DIR = REPO_ROOT.joinpath("build", "prime3_wii_runtime")


def _load_build_module(module_name: str = "prime3_wii_runtime_build_payload_test"):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _remove_generated_artifacts() -> None:
    if BUILD_OUTPUT_DIR.is_dir():
        for artifact in BUILD_OUTPUT_DIR.iterdir():
            artifact.unlink()
        BUILD_OUTPUT_DIR.rmdir()


def _devkitppc_is_available() -> bool:
    return Path(r"C:\devkitPro\devkitPPC\bin\powerpc-eabi-gcc.exe").is_file()


def _run_script(script_path: Path | str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, os.fspath(script_path)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_build_prime3_runtime_payload_reproducible(tmp_path: Path) -> None:
    module = _load_build_module()
    if not _devkitppc_is_available():
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


def test_direct_invocation_by_relative_path_works_from_repo_root() -> None:
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    _remove_generated_artifacts()
    result = _run_script(Path("tools/prime3_wii_runtime/build_payload.py"), REPO_ROOT)

    assert result.returncode == 0, result.stderr
    assert BUILD_OUTPUT_DIR.joinpath("payload.elf").is_file()
    assert BUILD_OUTPUT_DIR.joinpath("payload.bin").is_file()
    assert BUILD_OUTPUT_DIR.joinpath("payload.json").is_file()
    load_prime3_runtime_payload_artifact(
        manifest_path=BUILD_OUTPUT_DIR.joinpath("payload.json"),
        payload_path=BUILD_OUTPUT_DIR.joinpath("payload.bin"),
        load_address=0x80510000,
    )
    _remove_generated_artifacts()


def test_direct_invocation_by_absolute_path_works_from_other_directory(tmp_path: Path) -> None:
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    _remove_generated_artifacts()
    result = _run_script(SCRIPT_PATH, tmp_path)

    assert result.returncode == 0, result.stderr
    assert BUILD_OUTPUT_DIR.joinpath("payload.elf").is_file()
    assert BUILD_OUTPUT_DIR.joinpath("payload.bin").is_file()
    assert BUILD_OUTPUT_DIR.joinpath("payload.json").is_file()
    _remove_generated_artifacts()


def test_importing_module_does_not_insert_duplicate_repo_root_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root_str = os.fspath(REPO_ROOT)
    monkeypatch.setattr(sys, "path", [repo_root_str, "sentinel", repo_root_str])

    _load_build_module("prime3_wii_runtime_build_payload_duplicate_check")

    assert sys.path.count(repo_root_str) == 2


def test_direct_invocation_without_toolchain_reports_normal_toolchain_error(tmp_path: Path) -> None:
    script = (
        "import os, runpy; "
        "os.environ['DEVKITPRO'] = r'C:\\\\missing-devkitpro'; "
        "os.environ['DEVKITPPC'] = r'C:\\\\missing-devkitpro\\\\devkitPPC'; "
        f"runpy.run_path(r'{SCRIPT_PATH}', run_name='__main__')"
    )
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode != 0
    assert "Prime3DolPatchError" in result.stderr
    assert "Missing devkitPro installation metadata" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
