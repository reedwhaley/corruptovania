from __future__ import annotations

import struct

import pytest

from randovania.game_connection.executor import prime3_wii_runtime_diagnostics as diagnostics
from randovania.game_connection.executor.prime3_wii_runtime_diagnostics import (
    CP3W_UDP_PORT,
    DIAGNOSTIC_FIELDS,
    DIAGNOSTICS_MAGIC,
    DIAGNOSTICS_SIZE,
    DIAGNOSTICS_VERSION,
    HEARTBEAT_PREFIX,
    encode_heartbeat,
    parse_diagnostics,
)


def _diagnostic_bytes(**overrides: int) -> bytes:
    values = dict.fromkeys(DIAGNOSTIC_FIELDS, 0)
    values.update(
        magic=DIAGNOSTICS_MAGIC,
        version=DIAGNOSTICS_VERSION,
        size=DIAGNOSTICS_SIZE,
        build_id=0x50335731,
        requested_bind_port=CP3W_UDP_PORT,
    )
    values.update(overrides)
    return struct.pack(
        ">" + "I" * len(DIAGNOSTIC_FIELDS), *(values[field] & 0xFFFF_FFFF for field in DIAGNOSTIC_FIELDS)
    )


def test_diagnostics_layout_is_fixed_and_parses_signed_results() -> None:
    raw = _diagnostic_bytes(socket_descriptor=-1, bind_result=-22, current_phase=98)

    result = parse_diagnostics(raw)

    assert len(raw) == 256
    assert result["socket_descriptor"] == -1
    assert result["bind_result"] == -22
    assert result["current_phase"] == 98
    assert result.build_id_text == "P3W1"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"magic": 0}, "magic"),
        ({"version": 2}, "version"),
        ({"size": 4}, "invalid size"),
        ({"requested_bind_port": 43673}, "unexpected UDP port"),
    ],
)
def test_diagnostics_rejects_incompatible_layout(overrides: dict[str, int], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_diagnostics(_diagnostic_bytes(**overrides))


def test_heartbeat_payload_is_deterministic() -> None:
    payload = encode_heartbeat(build_id=0x50335731, phase=106)

    assert payload.startswith(HEARTBEAT_PREFIX + b"\0")
    assert payload[-8:] == bytes.fromhex("503357310000006a")


def test_wii_sockaddr_encodes_inaddr_any_and_cp3w_port_in_network_order() -> None:
    assert diagnostics.encode_wii_sockaddr().hex() == "0802aa9a00000000"


@pytest.mark.parametrize(
    ("socket_descriptor", "auto_retry", "socket_lost", "expected"),
    [
        (-1, True, False, diagnostics.NetworkPhase.RETRY_DELAY),
        (4, True, False, diagnostics.NetworkPhase.CLOSE_SOCKET_FOR_RECOVERY),
        (4, True, True, diagnostics.NetworkPhase.SOCKET_LOST),
        (4, False, True, diagnostics.NetworkPhase.FATAL_ERROR),
    ],
)
def test_failure_state_transition(
    socket_descriptor: int,
    auto_retry: bool,
    socket_lost: bool,
    expected: diagnostics.NetworkPhase,
) -> None:
    assert (
        diagnostics.phase_after_failure(
            socket_descriptor=socket_descriptor,
            auto_retry=auto_retry,
            socket_lost=socket_lost,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("ip_open", "service_started", "host_id_ready", "expected"),
    [
        (False, False, False, diagnostics.NetworkPhase.OPEN_IP),
        (True, False, False, diagnostics.NetworkPhase.SO_STARTUP),
        (True, True, False, diagnostics.NetworkPhase.GET_HOST_ID),
        (True, True, True, diagnostics.NetworkPhase.CREATE_SOCKET),
    ],
)
def test_retry_resumes_at_first_incomplete_initialization_stage(
    ip_open: bool,
    service_started: bool,
    host_id_ready: bool,
    expected: diagnostics.NetworkPhase,
) -> None:
    assert (
        diagnostics.phase_after_retry_delay(
            ip_open=ip_open,
            service_started=service_started,
            host_id_ready=host_id_ready,
        )
        == expected
    )
