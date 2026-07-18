from __future__ import annotations

from host.udp_cp3w_hello_session_test import build_scenarios


def test_build_scenarios_cover_full_hello_session_live_sequence() -> None:
    scenarios = build_scenarios()

    assert [scenario.name for scenario in scenarios] == [
        "pre_hello_ping",
        "unsupported_version_hello",
        "valid_hello",
        "duplicate_hello",
        "changed_hello",
        "post_hello_ping",
        "unsupported_command",
        "invalid_magic",
        "bad_crc",
        "final_ping_zero_bytes",
    ]

    assert scenarios[0].request_id == 1
    assert scenarios[0].expected_kind == "not_negotiated"

    assert scenarios[1].request_id == 2
    assert scenarios[1].expected_kind == "unsupported_version"

    assert scenarios[2].request_id == 3
    assert scenarios[2].expected_kind == "hello_success"

    assert scenarios[3].request_id == 4
    assert scenarios[3].expected_kind == "hello_duplicate"

    assert scenarios[4].request_id == 5
    assert scenarios[4].expected_kind == "invalid_state"

    assert scenarios[5].request_id == 6
    assert scenarios[5].expected_kind == "pong"
    assert scenarios[5].expected_payload == b"after-hello"

    assert scenarios[6].request_id == 7
    assert scenarios[6].expected_kind == "unknown_command"

    assert scenarios[7].request_id == 8
    assert scenarios[7].expected_kind == "timeout"

    assert scenarios[8].request_id == 9
    assert scenarios[8].expected_kind == "timeout"

    assert scenarios[9].request_id == 0xFFFFFFFF
    assert scenarios[9].expected_kind == "pong"
    assert scenarios[9].expected_payload == b"\x00after\x00hello\x00"
