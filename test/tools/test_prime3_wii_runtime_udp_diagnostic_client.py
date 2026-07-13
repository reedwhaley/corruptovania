from __future__ import annotations

import importlib.util
import json
import socket
import sys
import threading
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2].joinpath("tools", "prime3_wii_runtime", "udp_diagnostic_client.py")


def _load_module(module_name: str = "prime3_wii_runtime_udp_diagnostic_client_test"):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _response_bytes(module, *, sequence: int, recurring_poll_counter: int = 123, transport_state: int = 21) -> bytes:
    echoed_preview = module.REQUEST_STRUCT.pack(module.REQUEST_MAGIC, module.PROTOCOL_VERSION, sequence, 0)
    return module.RESPONSE_STRUCT.pack(
        module.RESPONSE_MAGIC,
        module.PROTOCOL_VERSION,
        77,
        recurring_poll_counter,
        transport_state,
        0xC0A80164,
        5,
        module.REQUEST_STRUCT.size,
        echoed_preview,
    )


def test_build_request_generates_32_bit_sequence() -> None:
    module = _load_module()

    request = module.build_request()

    assert 0 <= request.sequence <= 0xFFFFFFFF
    assert request.to_bytes().startswith(module.REQUEST_MAGIC)


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
    assert result.sequence == 77
    assert result.heartbeat == 123
    assert result.recurring_poll_counter == 123
    assert result.transport_state == 21


def test_parse_response_rejects_wrong_magic() -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_magic_test")
    packet = bytearray(_response_bytes(module, sequence=1))
    packet[:4] = b"NOPE"

    with pytest.raises(ValueError, match="Wrong response magic"):
        module.parse_response(
            bytes(packet),
            expected_sequence=1,
            responding_address=("127.0.0.1", 1),
            round_trip_ms=1.0,
        )


def test_parse_response_rejects_wrong_length() -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_length_test")

    with pytest.raises(ValueError, match="Expected 48 response bytes"):
        module.parse_response(b"\x00" * 47, expected_sequence=1, responding_address=("127.0.0.1", 1), round_trip_ms=1.0)


def test_parse_response_rejects_wrong_sequence() -> None:
    module = _load_module("prime3_wii_runtime_udp_diagnostic_client_sequence_test")
    packet = _response_bytes(module, sequence=2)

    with pytest.raises(ValueError, match="Wrong echoed request sequence"):
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
                sequence = int.from_bytes(payload[8:12], "big")
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
            sequence=88,
            heartbeat=10,
            recurring_poll_counter=10,
            transport_state=21,
            host_id=0xC0A80164,
            receive_count=3,
            last_receive_length=16,
            echoed_request_preview_hex="00" * 16,
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
    assert payload["heartbeat"] == 10
