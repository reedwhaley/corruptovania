from __future__ import annotations

import json
import struct

import pytest

from host import udp_cp3w_inventory_test as validator
from randovania.game_connection.executor.prime3_wii_protocol import (
    INVENTORY_PAYLOAD_SIZE,
    Prime3WiiCommand,
    Prime3WiiInventoryAvailability,
    Prime3WiiInventoryRecord,
    Prime3WiiInventorySnapshot,
    Prime3WiiProtocolError,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    encode_inventory_payload,
    encode_response,
)

AVAILABLE = (
    Prime3WiiInventoryAvailability.EXECUTABLE_RECOGNIZED
    | Prime3WiiInventoryAvailability.GAME_STATE_POINTER_VALID
    | Prime3WiiInventoryAvailability.INVENTORY_ROOT_VALID
    | Prime3WiiInventoryAvailability.RANGE_VALID
    | Prime3WiiInventoryAvailability.CONSISTENCY_CHECK_PASSED
    | Prime3WiiInventoryAvailability.SNAPSHOT_AVAILABLE
)


def _packet(snapshot: Prime3WiiInventorySnapshot, *, request_id: int = 5) -> bytes:
    return encode_response(
        Prime3WiiResponse(
            Prime3WiiCommand.GET_INVENTORY,
            request_id,
            Prime3WiiResponseStatus.OK,
            encode_inventory_payload(snapshot),
        )
    )


def test_primary_sequence_is_exactly_fourteen_datagrams() -> None:
    scenarios = validator.build_primary_scenarios()
    assert len(scenarios) == 14
    assert [scenario.name for scenario in scenarios][4:7] == ["inventory_1", "inventory_2", "ping"]
    assert scenarios[-1].name == "inventory_final"


def test_full_snapshot_decode_is_big_endian_and_json_compatible() -> None:
    records = tuple(Prime3WiiInventoryRecord(index, 0x10000000 + index) for index in range(59))
    snapshot = Prime3WiiInventorySnapshot(
        availability_flags=AVAILABLE,
        snapshot_sequence=0xFFFFFFFE,
        records=records,
    )
    packet = _packet(snapshot)
    decoded = validator.decode_inventory_response(packet, 5)
    assert decoded == snapshot
    assert len(decoded.records) == 59
    assert encode_inventory_payload(snapshot)[12:20] == struct.pack(">II", 0, 0x10000000)
    summary = validator._summarize_snapshot(decoded)
    json.dumps(summary, allow_nan=False)


def test_selected_slot_assertions_use_native_item_ids() -> None:
    records = list(Prime3WiiInventorySnapshot().records)
    records[17] = Prime3WiiInventoryRecord(5, 5)
    records[-1] = Prime3WiiInventoryRecord(7, 9)
    snapshot = Prime3WiiInventorySnapshot(availability_flags=AVAILABLE, records=tuple(records))
    validator.assert_selected_records(snapshot, {17: (5, 5), 69: (7, 9)})
    with pytest.raises(ValueError, match="Item ID 69"):
        validator.assert_selected_records(snapshot, {69: (8, 9)})


def test_unavailable_snapshot_is_success_with_zero_records() -> None:
    snapshot = Prime3WiiInventorySnapshot(
        availability_flags=Prime3WiiInventoryAvailability.TEMPORARILY_UNAVAILABLE,
        snapshot_sequence=0xFFFFFFFF,
    )
    decoded = validator.decode_inventory_response(_packet(snapshot), 5)
    assert not decoded.is_available
    assert all(record == Prime3WiiInventoryRecord(0, 0) for record in decoded.records)


@pytest.mark.parametrize(("offset", "value"), [(0, 2), (1, 58), (2, 12), (3, 1)])
def test_decode_rejects_wrong_inventory_header(offset: int, value: int) -> None:
    payload = bytearray(encode_inventory_payload(Prime3WiiInventorySnapshot()))
    payload[offset] = value
    packet = encode_response(
        Prime3WiiResponse(Prime3WiiCommand.GET_INVENTORY, 5, Prime3WiiResponseStatus.OK, bytes(payload))
    )
    with pytest.raises(Prime3WiiProtocolError):
        validator.decode_inventory_response(packet, 5)


def test_decode_rejects_wrong_payload_length_command_status_and_request_id() -> None:
    snapshot = Prime3WiiInventorySnapshot()
    short = encode_response(
        Prime3WiiResponse(
            Prime3WiiCommand.GET_INVENTORY,
            5,
            Prime3WiiResponseStatus.OK,
            encode_inventory_payload(snapshot)[: INVENTORY_PAYLOAD_SIZE - 1],
        )
    )
    with pytest.raises(ValueError, match="payload bytes"):
        validator.decode_inventory_response(short, 5)
    with pytest.raises(Prime3WiiProtocolError):
        validator.decode_inventory_response(_packet(snapshot, request_id=6), 5)
    wrong_command = encode_response(Prime3WiiResponse(Prime3WiiCommand.PING, 5, Prime3WiiResponseStatus.OK, b""))
    with pytest.raises(ValueError, match="command or status"):
        validator.decode_inventory_response(wrong_command, 5)


def test_sequence_wrap_and_capability_omission_shape() -> None:
    first = Prime3WiiInventorySnapshot(snapshot_sequence=0xFFFFFFFF)
    wrapped = Prime3WiiInventorySnapshot(snapshot_sequence=0)
    assert validator.decode_inventory_response(_packet(first), 5).snapshot_sequence == 0xFFFFFFFF
    assert validator.decode_inventory_response(_packet(wrapped), 5).snapshot_sequence == 0
    omission = validator.build_capability_omission_scenarios()
    assert len(omission) == 2
    assert omission[-1].expected == "capability_not_negotiated"
