from __future__ import annotations

import struct

import pytest

from randovania.game_connection.executor import prime3_wii_protocol
from randovania.game_connection.executor.prime3_wii_protocol import (
    CRC_SIZE,
    ERROR_HEADER_FORMAT,
    HEADER_FORMAT,
    HEADER_SIZE,
    HELLO_PAYLOAD_FORMAT,
    PROTOCOL_MAGIC,
    PROTOCOL_VERSION,
    READ_MEMORY_PAYLOAD_FORMAT,
    decode_request,
    decode_response,
)
from randovania.game_connection.executor.prime3_wii_protocol_artifacts import (
    protocol_manifest,
    protocol_manifest_json,
    protocol_vectors,
    protocol_vectors_json,
)


def test_protocol_manifest_matches_python_protocol():
    manifest = protocol_manifest()

    assert manifest["magic_ascii"] == PROTOCOL_MAGIC.decode("ascii")
    assert manifest["magic_hex"] == PROTOCOL_MAGIC.hex()
    assert manifest["protocol_version"] == PROTOCOL_VERSION
    assert manifest["packet_layout"]["header_format"] == HEADER_FORMAT
    assert manifest["packet_layout"]["header_size"] == HEADER_SIZE
    assert manifest["packet_layout"]["crc_size"] == CRC_SIZE
    assert manifest["packet_layout"]["fixed_packet_overhead"] == HEADER_SIZE + CRC_SIZE
    assert manifest["payload_layouts"]["hello_response"]["struct_format"] == HELLO_PAYLOAD_FORMAT
    assert manifest["payload_layouts"]["hello_response"]["payload_size"] == struct.calcsize(HELLO_PAYLOAD_FORMAT)
    assert manifest["payload_layouts"]["read_memory_request"]["struct_format"] == READ_MEMORY_PAYLOAD_FORMAT
    assert manifest["payload_layouts"]["read_memory_request"]["payload_size"] == struct.calcsize(
        READ_MEMORY_PAYLOAD_FORMAT
    )
    assert manifest["payload_layouts"]["error_response"]["struct_format"] == ERROR_HEADER_FORMAT
    assert manifest["payload_layouts"]["error_response"]["fixed_header_size"] == struct.calcsize(ERROR_HEADER_FORMAT)


def test_protocol_vectors_are_deterministic_json():
    assert protocol_manifest_json() == protocol_manifest_json()
    assert protocol_vectors_json() == protocol_vectors_json()


def test_protocol_vectors_decode_as_declared():
    expected_names = {
        "hello_request",
        "hello_success_response",
        "read_memory_request",
        "read_memory_success_response",
        "ping_request",
        "ping_response",
        "disconnect_request",
        "disconnect_response",
        "invalid_range_error_response",
        "corrupted_crc_packet",
        "truncated_packet",
        "reserved_mailbox_command",
    }
    vectors = {vector.name: vector for vector in protocol_vectors()}
    assert set(vectors) == expected_names

    for vector in vectors.values():
        packet = bytes.fromhex(vector.packet_hex)
        if "error" in vector.expected:
            error_type = getattr(prime3_wii_protocol, vector.expected["error"])
            if vector.decode_as == "request":
                with pytest.raises(error_type):
                    decode_request(packet)
            else:
                with pytest.raises(error_type):
                    decode_response(packet)
            continue

        if vector.decode_as == "request":
            decoded = decode_request(packet)
            expected = vector.expected
            assert decoded.command.name == expected["command"]
            assert decoded.request_id == expected["request_id"]
            assert decoded.payload.hex() == expected["payload_hex"]
        else:
            decoded = decode_response(packet, expected_request_id=vector.expected["request_id"])
            assert decoded.command.name == vector.expected["command"]
            assert decoded.request_id == vector.expected["request_id"]
            if hasattr(decoded, "status"):
                assert decoded.status.name == vector.expected["status"]
            if "payload_hex" in vector.expected:
                assert decoded.payload.hex() == vector.expected["payload_hex"]
            if "error_code" in vector.expected:
                assert decoded.error_code.name == vector.expected["error_code"]
                assert decoded.message == vector.expected["message"]
