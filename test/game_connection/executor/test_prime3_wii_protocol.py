from __future__ import annotations

import struct
import zlib

import pytest

from randovania.game_connection.executor.prime3_wii_protocol import (
    BadMagicError,
    CorruptedChecksumError,
    HelloPayload,
    InvalidPayloadLengthError,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    UnknownCommandError,
    UnsupportedProtocolVersionError,
    decode_hello_payload,
    decode_request,
    decode_response,
    encode_error_response,
    encode_hello_payload,
    encode_request,
    encode_response,
)


def _with_crc(body: bytes) -> bytes:
    return body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def test_request_round_trip():
    request = Prime3WiiRequest(Prime3WiiCommand.READ_MEMORY, 7, b"payload")

    decoded = decode_request(encode_request(request))

    assert decoded == request


def test_response_round_trip():
    response = Prime3WiiResponse(Prime3WiiCommand.PING, 19, Prime3WiiResponseStatus.OK, b"pong")

    decoded = decode_response(encode_response(response), expected_request_id=19)

    assert decoded == response


def test_request_id_preserved():
    request = Prime3WiiRequest(Prime3WiiCommand.HELLO, 0x10203040)

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


def test_hello_capability_round_trip():
    hello = HelloPayload(1, 2048, Prime3WiiCapability.READ_MEMORY | Prime3WiiCapability.STRUCTURED_MAILBOX)

    decoded = decode_hello_payload(encode_hello_payload(hello))

    assert decoded == hello


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
