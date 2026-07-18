from __future__ import annotations

import struct

import pytest

from randovania.game_connection.executor.prime3_wii_protocol import (
    DEFAULT_RUNTIME_BUILD_ID,
    DEFAULT_RUNTIME_NAME,
    HELLO_METADATA_VERSION,
    HELLO_RUNTIME_CAPABILITIES,
    INVALID_STATE_MESSAGE,
    NOT_NEGOTIATED_MESSAGE,
    BadMagicError,
    CorruptedChecksumError,
    HelloRequestPayload,
    HelloResponsePayload,
    InvalidPayloadLengthError,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    UnknownCommandError,
    UnsupportedProtocolVersionError,
    compute_accepted_capabilities,
    crc32_bytes,
    decode_hello_request_payload,
    decode_hello_response_payload,
    decode_request,
    decode_response,
    derive_session_id,
    encode_error_response,
    encode_hello_request_payload,
    encode_hello_response_payload,
    encode_request,
    encode_response,
)


def _with_crc(body: bytes) -> bytes:
    return body + struct.pack(">I", crc32_bytes(body))


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
