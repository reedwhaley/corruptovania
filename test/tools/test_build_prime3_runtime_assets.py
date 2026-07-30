from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from randovania.games.prime3.exporter.dol_patcher import Prime3DolPatchError
from randovania.games.prime3.exporter.runtime_payload import Prime3RuntimeTransportMetadata

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT.joinpath("tools", "build_prime3_runtime_assets.py")


def _load_module(module_name: str = "build_prime3_runtime_assets_test"):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_builder_uses_tcp_runtime_and_configurable_toolchain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_module()
    devkitppc = tmp_path.joinpath("devkitPro", "devkitPPC")
    output_dir = tmp_path.joinpath("production")
    received: dict[str, object] = {}
    toolchain = SimpleNamespace(
        compiler_path=devkitppc.joinpath("bin", "powerpc-eabi-gcc"),
        linker_path=devkitppc.joinpath("bin", "powerpc-eabi-ld"),
        objcopy_path=devkitppc.joinpath("bin", "powerpc-eabi-objcopy"),
    )
    transport = Prime3RuntimeTransportMetadata(
        transport_kind="tcp",
        protocol_magic_hex="43503354",
        protocol_version=1,
        frame_size=64,
        diagnostics_enabled=False,
        inbound_queue_depth=4,
        outbound_queue_depth=4,
        cp3c_config_offset=0xC900,
        cp3c_config_size=0x20,
        server_ipv4_offset=0xC90C,
        server_ipv4_size=4,
        server_ipv4_byte_order="big",
        server_port_offset=0xC910,
        server_port_size=2,
        server_port_byte_order="big",
        inventory_tracker_capability=True,
        tracker_snapshot_capability=True,
        tracker_delta_capability=True,
        resync_capability=True,
        kd_startup_capability=True,
        ip_startup_capability=True,
        tcp_connect_capability=True,
        tcp_send_capability=True,
        tcp_receive_capability=True,
        wait_connect_tcp_capability=True,
    )

    def fake_resolve(environment: dict[str, str]) -> SimpleNamespace:
        assert environment["DEVKITPPC"] == str(devkitppc)
        assert environment["DEVKITPRO"] == str(devkitppc.parent)
        return toolchain

    def fake_build(output: Path, **kwargs: object) -> SimpleNamespace:
        received.update(kwargs)
        output.mkdir(parents=True)
        output.joinpath("payload.elf").write_bytes(b"\x7fELF")
        output.joinpath("payload.json").write_bytes(b"{}")
        return SimpleNamespace(
            payload_sha256="a" * 64,
            relocated_runtime=SimpleNamespace(transport=transport),
        )

    monkeypatch.setattr(module, "resolve_prime3_runtime_toolchain", fake_resolve)
    monkeypatch.setattr(module, "build_prime3_runtime_payload", fake_build)

    module.build_canonical_tcp_assets(output_dir, devkitppc=devkitppc)

    assert received["payload_mode"] == "relocated_continue"
    assert received["enable_tcp_tracker"] is True
    assert received["enable_ios_network_lifecycle"] is True
    assert received.get("enable_ios_udp_diagnostic", False) is False
    assert received["reserved_high"] == 0x817E0000
    assert received["diagnostic_address"] == 0x817E0100
    assert received["devkitppc_path"] == devkitppc
    assert output_dir.joinpath("payload.elf").is_file()
    assert output_dir.joinpath("payload.json").is_file()


def test_canonical_builder_rejects_missing_toolchain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module("build_prime3_runtime_assets_missing_toolchain_test")

    def missing_toolchain(_environment: dict[str, str]) -> None:
        raise Prime3DolPatchError("DEVKITPRO and DEVKITPPC must be set for Prime 3 Wii runtime payload builds.")

    monkeypatch.setattr(module, "resolve_prime3_runtime_toolchain", missing_toolchain)

    with pytest.raises(Prime3DolPatchError, match="DEVKITPRO and DEVKITPPC must be set"):
        module.build_canonical_tcp_assets(tmp_path)


def test_builder_source_selects_tcp_runtime_not_udp_runtime() -> None:
    source = REPO_ROOT.joinpath("tools", "prime3_wii_runtime", "build_payload.py").read_text(encoding="utf-8")

    assert 'Path("../prime3_tcp_runtime_clean/runtime.c")' in source
    assert 'Path("../prime3_tcp_runtime_clean/runtime.S")' in source
    assert 'Path("../prime3_tcp_runtime_clean/runtime.ld")' in source
    assert 'joinpath("prime3_tcp_runtime_clean", "runtime.c")' in source
    assert 'joinpath("prime3_wii_runtime", "relocated_runtime.c")' not in source


def test_canonical_tcp_runtime_enables_lifecycle_without_udp_diagnostics() -> None:
    source = REPO_ROOT.joinpath("tools", "prime3_tcp_runtime_clean", "runtime.c").read_text(encoding="utf-8")

    assert "PRIME3_ENABLE_TCP_TRACKER" in source
    assert "PRIME3_ENABLE_IOS_NETWORK_LIFECYCLE" in source
    assert "PRIME3_ENABLE_TCP_TRACKER || runtime_transport_is_cp3w_frame_validation_mode()" in source
    assert "RUNTIME_TRANSPORT_PHASE_WAIT_CONNECT_TCP" in source
    assert "IOCTL_SO_CONNECT = 4" in source
    assert "IOCTLV_SO_SENDTO = 13" in source
    assert "IOCTLV_SO_RECVFROM = 12" in source
