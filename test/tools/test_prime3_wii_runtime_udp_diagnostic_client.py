from __future__ import annotations

import importlib.util
import json
import socket
import sys
import threading
from pathlib import Path

import pytest

from randovania.game_connection.executor.prime3_wii_protocol import (
    INVENTORY_RUNTIME_CAPABILITIES,
    HelloResponsePayload,
    Prime3WiiCommand,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    decode_request,
    encode_hello_response_payload,
    encode_response,
)

SCRIPT_PATH = Path(__file__).resolve().parents[2].joinpath("tools", "prime3_wii_runtime", "udp_diagnostic_client.py")


def _load_module(module_name: str = "prime3_wii_runtime_udp_diagnostic_client_test"):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _response_bytes(module, *, sequence: int) -> bytes:
    hello = HelloResponsePayload(
        selected_protocol_version=module.PROTOCOL_VERSION,
        runtime_capabilities=INVENTORY_RUNTIME_CAPABILITIES,
        accepted_client_capabilities=INVENTORY_RUNTIME_CAPABILITIES,
        session_id=0x10203040,
        runtime_build_id=0x50335731,
        runtime_mode=22,
        runtime_name="Prime3 Wii CP3W",
    )
    return encode_response(
        Prime3WiiResponse(
            command=Prime3WiiCommand.HELLO,
            request_id=sequence,
            status=Prime3WiiResponseStatus.OK,
            payload=encode_hello_response_payload(hello),
        )
    )


def test_build_request_generates_32_bit_sequence() -> None:
    module = _load_module()

    request = module.build_request()

    assert 0 <= request.sequence <= 0xFFFFFFFF
    assert request.to_bytes().startswith(b"CP3W")
    assert decode_request(request.to_bytes()).command is Prime3WiiCommand.HELLO


def test_build_request_rejects_out_of_range_sequence() -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_range_test")

    with pytest.raises(ValueError, match="32-bit unsigned integer"):
        module.build_request(sequence=0x1_0000_0000)


def test_parse_response_accepts_valid_packet() -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_parse_test")
    packet = _response_bytes(module, sequence=0x12345678)

    result = module.parse_response(
        packet,
        expected_sequence=0x12345678,
        responding_address=("192.168.1.100", 43674),
        round_trip_ms=12.5,
    )

    assert result.responding_address == "192.168.1.100"
    assert result.responding_port == 43674
    assert result.request_id == 0x12345678
    assert result.runtime_build_id_text == "P3W1"
    assert result.runtime_mode == 22


def test_parse_response_rejects_wrong_magic() -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_magic_test")
    packet = bytearray(_response_bytes(module, sequence=1))
    packet[:4] = b"NOPE"

    with pytest.raises(ValueError, match="Malformed CP3W response"):
        module.parse_response(
            bytes(packet),
            expected_sequence=1,
            responding_address=("127.0.0.1", 1),
            round_trip_ms=1.0,
        )


def test_parse_response_rejects_wrong_length() -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_length_test")

    with pytest.raises(ValueError, match="shorter than minimum"):
        module.parse_response(b"\x00" * 4, expected_sequence=1, responding_address=("127.0.0.1", 1), round_trip_ms=1.0)


def test_parse_response_rejects_wrong_sequence() -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_sequence_test")
    packet = _response_bytes(module, sequence=2)

    with pytest.raises(ValueError, match="request id"):
        module.parse_response(packet, expected_sequence=1, responding_address=("127.0.0.1", 1), round_trip_ms=1.0)


def test_query_runtime_retries_then_succeeds() -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_query_test")
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    attempts: list[bytes] = []

    def _serve() -> None:
        for _ in range(2):
            payload, address = server.recvfrom(64)
            attempts.append(payload)
            if len(attempts) == 2:
                sequence = decode_request(payload).request_id
                server.sendto(_response_bytes(module, sequence=sequence), address)
        server.close()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()

    result = module.query_runtime("127.0.0.1", port=port, timeout=0.05, retries=2)

    thread.join(timeout=1.0)
    assert len(attempts) == 2
    assert result.responding_address == "127.0.0.1"


def test_query_runtime_times_out_after_bounded_retries() -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_timeout_test")

    with pytest.raises(TimeoutError, match="after 2 attempts"):
        module.query_runtime("127.0.0.1", port=65530, timeout=0.01, retries=2, sequence=1)


def test_cli_writes_json_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_cli_test")
    output_path = tmp_path.joinpath("report.json")

    def _fake_query_runtime(host: str, *, port: int, sequence: int | None, timeout: float, retries: int):
        assert host == "127.0.0.1"
        assert port == 43674
        assert sequence == 7
        assert timeout == 0.5
        assert retries == 2
        return module.DiagnosticResponse(
            responding_address="127.0.0.1",
            responding_port=43674,
            request_id=7,
            selected_protocol_version=1,
            runtime_capabilities=int(INVENTORY_RUNTIME_CAPABILITIES),
            accepted_client_capabilities=int(INVENTORY_RUNTIME_CAPABILITIES),
            session_id=1,
            runtime_build_id=0x50335731,
            runtime_build_id_text="P3W1",
            runtime_mode=22,
            runtime_metadata_version=1,
            runtime_name="Prime3 Wii CP3W",
            round_trip_ms=2.5,
        )

    monkeypatch.setattr(module, "query_runtime", _fake_query_runtime)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "udp_diagnostic_client.py",
            "--host",
            "127.0.0.1",
            "--sequence",
            "7",
            "--timeout",
            "0.5",
            "--retries",
            "2",
            "--output",
            str(output_path),
        ],
    )

    module.main()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["responding_address"] == "127.0.0.1"
    assert payload["runtime_build_id_text"] == "P3W1"
