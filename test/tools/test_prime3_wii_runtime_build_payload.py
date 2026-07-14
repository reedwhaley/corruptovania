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
    sys.modules[module_name] = module
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


def test_build_prime3_runtime_probe_payload_reproducible(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_probe_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    first_dir = tmp_path.joinpath("first-probe")
    second_dir = tmp_path.joinpath("second-probe")
    first_manifest = module.build_prime3_runtime_payload(first_dir, probe=True)
    second_manifest = module.build_prime3_runtime_payload(second_dir, probe=True)

    assert first_dir.joinpath("payload.bin").read_bytes() == second_dir.joinpath("payload.bin").read_bytes()
    assert first_dir.joinpath("payload.elf").read_bytes() == second_dir.joinpath("payload.elf").read_bytes()
    assert first_manifest.canary_start_offset is not None
    assert first_manifest.canary_size == second_manifest.canary_size
    assert first_manifest.counter_offset is not None
    assert first_manifest.counter_size == 4


def test_build_prime3_runtime_bootstrap_halt_payload_reproducible(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_bootstrap_halt_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    first_dir = tmp_path.joinpath("first-bootstrap-halt")
    second_dir = tmp_path.joinpath("second-bootstrap-halt")
    first_manifest = module.build_prime3_runtime_payload(
        first_dir,
        payload_mode="entry_bootstrap_halt",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )
    module.build_prime3_runtime_payload(
        second_dir,
        payload_mode="entry_bootstrap_halt",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert first_dir.joinpath("payload.bin").read_bytes() == second_dir.joinpath("payload.bin").read_bytes()
    assert first_dir.joinpath("payload.elf").read_bytes() == second_dir.joinpath("payload.elf").read_bytes()
    assert first_dir.joinpath("payload.json").read_text(encoding="utf-8") == second_dir.joinpath(
        "payload.json"
    ).read_text(encoding="utf-8")
    assert first_manifest.entry_bootstrap is not None
    assert first_manifest.entry_bootstrap.original_branch_target == 0x8000648C
    assert first_manifest.entry_bootstrap.halt_loop_address is not None


def test_build_prime3_runtime_bootstrap_continue_payload_reproducible(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_bootstrap_continue_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    first_dir = tmp_path.joinpath("first-bootstrap-continue")
    second_dir = tmp_path.joinpath("second-bootstrap-continue")
    first_manifest = module.build_prime3_runtime_payload(
        first_dir,
        payload_mode="entry_bootstrap_continue",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )
    module.build_prime3_runtime_payload(
        second_dir,
        payload_mode="entry_bootstrap_continue",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert first_dir.joinpath("payload.bin").read_bytes() == second_dir.joinpath("payload.bin").read_bytes()
    assert first_dir.joinpath("payload.elf").read_bytes() == second_dir.joinpath("payload.elf").read_bytes()
    assert first_dir.joinpath("payload.json").read_text(encoding="utf-8") == second_dir.joinpath(
        "payload.json"
    ).read_text(encoding="utf-8")
    assert first_manifest.entry_bootstrap is not None
    assert first_manifest.entry_bootstrap.halt_loop_address is None


@pytest.mark.parametrize(
    ("payload_mode", "module_name", "expect_halt_loop"),
    [
        ("relocated_copy_halt", "prime3_wii_runtime_build_payload_relocated_copy_test", True),
        ("relocated_return_halt", "prime3_wii_runtime_build_payload_relocated_return_test", True),
        ("relocated_continue", "prime3_wii_runtime_build_payload_relocated_continue_test", False),
    ],
)
def test_build_prime3_runtime_relocated_payload_reproducible(
    tmp_path: Path,
    payload_mode: str,
    module_name: str,
    expect_halt_loop: bool,
) -> None:
    module = _load_build_module(module_name)
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    first_dir = tmp_path.joinpath(f"first-{payload_mode}")
    second_dir = tmp_path.joinpath(f"second-{payload_mode}")
    first_manifest = module.build_prime3_runtime_payload(
        first_dir,
        payload_mode=payload_mode,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )
    second_manifest = module.build_prime3_runtime_payload(
        second_dir,
        payload_mode=payload_mode,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert first_dir.joinpath("payload.bin").read_bytes() == second_dir.joinpath("payload.bin").read_bytes()
    assert first_dir.joinpath("payload.elf").read_bytes() == second_dir.joinpath("payload.elf").read_bytes()
    assert first_dir.joinpath("payload.json").read_text(encoding="utf-8") == second_dir.joinpath(
        "payload.json"
    ).read_text(encoding="utf-8")
    assert first_manifest.entry_bootstrap is not None
    assert first_manifest.relocated_runtime is not None
    assert (first_manifest.entry_bootstrap.halt_loop_address is not None) is expect_halt_loop
    assert first_manifest.relocated_runtime.runtime_destination_address == 0x817E1000
    assert first_manifest.relocated_runtime.runtime_entry_address == 0x817E1000
    assert (
        first_manifest.relocated_runtime.embedded_runtime_blob_offset
        == first_manifest.relocated_runtime.low_bootstrap_size
    )
    assert first_manifest.relocated_runtime.embedded_runtime_blob_size > 0
    assert first_manifest.relocated_runtime.ios_udp_diagnostic_enabled is False
    assert first_manifest.relocated_runtime.transport is None
    assert first_manifest.payload_sha256 == second_manifest.payload_sha256


def test_build_prime3_runtime_relocated_continue_transport_reproducible(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_relocated_continue_transport_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    first_dir = tmp_path.joinpath("first-relocated-continue-transport")
    second_dir = tmp_path.joinpath("second-relocated-continue-transport")
    first_manifest = module.build_prime3_runtime_payload(
        first_dir,
        payload_mode="relocated_continue",
        enable_ios_udp_diagnostic=True,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )
    second_manifest = module.build_prime3_runtime_payload(
        second_dir,
        payload_mode="relocated_continue",
        enable_ios_udp_diagnostic=True,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert first_dir.joinpath("payload.bin").read_bytes() == second_dir.joinpath("payload.bin").read_bytes()
    assert first_dir.joinpath("payload.elf").read_bytes() == second_dir.joinpath("payload.elf").read_bytes()
    assert first_dir.joinpath("payload.json").read_text(encoding="utf-8") == second_dir.joinpath(
        "payload.json"
    ).read_text(encoding="utf-8")
    assert first_manifest.relocated_runtime is not None
    assert first_manifest.relocated_runtime.ios_udp_diagnostic_enabled is True
    assert first_manifest.relocated_runtime.transport is not None
    assert first_manifest.relocated_runtime.transport.last_receive_preview_size == 16
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


def test_build_prime3_runtime_payload_rejects_transport_without_relocated_continue(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_transport_mode_guard")

    with pytest.raises(RuntimeError, match="requires relocated_continue mode"):
        module.build_prime3_runtime_payload(
            tmp_path,
            payload_mode="relocated_return_halt",
            enable_ios_udp_diagnostic=True,
            reserved_high=0x817E0000,
            diagnostic_address=0x817E0100,
        )


@pytest.mark.parametrize("ios_udp_mode", ["dry_run", "retail_wrapper_open_kd_once"])
def test_build_prime3_runtime_payload_rejects_developer_ios_mode_without_transport(
    tmp_path: Path,
    ios_udp_mode: str,
) -> None:
    module = _load_build_module(f"prime3_wii_runtime_build_payload_{ios_udp_mode}_guard")

    with pytest.raises(RuntimeError, match="developer modes require enable_ios_udp_diagnostic"):
        module.build_prime3_runtime_payload(
            tmp_path,
            payload_mode="relocated_continue",
            enable_recurring_hook_diagnostics=True,
            enable_ios_udp_diagnostic=False,
            ios_udp_mode=ios_udp_mode,
            reserved_high=0x817E0000,
            diagnostic_address=0x817E0100,
        )


def test_build_prime3_runtime_payload_relocated_continue_diagnostics_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_relocated_continue_diagnostics_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="retail_wrapper_open_kd_once",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.diagnostics is not None
    assert manifest.relocated_runtime.diagnostics.mode == "retail_wrapper_open_kd_once"
    assert manifest.relocated_runtime.transport is not None
    assert manifest.relocated_runtime.retail_ios_wrapper is not None
    assert manifest.relocated_runtime.retail_ios_wrapper.open_async_address == 0x80504668


def test_build_prime3_runtime_payload_relocated_continue_abi_probe_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_relocated_continue_abi_probe_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="retail_wrapper_ioctl_async_abi_probe",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.abi_probe is not None
    assert manifest.relocated_runtime.abi_probe.mode == "retail_wrapper_ioctl_async_abi_probe"
    assert manifest.relocated_runtime.abi_probe.expected_return_value == 0x13579BDF


def test_build_prime3_runtime_payload_relocated_continue_open_ip_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_relocated_continue_open_ip_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="retail_wrapper_nwc24_close_open_ip_once",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    assert manifest.relocated_runtime.transport.mode == "retail_wrapper_nwc24_close_open_ip_once"
    assert manifest.relocated_runtime.transport.terminal_phase_name == "IP_OPEN"
    assert manifest.relocated_runtime.transport.open_ip_path_pointer_address is not None
    assert manifest.relocated_runtime.transport.ip_fd_before_open_ip_address is not None


def test_main_rejects_failed_direct_ios_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_failed_direct_flag")
    monkeypatch.setattr(sys, "argv", ["build_payload.py", "--ios-open-kd-once"])

    with pytest.raises(RuntimeError, match="failed direct-submit experiment"):
        module.main()


def test_validate_retail_call_veneer_instructions_accepts_balanced_lr_restore() -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_veneer_validator_good")

    module._validate_retail_call_veneer_instructions(
        veneer_name="runtime_call_retail_ios_open_async",
        expected_target=0x80504668,
        instructions=[
            (0x1000, "stwu", "r1,-32(r1)"),
            (0x1004, "mflr", "r0"),
            (0x1008, "stw", "r0,8(r1)"),
            (0x100C, "stw", "r2,12(r1)"),
            (0x1010, "stw", "r13,16(r1)"),
            (0x1014, "lis", "r12,-32688"),
            (0x1018, "ori", "r12,r12,18024"),
            (0x101C, "mtctr", "r12"),
            (0x1020, "bctrl", ""),
            (0x1024, "stw", "r3,20(r1)"),
            (0x1028, "lwz", "r2,12(r1)"),
            (0x102C, "lwz", "r13,16(r1)"),
            (0x1030, "lwz", "r0,8(r1)"),
            (0x1034, "mtlr", "r0"),
            (0x1038, "lwz", "r3,20(r1)"),
            (0x103C, "addi", "r1,r1,32"),
            (0x1040, "blr", ""),
        ],
    )


def test_validate_retail_call_veneer_instructions_rejects_missing_lr_restore() -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_veneer_validator_bad")

    with pytest.raises(RuntimeError, match="locate 'lwz'|restore LR and stack"):
        module._validate_retail_call_veneer_instructions(
            veneer_name="runtime_call_retail_ios_open_async",
            expected_target=0x80504668,
            instructions=[
                (0x1000, "stwu", "r1,-32(r1)"),
                (0x1004, "mflr", "r0"),
                (0x1008, "stw", "r0,8(r1)"),
                (0x100C, "lis", "r12,-32688"),
                (0x1010, "ori", "r12,r12,18024"),
                (0x1014, "mtctr", "r12"),
                (0x1018, "bctrl", ""),
                (0x101C, "addi", "r1,r1,32"),
                (0x1020, "blr", ""),
            ],
        )


def test_validate_retail_call_veneer_instructions_rejects_pre_bctrl_argument_clobber() -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_veneer_validator_clobber")

    with pytest.raises(RuntimeError, match="clobbers r9 before bctrl"):
        module._validate_retail_call_veneer_instructions(
            veneer_name="runtime_call_retail_read_async",
            expected_target=0x80504A08,
            instructions=[
                (0x1000, "stwu", "r1,-32(r1)"),
                (0x1004, "mflr", "r0"),
                (0x1008, "stw", "r0,8(r1)"),
                (0x100C, "stw", "r2,12(r1)"),
                (0x1010, "stw", "r13,16(r1)"),
                (0x1014, "mr", "r9,r2"),
                (0x1018, "lis", "r12,-32688"),
                (0x101C, "ori", "r12,r12,18952"),
                (0x1020, "mtctr", "r12"),
                (0x1024, "bctrl", ""),
                (0x1028, "lwz", "r2,12(r1)"),
                (0x102C, "lwz", "r13,16(r1)"),
                (0x1030, "lwz", "r0,8(r1)"),
                (0x1034, "mtlr", "r0"),
                (0x1038, "addi", "r1,r1,32"),
                (0x103C, "blr", ""),
            ],
        )


def test_validate_retail_call_veneer_instructions_rejects_argument_register_target_load() -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_veneer_validator_bad_target_reg")

    with pytest.raises(RuntimeError, match="must not use argument register r10"):
        module._validate_retail_call_veneer_instructions(
            veneer_name="runtime_call_retail_read_async",
            expected_target=0x80504A08,
            instructions=[
                (0x1000, "stwu", "r1,-32(r1)"),
                (0x1004, "mflr", "r0"),
                (0x1008, "stw", "r0,8(r1)"),
                (0x100C, "stw", "r2,12(r1)"),
                (0x1010, "stw", "r13,16(r1)"),
                (0x1014, "lis", "r10,-32688"),
                (0x1018, "ori", "r10,r10,18952"),
                (0x101C, "mtctr", "r10"),
                (0x1020, "bctrl", ""),
                (0x1024, "lwz", "r2,12(r1)"),
                (0x1028, "lwz", "r13,16(r1)"),
                (0x102C, "lwz", "r0,8(r1)"),
                (0x1030, "mtlr", "r0"),
                (0x1034, "addi", "r1,r1,32"),
                (0x1038, "blr", ""),
            ],
        )
