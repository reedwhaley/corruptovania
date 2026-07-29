import struct

import pytest

from randovania.server.prime3_tracker import (
    CLIENT_HELLO,
    SERVER_HELLO_ACK,
    STATUS_OK,
    TRACKER_ACK,
    TRACKER_DELTA,
    TRACKER_RESYNC_REQUEST,
    TRACKER_SNAPSHOT,
    Prime3TrackerAdapter,
    Prime3TrackerFrame,
    Prime3TrackerProtocolError,
)


def _frame(message_type: int, sequence: int, words: list[int]) -> Prime3TrackerFrame:
    payload = struct.pack(f">{len(words)}I", *words)
    return Prime3TrackerFrame(message_type, sequence, 0, len(payload), 0, payload)


def _hello(sequence: int = 1) -> Prime3TrackerFrame:
    return _frame(CLIENT_HELLO, sequence, [0x524D3345, 0x1234, 0xF, 0x43503357, 0, 0, 4, 4, 0])


def test_frame_round_trip_and_crc_validation():
    frame = _hello()
    assert Prime3TrackerFrame.decode(frame.encode()) == frame
    raw = bytearray(frame.encode())
    raw[24] ^= 1
    with pytest.raises(Prime3TrackerProtocolError, match="CRC"):
        Prime3TrackerFrame.decode(bytes(raw))


def test_hello_snapshot_delta_and_idempotency():
    events = []
    adapter = Prime3TrackerAdapter(events.append)
    session, ack = adapter.handle_hello(_hello())
    assert ack.message_type == SERVER_HELLO_ACK
    snapshot = _frame(TRACKER_SNAPSHOT, 2, [7, 0, 1, 99, 1, 8, 10, 20])
    response = adapter.apply_snapshot(session, snapshot)
    assert response is not None
    assert response.message_type == TRACKER_ACK
    assert struct.unpack(">4I", response.payload) == (7, 0, 1, STATUS_OK)
    delta = _frame(TRACKER_DELTA, 3, [7, 1, 1, 25, 0])
    assert adapter.apply_delta(session, delta).message_type == TRACKER_ACK
    assert adapter.apply_delta(session, delta).message_type == TRACKER_ACK
    assert adapter.session_status(session.client_nonce)["tracker_words"] == (10, 25)
    assert events


def test_snapshot_missing_or_conflicting_chunk_requests_resync():
    adapter = Prime3TrackerAdapter()
    session, _ = adapter.handle_hello(_hello())
    first = _frame(TRACKER_SNAPSHOT, 2, [8, 0, 2, 0, 1, 4, 1])
    assert adapter.apply_snapshot(session, first) is None
    conflict = _frame(TRACKER_SNAPSHOT, 3, [8, 0, 2, 0, 1, 4, 2])
    assert adapter.apply_snapshot(session, conflict).message_type == TRACKER_RESYNC_REQUEST


def test_out_of_order_delta_requests_resync():
    adapter = Prime3TrackerAdapter()
    session, _ = adapter.handle_hello(_hello())
    adapter.apply_snapshot(session, _frame(TRACKER_SNAPSHOT, 2, [1, 0, 1, 0, 1, 4, 10]))
    response = adapter.apply_delta(session, _frame(TRACKER_DELTA, 3, [1, 2, 0, 20, 0]))
    assert response.message_type == TRACKER_RESYNC_REQUEST
