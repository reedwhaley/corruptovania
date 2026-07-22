from __future__ import annotations

from pathlib import Path

RUNTIME_SOURCE = Path(__file__).resolve().parents[2] / "tools" / "prime3_wii_runtime" / "relocated_runtime.c"


def test_native_runtime_has_persistent_delays_and_socket_recovery() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")

    assert "RUNTIME_INITIAL_DELAY_POLL_INTERVAL = 300" in source
    assert "RUNTIME_RETRY_DELAY_POLL_INTERVAL = 120" in source
    assert "RUNTIME_TRANSPORT_PHASE_RETRY_DELAY" in source
    assert "RUNTIME_TRANSPORT_PHASE_SOCKET_LOST" in source
    assert "RUNTIME_TRANSPORT_PHASE_CLOSE_SOCKET_FOR_RECOVERY" in source
    assert "runtime_transport_retry_deadline" in source


def test_native_runtime_treats_endpoint_verification_as_advisory() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")

    assert "RUNTIME_UDP_PORT = 43674" in source
    assert "IOCTL_SO_GETSOCKNAME = 7" in source
    assert "actual_port != 0" in source
    assert "actual_port != RUNTIME_UDP_PORT" in source
    assert "runtime_transport_actual_bound_address = runtime_read_be32" in source
    assert "runtime_record_endpoint_verification_warning" in source
    assert "runtime_enter_listening_after_bind(0);" in source
    assert "runtime_enter_listening_after_bind(1);" in source
    assert "runtime_transport_actual_bound_port = 0;" in source
    assert "runtime_transport_actual_bound_address = 0;" in source
    assert "runtime_transport_bound_port = RUNTIME_UDP_PORT;" in source
    assert "runtime_transport_bound_flag = 1" in source
    assert "43673" not in source


def test_degraded_listening_still_submits_receive() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")

    listening_branch = source.split("if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_LISTENING)", maxsplit=1)[
        1
    ].split("if (runtime_transport_phase == RUNTIME_TRANSPORT_PHASE_SUBMIT_HEARTBEAT)", maxsplit=1)[0]
    assert "RUNTIME_TRANSPORT_PHASE_SUBMIT_RECEIVE_ONCE" in listening_branch
    assert "RUNTIME_TRANSPORT_PHASE_BOUND_NO_RECV" in listening_branch


def test_native_diagnostics_abi_and_controls_are_fixed() -> None:
    source = RUNTIME_SOURCE.read_text(encoding="utf-8")

    assert "RUNTIME_DIAGNOSTICS_MAGIC = 0x43503344" in source
    assert "RUNTIME_DIAGNOSTICS_VERSION = 1" in source
    assert "RUNTIME_DIAGNOSTICS_SIZE = 0x100" in source
    assert "sizeof(runtime_network_diagnostics) == 0x100" in source
    assert "runtime_network_diagnostics_block.restart_request" in source
    assert "runtime_network_diagnostics_block.heartbeat_request" in source
    assert "runtime_sync_network_diagnostics();" in source
