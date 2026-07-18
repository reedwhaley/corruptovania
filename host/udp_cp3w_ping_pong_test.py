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
    PROTOCOL_MAGIC,
    PROTOCOL_VERSION,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiErrorResponse,
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
UNSUPPORTED_MESSAGE = "Command is unsupported"
EXPECTED_RESPONSE_COMMAND = Prime3WiiCommand.PING


@dataclasses.dataclass(frozen=True)
class Scenario:
    name: str
    packet: bytes
    request_id: int
    request_command: int
    request_payload: bytes
    expected_kind: str


@dataclasses.dataclass
class ScenarioResult:
    name: str
    request_id: int
    request_command: str
    request_payload_hex: str
    request_payload_ascii: str | None
    expected_kind: str
    sent_bytes: int
    packet_hex: str
    result: str
    endpoint: str | None = None
    round_trip_ms: float | None = None
    response_hex: str | None = None
    response_command: str | None = None
    response_status: str | None = None
    response_payload_hex: str | None = None
    response_payload_ascii: str | None = None
    response_error_code: str | None = None
    response_message: str | None = None


def _decode_ascii_if_possible(payload: bytes) -> str | None:
    try:
        return payload.decode("ascii")
    except UnicodeDecodeError:
        return None


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


def build_scenarios() -> list[Scenario]:
    ping_empty = Prime3WiiRequest(Prime3WiiCommand.PING, 1, b"")
    ping_ascii = Prime3WiiRequest(Prime3WiiCommand.PING, 2, b"prime3")
    unsupported = Prime3WiiRequest(Prime3WiiCommand.DISCONNECT, 3, b"")
    ping_binary = Prime3WiiRequest(Prime3WiiCommand.PING, 42, b"\x00prime3\x00")
    ping_final = Prime3WiiRequest(Prime3WiiCommand.PING, 0xFFFFFFFF, b"cp3w-final-20260718")
    return [
        Scenario("ping_empty", encode_request(ping_empty), 1, Prime3WiiCommand.PING, b"", "pong"),
        Scenario("ping_prime3", encode_request(ping_ascii), 2, Prime3WiiCommand.PING, b"prime3", "pong"),
        Scenario(
            "disconnect_unsupported",
            encode_request(unsupported),
            3,
            Prime3WiiCommand.DISCONNECT,
            b"",
            "error",
        ),
        Scenario(
            "invalid_magic",
            _encode_raw_request(
                command_raw=Prime3WiiCommand.PING,
                request_id=4,
                payload=b"bad-magic",
                magic=b"XP3W",
            ),
            4,
            Prime3WiiCommand.PING,
            b"bad-magic",
            "timeout",
        ),
        Scenario(
            "bad_crc",
            _encode_raw_request(
                command_raw=Prime3WiiCommand.PING,
                request_id=5,
                payload=b"bad-crc",
                corrupt_crc=True,
            ),
            5,
            Prime3WiiCommand.PING,
            b"bad-crc",
            "timeout",
        ),
        Scenario(
            "payload_length_mismatch",
            _encode_raw_request(
                command_raw=Prime3WiiCommand.PING,
                request_id=6,
                payload=b"length-mismatch",
                declared_payload_length=len(b"length-mismatch") + 2,
            ),
            6,
            Prime3WiiCommand.PING,
            b"length-mismatch",
            "timeout",
        ),
        Scenario(
            "ping_binary_payload",
            encode_request(ping_binary),
            42,
            Prime3WiiCommand.PING,
            b"\x00prime3\x00",
            "pong",
        ),
        Scenario(
            "ping_final_payload",
            encode_request(ping_final),
            0xFFFFFFFF,
            Prime3WiiCommand.PING,
            b"cp3w-final-20260718",
            "pong",
        ),
    ]


def _expect_no_reply(udp_socket: socket.socket, timeout_seconds: float) -> None:
    udp_socket.settimeout(timeout_seconds)
    try:
        packet, address = udp_socket.recvfrom(4096)
    except TimeoutError:
        return
    raise RuntimeError(f"Unexpected reply from {address[0]}:{address[1]}: {packet.hex()}")


def _validate_success_response(
    scenario: Scenario,
    decoded: Prime3WiiResponse | Prime3WiiErrorResponse,
) -> tuple[str, str | None]:
    if not isinstance(decoded, Prime3WiiResponse):
        raise RuntimeError(f"Expected normal PING response for {scenario.name}, got {decoded!r}")
    if decoded.command is not EXPECTED_RESPONSE_COMMAND:
        raise RuntimeError(
            f"Expected {EXPECTED_RESPONSE_COMMAND.name} response command for {scenario.name}, "
            f"got {decoded.command.name}"
        )
    if decoded.status is not Prime3WiiResponseStatus.OK:
        raise RuntimeError(f"Expected OK response status for {scenario.name}, got {decoded.status.name}")
    if decoded.payload != scenario.request_payload:
        raise RuntimeError(
            f"Expected echoed payload {scenario.request_payload!r} for {scenario.name}, got {decoded.payload!r}"
        )
    return decoded.payload.hex(), _decode_ascii_if_possible(decoded.payload)


def _validate_error_response(scenario: Scenario, decoded: Prime3WiiResponse | Prime3WiiErrorResponse) -> str:
    if not isinstance(decoded, Prime3WiiErrorResponse):
        raise RuntimeError(f"Expected structured error response for {scenario.name}, got {decoded!r}")
    if decoded.command.value != scenario.request_command:
        raise RuntimeError(
            f"Expected error command {Prime3WiiCommand(scenario.request_command).name} for {scenario.name}, "
            f"got {decoded.command.name}"
        )
    if decoded.error_code is not Prime3WiiErrorCode.UNKNOWN_COMMAND:
        raise RuntimeError(f"Expected UNKNOWN_COMMAND error for {scenario.name}, got {decoded.error_code.name}")
    if decoded.message != UNSUPPORTED_MESSAGE:
        raise RuntimeError(
            f"Expected unsupported message {UNSUPPORTED_MESSAGE!r} for {scenario.name}, got {decoded.message!r}"
        )
    return decoded.message


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
        request_command=Prime3WiiCommand(scenario.request_command).name,
        request_payload_hex=scenario.request_payload.hex(),
        request_payload_ascii=_decode_ascii_if_possible(scenario.request_payload),
        expected_kind=scenario.expected_kind,
        sent_bytes=len(scenario.packet),
        packet_hex=scenario.packet.hex(),
        result="pending",
    )

    if scenario.expected_kind == "timeout":
        _expect_no_reply(udp_socket, timeout_seconds)
        result.result = "timeout_expected"
        return result

    udp_socket.settimeout(timeout_seconds)
    response_packet, address = udp_socket.recvfrom(4096)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    decoded = decode_response(response_packet, expected_request_id=scenario.request_id)

    result.result = "reply_received"
    result.endpoint = f"{address[0]}:{address[1]}"
    result.round_trip_ms = elapsed_ms
    result.response_hex = response_packet.hex()

    if scenario.expected_kind == "pong":
        payload_hex, payload_ascii = _validate_success_response(scenario, decoded)
        result.response_command = EXPECTED_RESPONSE_COMMAND.name
        result.response_status = Prime3WiiResponseStatus.OK.name
        result.response_payload_hex = payload_hex
        result.response_payload_ascii = payload_ascii
    else:
        message = _validate_error_response(scenario, decoded)
        result.response_command = Prime3WiiCommand(scenario.request_command).name
        result.response_status = Prime3WiiResponseStatus.ERROR.name
        result.response_error_code = Prime3WiiErrorCode.UNKNOWN_COMMAND.name
        result.response_message = message

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
        "unsupported_message_ascii": UNSUPPORTED_MESSAGE,
        "expected_response_command": EXPECTED_RESPONSE_COMMAND.name,
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
