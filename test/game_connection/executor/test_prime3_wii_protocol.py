from __future__ import annotations

import struct

import pytest

from randovania.game_connection.executor.prime3_wii_protocol import (
    DEFAULT_RUNTIME_BUILD_ID,
    DEFAULT_RUNTIME_NAME,
    GAME_IDENTITY_FIELD_OFFSETS,
    GAME_IDENTITY_PAYLOAD_SIZE,
    HELLO_METADATA_VERSION,
    HELLO_RUNTIME_CAPABILITIES,
    INVALID_STATE_MESSAGE,
    INVENTORY_FIELD_OFFSETS,
    INVENTORY_FRAME_SIZE,
    INVENTORY_ITEM_IDS,
    INVENTORY_PAYLOAD_SIZE,
    INVENTORY_RECORD_COUNT,
    INVENTORY_RECORD_SIZE,
    NOT_NEGOTIATED_MESSAGE,
    PRIME3_NTSC_RETAIL_PROFILE_FINGERPRINT,
    BadMagicError,
    CorruptedChecksumError,
    GameIdentityPayload,
    HelloRequestPayload,
    HelloResponsePayload,
    InvalidPayloadLengthError,
    Prime3WiiAvailability,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiInventoryAvailability,
    Prime3WiiInventoryRecord,
    Prime3WiiInventorySnapshot,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    UnknownCommandError,
    UnsupportedIdentitySchemaError,
    UnsupportedProtocolVersionError,
    compute_accepted_capabilities,
    crc32_bytes,
    decode_game_identity_payload,
    decode_hello_request_payload,
    decode_hello_response_payload,
    decode_inventory_payload,
    decode_request,
    decode_response,
    derive_session_id,
    encode_error_response,
    encode_game_identity_payload,
    encode_hello_request_payload,
    encode_hello_response_payload,
    encode_inventory_payload,
    encode_request,
    encode_response,
)


def _with_crc(body: bytes) -> bytes:
    return body + struct.pack(">I", crc32_bytes(body))


def test_game_identity_protocol_values_and_layout_are_stable() -> None:
    assert Prime3WiiCommand.GET_GAME_IDENTITY == 5
    assert Prime3WiiCapability.GAME_IDENTITY == 1 << 11
    assert Prime3WiiErrorCode.CAPABILITY_NOT_NEGOTIATED == 11
    assert GAME_IDENTITY_PAYLOAD_SIZE == 28
    assert GAME_IDENTITY_FIELD_OFFSETS["revision_id"] == 4
    assert GAME_IDENTITY_FIELD_OFFSETS["reserved"] == 24
    assert PRIME3_NTSC_RETAIL_PROFILE_FINGERPRINT == 0x67B00CE6


def test_inventory_protocol_values_layout_and_order_are_stable() -> None:
    assert Prime3WiiCommand.GET_INVENTORY == 6
    assert Prime3WiiCapability.INVENTORY_STATE == 1 << 12
    assert INVENTORY_RECORD_COUNT == 59
    assert INVENTORY_RECORD_SIZE == 8
    assert INVENTORY_PAYLOAD_SIZE == 484
    assert INVENTORY_FRAME_SIZE == 504
    assert INVENTORY_FIELD_OFFSETS["records"] == 12
    assert INVENTORY_ITEM_IDS == (*range(43), 44, 45, 46, 48, 49, 50, 51, 52, *range(62, 70))


def test_inventory_payload_round_trip_is_big_endian_and_deterministic() -> None:
    records = tuple(Prime3WiiInventoryRecord(index, index + 100) for index in range(INVENTORY_RECORD_COUNT))
    snapshot = Prime3WiiInventorySnapshot(
        availability_flags=(
            Prime3WiiInventoryAvailability.EXECUTABLE_RECOGNIZED
            | Prime3WiiInventoryAvailability.GAME_STATE_POINTER_VALID
            | Prime3WiiInventoryAvailability.INVENTORY_ROOT_VALID
            | Prime3WiiInventoryAvailability.RANGE_VALID
            | Prime3WiiInventoryAvailability.CONSISTENCY_CHECK_PASSED
            | Prime3WiiInventoryAvailability.SNAPSHOT_AVAILABLE
        ),
        snapshot_sequence=0x10203040,
        records=records,
    )
    encoded = encode_inventory_payload(snapshot)
    assert encoded == encode_inventory_payload(snapshot)
    assert encoded[8:12] == b"\x10\x20\x30\x40"
    assert encoded[12:20] == struct.pack(">II", 0, 100)
    assert decode_inventory_payload(encoded) == snapshot


def test_inventory_payload_rejects_malformed_layout_and_unavailable_data() -> None:
    encoded = bytearray(encode_inventory_payload(Prime3WiiInventorySnapshot()))
    with pytest.raises(InvalidPayloadLengthError):
        decode_inventory_payload(bytes(encoded[:-1]))
    encoded[1] = 58
    with pytest.raises(InvalidPayloadLengthError, match="record count"):
        decode_inventory_payload(bytes(encoded))
    encoded[1] = 59
    encoded[2] = 12
    with pytest.raises(InvalidPayloadLengthError, match="record size"):
        decode_inventory_payload(bytes(encoded))
    encoded[2] = 8
    encoded[3] = 1
    with pytest.raises(InvalidPayloadLengthError, match="reserved"):
        decode_inventory_payload(bytes(encoded))
    encoded[3] = 0
    encoded[19] = 1
    with pytest.raises(InvalidPayloadLengthError, match="must be zero"):
        decode_inventory_payload(bytes(encoded))


def test_game_identity_payload_round_trip_is_big_endian_and_deterministic() -> None:
    identity = GameIdentityPayload(
        availability_flags=(
            Prime3WiiAvailability.EXECUTABLE_RECOGNIZED
            | Prime3WiiAvailability.PLAYER_STATE_POINTER_VALID
        )
    )
    encoded = encode_game_identity_payload(identity)
    assert encoded == encode_game_identity_payload(identity)
    assert encoded[4:6] == b"\x00\x01"
    assert encoded[12:16] == PRIME3_NTSC_RETAIL_PROFILE_FINGERPRINT.to_bytes(4, "big")
    assert encoded[24:28] == b"\0\0\0\0"
    assert decode_game_identity_payload(encoded) == identity


def test_game_identity_payload_rejects_wrong_size_schema_and_reserved() -> None:
    encoded = bytearray(encode_game_identity_payload(GameIdentityPayload()))
    with pytest.raises(InvalidPayloadLengthError):
        decode_game_identity_payload(bytes(encoded[:-1]))
    encoded[0] = 2
    with pytest.raises(UnsupportedIdentitySchemaError):
        decode_game_identity_payload(bytes(encoded))
    encoded[0] = 1
    encoded[-1] = 1
    with pytest.raises(InvalidPayloadLengthError, match="reserved"):
        decode_game_identity_payload(bytes(encoded))


def test_request_round_trip():
    request = Prime3WiiRequest(Prime3WiiCommand.READ_MEMORY, 7, b"payload")

    decoded = decode_request(encode_request(request))

    assert decoded == request


def test_response_round_trip():
    response = Prime3WiiResponse(Prime3WiiCommand.PING, 19, Prime3WiiResponseStatus.OK, b"pong")

    decoded = decode_response(encode_response(response), expected_request_id=19)

    assert decoded == response


def test_request_id_preserved():
    request = Prime3WiiRequest(Prime3WiiCommand.HELLO, 0x10203040, b"payload")

    decoded = decode_request(encode_request(request))

    assert decoded.request_id == 0x10203040


def test_bad_magic():
    packet = bytearray(encode_request(Prime3WiiRequest(Prime3WiiCommand.PING, 1)))
    packet[:4] = b"NOPE"

    with pytest.raises(BadMagicError):
        decode_request(_with_crc(bytes(packet[:-4])))


def test_unsupported_protocol_version():
    packet = bytearray(encode_request(Prime3WiiRequest(Prime3WiiCommand.PING, 1)))
    packet[4] = 2

    with pytest.raises(UnsupportedProtocolVersionError):
        decode_request(_with_crc(bytes(packet[:-4])))


def test_unknown_command():
    request = encode_request(Prime3WiiRequest(Prime3WiiCommand.PING, 1))
    packet = bytearray(request)
    packet[6] = 99
    corrupted = _with_crc(bytes(packet[:-4]))

    with pytest.raises(UnknownCommandError):
        decode_request(corrupted)


def test_invalid_payload_length():
    packet = encode_request(Prime3WiiRequest(Prime3WiiCommand.PING, 1))
    body = bytearray(packet[:-4])
    body[12:16] = struct.pack(">I", 10)
    broken = _with_crc(bytes(body))

    with pytest.raises(InvalidPayloadLengthError):
        decode_request(broken)


def test_truncated_packet():
    with pytest.raises(InvalidPayloadLengthError):
        decode_request(b"\x00")


def test_corrupted_checksum():
    packet = bytearray(encode_request(Prime3WiiRequest(Prime3WiiCommand.PING, 1)))
    packet[-1] ^= 0xFF

    with pytest.raises(CorruptedChecksumError):
        decode_request(bytes(packet))


def test_hello_request_round_trip():
    hello = HelloRequestPayload(
        min_protocol_version=1,
        max_protocol_version=1,
        capabilities=Prime3WiiCapability.PING | Prime3WiiCapability.READ_MEMORY,
        client_nonce=0x12345678,
        client_name="rdv",
    )

    decoded = decode_hello_request_payload(encode_hello_request_payload(hello))

    assert decoded == hello


def test_hello_response_round_trip():
    hello = HelloResponsePayload(
        selected_protocol_version=1,
        runtime_capabilities=HELLO_RUNTIME_CAPABILITIES | Prime3WiiCapability.READ_MEMORY,
        accepted_client_capabilities=Prime3WiiCapability.PING | Prime3WiiCapability.READ_MEMORY,
        session_id=0xAABBCCDD,
        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
        runtime_mode=19,
        runtime_metadata_version=HELLO_METADATA_VERSION,
        runtime_name=DEFAULT_RUNTIME_NAME,
    )

    decoded = decode_hello_response_payload(encode_hello_response_payload(hello))

    assert decoded == hello


def test_hello_request_empty_name_supported():
    hello = HelloRequestPayload(
        min_protocol_version=1,
        max_protocol_version=1,
        capabilities=Prime3WiiCapability.PING,
        client_nonce=1,
        client_name="",
    )

    decoded = decode_hello_request_payload(encode_hello_request_payload(hello))

    assert decoded.client_name == ""


def test_hello_response_bounded_name_supported():
    name = "x" * 31
    hello = HelloResponsePayload(
        selected_protocol_version=1,
        runtime_capabilities=HELLO_RUNTIME_CAPABILITIES,
        accepted_client_capabilities=Prime3WiiCapability.PING,
        session_id=2,
        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
        runtime_mode=19,
        runtime_name=name,
    )

    decoded = decode_hello_response_payload(encode_hello_response_payload(hello))

    assert decoded.runtime_name == name


def test_accepted_capability_mask_is_intersection():
    client = Prime3WiiCapability.PING | Prime3WiiCapability.READ_MEMORY | Prime3WiiCapability.RECONNECT
    runtime = HELLO_RUNTIME_CAPABILITIES | Prime3WiiCapability.READ_MEMORY

    accepted = compute_accepted_capabilities(client, runtime)

    assert accepted == (Prime3WiiCapability.PING | Prime3WiiCapability.READ_MEMORY)


def test_deterministic_session_id_derivation():
    session_id = derive_session_id(
        selected_protocol_version=1,
        client_nonce=0x12345678,
        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
        runtime_capabilities=HELLO_RUNTIME_CAPABILITIES,
        accepted_client_capabilities=Prime3WiiCapability.PING,
    )

    assert session_id == derive_session_id(
        selected_protocol_version=1,
        client_nonce=0x12345678,
        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
        runtime_capabilities=HELLO_RUNTIME_CAPABILITIES,
        accepted_client_capabilities=Prime3WiiCapability.PING,
    )


def test_changed_nonce_changes_session_id():
    first = derive_session_id(
        selected_protocol_version=1,
        client_nonce=1,
        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
        runtime_capabilities=HELLO_RUNTIME_CAPABILITIES,
        accepted_client_capabilities=Prime3WiiCapability.PING,
    )
    second = derive_session_id(
        selected_protocol_version=1,
        client_nonce=2,
        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
        runtime_capabilities=HELLO_RUNTIME_CAPABILITIES,
        accepted_client_capabilities=Prime3WiiCapability.PING,
    )

    assert first != second


def test_changed_accepted_capabilities_changes_session_id():
    first = derive_session_id(
        selected_protocol_version=1,
        client_nonce=1,
        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
        runtime_capabilities=HELLO_RUNTIME_CAPABILITIES,
        accepted_client_capabilities=Prime3WiiCapability.PING,
    )
    second = derive_session_id(
        selected_protocol_version=1,
        client_nonce=1,
        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
        runtime_capabilities=HELLO_RUNTIME_CAPABILITIES,
        accepted_client_capabilities=Prime3WiiCapability.PING | Prime3WiiCapability.READ_MEMORY,
    )

    assert first != second


def test_error_response_round_trip():
    packet = encode_error_response(
        Prime3WiiCommand.READ_MEMORY,
        55,
        Prime3WiiErrorCode.INVALID_ADDRESS,
        "bad address",
    )

    decoded = decode_response(packet, expected_request_id=55)

    assert decoded.command is Prime3WiiCommand.READ_MEMORY
    assert decoded.request_id == 55
    assert decoded.error_code is Prime3WiiErrorCode.INVALID_ADDRESS
    assert decoded.message == "bad address"


def test_not_negotiated_error_response_round_trip():
    packet = encode_error_response(
        Prime3WiiCommand.PING,
        99,
        Prime3WiiErrorCode.NOT_NEGOTIATED,
        NOT_NEGOTIATED_MESSAGE,
    )

    decoded = decode_response(packet, expected_request_id=99)

    assert decoded.error_code is Prime3WiiErrorCode.NOT_NEGOTIATED
    assert decoded.message == NOT_NEGOTIATED_MESSAGE


def test_invalid_state_error_response_round_trip():
    packet = encode_error_response(
        Prime3WiiCommand.HELLO,
        100,
        Prime3WiiErrorCode.INVALID_STATE,
        INVALID_STATE_MESSAGE,
    )

    decoded = decode_response(packet, expected_request_id=100)

    assert decoded.error_code is Prime3WiiErrorCode.INVALID_STATE
    assert decoded.message == INVALID_STATE_MESSAGE
