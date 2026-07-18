"""
Version 1 UDP protocol used by Corruptovania to communicate with Metroid Prime 3 Wii.

Version 1 preserves a fixed CP3W packet framing layer and currently defines
deterministic HELLO negotiation, PING, READ_MEMORY, and DISCONNECT command
families. Arbitrary memory writes and gameplay mailbox traffic remain deferred.

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
HELLO_REQUEST_FIXED_FORMAT = ">BBII"
HELLO_RESPONSE_FIXED_FORMAT = ">BIIIIBB"
READ_MEMORY_PAYLOAD_FORMAT = ">II"
ERROR_HEADER_FORMAT = ">HHH"
HELLO_NAME_LENGTH_FORMAT = ">B"
HELLO_REQUEST_FIXED_SIZE = struct.calcsize(HELLO_REQUEST_FIXED_FORMAT)
HELLO_RESPONSE_FIXED_SIZE = struct.calcsize(HELLO_RESPONSE_FIXED_FORMAT)
HELLO_NAME_LENGTH_SIZE = struct.calcsize(HELLO_NAME_LENGTH_FORMAT)
HELLO_MAX_NAME_LENGTH = 31
HELLO_METADATA_VERSION = 1
DEFAULT_RUNTIME_NAME = "Prime3 Wii Runtime"
DEFAULT_RUNTIME_BUILD_ID = 0x50335731
NOT_NEGOTIATED_MESSAGE = "Negotiation required before PING."
UNSUPPORTED_VERSION_MESSAGE = "Unsupported protocol version range."
INVALID_STATE_MESSAGE = "Session is already negotiated."
UNKNOWN_COMMAND_MESSAGE = "Command is unsupported"


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
    HELLO_NEGOTIATION = 1 << 0
    PING = 1 << 1
    STRUCTURED_ERRORS = 1 << 2
    DETERMINISTIC_SESSION_ID = 1 << 3
    READ_MEMORY = 1 << 4
    STRUCTURED_MAILBOX = 1 << 5
    MEMORY_WRITE = 1 << 6
    GAMEPLAY_MAILBOX = 1 << 7
    EVENT_STREAMING = 1 << 8
    RECONNECT = 1 << 9
    AUTHENTICATION = 1 << 10


HELLO_RUNTIME_CAPABILITIES = (
    Prime3WiiCapability.HELLO_NEGOTIATION
    | Prime3WiiCapability.PING
    | Prime3WiiCapability.STRUCTURED_ERRORS
    | Prime3WiiCapability.DETERMINISTIC_SESSION_ID
)

READ_ONLY_RUNTIME_CAPABILITIES = HELLO_RUNTIME_CAPABILITIES | Prime3WiiCapability.READ_MEMORY


class Prime3WiiErrorCode(enum.IntEnum):
    MALFORMED_PACKET = 1
    BAD_MAGIC = 2
    UNSUPPORTED_VERSION = 3
    UNKNOWN_COMMAND = 4
    INVALID_PAYLOAD_LENGTH = 5
    CHECKSUM_MISMATCH = 6
    INVALID_ADDRESS = 7
    SERVER_ERROR = 8
    NOT_NEGOTIATED = 9
    INVALID_STATE = 10


@dataclasses.dataclass(frozen=True)
class HelloRequestPayload:
    min_protocol_version: int
    max_protocol_version: int
    capabilities: Prime3WiiCapability
    client_nonce: int
    client_name: str = ""


@dataclasses.dataclass(frozen=True)
class HelloResponsePayload:
    selected_protocol_version: int
    runtime_capabilities: Prime3WiiCapability
    accepted_client_capabilities: Prime3WiiCapability
    session_id: int
    runtime_build_id: int
    runtime_mode: int
    runtime_metadata_version: int = HELLO_METADATA_VERSION
    runtime_name: str = DEFAULT_RUNTIME_NAME


HelloPayload = HelloResponsePayload


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


def crc32_bytes(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def _validate_u8(value: int, label: str) -> None:
    if value < 0 or value > 0xFF:
        raise InvalidPayloadLengthError(f"{label} must fit in uint8, got {value}.")


def _validate_u32(value: int, label: str) -> None:
    if value < 0 or value > 0xFFFFFFFF:
        raise InvalidPayloadLengthError(f"{label} must fit in uint32, got {value}.")


def _encode_bounded_name(name: str, *, field_name: str) -> bytes:
    encoded = name.encode("utf-8")
    if len(encoded) > HELLO_MAX_NAME_LENGTH:
        raise InvalidPayloadLengthError(
            f"{field_name} must be at most {HELLO_MAX_NAME_LENGTH} UTF-8 bytes, got {len(encoded)}."
        )
    return struct.pack(HELLO_NAME_LENGTH_FORMAT, len(encoded)) + encoded


def _decode_bounded_name(payload: bytes, *, offset: int, field_name: str) -> tuple[str, int]:
    if len(payload) < offset + HELLO_NAME_LENGTH_SIZE:
        raise InvalidPayloadLengthError(f"{field_name} payload is missing the name-length field.")
    (name_length,) = struct.unpack(HELLO_NAME_LENGTH_FORMAT, payload[offset : offset + HELLO_NAME_LENGTH_SIZE])
    start = offset + HELLO_NAME_LENGTH_SIZE
    end = start + name_length
    if end != len(payload):
        raise InvalidPayloadLengthError(
            f"{field_name} payload length mismatch: expected trailing name bytes {name_length}, "
            f"got {len(payload) - start}."
        )
    if name_length > HELLO_MAX_NAME_LENGTH:
        raise InvalidPayloadLengthError(
            f"{field_name} name must be at most {HELLO_MAX_NAME_LENGTH} bytes, got {name_length}."
        )
    try:
        return payload[start:end].decode("utf-8"), name_length
    except UnicodeDecodeError as exc:
        raise InvalidPayloadLengthError(f"{field_name} name is not valid UTF-8.") from exc


def negotiate_protocol_version(payload: HelloRequestPayload) -> int | None:
    if payload.min_protocol_version > payload.max_protocol_version:
        return None
    if payload.min_protocol_version <= PROTOCOL_VERSION <= payload.max_protocol_version:
        return PROTOCOL_VERSION
    return None


def compute_accepted_capabilities(
    client_capabilities: Prime3WiiCapability,
    runtime_capabilities: Prime3WiiCapability,
) -> Prime3WiiCapability:
    return Prime3WiiCapability(int(client_capabilities) & int(runtime_capabilities))


def derive_session_id(
    *,
    selected_protocol_version: int,
    client_nonce: int,
    runtime_build_id: int,
    runtime_capabilities: Prime3WiiCapability,
    accepted_client_capabilities: Prime3WiiCapability,
) -> int:
    _validate_u8(selected_protocol_version, "selected_protocol_version")
    _validate_u32(client_nonce, "client_nonce")
    _validate_u32(runtime_build_id, "runtime_build_id")
    canonical = struct.pack(
        ">BIIII",
        selected_protocol_version,
        client_nonce,
        int(runtime_build_id),
        int(runtime_capabilities),
        int(accepted_client_capabilities),
    )
    return crc32_bytes(canonical)


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
    checksum = crc32_bytes(body)
    return body + struct.pack(">I", checksum)


def _decode_packet(
    packet: bytes,
) -> tuple[Prime3WiiPacketKind, Prime3WiiCommand, Prime3WiiResponseStatus, int, bytes]:
    if len(packet) < HEADER_SIZE + CRC_SIZE:
        raise InvalidPayloadLengthError("Packet shorter than minimum header size")

    payload_end = len(packet) - CRC_SIZE
    body = packet[:payload_end]
    actual_crc = crc32_bytes(body)
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


def encode_hello_request_payload(payload: HelloRequestPayload) -> bytes:
    _validate_u8(payload.min_protocol_version, "min_protocol_version")
    _validate_u8(payload.max_protocol_version, "max_protocol_version")
    _validate_u32(payload.client_nonce, "client_nonce")
    name_bytes = _encode_bounded_name(payload.client_name, field_name="HELLO request")
    return (
        struct.pack(
            HELLO_REQUEST_FIXED_FORMAT,
            payload.min_protocol_version,
            payload.max_protocol_version,
            int(payload.capabilities),
            payload.client_nonce,
        )
        + name_bytes
    )


def decode_hello_request_payload(payload: bytes) -> HelloRequestPayload:
    if len(payload) < HELLO_REQUEST_FIXED_SIZE + HELLO_NAME_LENGTH_SIZE:
        raise InvalidPayloadLengthError(
            f"HELLO request payload must be at least {HELLO_REQUEST_FIXED_SIZE + HELLO_NAME_LENGTH_SIZE} bytes, "
            f"got {len(payload)}"
        )
    min_protocol_version, max_protocol_version, capabilities, client_nonce = struct.unpack(
        HELLO_REQUEST_FIXED_FORMAT, payload[:HELLO_REQUEST_FIXED_SIZE]
    )
    client_name, _ = _decode_bounded_name(payload, offset=HELLO_REQUEST_FIXED_SIZE, field_name="HELLO request")
    return HelloRequestPayload(
        min_protocol_version=min_protocol_version,
        max_protocol_version=max_protocol_version,
        capabilities=Prime3WiiCapability(capabilities),
        client_nonce=client_nonce,
        client_name=client_name,
    )


def encode_hello_response_payload(payload: HelloResponsePayload) -> bytes:
    _validate_u8(payload.selected_protocol_version, "selected_protocol_version")
    _validate_u32(payload.session_id, "session_id")
    _validate_u32(payload.runtime_build_id, "runtime_build_id")
    _validate_u8(payload.runtime_mode, "runtime_mode")
    _validate_u8(payload.runtime_metadata_version, "runtime_metadata_version")
    name_bytes = _encode_bounded_name(payload.runtime_name, field_name="HELLO response")
    return (
        struct.pack(
            HELLO_RESPONSE_FIXED_FORMAT,
            payload.selected_protocol_version,
            int(payload.runtime_capabilities),
            int(payload.accepted_client_capabilities),
            payload.session_id,
            payload.runtime_build_id,
            payload.runtime_mode,
            payload.runtime_metadata_version,
        )
        + name_bytes
    )


def decode_hello_response_payload(payload: bytes) -> HelloResponsePayload:
    if len(payload) < HELLO_RESPONSE_FIXED_SIZE + HELLO_NAME_LENGTH_SIZE:
        raise InvalidPayloadLengthError(
            f"HELLO response payload must be at least {HELLO_RESPONSE_FIXED_SIZE + HELLO_NAME_LENGTH_SIZE} bytes, "
            f"got {len(payload)}"
        )
    (
        selected_protocol_version,
        runtime_capabilities,
        accepted_client_capabilities,
        session_id,
        runtime_build_id,
        runtime_mode,
        runtime_metadata_version,
    ) = struct.unpack(HELLO_RESPONSE_FIXED_FORMAT, payload[:HELLO_RESPONSE_FIXED_SIZE])
    runtime_name, _ = _decode_bounded_name(payload, offset=HELLO_RESPONSE_FIXED_SIZE, field_name="HELLO response")
    return HelloResponsePayload(
        selected_protocol_version=selected_protocol_version,
        runtime_capabilities=Prime3WiiCapability(runtime_capabilities),
        accepted_client_capabilities=Prime3WiiCapability(accepted_client_capabilities),
        session_id=session_id,
        runtime_build_id=runtime_build_id,
        runtime_mode=runtime_mode,
        runtime_metadata_version=runtime_metadata_version,
        runtime_name=runtime_name,
    )


def encode_hello_payload(payload: HelloPayload) -> bytes:
    return encode_hello_response_payload(payload)


def decode_hello_payload(payload: bytes) -> HelloPayload:
    return decode_hello_response_payload(payload)


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
