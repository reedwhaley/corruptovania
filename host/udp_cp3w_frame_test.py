from __future__ import annotations

import argparse
import dataclasses
import json
import os
import socket
import struct
import sys
import time
import zlib
from pathlib import Path

if __package__ in {None, ""}:
    _repository_root = Path(__file__).resolve().parents[1]
    _repository_root_str = os.fspath(_repository_root)
    if _repository_root_str not in sys.path:
        sys.path.insert(0, _repository_root_str)

from randovania.game_connection.executor.prime3_wii_protocol import (
    HEADER_FORMAT,
    HEADER_SIZE,
    PROTOCOL_MAGIC,
    PROTOCOL_VERSION,
    Prime3WiiCommand,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    decode_response,
    encode_request,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 43674
DEFAULT_TIMEOUT_SECONDS = 1.0
EXTRA_REPLY_TIMEOUT_SECONDS = 0.25
REQUEST_PAYLOAD = b"P3_FRAME_TEST_20260717"
RESPONSE_PAYLOAD = b"P3_FRAME_ACK_20260717"


@dataclasses.dataclass(frozen=True)
class Scenario:
    name: str
    packet: bytes
    request_id: int | None
    expect_reply: bool


@dataclasses.dataclass
class ScenarioResult:
    name: str
    request_id: int | None
    expect_reply: bool
    sent_bytes: int
    packet_hex: str
    result: str
    endpoint: str | None = None
    round_trip_ms: float | None = None
    response_hex: str | None = None
    response_payload_ascii: str | None = None
    response_request_id: int | None = None
    response_command: str | None = None
    response_status: str | None = None


def _encode_raw_request(
    *,
    command_raw: int,
    request_id: int,
    payload: bytes,
    magic: bytes = PROTOCOL_MAGIC,
    version: int = PROTOCOL_VERSION,
    packet_kind: int = 1,
    response_status: int = 0,
    declared_payload_length: int | None = None,
    corrupt_crc: bool = False,
) -> bytes:
    body = struct.pack(
        HEADER_FORMAT,
        magic,
        version,
        packet_kind,
        command_raw,
        response_status,
        request_id,
        len(payload) if declared_payload_length is None else declared_payload_length,
    ) + payload
    checksum = zlib.crc32(body) & 0xFFFFFFFF
    if corrupt_crc:
        checksum ^= 0xFFFFFFFF
    return body + struct.pack(">I", checksum)


def _valid_request(request_id: int) -> bytes:
    return encode_request(Prime3WiiRequest(Prime3WiiCommand.RESERVED_MAILBOX, request_id, REQUEST_PAYLOAD))


def build_scenarios() -> list[Scenario]:
    valid_request_1 = _valid_request(1)
    valid_request_42 = _valid_request(42)
    invalid_magic = _encode_raw_request(
        command_raw=Prime3WiiCommand.RESERVED_MAILBOX,
        request_id=2,
        payload=REQUEST_PAYLOAD,
        magic=b"XP3W",
    )
    truncated = valid_request_1[: HEADER_SIZE - 1]
    payload_length_mismatch = _encode_raw_request(
        command_raw=Prime3WiiCommand.RESERVED_MAILBOX,
        request_id=4,
        payload=REQUEST_PAYLOAD,
        declared_payload_length=len(REQUEST_PAYLOAD) + 1,
    )
    unsupported_command = _encode_raw_request(
        command_raw=0x7E,
        request_id=5,
        payload=REQUEST_PAYLOAD,
    )
    bad_crc = _encode_raw_request(
        command_raw=Prime3WiiCommand.RESERVED_MAILBOX,
        request_id=6,
        payload=REQUEST_PAYLOAD,
        corrupt_crc=True,
    )
    return [
        Scenario("valid_request_1", valid_request_1, 1, True),
        Scenario("invalid_magic", invalid_magic, None, False),
        Scenario("truncated_packet", truncated, None, False),
        Scenario("payload_length_mismatch", payload_length_mismatch, None, False),
        Scenario("unsupported_command", unsupported_command, None, False),
        Scenario("bad_crc", bad_crc, None, False),
        Scenario("valid_request_42", valid_request_42, 42, True),
    ]


def _expect_no_reply(udp_socket: socket.socket, timeout_seconds: float) -> None:
    udp_socket.settimeout(timeout_seconds)
    try:
        packet, address = udp_socket.recvfrom(4096)
    except TimeoutError:
        return
    raise RuntimeError(f"Unexpected reply from {address[0]}:{address[1]}: {packet.hex()}")


def _run_scenario(
    udp_socket: socket.socket,
    host: str,
    port: int,
    scenario: Scenario,
    timeout_seconds: float,
) -> ScenarioResult:
    started = time.perf_counter()
    udp_socket.sendto(scenario.packet, (host, port))
    result = ScenarioResult(
        name=scenario.name,
        request_id=scenario.request_id,
        expect_reply=scenario.expect_reply,
        sent_bytes=len(scenario.packet),
        packet_hex=scenario.packet.hex(),
        result="pending",
    )
    if not scenario.expect_reply:
        _expect_no_reply(udp_socket, timeout_seconds)
        result.result = "timeout_expected"
        return result

    udp_socket.settimeout(timeout_seconds)
    packet, address = udp_socket.recvfrom(4096)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    decoded = decode_response(packet, expected_request_id=scenario.request_id)
    if not isinstance(decoded, Prime3WiiResponse):
        raise RuntimeError(f"Expected normal response for {scenario.name}, got error response {decoded!r}")
    if decoded.command is not Prime3WiiCommand.RESERVED_MAILBOX:
        raise RuntimeError(f"Expected RESERVED_MAILBOX response for {scenario.name}, got {decoded.command.name}")
    if decoded.status is not Prime3WiiResponseStatus.OK:
        raise RuntimeError(f"Expected OK status for {scenario.name}, got {decoded.status.name}")
    if decoded.payload != RESPONSE_PAYLOAD:
        raise RuntimeError(
            f"Expected fixed CP3W response payload {RESPONSE_PAYLOAD!r} for {scenario.name}, got {decoded.payload!r}"
        )
    result.result = "reply_received"
    result.endpoint = f"{address[0]}:{address[1]}"
    result.round_trip_ms = elapsed_ms
    result.response_hex = packet.hex()
    result.response_payload_ascii = decoded.payload.decode("ascii")
    result.response_request_id = decoded.request_id
    result.response_command = decoded.command.name
    result.response_status = decoded.status.name
    _expect_no_reply(udp_socket, EXTRA_REPLY_TIMEOUT_SECONDS)
    return result


def run_validation(
    *,
    host: str,
    port: int,
    timeout_seconds: float,
) -> dict[str, object]:
    scenarios = build_scenarios()
    results: list[ScenarioResult] = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        for scenario in scenarios:
            results.append(_run_scenario(udp_socket, host, port, scenario, timeout_seconds))
        _expect_no_reply(udp_socket, EXTRA_REPLY_TIMEOUT_SECONDS)
    return {
        "host": host,
        "port": port,
        "timeout_seconds": timeout_seconds,
        "request_payload_ascii": REQUEST_PAYLOAD.decode("ascii"),
        "response_payload_ascii": RESPONSE_PAYLOAD.decode("ascii"),
        "scenario_order": [scenario.name for scenario in scenarios],
        "results": [dataclasses.asdict(result) for result in results],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_validation(host=args.host, port=args.port, timeout_seconds=args.timeout)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(text)
        return
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
