"""Bounded CP3W TCP tracker service for read-only Prime 3 telemetry."""

from __future__ import annotations

import binascii
import dataclasses
import logging
import socketserver
import struct
import threading
import time
from typing import TYPE_CHECKING, Final, cast

if TYPE_CHECKING:
    import socket
    from collections.abc import Callable

FRAME_SIZE: Final = 64
PAYLOAD_SIZE: Final = 36
MAGIC: Final = b"CP3W"
VERSION: Final = 1
CLIENT_HELLO: Final = 0x01
SERVER_HELLO_ACK: Final = 0x02
TRACKER_SNAPSHOT: Final = 0x20
TRACKER_DELTA: Final = 0x21
TRACKER_ACK: Final = 0x22
TRACKER_RESYNC_REQUEST: Final = 0x23
ERROR: Final = 0x7F
STATUS_OK: Final = 0
STATUS_RESYNC: Final = 1
MAX_CHUNKS: Final = 16
HEADER: Final = struct.Struct(">4sBBHIIII")


class Prime3TrackerProtocolError(ValueError):
    """A peer sent a frame that cannot update tracker state."""


@dataclasses.dataclass(frozen=True)
class Prime3TrackerFrame:
    message_type: int
    sequence: int
    acknowledgement: int
    payload_length: int
    flags: int
    payload: bytes

    def encode(self) -> bytes:
        if len(self.payload) > PAYLOAD_SIZE or self.payload_length != len(self.payload):
            raise Prime3TrackerProtocolError("invalid tracker payload length")
        raw = bytearray(
            HEADER.pack(
                MAGIC,
                VERSION,
                self.message_type,
                FRAME_SIZE,
                self.sequence,
                self.acknowledgement,
                self.payload_length,
                self.flags,
            )
        )
        raw.extend(self.payload)
        raw.extend(bytes(PAYLOAD_SIZE - len(self.payload)))
        raw.extend(struct.pack(">I", binascii.crc32(raw) & 0xFFFFFFFF))
        return bytes(raw)

    @classmethod
    def decode(cls, raw: bytes) -> Prime3TrackerFrame:
        if len(raw) != FRAME_SIZE:
            raise Prime3TrackerProtocolError("invalid tracker frame length")
        magic, version, message_type, length, sequence, acknowledgement, payload_length, flags = HEADER.unpack(raw[:24])
        if magic != MAGIC or version != VERSION or length != FRAME_SIZE:
            raise Prime3TrackerProtocolError("unsupported tracker envelope")
        if payload_length > PAYLOAD_SIZE:
            raise Prime3TrackerProtocolError("tracker payload exceeds frame")
        if struct.unpack(">I", raw[60:64])[0] != binascii.crc32(raw[:60]) & 0xFFFFFFFF:
            raise Prime3TrackerProtocolError("invalid tracker CRC")
        return cls(message_type, sequence, acknowledgement, payload_length, flags, raw[24 : 24 + payload_length])


@dataclasses.dataclass
class Prime3TrackerSession:
    client_nonce: int
    build_id: int
    capabilities: int
    seed_id: int = 0
    connected: bool = True
    last_update: float = dataclasses.field(default_factory=time.time)
    last_snapshot_id: int = 0
    last_delta_id: int = 0
    last_client_sequence: int = 0
    server_sequence: int = 1
    pending_snapshot_id: int = 0
    pending_chunk_count: int = 0
    pending_chunks: dict[int, bytes] = dataclasses.field(default_factory=dict)
    tracker_words: tuple[int, ...] = ()
    last_error: str | None = None


class Prime3TrackerAdapter:
    """Owns tracker sessions and only publishes complete, validated state."""

    def __init__(
        self,
        publisher: Callable[[dict[str, object]], None] | None = None,
        session_binder: Callable[[Prime3TrackerSession], bool] | None = None,
    ):
        self._publisher = publisher or (lambda _event: None)
        self._session_binder = session_binder
        self._sessions: dict[int, Prime3TrackerSession] = {}
        self._lock = threading.Lock()

    def session_status(self, client_nonce: int) -> dict[str, object] | None:
        with self._lock:
            session = self._sessions.get(client_nonce)
            return None if session is None else self._status(session)

    def handle_hello(self, frame: Prime3TrackerFrame) -> tuple[Prime3TrackerSession, Prime3TrackerFrame]:
        if frame.message_type != CLIENT_HELLO or frame.payload_length != PAYLOAD_SIZE:
            raise Prime3TrackerProtocolError("expected complete CLIENT_HELLO")
        words = struct.unpack(">9I", frame.payload)
        game_id, build_id, capabilities, nonce = words[:4]
        if game_id != 0x524D3345:
            raise Prime3TrackerProtocolError("unsupported game id")
        with self._lock:
            prior = self._sessions.get(nonce)
            if prior is not None and prior.connected:
                raise Prime3TrackerProtocolError("duplicate active tracker session")
            session = Prime3TrackerSession(nonce, build_id, capabilities)
            session.last_client_sequence = frame.sequence
            if self._session_binder is not None and not self._session_binder(session):
                raise Prime3TrackerProtocolError("no unambiguous Prime 3 tracker connection")
            self._sessions[nonce] = session
        self._publish(session)
        return session, self._response(
            session,
            SERVER_HELLO_ACK,
            frame.sequence,
            [nonce, 0x53525631, STATUS_OK, 0, capabilities, VERSION, 60],
        )

    def apply_snapshot(self, session: Prime3TrackerSession, frame: Prime3TrackerFrame) -> Prime3TrackerFrame | None:
        if frame.payload_length < 24:
            raise Prime3TrackerProtocolError("short tracker snapshot")
        snapshot_id, chunk_index, chunk_count, seed_id, schema_version, data_length = struct.unpack(
            ">6I", frame.payload[:24]
        )
        if schema_version != VERSION or chunk_count == 0 or chunk_count > MAX_CHUNKS or chunk_index >= chunk_count:
            return self._resync(session, frame.sequence, "invalid snapshot metadata")
        if data_length > PAYLOAD_SIZE - 24 or data_length % 4:
            return self._resync(session, frame.sequence, "invalid snapshot data length")
        if snapshot_id < session.last_snapshot_id:
            return self._resync(session, frame.sequence, "stale snapshot")
        if session.pending_snapshot_id not in (0, snapshot_id):
            return self._resync(session, frame.sequence, "inconsistent snapshot")
        if session.pending_chunks.get(chunk_index) not in (None, frame.payload[24 : 24 + data_length]):
            return self._resync(session, frame.sequence, "conflicting snapshot chunk")
        session.pending_snapshot_id = snapshot_id
        session.pending_chunk_count = chunk_count
        session.seed_id = seed_id
        session.pending_chunks[chunk_index] = frame.payload[24 : 24 + data_length]
        session.last_client_sequence = frame.sequence
        session.last_update = time.time()
        if len(session.pending_chunks) != chunk_count:
            return None
        session.tracker_words = tuple(
            value
            for index in range(chunk_count)
            for value in struct.unpack(f">{len(session.pending_chunks[index]) // 4}I", session.pending_chunks[index])
        )
        session.last_snapshot_id = snapshot_id
        session.pending_snapshot_id = 0
        session.pending_chunk_count = 0
        session.pending_chunks.clear()
        self._publish(session)
        return self._response(
            session,
            TRACKER_ACK,
            frame.sequence,
            [snapshot_id, session.last_delta_id, VERSION, STATUS_OK],
        )

    def apply_delta(self, session: Prime3TrackerSession, frame: Prime3TrackerFrame) -> Prime3TrackerFrame:
        if frame.payload_length < 20:
            return self._resync(session, frame.sequence, "short delta")
        snapshot_id, delta_id, field_id, new_value, _flags = struct.unpack(">5I", frame.payload[:20])
        if snapshot_id != session.last_snapshot_id or delta_id < session.last_delta_id:
            return self._resync(session, frame.sequence, "out of order delta")
        if delta_id == session.last_delta_id:
            return self._response(session, TRACKER_ACK, frame.sequence, [snapshot_id, delta_id, VERSION, STATUS_OK])
        if delta_id != session.last_delta_id + 1:
            return self._resync(session, frame.sequence, "out of order delta")
        if field_id >= len(session.tracker_words):
            return self._resync(session, frame.sequence, "unknown tracker field")
        values = list(session.tracker_words)
        values[field_id] = new_value
        session.tracker_words = tuple(values)
        session.last_delta_id = delta_id
        session.last_client_sequence = frame.sequence
        session.last_update = time.time()
        self._publish(session)
        return self._response(session, TRACKER_ACK, frame.sequence, [snapshot_id, delta_id, VERSION, STATUS_OK])

    def disconnect(self, session: Prime3TrackerSession, reason: str | None = None) -> None:
        with self._lock:
            session.connected = False
            session.last_error = reason
            session.last_update = time.time()
        self._publish(session)

    def _response(
        self, session: Prime3TrackerSession, message_type: int, acknowledgement: int, words: list[int]
    ) -> Prime3TrackerFrame:
        payload = struct.pack(f">{len(words)}I", *words)
        frame = Prime3TrackerFrame(message_type, session.server_sequence, acknowledgement, len(payload), 0, payload)
        session.server_sequence += 1
        return frame

    def _resync(self, session: Prime3TrackerSession, acknowledgement: int, error: str) -> Prime3TrackerFrame:
        session.last_error = error
        session.pending_snapshot_id = 0
        session.pending_chunks.clear()
        return self._response(session, TRACKER_RESYNC_REQUEST, acknowledgement, [VERSION, STATUS_RESYNC])

    def _status(self, session: Prime3TrackerSession) -> dict[str, object]:
        return {
            "connected": session.connected,
            "last_update": session.last_update,
            "last_snapshot_id": session.last_snapshot_id,
            "last_delta_id": session.last_delta_id,
            "protocol_version": VERSION,
            "game_build_id": session.build_id,
            "seed_id": session.seed_id,
            "last_error": session.last_error,
            "tracker_words": session.tracker_words,
        }

    def _publish(self, session: Prime3TrackerSession) -> None:
        self._publisher({"client_nonce": session.client_nonce, **self._status(session)})


class _Prime3TrackerRequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        service: Prime3TrackerService = self.server.service  # type: ignore[attr-defined]
        service.handle_socket(self.request, self.client_address)


class _Prime3TrackerTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class Prime3TrackerService:
    def __init__(self, configuration: dict[str, object], adapter: Prime3TrackerAdapter):
        self._configuration = configuration
        self._adapter = adapter
        self._server: _Prime3TrackerTCPServer | None = None
        self._thread: threading.Thread | None = None
        self._bind_host: str | None = None
        self._bind_port: int | None = None
        self._active_connections = 0
        self._connection_lock = threading.Lock()
        self._logger = logging.getLogger(type(self).__name__)

    def start(self) -> None:
        if not self._configuration.get("enabled", True) or self._server is not None:
            return
        host = str(self._configuration.get("bind_host", "0.0.0.0"))
        port = int(cast("int | str", self._configuration.get("bind_port", 43674)))
        self._server = _Prime3TrackerTCPServer((host, port), _Prime3TrackerRequestHandler)
        self._server.service = self  # type: ignore[attr-defined]
        self._bind_host, self._bind_port = self._server.server_address
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True, name="prime3-tracker")
        self._thread.start()
        self._logger.info("Prime 3 TCP tracker listening on %s:%s", self._bind_host, self._bind_port)
        self._logger.info("Waiting for inbound Prime 3 Wii connection")

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None
        self._bind_host = None
        self._bind_port = None

    def status(self) -> dict[str, object]:
        with self._connection_lock:
            active_connections = self._active_connections
        return {
            "listening": self._server is not None,
            "status": "connected" if active_connections else "waiting",
            "status_message": "Prime 3 Wii connected" if active_connections else "Waiting for Wii connection",
            "active_connections": active_connections,
            "bind_host": self._bind_host,
            "bind_port": self._bind_port,
        }

    def handle_socket(self, connection: socket.socket, address: tuple[str, int] | None = None) -> None:
        maximum_clients = int(cast("int | str", self._configuration.get("maximum_clients", 8)))
        with self._connection_lock:
            if self._active_connections >= maximum_clients:
                self._logger.warning("Rejecting Prime 3 Wii connection: client limit reached")
                return
            self._active_connections += 1
        connection.settimeout(float(cast("float | int | str", self._configuration.get("idle_timeout_seconds", 30))))
        session: Prime3TrackerSession | None = None
        try:
            self._logger.info("Prime 3 Wii connected from %s", address[0] if address else "unknown address")
            while True:
                raw = self._receive_exact(connection)
                if raw is None:
                    return
                frame = Prime3TrackerFrame.decode(raw)
                response: Prime3TrackerFrame | None
                if session is None:
                    session, response = self._adapter.handle_hello(frame)
                    self._logger.info("CLIENT_HELLO accepted")
                elif frame.sequence != session.last_client_sequence + 1:
                    response = self._adapter._resync(session, frame.sequence, "out of order sequence")
                elif frame.message_type == TRACKER_SNAPSHOT:
                    response = self._adapter.apply_snapshot(session, frame)
                    if response is not None and response.message_type == TRACKER_ACK:
                        self._logger.info("Tracker snapshot accepted")
                elif frame.message_type == TRACKER_DELTA:
                    response = self._adapter.apply_delta(session, frame)
                else:
                    raise Prime3TrackerProtocolError("unsupported tracker message")
                if response is not None:
                    connection.sendall(response.encode())
        except (ConnectionError, OSError, Prime3TrackerProtocolError) as error:
            self._logger.info("Prime 3 tracker connection closed: %s", error)
            if session is not None:
                self._adapter.disconnect(session, str(error))
        finally:
            if session is not None:
                self._adapter.disconnect(session)
            with self._connection_lock:
                self._active_connections -= 1
            self._logger.info("Waiting for inbound Prime 3 Wii connection")

    @staticmethod
    def _receive_exact(connection: socket.socket) -> bytes | None:
        data = bytearray()
        while len(data) < FRAME_SIZE:
            chunk = connection.recv(FRAME_SIZE - len(data))
            if not chunk:
                return None
            data.extend(chunk)
        return bytes(data)
