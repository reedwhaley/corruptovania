from __future__ import annotations

import struct

from host.udp_cp3w_frame_test import build_scenarios
from randovania.game_connection.executor.prime3_wii_protocol import HEADER_FORMAT, HEADER_SIZE


def test_build_scenarios_use_distinct_validation_shapes() -> None:
    scenarios = {scenario.name: scenario for scenario in build_scenarios()}

    truncated = scenarios["truncated_packet"].packet
    assert len(truncated) < HEADER_SIZE + 4

    mismatch = scenarios["payload_length_mismatch"].packet
    header = mismatch[:HEADER_SIZE]
    magic, version, packet_kind, command, response_status, request_id, declared_payload_length = struct.unpack(
        HEADER_FORMAT,
        header,
    )
    actual_payload_length = len(mismatch) - HEADER_SIZE - 4

    assert magic == b"CP3W"
    assert version == 1
    assert packet_kind == 1
    assert command == 127
    assert response_status == 0
    assert request_id == 4
    assert declared_payload_length == actual_payload_length + 1
