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


def test_native_execution_aliases_reuse_unused_v1_fields() -> None:
    raw = _diagnostic_bytes(
        ios_version=diagnostics.NATIVE_EXECUTION_CANARY,
        ios_revision=7,
        shutdown_call_count=1234,
        overlay_page=-1,
    )

    result = parse_diagnostics(raw)

    assert len(raw) == DIAGNOSTICS_SIZE
    assert result.native_execution_canary == diagnostics.NATIVE_EXECUTION_CANARY
    assert result.native_execution_stage == 7
    assert result.native_recurring_hook_count == 1234
    assert result.native_post_copy_hook_result == -1


def test_diagnostics_preserve_advisory_verification_failure_without_claiming_endpoint() -> None:
    raw = _diagnostic_bytes(
        getsockname_result=-22,
        last_error_phase=98,
        actual_bind_address=0,
        actual_bind_port=0,
        requested_bind_port=43674,
        listening=1,
    )

    result = parse_diagnostics(raw)

    assert result["getsockname_result"] == -22
    assert result["last_error_phase"] == 98
    assert result["actual_bind_address"] == 0
    assert result["actual_bind_port"] == 0
    assert result["requested_bind_port"] == 43674
    assert result["listening"] == 1


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


def test_verified_cp3w_endpoint_is_accepted() -> None:
    assert diagnostics.classify_bound_endpoint(0, diagnostics.encode_wii_sockaddr()) == (
        diagnostics.EndpointVerification.VERIFIED,
        0,
        43674,
    )


@pytest.mark.parametrize(
    ("result", "sockaddr"),
    [
        (0, b"\0" * 8),
        (0, bytes.fromhex("0802000000000000")),
        (-22, diagnostics.encode_wii_sockaddr()),
        (0, bytes.fromhex("0702aa9a00000000")),
    ],
)
def test_unverifiable_endpoint_is_advisory_and_does_not_claim_actual_values(result: int, sockaddr: bytes) -> None:
    assert diagnostics.classify_bound_endpoint(result, sockaddr) == (
        diagnostics.EndpointVerification.ADVISORY_UNVERIFIED,
        0,
        0,
    )


def test_structurally_valid_wrong_nonzero_port_requires_cleanup() -> None:
    assert diagnostics.classify_bound_endpoint(0, bytes.fromhex("080212340a000001")) == (
        diagnostics.EndpointVerification.WRONG_NONZERO_PORT,
        0x0A000001,
        0x1234,
    )


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
