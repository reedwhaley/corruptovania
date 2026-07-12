"""
Version 1 UDP protocol used by Corruptovania to read Metroid Prime 3 Wii memory.

Version 1 is intentionally read-only. It supports HELLO negotiation, PING,
READ_MEMORY, and DISCONNECT, and reserves a future structured mailbox command
for bidirectional gameplay communication. Arbitrary memory writes are not part
of this protocol.

Packet format, big-endian:

- magic: 4 bytes, ASCII ``CP3W``
- protocol_version: uint8
- packet_kind: uint8
- command: uint8
- response_status: uint8
- request_id: uint32
- payload_length: uint32
- payload: ``payload_length`` bytes
- crc32: uint32 over every previous byte in the packet
"""

from __future__ import annotations

import dataclasses
import enum
import struct
import zlib

PROTOCOL_MAGIC = b"CP3W"
PROTOCOL_VERSION = 1
HEADER_FORMAT = ">4sBBBBII"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
CRC_SIZE = 4
HELLO_PAYLOAD_FORMAT = ">HII"
READ_MEMORY_PAYLOAD_FORMAT = ">II"
ERROR_HEADER_FORMAT = ">HHH"


class Prime3WiiProtocolError(Exception):
    pass


class MalformedPacketError(Prime3WiiProtocolError):
    pass


class BadMagicError(MalformedPacketError):
    pass


class UnsupportedProtocolVersionError(MalformedPacketError):
    pass


class UnknownCommandError(MalformedPacketError):
    pass


class InvalidPayloadLengthError(MalformedPacketError):
    pass


class CorruptedChecksumError(MalformedPacketError):
    pass


class MismatchedRequestIdError(Prime3WiiProtocolError):
    pass


class ServerSideProtocolError(Prime3WiiProtocolError):
    def __init__(self, error_code: Prime3WiiErrorCode, message: str, command: Prime3WiiCommand):
        super().__init__(f"{error_code.name} for {command.name}: {message}")
        self.error_code = error_code
        self.message = message
        self.command = command


class Prime3WiiPacketKind(enum.IntEnum):
    REQUEST = 1
    RESPONSE = 2


class Prime3WiiCommand(enum.IntEnum):
    HELLO = 1
    READ_MEMORY = 2
    PING = 3
    DISCONNECT = 4
    RESERVED_MAILBOX = 127


class Prime3WiiResponseStatus(enum.IntEnum):
    OK = 0
    ERROR = 1


class Prime3WiiCapability(enum.IntFlag):
    READ_MEMORY = 1 << 0
    STRUCTURED_MAILBOX = 1 << 1


class Prime3WiiErrorCode(enum.IntEnum):
    MALFORMED_PACKET = 1
    BAD_MAGIC = 2
    UNSUPPORTED_VERSION = 3
    UNKNOWN_COMMAND = 4
    INVALID_PAYLOAD_LENGTH = 5
    CHECKSUM_MISMATCH = 6
    INVALID_ADDRESS = 7
    SERVER_ERROR = 8


@dataclasses.dataclass(frozen=True)
class HelloPayload:
    protocol_version: int
    max_read_size: int
    capabilities: Prime3WiiCapability


@dataclasses.dataclass(frozen=True)
class ReadMemoryPayload:
    address: int
    size: int


@dataclasses.dataclass(frozen=True)
class Prime3WiiRequest:
    command: Prime3WiiCommand
    request_id: int
    payload: bytes = b""


@dataclasses.dataclass(frozen=True)
class Prime3WiiResponse:
    command: Prime3WiiCommand
    request_id: int
    status: Prime3WiiResponseStatus
    payload: bytes = b""


@dataclasses.dataclass(frozen=True)
class Prime3WiiErrorResponse:
    command: Prime3WiiCommand
    request_id: int
    error_code: Prime3WiiErrorCode
    message: str


def _encode_packet(
    packet_kind: Prime3WiiPacketKind,
    command: Prime3WiiCommand,
    response_status: Prime3WiiResponseStatus,
    request_id: int,
    payload: bytes,
) -> bytes:
    header = struct.pack(
        HEADER_FORMAT,
        PROTOCOL_MAGIC,
        PROTOCOL_VERSION,
        packet_kind,
        command,
        response_status,
        request_id,
        len(payload),
    )
    body = header + payload
    checksum = zlib.crc32(body) & 0xFFFFFFFF
    return body + struct.pack(">I", checksum)


def _decode_packet(
    packet: bytes,
) -> tuple[Prime3WiiPacketKind, Prime3WiiCommand, Prime3WiiResponseStatus, int, bytes]:
    if len(packet) < HEADER_SIZE + CRC_SIZE:
        raise InvalidPayloadLengthError("Packet shorter than minimum header size")

    payload_end = len(packet) - CRC_SIZE
    body = packet[:payload_end]
    actual_crc = zlib.crc32(body) & 0xFFFFFFFF
    expected_crc = struct.unpack(">I", packet[payload_end:])[0]
    if actual_crc != expected_crc:
        raise CorruptedChecksumError("CRC32 mismatch")

    magic, version, packet_kind_raw, command_raw, response_status_raw, request_id, payload_length = struct.unpack(
        HEADER_FORMAT, packet[:HEADER_SIZE]
    )

    if magic != PROTOCOL_MAGIC:
        raise BadMagicError(f"Unexpected magic {magic!r}")
    if version != PROTOCOL_VERSION:
        raise UnsupportedProtocolVersionError(f"Unsupported protocol version {version}")

    try:
        packet_kind = Prime3WiiPacketKind(packet_kind_raw)
    except ValueError as e:
        raise MalformedPacketError(f"Unknown packet kind {packet_kind_raw}") from e

    try:
        command = Prime3WiiCommand(command_raw)
    except ValueError as e:
        raise UnknownCommandError(f"Unknown command {command_raw}") from e

    try:
        response_status = Prime3WiiResponseStatus(response_status_raw)
    except ValueError as e:
        raise MalformedPacketError(f"Unknown response status {response_status_raw}") from e

    actual_payload = packet[HEADER_SIZE:payload_end]
    if len(actual_payload) != payload_length:
        raise InvalidPayloadLengthError(
            f"Payload length mismatch: header says {payload_length}, packet contains {len(actual_payload)}"
        )

    return packet_kind, command, response_status, request_id, actual_payload


def encode_request(request: Prime3WiiRequest) -> bytes:
    return _encode_packet(
        Prime3WiiPacketKind.REQUEST,
        request.command,
        Prime3WiiResponseStatus.OK,
        request.request_id,
        request.payload,
    )


def decode_request(packet: bytes) -> Prime3WiiRequest:
    packet_kind, command, response_status, request_id, payload = _decode_packet(packet)
    if packet_kind is not Prime3WiiPacketKind.REQUEST:
        raise MalformedPacketError(f"Expected request packet, got {packet_kind.name}")
    if response_status is not Prime3WiiResponseStatus.OK:
        raise MalformedPacketError("Requests must use response status OK")
    return Prime3WiiRequest(command=command, request_id=request_id, payload=payload)


def encode_response(response: Prime3WiiResponse) -> bytes:
    return _encode_packet(
        Prime3WiiPacketKind.RESPONSE,
        response.command,
        response.status,
        response.request_id,
        response.payload,
    )


def decode_response(
    packet: bytes,
    *,
    expected_request_id: int | None = None,
) -> Prime3WiiResponse | Prime3WiiErrorResponse:
    packet_kind, command, response_status, request_id, payload = _decode_packet(packet)
    if packet_kind is not Prime3WiiPacketKind.RESPONSE:
        raise MalformedPacketError(f"Expected response packet, got {packet_kind.name}")
    if expected_request_id is not None and request_id != expected_request_id:
        raise MismatchedRequestIdError(f"Expected request id {expected_request_id}, got {request_id}")

    if response_status is Prime3WiiResponseStatus.ERROR:
        return decode_error_response_payload(command, request_id, payload)

    return Prime3WiiResponse(command=command, request_id=request_id, status=response_status, payload=payload)


def encode_hello_payload(payload: HelloPayload) -> bytes:
    return struct.pack(
        HELLO_PAYLOAD_FORMAT,
        payload.protocol_version,
        payload.max_read_size,
        int(payload.capabilities),
    )


def decode_hello_payload(payload: bytes) -> HelloPayload:
    expected_size = struct.calcsize(HELLO_PAYLOAD_FORMAT)
    if len(payload) != expected_size:
        raise InvalidPayloadLengthError(f"HELLO payload must be {expected_size} bytes, got {len(payload)}")
    protocol_version, max_read_size, capabilities = struct.unpack(HELLO_PAYLOAD_FORMAT, payload)
    return HelloPayload(
        protocol_version=protocol_version,
        max_read_size=max_read_size,
        capabilities=Prime3WiiCapability(capabilities),
    )


def encode_read_memory_payload(payload: ReadMemoryPayload) -> bytes:
    return struct.pack(READ_MEMORY_PAYLOAD_FORMAT, payload.address, payload.size)


def decode_read_memory_payload(payload: bytes) -> ReadMemoryPayload:
    expected_size = struct.calcsize(READ_MEMORY_PAYLOAD_FORMAT)
    if len(payload) != expected_size:
        raise InvalidPayloadLengthError(f"READ_MEMORY payload must be {expected_size} bytes, got {len(payload)}")
    address, size = struct.unpack(READ_MEMORY_PAYLOAD_FORMAT, payload)
    return ReadMemoryPayload(address=address, size=size)


def encode_error_response(
    command: Prime3WiiCommand,
    request_id: int,
    error_code: Prime3WiiErrorCode,
    message: str,
) -> bytes:
    message_bytes = message.encode("utf-8")
    payload = struct.pack(ERROR_HEADER_FORMAT, error_code, command, len(message_bytes)) + message_bytes
    return encode_response(
        Prime3WiiResponse(
            command=command,
            request_id=request_id,
            status=Prime3WiiResponseStatus.ERROR,
            payload=payload,
        )
    )


def decode_error_response_payload(
    command: Prime3WiiCommand,
    request_id: int,
    payload: bytes,
) -> Prime3WiiErrorResponse:
    minimum_size = struct.calcsize(ERROR_HEADER_FORMAT)
    if len(payload) < minimum_size:
        raise InvalidPayloadLengthError("Error payload shorter than minimum size")

    error_code_raw, command_raw, message_length = struct.unpack(ERROR_HEADER_FORMAT, payload[:minimum_size])
    message_bytes = payload[minimum_size:]
    if len(message_bytes) != message_length:
        raise InvalidPayloadLengthError(
            f"Error payload length mismatch: header says {message_length}, packet contains {len(message_bytes)}"
        )
    try:
        error_code = Prime3WiiErrorCode(error_code_raw)
    except ValueError as e:
        raise MalformedPacketError(f"Unknown error code {error_code_raw}") from e

    try:
        payload_command = Prime3WiiCommand(command_raw)
    except ValueError as e:
        raise UnknownCommandError(f"Unknown error payload command {command_raw}") from e

    if payload_command is not command:
        raise MalformedPacketError(
            f"Error payload command {payload_command.name} does not match response command {command.name}"
        )

    return Prime3WiiErrorResponse(
        command=command,
        request_id=request_id,
        error_code=error_code,
        message=message_bytes.decode("utf-8"),
    )
