import socket
import struct
import threading

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
    Prime3TrackerService,
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


def test_tcp_listener_starts_without_a_wii_ip_or_legacy_udp_connector():
    service = Prime3TrackerService(
        {"enabled": True, "bind_host": "127.0.0.1", "bind_port": 0},
        Prime3TrackerAdapter(),
    )
    try:
        assert service.status() == {
            "listening": False,
            "status": "waiting",
            "status_message": "Waiting for Wii connection",
            "active_connections": 0,
            "bind_host": None,
            "bind_port": None,
        }
        service.start()
        assert service.status()["listening"] is True
        assert service.status()["status_message"] == "Waiting for Wii connection"
        assert service.status()["bind_host"] == "127.0.0.1"
        assert service.status()["bind_port"] != 43674
    finally:
        service.stop()


def test_disabled_tracker_service_does_not_start_a_listener():
    service = Prime3TrackerService(
        {"enabled": False, "bind_host": "127.0.0.1", "bind_port": 43674}, Prime3TrackerAdapter()
    )

    service.start()

    assert service.status()["listening"] is False


def test_inbound_tcp_hello_attaches_tracker_session_and_accepts_snapshot():
    adapter = Prime3TrackerAdapter()
    service = Prime3TrackerService({"idle_timeout_seconds": 1}, adapter)
    server_socket, wii_socket = socket.socketpair()
    thread = threading.Thread(target=service.handle_socket, args=(server_socket, ("192.168.50.19", 43674)))
    thread.start()
    try:
        wii_socket.sendall(_hello().encode())
        assert Prime3TrackerFrame.decode(wii_socket.recv(64)).message_type == SERVER_HELLO_ACK
        assert service.status()["status"] == "connected"

        wii_socket.sendall(_frame(TRACKER_SNAPSHOT, 2, [7, 0, 1, 99, 1, 8, 10, 20]).encode())
        assert Prime3TrackerFrame.decode(wii_socket.recv(64)).message_type == TRACKER_ACK
        status = adapter.session_status(0x43503357)
        assert status is not None
        assert status["last_snapshot_id"] == 7
        assert status["tracker_words"] == (10, 20)
    finally:
        wii_socket.close()
        thread.join(timeout=1)
        server_socket.close()
    assert service.status()["status"] == "waiting"
