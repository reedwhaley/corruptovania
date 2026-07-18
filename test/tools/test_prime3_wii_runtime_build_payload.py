from __future__ import annotations

import importlib.util
import os
import shutil
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
            if artifact.is_dir():
                shutil.rmtree(artifact)
            else:
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


def test_build_prime3_runtime_payload_relocated_continue_so_startup_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_relocated_continue_so_startup_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="retail_wrapper_nwc24_close_open_ip_startup_once",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    assert manifest.relocated_runtime.transport.mode == "retail_wrapper_nwc24_close_open_ip_startup_once"
    assert manifest.relocated_runtime.transport.terminal_phase_name == "SO_STARTED"
    assert manifest.relocated_runtime.transport.startup_target_address is not None
    assert manifest.relocated_runtime.transport.startup_pre_call_args_address is not None
    assert manifest.relocated_runtime.transport.service_started_address is not None


def test_build_prime3_runtime_payload_relocated_continue_create_socket_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_relocated_continue_create_socket_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="retail_wrapper_create_socket_once",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    assert manifest.relocated_runtime.transport.mode == "retail_wrapper_create_socket_once"
    assert manifest.relocated_runtime.transport.terminal_phase_name == "SOCKET_READY"
    assert manifest.relocated_runtime.transport.socket_target_address is not None
    assert manifest.relocated_runtime.transport.socket_command_address is not None
    assert manifest.relocated_runtime.transport.socket_request_address_address is not None
    assert manifest.relocated_runtime.transport.socket_request_bytes_address is not None
    assert manifest.relocated_runtime.transport.socket_request_bytes_size == 12
    assert manifest.relocated_runtime.transport.socket_pre_call_args_size == 0x20


def test_build_prime3_runtime_payload_relocated_continue_bind_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_relocated_continue_bind_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="retail_wrapper_bind_once",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = manifest.relocated_runtime.transport
    assert transport.mode == "retail_wrapper_bind_once"
    assert transport.terminal_phase_name == "BOUND_NO_RECV"
    assert transport.bind_target_address is not None
    assert transport.bind_command_address is not None
    assert transport.bind_request_logical_size_size == 4
    assert transport.bind_request_bytes_size == 36
    assert transport.bind_pre_call_args_size == 0x20
    assert transport.cleanup_close_request_logical_size_size == 4
    assert transport.cleanup_close_request_bytes_size == 4
    assert transport.bound_flag_address is not None
    assert transport.bound_address_address is not None
    assert transport.socket_closed_after_bind_failure_address is not None
    assert transport.socket_leak_detected_address is not None


def test_build_prime3_runtime_payload_relocated_continue_recvfrom_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_relocated_continue_recvfrom_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="retail_wrapper_recvfrom_once",
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = manifest.relocated_runtime.transport
    assert transport.mode == "retail_wrapper_recvfrom_once"
    assert transport.receive_enabled is True
    assert transport.send_enabled is False
    assert transport.terminal_phase_value == 27
    assert transport.terminal_phase_name == "RECEIVED_DATAGRAM"


def test_main_rejects_failed_direct_ios_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_failed_direct_flag")
    monkeypatch.setattr(sys, "argv", ["build_payload.py", "--ios-open-kd-once"])

    with pytest.raises(RuntimeError, match="failed direct-submit experiment"):
        module.main()


def test_main_selects_recvfrom_once_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_recvfrom_mode")
    captured: dict[str, object] = {}

    def _fake_build(output_dir: Path, **kwargs):
        captured["output_dir"] = output_dir
        captured.update(kwargs)
        raise RuntimeError("stop after argument selection")

    monkeypatch.setattr(module, "build_prime3_runtime_payload", _fake_build)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-recvfrom-once",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="stop after argument selection"):
        module.main()

    assert captured["ios_udp_mode"] == "retail_wrapper_recvfrom_once"
    assert captured["enable_ios_udp_diagnostic"] is True
    assert captured["payload_mode"] == "relocated_continue"


def test_main_selects_recv_send_once_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_recv_send_mode")
    captured: dict[str, object] = {}

    def _fake_build(output_dir: Path, **kwargs):
        captured["output_dir"] = output_dir
        captured.update(kwargs)
        raise RuntimeError("stop after argument selection")

    monkeypatch.setattr(module, "build_prime3_runtime_payload", _fake_build)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-recv-send-once",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="stop after argument selection"):
        module.main()

    assert captured["ios_udp_mode"] == "retail_wrapper_recv_send_once"
    assert captured["enable_ios_udp_diagnostic"] is True
    assert captured["payload_mode"] == "relocated_continue"


def test_main_selects_recv_send_loop_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_recv_send_loop_mode")
    captured: dict[str, object] = {}

    def _fake_build(output_dir: Path, **kwargs):
        captured["output_dir"] = output_dir
        captured.update(kwargs)
        raise RuntimeError("stop after argument selection")

    monkeypatch.setattr(module, "build_prime3_runtime_payload", _fake_build)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-recv-send-loop",
            "--ios-recv-send-loop-count",
            "3",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="stop after argument selection"):
        module.main()

    assert captured["ios_udp_mode"] == "retail_wrapper_recv_send_loop"
    assert captured["ios_udp_loop_count"] == 3
    assert captured["enable_ios_udp_diagnostic"] is True
    assert captured["payload_mode"] == "relocated_continue"


def test_main_rejects_recv_send_loop_count_without_loop_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_recv_send_loop_count_rejected")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-recv-send-loop-count",
            "4",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="requires --ios-recv-send-loop"):
        module.main()


def test_main_selects_cp3w_frame_validation_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_mode")
    captured: dict[str, object] = {}

    def _fake_build(output_dir: Path, **kwargs):
        captured["output_dir"] = output_dir
        captured.update(kwargs)
        raise RuntimeError("stop after argument selection")

    monkeypatch.setattr(module, "build_prime3_runtime_payload", _fake_build)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-frame-validation",
            "--ios-cp3w-frame-validation-count",
            "6",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="stop after argument selection"):
        module.main()

    assert captured["ios_udp_mode"] == "cp3w_frame_validation"
    assert captured["ios_udp_loop_count"] == 6
    assert captured["enable_ios_udp_diagnostic"] is True
    assert captured["payload_mode"] == "relocated_continue"


def test_main_rejects_cp3w_frame_validation_count_without_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_count_rejected")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-frame-validation-count",
            "7",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="requires --ios-cp3w-frame-validation"):
        module.main()


def test_main_selects_cp3w_ping_pong_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_ping_pong_mode")
    captured: dict[str, object] = {}

    def _fake_build(output_dir: Path, **kwargs):
        captured["output_dir"] = output_dir
        captured.update(kwargs)
        raise RuntimeError("stop after argument selection")

    monkeypatch.setattr(module, "build_prime3_runtime_payload", _fake_build)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-ping-pong",
            "--ios-cp3w-ping-pong-count",
            "8",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="stop after argument selection"):
        module.main()

    assert captured["ios_udp_mode"] == "cp3w_ping_pong"
    assert captured["ios_udp_loop_count"] == 8
    assert captured["enable_ios_udp_diagnostic"] is True
    assert captured["payload_mode"] == "relocated_continue"


def test_main_rejects_cp3w_ping_pong_count_without_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_ping_pong_count_rejected")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-ping-pong-count",
            "9",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="requires --ios-cp3w-ping-pong"):
        module.main()


def test_main_selects_cp3w_hello_session_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_hello_session_mode")
    captured: dict[str, object] = {}

    def _fake_build(output_dir: Path, **kwargs):
        captured["output_dir"] = output_dir
        captured.update(kwargs)
        raise RuntimeError("stop after argument selection")

    monkeypatch.setattr(module, "build_prime3_runtime_payload", _fake_build)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-hello-session",
            "--ios-cp3w-hello-session-count",
            "10",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="stop after argument selection"):
        module.main()

    assert captured["ios_udp_mode"] == "cp3w_hello_session"
    assert captured["ios_udp_loop_count"] == 10
    assert captured["enable_ios_udp_diagnostic"] is True
    assert captured["payload_mode"] == "relocated_continue"


def test_main_rejects_cp3w_hello_session_count_without_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_hello_session_count_rejected")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-hello-session-count",
            "10",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="requires --ios-cp3w-hello-session"):
        module.main()


@pytest.mark.parametrize("count", [0, -1, 101])
def test_main_rejects_out_of_range_cp3w_ping_pong_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    count: int,
) -> None:
    module = _load_build_module(f"prime3_wii_runtime_build_payload_cp3w_ping_pong_count_{count}")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-ping-pong",
            "--ios-cp3w-ping-pong-count",
            str(count),
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="must be between 1 and 100"):
        module.main()


@pytest.mark.parametrize("count", [0, -1, 101])
def test_main_rejects_out_of_range_cp3w_hello_session_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    count: int,
) -> None:
    module = _load_build_module(f"prime3_wii_runtime_build_payload_cp3w_hello_session_count_{count}")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-hello-session",
            "--ios-cp3w-hello-session-count",
            str(count),
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="must be between 1 and 100"):
        module.main()


@pytest.mark.parametrize("count", [0, -1, 101])
def test_main_rejects_out_of_range_cp3w_frame_validation_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    count: int,
) -> None:
    module = _load_build_module(f"prime3_wii_runtime_build_payload_cp3w_count_{count}")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-frame-validation",
            "--ios-cp3w-frame-validation-count",
            str(count),
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="must be between 1 and 100"):
        module.main()


def test_main_rejects_non_integer_cp3w_frame_validation_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_count_non_integer")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-frame-validation",
            "--ios-cp3w-frame-validation-count",
            "abc",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(SystemExit):
        module.main()


def test_main_rejects_non_integer_cp3w_hello_session_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_hello_session_count_non_integer")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-hello-session",
            "--ios-cp3w-hello-session-count",
            "abc",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(SystemExit):
        module.main()


def test_main_rejects_conflicting_cp3w_and_loop_modes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_mode_conflict")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-recv-send-loop",
            "--ios-cp3w-frame-validation",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="at most one IOS UDP diagnostic sub-mode flag"):
        module.main()


def test_main_rejects_conflicting_cp3w_ping_pong_and_hello_session_modes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_ping_pong_hello_conflict")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--enable-ios-udp-diagnostic",
            "--ios-cp3w-ping-pong",
            "--ios-cp3w-hello-session",
            "--reserved-high",
            "0x817E0000",
            "--diagnostic-address",
            "0x817E0100",
            "--output-dir",
            os.fspath(tmp_path),
        ],
    )

    with pytest.raises(RuntimeError, match="at most one IOS UDP diagnostic sub-mode flag"):
        module.main()


def test_build_prime3_runtime_payload_relocated_continue_recv_send_loop_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_relocated_continue_recv_send_loop_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="retail_wrapper_recv_send_loop",
        ios_udp_loop_count=3,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = manifest.relocated_runtime.transport
    assert transport.mode == "retail_wrapper_recv_send_loop"
    assert transport.receive_enabled is True
    assert transport.send_enabled is True
    assert transport.terminal_phase_value == 45
    assert transport.terminal_phase_name == "LOOP_COMPLETE"
    assert transport.receive_arm_count_address is not None
    assert transport.receive_rearm_count_address is not None
    assert transport.configured_exchange_limit_address is not None
    assert transport.completed_exchange_count_address is not None
    assert transport.current_exchange_index_address is not None
    assert transport.last_completed_exchange_index_address is not None
    assert transport.rearm_submission_failure_count_address is not None
    assert transport.loop_complete_transition_count_address is not None
    assert transport.polls_while_receive_pending_address is not None
    assert transport.polls_after_loop_complete_address is not None


def test_build_prime3_runtime_payload_relocated_continue_cp3w_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_manifest_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="cp3w_frame_validation",
        ios_udp_loop_count=6,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = manifest.relocated_runtime.transport
    assert transport.mode == "cp3w_frame_validation"
    assert transport.receive_enabled is True
    assert transport.send_enabled is True
    assert transport.terminal_phase_value == 55
    assert transport.terminal_phase_name == "CP3W_FRAME_LOOP_COMPLETE"
    assert transport.cp3w_magic_hex == "43503357"
    assert transport.cp3w_protocol_version == 1
    assert transport.cp3w_header_size == 16
    assert transport.cp3w_crc_size == 4
    assert transport.cp3w_crc_initial_value == 0xFFFFFFFF
    assert transport.cp3w_crc_final_xor_value == 0xFFFFFFFF
    assert transport.cp3w_crc_polynomial == 0xEDB88320
    assert transport.cp3w_crc_reflected is True
    assert transport.cp3w_packet_kind_request == 1
    assert transport.cp3w_packet_kind_response == 2
    assert transport.cp3w_command_reserved_mailbox == 127
    assert transport.cp3w_packet_kind_offset == 5
    assert transport.cp3w_command_offset == 6
    assert transport.cp3w_response_status_offset == 7
    assert transport.cp3w_request_id_offset == 8
    assert transport.cp3w_payload_length_offset == 12
    assert transport.cp3w_request_payload_ascii == "P3_FRAME_TEST_20260717"
    assert transport.cp3w_response_payload_ascii == "P3_FRAME_ACK_20260717"
    assert transport.prepared_send_length_address is not None
    assert transport.cp3w_datagrams_processed_address is not None
    assert transport.cp3w_frames_valid_address is not None
    assert transport.cp3w_frames_invalid_address is not None
    assert transport.cp3w_frames_too_short_address is not None
    assert transport.cp3w_frames_invalid_magic_address is not None
    assert transport.cp3w_frames_invalid_version_address is not None
    assert transport.cp3w_frames_unsupported_type_address is not None
    assert transport.cp3w_frames_nonzero_flags_address is not None
    assert transport.cp3w_frames_length_mismatch_address is not None
    assert transport.cp3w_frames_payload_too_large_address is not None
    assert transport.cp3w_frames_invalid_payload_address is not None
    assert transport.cp3w_frames_malformed_address is not None
    assert transport.cp3w_framed_responses_submitted_address is not None
    assert transport.cp3w_framed_responses_completed_address is not None
    assert transport.cp3w_last_request_id_address is not None
    assert transport.cp3w_last_response_id_address is not None
    assert transport.cp3w_last_message_type_address is not None
    assert transport.cp3w_last_declared_payload_length_address is not None
    assert transport.cp3w_last_actual_payload_length_address is not None
    assert transport.cp3w_last_frame_result_address is not None
    assert transport.cp3w_final_datagram_index_address is not None


def test_build_prime3_runtime_payload_relocated_continue_cp3w_ping_pong_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_ping_pong_manifest_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="cp3w_ping_pong",
        ios_udp_loop_count=8,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = manifest.relocated_runtime.transport
    assert transport.mode == "cp3w_ping_pong"
    assert transport.receive_enabled is True
    assert transport.send_enabled is True
    assert transport.terminal_phase_value == 61
    assert transport.terminal_phase_name == "CP3W_PING_PONG_LOOP_COMPLETE"
    assert transport.cp3w_response_status_error == 1
    assert transport.cp3w_command_ping == 3
    assert transport.cp3w_pong_command == 3
    assert transport.cp3w_pong_uses_ping_command is True
    assert transport.cp3w_error_code_unknown_command == 4
    assert transport.cp3w_ping_max_payload_length is not None
    assert transport.cp3w_ping_max_payload_length > 0
    assert transport.cp3w_unsupported_message_ascii == "Command is unsupported"
    assert transport.cp3w_requests_dispatched_address is not None
    assert transport.cp3w_ping_requests_received_address is not None
    assert transport.cp3w_pong_responses_submitted_address is not None
    assert transport.cp3w_pong_responses_completed_address is not None
    assert transport.cp3w_unsupported_commands_received_address is not None
    assert transport.cp3w_unsupported_responses_submitted_address is not None
    assert transport.cp3w_unsupported_responses_completed_address is not None
    assert transport.cp3w_last_command_address is not None
    assert transport.cp3w_last_response_status_address is not None
    assert transport.cp3w_last_ping_payload_length_address is not None
    assert transport.cp3w_last_dispatch_result_address is not None


def test_build_prime3_runtime_payload_relocated_continue_cp3w_hello_session_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_hello_session_manifest_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="cp3w_hello_session",
        ios_udp_loop_count=10,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = manifest.relocated_runtime.transport
    assert transport.mode == "cp3w_hello_session"
    assert transport.receive_enabled is True
    assert transport.send_enabled is True
    assert transport.terminal_phase_value == 69
    assert transport.terminal_phase_name == "CP3W_HELLO_SESSION_LOOP_COMPLETE"
    assert transport.cp3w_response_status_error == 1
    assert transport.cp3w_command_ping == 3
    assert transport.cp3w_pong_command == 3
    assert transport.cp3w_pong_uses_ping_command is True
    assert transport.cp3w_error_code_unknown_command == 4
    assert transport.cp3w_ping_max_payload_length is not None
    assert transport.cp3w_unsupported_message_ascii == "Command is unsupported"
    assert transport.cp3w_hello_requests_received_address is not None
    assert transport.cp3w_hello_successes_address is not None
    assert transport.cp3w_hello_version_rejections_address is not None
    assert transport.cp3w_hello_responses_submitted_address is not None
    assert transport.cp3w_hello_responses_completed_address is not None
    assert transport.cp3w_hello_duplicate_requests_address is not None
    assert transport.cp3w_hello_renegotiation_rejections_address is not None
    assert transport.cp3w_pre_hello_gated_commands_address is not None
    assert transport.cp3w_not_negotiated_responses_submitted_address is not None
    assert transport.cp3w_not_negotiated_responses_completed_address is not None
    assert transport.cp3w_negotiated_flag_address is not None
    assert transport.cp3w_selected_protocol_version_address is not None
    assert transport.cp3w_client_nonce_address is not None
    assert transport.cp3w_client_capabilities_address is not None
    assert transport.cp3w_runtime_capabilities_address is not None
    assert transport.cp3w_accepted_capabilities_address is not None
    assert transport.cp3w_session_id_address is not None
    assert transport.cp3w_runtime_build_id_address is not None


def test_build_prime3_runtime_payload_relocated_continue_cp3w_game_identity_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_game_identity_manifest_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="cp3w_game_identity",
        ios_udp_loop_count=12,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )

    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = manifest.relocated_runtime.transport
    assert transport.mode == "cp3w_game_identity"
    assert transport.terminal_phase_value == 79
    assert transport.terminal_phase_name == "CP3W_GAME_IDENTITY_LOOP_COMPLETE"
    assert transport.cp3w_game_identity is not None
    identity = transport.cp3w_game_identity
    assert identity.command_value == 5
    assert identity.capability_value == 1 << 11
    assert identity.schema_version == 1
    assert identity.payload_size == 28
    assert identity.profile_fingerprint == 0x67B00CE6
    assert identity.runtime_build_id == 0x50335731
    assert identity.configured_count == 12
    assert identity.phase_names["LOOP_COMPLETE"] == 79
    assert identity.field_offsets["reserved"] == 24
    assert set(identity.state_addresses) >= {
        "requests",
        "successes",
        "capability_rejections",
        "invalid_payload_rejections",
        "last_availability",
        "game_state_pointer",
        "player_state_pointer",
        "inventory_root_pointer",
    }


def test_receive_completion_routes_all_cp3w_modes_to_frame_validation() -> None:
    source = (Path(__file__).parents[2] / "tools" / "prime3_wii_runtime" / "relocated_runtime.c").read_text()
    receive_completion = source.split("static s32 runtime_consume_receive_completion(void)", 2)[2].split(
        "static s32 runtime_consume_send_completion(void)", 1
    )[0]

    assert "runtime_transport_is_cp3w_mode()" in receive_completion


def test_inventory_packet_fits_send_buffer_without_expanding_ping_limit() -> None:
    source = (Path(__file__).parents[2] / "tools" / "prime3_wii_runtime" / "relocated_runtime.c").read_text()

    assert "RUNTIME_UDP_SEND_CAPACITY = 512" in source
    assert "RUNTIME_CP3W_MAX_PING_PAYLOAD_LENGTH = 44" in source


def test_build_prime3_runtime_payload_cp3w_inventory_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_inventory_manifest_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")
    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_recurring_hook_diagnostics=True,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="cp3w_inventory",
        ios_udp_loop_count=14,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )
    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = manifest.relocated_runtime.transport
    assert transport.mode == "cp3w_inventory"
    assert transport.terminal_phase_value == 93
    assert transport.cp3w_inventory is not None
    assert transport.cp3w_game_identity is not None
    inventory = transport.cp3w_inventory
    assert inventory.command_value == 6
    assert inventory.capability_value == 1 << 12
    assert len(inventory.item_ids) == 59
    assert inventory.payload_size == 484
    assert inventory.frame_size == 504
    assert inventory.send_buffer_size == 512
    assert inventory.ping_payload_limit == 44
    assert inventory.phase_names["LOOP_COMPLETE"] == 93


def test_build_prime3_runtime_payload_cp3w_inventory_service_manifest(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_inventory_service_manifest_test")
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")
    manifest = module.build_prime3_runtime_payload(
        tmp_path,
        payload_mode="relocated_continue",
        enable_ios_udp_diagnostic=True,
        ios_udp_mode="cp3w_inventory_service",
        ios_udp_loop_count=0,
        reserved_high=0x817E0000,
        diagnostic_address=0x817E0100,
    )
    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = manifest.relocated_runtime.transport
    assert transport.mode == "cp3w_inventory_service"
    assert transport.udp_port == 43674
    assert transport.terminal_phase_value == 26
    assert transport.terminal_phase_name == "WAIT_RECEIVE"
    assert transport.cp3w_inventory is not None
    assert transport.cp3w_inventory.mode_value == 22
    assert transport.cp3w_inventory.configured_count == 0


def test_cp3w_inventory_service_rearms_without_exchange_limit() -> None:
    source = (Path(__file__).parents[2] / "tools" / "prime3_wii_runtime" / "relocated_runtime.c").read_text()

    assert "RUNTIME_IOS_UDP_DIAGNOSTIC_MODE_CP3W_INVENTORY_SERVICE = 22" in source
    assert "runtime_transport_is_unbounded_cp3w_inventory_service()" in source
    assert "!runtime_transport_is_unbounded_cp3w_inventory_service()" in source
    assert "if (command == RUNTIME_CP3W_COMMAND_DISCONNECT)" in source
    assert "dispatch_result == 14" in source


@pytest.mark.parametrize("count", [0, -1, 101])
def test_main_rejects_out_of_range_cp3w_inventory_count(count: int, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_build_module(f"prime3_wii_runtime_build_payload_cp3w_inventory_count_{count}")
    monkeypatch.setattr(
        sys,
        "argv",
        ["build_payload.py", "--relocated-continue", "--ios-cp3w-inventory", "--ios-cp3w-inventory-count", str(count)],
    )
    with pytest.raises(RuntimeError, match="between 1 and 100"):
        module.main()


def test_main_rejects_cp3w_inventory_count_without_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_inventory_count_without_mode")
    monkeypatch.setattr(sys, "argv", ["build_payload.py", "--ios-cp3w-inventory-count", "14"])
    with pytest.raises(RuntimeError, match="requires --ios-cp3w-inventory"):
        module.main()


@pytest.mark.parametrize("count", [0, -1, 101])
def test_main_rejects_out_of_range_cp3w_game_identity_count(
    count: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_build_module(f"prime3_wii_runtime_build_payload_cp3w_game_identity_count_{count}")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_payload.py",
            "--relocated-continue",
            "--ios-cp3w-game-identity",
            "--ios-cp3w-game-identity-count",
            str(count),
        ],
    )
    with pytest.raises(RuntimeError, match="between 1 and 100"):
        module.main()


def test_main_rejects_cp3w_game_identity_count_without_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3w_game_identity_count_without_mode")
    monkeypatch.setattr(sys, "argv", ["build_payload.py", "--ios-cp3w-game-identity-count", "12"])
    with pytest.raises(RuntimeError, match="requires --ios-cp3w-game-identity"):
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
