from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from randovania.games.prime3.exporter.dol_patcher import Prime3DolPatchError
from randovania.games.prime3.exporter.runtime_payload import Prime3RuntimeTransportMetadata

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT.joinpath("tools", "prime3_wii_runtime", "build_payload.py")


def _load_build_module(module_name: str = "prime3_wii_runtime_build_payload_test"):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _devkitppc_is_available() -> bool:
    return Path(r"C:\devkitPro\devkitPPC\bin\powerpc-eabi-gcc.exe").is_file()


def test_canonical_builder_selects_tcp_sources_and_linker() -> None:
    module = _load_build_module()

    assert module.SOURCE_FILES[2:5] == (
        Path("../prime3_tcp_runtime_clean/runtime.c"),
        Path("../prime3_tcp_runtime_clean/runtime.S"),
        Path("../prime3_tcp_runtime_clean/runtime.ld"),
    )


def test_canonical_builder_requires_cp3c_symbols() -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_cp3c_symbols")

    assert module.CP3C_CONFIG_START_SYMBOL == "__cp3c_config_start"
    assert module.CP3C_CONFIG_END_SYMBOL == "__cp3c_config_end"
    assert module.CP3C_SERVER_IPV4_SYMBOL == "__cp3c_server_ipv4"
    assert module.CP3C_SERVER_PORT_SYMBOL == "__cp3c_server_port"
    with pytest.raises(RuntimeError, match="Unable to locate symbol"):
        module._extract_symbol_address("", module.CP3C_CONFIG_START_SYMBOL)


def test_tcp_metadata_rejects_legacy_udp_fields() -> None:
    with pytest.raises(Prime3DolPatchError, match="Legacy UDP"):
        Prime3RuntimeTransportMetadata.from_json_dict({"udp_port": 43674})


def test_missing_toolchain_reports_toolchain_error_after_tcp_argument_validation(tmp_path: Path) -> None:
    module = _load_build_module("prime3_wii_runtime_build_payload_tcp_toolchain")

    with pytest.raises(RuntimeError, match="reserved_high and diagnostic_address"):
        module.build_prime3_runtime_payload(tmp_path, payload_mode="relocated_continue")

    environment = os.environ.copy()
    environment.pop("DEVKITPRO", None)
    environment.pop("DEVKITPPC", None)
    result = subprocess.run(
        [sys.executable, os.fspath(SCRIPT_PATH)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    assert result.returncode != 0
    assert "DEVKITPRO and DEVKITPPC must be set" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr


def test_tcp_payload_is_deterministic_and_has_valid_cp3c_metadata(tmp_path: Path) -> None:
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    module = _load_build_module("prime3_wii_runtime_build_payload_tcp_manifest")
    first_dir = tmp_path.joinpath("first")
    second_dir = tmp_path.joinpath("second")
    kwargs = {
        "payload_mode": "relocated_continue",
        "reserved_high": 0x817E0000,
        "diagnostic_address": 0x817E0100,
    }
    first = module.build_prime3_runtime_payload(first_dir, **kwargs)
    second = module.build_prime3_runtime_payload(second_dir, **kwargs)

    assert first_dir.joinpath("payload.bin").read_bytes() == second_dir.joinpath("payload.bin").read_bytes()
    assert first.to_json_text() == second.to_json_text()
    assert first.relocated_runtime is not None
    transport = first.relocated_runtime.transport
    assert isinstance(transport, Prime3RuntimeTransportMetadata)
    assert transport.transport_kind == "tcp"
    assert transport.diagnostics_enabled is False
    assert transport.server_ipv4_size == 4
    assert transport.server_port_size == 2
    assert transport.server_ipv4_byte_order == "big"
    assert transport.server_port_byte_order == "big"
    assert transport.cp3c_config_offset < transport.server_ipv4_offset
    assert transport.cp3c_config_offset < transport.server_port_offset
    assert transport.inventory_tracker_capability
    assert transport.tracker_snapshot_capability
    assert transport.resync_capability


def test_direct_invocation_by_absolute_path_works_without_pythonpath(tmp_path: Path) -> None:
    if not _devkitppc_is_available():
        pytest.skip("devkitPPC is not available in this environment")

    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, os.fspath(SCRIPT_PATH)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
