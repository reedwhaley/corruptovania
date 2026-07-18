from __future__ import annotations

from host.udp_cp3w_ping_pong_test import (
    EXPECTED_RESPONSE_COMMAND,
    UNSUPPORTED_MESSAGE,
    build_scenarios,
)


def test_build_scenarios_cover_full_ping_pong_live_sequence() -> None:
    scenarios = build_scenarios()

    assert [scenario.name for scenario in scenarios] == [
        "ping_empty",
        "ping_prime3",
        "disconnect_unsupported",
        "invalid_magic",
        "bad_crc",
        "payload_length_mismatch",
        "ping_binary_payload",
        "ping_final_payload",
    ]

    assert scenarios[0].request_id == 1
    assert scenarios[0].request_payload == b""
    assert scenarios[0].expected_kind == "pong"

    assert scenarios[1].request_id == 2
    assert scenarios[1].request_payload == b"prime3"
    assert scenarios[1].expected_kind == "pong"

    assert scenarios[2].request_id == 3
    assert scenarios[2].request_command == 4
    assert scenarios[2].request_payload == b""
    assert scenarios[2].expected_kind == "error"

    assert scenarios[3].request_id == 4
    assert scenarios[3].expected_kind == "timeout"

    assert scenarios[4].request_id == 5
    assert scenarios[4].expected_kind == "timeout"

    assert scenarios[5].request_id == 6
    assert scenarios[5].expected_kind == "timeout"

    assert scenarios[6].request_id == 42
    assert scenarios[6].request_payload == b"\x00prime3\x00"
    assert scenarios[6].expected_kind == "pong"

    assert scenarios[7].request_id == 0xFFFFFFFF
    assert scenarios[7].request_payload == b"cp3w-final-20260718"
    assert scenarios[7].expected_kind == "pong"

    assert EXPECTED_RESPONSE_COMMAND.name == "PING"
    assert UNSUPPORTED_MESSAGE == "Command is unsupported"
