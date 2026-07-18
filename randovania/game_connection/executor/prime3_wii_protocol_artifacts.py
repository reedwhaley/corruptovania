from __future__ import annotations

import dataclasses
import json
import struct
from typing import Any, Literal

from randovania.game_connection.executor import prime3_wii_protocol
from randovania.game_connection.executor.prime3_wii_protocol import (
    CRC_SIZE,
    DEFAULT_RUNTIME_BUILD_ID,
    DEFAULT_RUNTIME_NAME,
    ERROR_HEADER_FORMAT,
    GAME_IDENTITY_FIELD_OFFSETS,
    GAME_IDENTITY_PAYLOAD_FORMAT,
    GAME_IDENTITY_PAYLOAD_SIZE,
    GAME_IDENTITY_PROFILE_FINGERPRINT_FORMAT,
    GAME_IDENTITY_SCHEMA_VERSION,
    HEADER_FORMAT,
    HEADER_SIZE,
    HELLO_MAX_NAME_LENGTH,
    HELLO_METADATA_VERSION,
    HELLO_REQUEST_FIXED_FORMAT,
    HELLO_REQUEST_FIXED_SIZE,
    HELLO_RESPONSE_FIXED_FORMAT,
    HELLO_RESPONSE_FIXED_SIZE,
    HELLO_RUNTIME_CAPABILITIES,
    INVENTORY_FIELD_OFFSETS,
    INVENTORY_FRAME_SIZE,
    INVENTORY_HEADER_FORMAT,
    INVENTORY_HEADER_SIZE,
    INVENTORY_ITEM_IDS,
    INVENTORY_PAYLOAD_SIZE,
    INVENTORY_RECORD_COUNT,
    INVENTORY_RECORD_FORMAT,
    INVENTORY_RECORD_SIZE,
    INVENTORY_SCHEMA_VERSION,
    PROTOCOL_MAGIC,
    PROTOCOL_VERSION,
    READ_MEMORY_PAYLOAD_FORMAT,
    CorruptedChecksumError,
    GameIdentityPayload,
    HelloRequestPayload,
    HelloResponsePayload,
    InvalidPayloadLengthError,
    Prime3WiiAvailability,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiGameId,
    Prime3WiiInventoryAvailability,
    Prime3WiiInventoryRecord,
    Prime3WiiInventorySnapshot,
    Prime3WiiPlatformId,
    Prime3WiiRegionId,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    Prime3WiiRevisionId,
    ReadMemoryPayload,
    compute_accepted_capabilities,
    decode_game_identity_payload,
    decode_hello_request_payload,
    decode_hello_response_payload,
    decode_inventory_payload,
    derive_session_id,
    encode_error_response,
    encode_game_identity_payload,
    encode_hello_request_payload,
    encode_hello_response_payload,
    encode_inventory_payload,
    encode_read_memory_payload,
    encode_request,
    encode_response,
)


def _enum_values(enum_type: type[Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in enum_type:
        assert item.name is not None
        result[item.name] = int(item)
    return result


def _hex_bytes(data: bytes) -> str:
    return data.hex()


def _normalized_request(request: Prime3WiiRequest) -> dict[str, Any]:
    result: dict[str, Any] = {
        "command": request.command.name,
        "request_id": request.request_id,
        "payload_hex": _hex_bytes(request.payload),
    }
    if request.command is Prime3WiiCommand.HELLO:
        hello_payload = decode_hello_request_payload(request.payload)
        result["payload"] = {
            "min_protocol_version": hello_payload.min_protocol_version,
            "max_protocol_version": hello_payload.max_protocol_version,
            "capabilities": int(hello_payload.capabilities),
            "capability_names": [item.name for item in Prime3WiiCapability if item in hello_payload.capabilities],
            "client_nonce": hello_payload.client_nonce,
            "client_name": hello_payload.client_name,
        }
    elif request.command is Prime3WiiCommand.READ_MEMORY:
        read_memory_payload = prime3_wii_protocol.decode_read_memory_payload(request.payload)
        result["payload"] = {
            "address": f"0x{read_memory_payload.address:08X}",
            "size": read_memory_payload.size,
        }
    return result


def _normalized_response(response: Prime3WiiResponse | prime3_wii_protocol.Prime3WiiErrorResponse) -> dict[str, Any]:
    result: dict[str, Any] = {
        "command": response.command.name,
        "request_id": response.request_id,
    }
    if isinstance(response, Prime3WiiResponse):
        result["status"] = response.status.name
        result["payload_hex"] = _hex_bytes(response.payload)
        if response.command is Prime3WiiCommand.HELLO:
            hello = decode_hello_response_payload(response.payload)
            result["payload"] = {
                "selected_protocol_version": hello.selected_protocol_version,
                "runtime_capabilities": int(hello.runtime_capabilities),
                "runtime_capability_names": [
                    item.name for item in Prime3WiiCapability if item in hello.runtime_capabilities
                ],
                "accepted_client_capabilities": int(hello.accepted_client_capabilities),
                "accepted_capability_names": [
                    item.name for item in Prime3WiiCapability if item in hello.accepted_client_capabilities
                ],
                "session_id": hello.session_id,
                "runtime_build_id": hello.runtime_build_id,
                "runtime_mode": hello.runtime_mode,
                "runtime_metadata_version": hello.runtime_metadata_version,
                "runtime_name": hello.runtime_name,
            }
        elif response.command is Prime3WiiCommand.GET_GAME_IDENTITY:
            identity = decode_game_identity_payload(response.payload)
            result["payload"] = {
                **dataclasses.asdict(identity),
                "game_id": identity.game_id.name,
                "platform_id": identity.platform_id.name,
                "region_id": identity.region_id.name,
                "revision_id": identity.revision_id.name,
                "availability_flags": int(identity.availability_flags),
                "availability_names": [
                    item.name for item in Prime3WiiAvailability if item in identity.availability_flags
                ],
            }
        elif response.command is Prime3WiiCommand.GET_INVENTORY:
            inventory = decode_inventory_payload(response.payload)
            result["payload"] = {
                "schema_version": inventory.schema_version,
                "availability_flags": int(inventory.availability_flags),
                "availability_names": [
                    item.name for item in Prime3WiiInventoryAvailability if item in inventory.availability_flags
                ],
                "snapshot_sequence": inventory.snapshot_sequence,
                "records": [dataclasses.asdict(record) for record in inventory.records],
            }
        return result

    result["status"] = "ERROR"
    result["error_code"] = response.error_code.name
    result["message"] = response.message
    return result


@dataclasses.dataclass(frozen=True)
class ProtocolVector:
    name: str
    decode_as: Literal["request", "response"]
    packet_hex: str
    fields: dict[str, Any]
    expected: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def protocol_manifest() -> dict[str, Any]:
    return {
        "name": "prime3_wii_protocol",
        "magic_ascii": PROTOCOL_MAGIC.decode("ascii"),
        "magic_hex": _hex_bytes(PROTOCOL_MAGIC),
        "protocol_version": PROTOCOL_VERSION,
        "byte_order": "big-endian",
        "hello_metadata_version": HELLO_METADATA_VERSION,
        "default_runtime_build_id": DEFAULT_RUNTIME_BUILD_ID,
        "default_runtime_name": DEFAULT_RUNTIME_NAME,
        "hello_runtime_capabilities": int(HELLO_RUNTIME_CAPABILITIES),
        "packet_layout": {
            "header_format": HEADER_FORMAT,
            "header_size": HEADER_SIZE,
            "crc_size": CRC_SIZE,
            "fixed_packet_overhead": HEADER_SIZE + CRC_SIZE,
            "fields": [
                {"name": "magic", "type": "4s", "size": 4},
                {"name": "protocol_version", "type": "uint8", "size": 1},
                {"name": "packet_kind", "type": "uint8", "size": 1},
                {"name": "command", "type": "uint8", "size": 1},
                {"name": "response_status", "type": "uint8", "size": 1},
                {"name": "request_id", "type": "uint32", "size": 4},
                {"name": "payload_length", "type": "uint32", "size": 4},
                {"name": "payload", "type": "bytes", "size": "payload_length"},
                {"name": "crc32", "type": "uint32", "size": 4},
            ],
            "crc32_coverage": (
                "CRC32 is computed over the header and payload bytes only; the trailing CRC field is excluded."
            ),
        },
        "packet_kinds": _enum_values(prime3_wii_protocol.Prime3WiiPacketKind),
        "commands": _enum_values(Prime3WiiCommand),
        "response_status": _enum_values(Prime3WiiResponseStatus),
        "capabilities": _enum_values(Prime3WiiCapability),
        "error_codes": _enum_values(Prime3WiiErrorCode),
        "game_ids": _enum_values(Prime3WiiGameId),
        "platform_ids": _enum_values(Prime3WiiPlatformId),
        "region_ids": _enum_values(Prime3WiiRegionId),
        "revision_ids": _enum_values(Prime3WiiRevisionId),
        "availability_flags": _enum_values(Prime3WiiAvailability),
        "inventory_availability_flags": _enum_values(Prime3WiiInventoryAvailability),
        "payload_layouts": {
            "hello_request": {
                "struct_format": HELLO_REQUEST_FIXED_FORMAT,
                "fixed_size": HELLO_REQUEST_FIXED_SIZE,
                "name_length_size": 1,
                "max_name_length": HELLO_MAX_NAME_LENGTH,
                "fields": [
                    {"name": "min_protocol_version", "type": "uint8"},
                    {"name": "max_protocol_version", "type": "uint8"},
                    {"name": "client_capabilities", "type": "uint32"},
                    {"name": "client_nonce", "type": "uint32"},
                    {"name": "client_name_length", "type": "uint8"},
                    {"name": "client_name_utf8", "type": "bytes", "size": "client_name_length"},
                ],
            },
            "hello_response": {
                "struct_format": HELLO_RESPONSE_FIXED_FORMAT,
                "fixed_size": HELLO_RESPONSE_FIXED_SIZE,
                "name_length_size": 1,
                "max_name_length": HELLO_MAX_NAME_LENGTH,
                "fields": [
                    {"name": "selected_protocol_version", "type": "uint8"},
                    {"name": "runtime_capabilities", "type": "uint32"},
                    {"name": "accepted_client_capabilities", "type": "uint32"},
                    {"name": "session_id", "type": "uint32"},
                    {"name": "runtime_build_id", "type": "uint32"},
                    {"name": "runtime_mode", "type": "uint8"},
                    {"name": "runtime_metadata_version", "type": "uint8"},
                    {"name": "runtime_name_length", "type": "uint8"},
                    {"name": "runtime_name_utf8", "type": "bytes", "size": "runtime_name_length"},
                ],
            },
            "read_memory_request": {
                "struct_format": READ_MEMORY_PAYLOAD_FORMAT,
                "payload_size": struct.calcsize(READ_MEMORY_PAYLOAD_FORMAT),
                "fields": [
                    {"name": "address", "type": "uint32"},
                    {"name": "size", "type": "uint32"},
                ],
            },
            "read_memory_response": {
                "payload_size": "requested size",
                "description": "READ_MEMORY success payload is the raw memory byte range returned by the server.",
            },
            "game_identity_request": {"payload_size": 0},
            "game_identity_response": {
                "struct_format": GAME_IDENTITY_PAYLOAD_FORMAT,
                "payload_size": GAME_IDENTITY_PAYLOAD_SIZE,
                "schema_version": GAME_IDENTITY_SCHEMA_VERSION,
                "field_offsets": GAME_IDENTITY_FIELD_OFFSETS,
                "fields": [
                    {"name": "schema_version", "type": "uint8"},
                    {"name": "game_id", "type": "uint8"},
                    {"name": "platform_id", "type": "uint8"},
                    {"name": "region_id", "type": "uint8"},
                    {"name": "revision_id", "type": "uint16"},
                    {"name": "protocol_version", "type": "uint8"},
                    {"name": "runtime_mode", "type": "uint8"},
                    {"name": "profile_id", "type": "uint32"},
                    {"name": "profile_fingerprint", "type": "uint32"},
                    {"name": "runtime_build_id", "type": "uint32"},
                    {"name": "availability_flags", "type": "uint32"},
                    {"name": "reserved", "type": "uint32", "required_value": 0},
                ],
            },
            "inventory_request": {"payload_size": 0},
            "inventory_response": {
                "header_format": INVENTORY_HEADER_FORMAT,
                "record_format": INVENTORY_RECORD_FORMAT,
                "header_size": INVENTORY_HEADER_SIZE,
                "record_size": INVENTORY_RECORD_SIZE,
                "record_count": INVENTORY_RECORD_COUNT,
                "payload_size": INVENTORY_PAYLOAD_SIZE,
                "frame_size": INVENTORY_FRAME_SIZE,
                "schema_version": INVENTORY_SCHEMA_VERSION,
                "field_offsets": INVENTORY_FIELD_OFFSETS,
                "item_ids": list(INVENTORY_ITEM_IDS),
            },
            "ping_request": {"payload_size": "variable"},
            "ping_response": {"payload_size": "variable"},
            "disconnect_request": {"payload_size": 0},
            "disconnect_response": {"payload_size": 0},
            "reserved_mailbox": {
                "command": Prime3WiiCommand.RESERVED_MAILBOX.name,
                "payload_size": "reserved",
                "description": "Reserved for a future structured mailbox command. Version 1 does not define a payload.",
            },
            "error_response": {
                "struct_format": ERROR_HEADER_FORMAT,
                "fixed_header_size": struct.calcsize(ERROR_HEADER_FORMAT),
                "fields": [
                    {"name": "error_code", "type": "uint16"},
                    {"name": "command", "type": "uint16"},
                    {"name": "message_length", "type": "uint16"},
                    {"name": "message_utf8", "type": "bytes", "size": "message_length"},
                ],
            },
        },
        "session_id_derivation": {
            "algorithm": "crc32",
            "byte_order": "big-endian",
            "fields": [
                "selected_protocol_version:uint8",
                "client_nonce:uint32",
                "runtime_build_id:uint32",
                "runtime_capabilities:uint32",
                "accepted_client_capabilities:uint32",
            ],
        },
        "profile_fingerprint_derivation": {
            "algorithm": "crc32",
            "byte_order": "big-endian",
            "struct_format": GAME_IDENTITY_PROFILE_FINGERPRINT_FORMAT,
            "description": "CRC32 over canonical compile-time game/profile roots and the expected DOL SHA-256 prefix.",
        },
    }


def protocol_vectors() -> tuple[ProtocolVector, ...]:
    hello_request_payload = HelloRequestPayload(
        min_protocol_version=1,
        max_protocol_version=1,
        capabilities=Prime3WiiCapability.PING | Prime3WiiCapability.READ_MEMORY | Prime3WiiCapability.RECONNECT,
        client_nonce=0x12345678,
        client_name="rdv",
    )
    runtime_capabilities = HELLO_RUNTIME_CAPABILITIES | Prime3WiiCapability.READ_MEMORY
    accepted_capabilities = compute_accepted_capabilities(hello_request_payload.capabilities, runtime_capabilities)
    session_id = derive_session_id(
        selected_protocol_version=PROTOCOL_VERSION,
        client_nonce=hello_request_payload.client_nonce,
        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
        runtime_capabilities=runtime_capabilities,
        accepted_client_capabilities=accepted_capabilities,
    )

    hello_request = Prime3WiiRequest(
        Prime3WiiCommand.HELLO,
        0x1001,
        encode_hello_request_payload(hello_request_payload),
    )
    hello_response = Prime3WiiResponse(
        Prime3WiiCommand.HELLO,
        0x1001,
        Prime3WiiResponseStatus.OK,
        encode_hello_response_payload(
            HelloResponsePayload(
                selected_protocol_version=PROTOCOL_VERSION,
                runtime_capabilities=runtime_capabilities,
                accepted_client_capabilities=accepted_capabilities,
                session_id=session_id,
                runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
                runtime_mode=19,
                runtime_metadata_version=HELLO_METADATA_VERSION,
                runtime_name=DEFAULT_RUNTIME_NAME,
            )
        ),
    )
    read_memory_request = Prime3WiiRequest(
        Prime3WiiCommand.READ_MEMORY,
        0x1002,
        encode_read_memory_payload(ReadMemoryPayload(address=0x80000020, size=4)),
    )
    read_memory_response = Prime3WiiResponse(
        Prime3WiiCommand.READ_MEMORY,
        0x1002,
        Prime3WiiResponseStatus.OK,
        b"ABCD",
    )
    ping_request = Prime3WiiRequest(Prime3WiiCommand.PING, 0x1003, b"ping")
    ping_response = Prime3WiiResponse(Prime3WiiCommand.PING, 0x1003, Prime3WiiResponseStatus.OK, b"ping")
    disconnect_request = Prime3WiiRequest(Prime3WiiCommand.DISCONNECT, 0x1004)
    disconnect_response = Prime3WiiResponse(
        Prime3WiiCommand.DISCONNECT,
        0x1004,
        Prime3WiiResponseStatus.OK,
        b"",
    )
    identity_request = Prime3WiiRequest(Prime3WiiCommand.GET_GAME_IDENTITY, 0x1007)
    identity_response = Prime3WiiResponse(
        Prime3WiiCommand.GET_GAME_IDENTITY,
        0x1007,
        Prime3WiiResponseStatus.OK,
        encode_game_identity_payload(
            GameIdentityPayload(
                availability_flags=(
                    Prime3WiiAvailability.EXECUTABLE_RECOGNIZED | Prime3WiiAvailability.GAME_STATE_POINTER_VALID
                )
            )
        ),
    )
    inventory_request = Prime3WiiRequest(Prime3WiiCommand.GET_INVENTORY, 0x1008)
    inventory_response = Prime3WiiResponse(
        Prime3WiiCommand.GET_INVENTORY,
        0x1008,
        Prime3WiiResponseStatus.OK,
        encode_inventory_payload(
            Prime3WiiInventorySnapshot(
                availability_flags=(
                    Prime3WiiInventoryAvailability.EXECUTABLE_RECOGNIZED
                    | Prime3WiiInventoryAvailability.GAME_STATE_POINTER_VALID
                    | Prime3WiiInventoryAvailability.INVENTORY_ROOT_VALID
                    | Prime3WiiInventoryAvailability.RANGE_VALID
                    | Prime3WiiInventoryAvailability.CONSISTENCY_CHECK_PASSED
                    | Prime3WiiInventoryAvailability.SNAPSHOT_AVAILABLE
                ),
                snapshot_sequence=1,
                records=(Prime3WiiInventoryRecord(0, 1),) * INVENTORY_RECORD_COUNT,
            )
        ),
    )
    mailbox_request = Prime3WiiRequest(Prime3WiiCommand.RESERVED_MAILBOX, 0x1005)

    invalid_state_response = encode_error_response(
        Prime3WiiCommand.PING,
        0x1006,
        Prime3WiiErrorCode.NOT_NEGOTIATED,
        "Session negotiation is required before PING.",
    )

    corrupted_crc_packet = bytearray(encode_request(ping_request))
    corrupted_crc_packet[-1] ^= 0xFF

    vectors = [
        ProtocolVector(
            name="hello_request",
            decode_as="request",
            packet_hex=_hex_bytes(encode_request(hello_request)),
            fields={
                "command": "HELLO",
                "request_id": 0x1001,
                "min_protocol_version": 1,
                "max_protocol_version": 1,
                "client_nonce": 0x12345678,
            },
            expected=_normalized_request(hello_request),
        ),
        ProtocolVector(
            name="hello_success_response",
            decode_as="response",
            packet_hex=_hex_bytes(encode_response(hello_response)),
            fields={
                "command": "HELLO",
                "request_id": 0x1001,
                "selected_protocol_version": PROTOCOL_VERSION,
                "runtime_build_id": DEFAULT_RUNTIME_BUILD_ID,
                "session_id": session_id,
                "runtime_mode": 19,
            },
            expected=_normalized_response(hello_response),
        ),
        ProtocolVector(
            name="read_memory_request",
            decode_as="request",
            packet_hex=_hex_bytes(encode_request(read_memory_request)),
            fields={
                "command": "READ_MEMORY",
                "request_id": 0x1002,
                "address": "0x80000020",
                "size": 4,
            },
            expected=_normalized_request(read_memory_request),
        ),
        ProtocolVector(
            name="read_memory_success_response",
            decode_as="response",
            packet_hex=_hex_bytes(encode_response(read_memory_response)),
            fields={
                "command": "READ_MEMORY",
                "request_id": 0x1002,
                "payload_hex": "41424344",
            },
            expected=_normalized_response(read_memory_response),
        ),
        ProtocolVector(
            name="game_identity_request",
            decode_as="request",
            packet_hex=_hex_bytes(encode_request(identity_request)),
            fields={"command": "GET_GAME_IDENTITY", "request_id": 0x1007, "payload_length": 0},
            expected=_normalized_request(identity_request),
        ),
        ProtocolVector(
            name="game_identity_success_response",
            decode_as="response",
            packet_hex=_hex_bytes(encode_response(identity_response)),
            fields={
                "command": "GET_GAME_IDENTITY",
                "request_id": 0x1007,
                "payload_length": GAME_IDENTITY_PAYLOAD_SIZE,
            },
            expected=_normalized_response(identity_response),
        ),
        ProtocolVector(
            name="inventory_request",
            decode_as="request",
            packet_hex=_hex_bytes(encode_request(inventory_request)),
            fields={"command": "GET_INVENTORY", "request_id": 0x1008, "payload_length": 0},
            expected=_normalized_request(inventory_request),
        ),
        ProtocolVector(
            name="inventory_success_response",
            decode_as="response",
            packet_hex=_hex_bytes(encode_response(inventory_response)),
            fields={
                "command": "GET_INVENTORY",
                "request_id": 0x1008,
                "payload_length": INVENTORY_PAYLOAD_SIZE,
            },
            expected=_normalized_response(inventory_response),
        ),
        ProtocolVector(
            name="ping_request",
            decode_as="request",
            packet_hex=_hex_bytes(encode_request(ping_request)),
            fields={"command": "PING", "request_id": 0x1003, "payload_length": 4},
            expected=_normalized_request(ping_request),
        ),
        ProtocolVector(
            name="ping_response",
            decode_as="response",
            packet_hex=_hex_bytes(encode_response(ping_response)),
            fields={"command": "PING", "request_id": 0x1003, "payload_length": 4},
            expected=_normalized_response(ping_response),
        ),
        ProtocolVector(
            name="disconnect_request",
            decode_as="request",
            packet_hex=_hex_bytes(encode_request(disconnect_request)),
            fields={"command": "DISCONNECT", "request_id": 0x1004, "payload_length": 0},
            expected=_normalized_request(disconnect_request),
        ),
        ProtocolVector(
            name="disconnect_response",
            decode_as="response",
            packet_hex=_hex_bytes(encode_response(disconnect_response)),
            fields={"command": "DISCONNECT", "request_id": 0x1004, "payload_length": 0},
            expected=_normalized_response(disconnect_response),
        ),
        ProtocolVector(
            name="not_negotiated_error_response",
            decode_as="response",
            packet_hex=_hex_bytes(invalid_state_response),
            fields={
                "command": "PING",
                "request_id": 0x1006,
                "error_code": "NOT_NEGOTIATED",
                "message": "Session negotiation is required before PING.",
            },
            expected={
                "command": "PING",
                "request_id": 0x1006,
                "status": "ERROR",
                "error_code": "NOT_NEGOTIATED",
                "message": "Session negotiation is required before PING.",
            },
        ),
        ProtocolVector(
            name="corrupted_crc_packet",
            decode_as="request",
            packet_hex=_hex_bytes(bytes(corrupted_crc_packet)),
            fields={"command": "PING", "request_id": 0x1003, "mutation": "last crc byte flipped"},
            expected={"error": CorruptedChecksumError.__name__},
        ),
        ProtocolVector(
            name="truncated_packet",
            decode_as="request",
            packet_hex="00",
            fields={"description": "Single-byte packet shorter than header"},
            expected={"error": InvalidPayloadLengthError.__name__},
        ),
        ProtocolVector(
            name="reserved_mailbox_command",
            decode_as="request",
            packet_hex=_hex_bytes(encode_request(mailbox_request)),
            fields={"command": "RESERVED_MAILBOX", "request_id": 0x1005, "payload_length": 0},
            expected=_normalized_request(mailbox_request),
        ),
    ]
    return tuple(vectors)


def protocol_manifest_json() -> str:
    return json.dumps(protocol_manifest(), indent=2, sort_keys=True) + "\n"


def protocol_vectors_json() -> str:
    return json.dumps([vector.as_dict() for vector in protocol_vectors()], indent=2, sort_keys=True) + "\n"
