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
    DEFAULT_RUNTIME_BUILD_ID,
    DEFAULT_RUNTIME_NAME,
    HEADER_FORMAT,
    HELLO_RUNTIME_CAPABILITIES,
    INVALID_STATE_MESSAGE,
    NOT_NEGOTIATED_MESSAGE,
    PROTOCOL_MAGIC,
    PROTOCOL_VERSION,
    UNKNOWN_COMMAND_MESSAGE,
    UNSUPPORTED_VERSION_MESSAGE,
    HelloRequestPayload,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiErrorResponse,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    compute_accepted_capabilities,
    decode_hello_response_payload,
    decode_response,
    derive_session_id,
    encode_hello_request_payload,
    encode_request,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 43674
DEFAULT_TIMEOUT_SECONDS = 1.0
EXTRA_REPLY_TIMEOUT_SECONDS = 0.25
CLIENT_CAPABILITIES = (
    Prime3WiiCapability.HELLO_NEGOTIATION
    | Prime3WiiCapability.PING
    | Prime3WiiCapability.STRUCTURED_ERRORS
    | Prime3WiiCapability.DETERMINISTIC_SESSION_ID
    | Prime3WiiCapability.READ_MEMORY
)
CLIENT_NONCE = 0x43503357
CLIENT_NAME = "randovania"
EXPECTED_RUNTIME_MODE = 19


@dataclasses.dataclass(frozen=True)
class Scenario:
    name: str
    packet: bytes
    request_id: int | None
    request_command: int
    expected_kind: str
    expected_payload: bytes | None = None


@dataclasses.dataclass
class ScenarioResult:
    name: str
    expected_kind: str
    request_command: str
    request_id: int | None
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
    session_id: int | None = None
    accepted_capabilities: int | None = None
    runtime_capabilities: int | None = None
    runtime_build_id: int | None = None


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
    valid_hello = HelloRequestPayload(
        min_protocol_version=1,
        max_protocol_version=1,
        capabilities=CLIENT_CAPABILITIES,
        client_nonce=CLIENT_NONCE,
        client_name=CLIENT_NAME,
    )
    changed_hello = dataclasses.replace(valid_hello, client_nonce=CLIENT_NONCE ^ 1)
    unsupported_hello = dataclasses.replace(valid_hello, min_protocol_version=2, max_protocol_version=3)
    return [
        Scenario(
            "pre_hello_ping",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.PING, 1, b"before")),
            1,
            Prime3WiiCommand.PING,
            "not_negotiated",
        ),
        Scenario(
            "unsupported_version_hello",
            encode_request(
                Prime3WiiRequest(
                    Prime3WiiCommand.HELLO,
                    2,
                    encode_hello_request_payload(unsupported_hello),
                )
            ),
            2,
            Prime3WiiCommand.HELLO,
            "unsupported_version",
        ),
        Scenario(
            "valid_hello",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.HELLO, 3, encode_hello_request_payload(valid_hello))),
            3,
            Prime3WiiCommand.HELLO,
            "hello_success",
        ),
        Scenario(
            "duplicate_hello",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.HELLO, 4, encode_hello_request_payload(valid_hello))),
            4,
            Prime3WiiCommand.HELLO,
            "hello_duplicate",
        ),
        Scenario(
            "changed_hello",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.HELLO, 5, encode_hello_request_payload(changed_hello))),
            5,
            Prime3WiiCommand.HELLO,
            "invalid_state",
        ),
        Scenario(
            "post_hello_ping",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.PING, 6, b"after-hello")),
            6,
            Prime3WiiCommand.PING,
            "pong",
            b"after-hello",
        ),
        Scenario(
            "unsupported_command",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.DISCONNECT, 7, b"")),
            7,
            Prime3WiiCommand.DISCONNECT,
            "unknown_command",
        ),
        Scenario(
            "invalid_magic",
            _encode_raw_request(command_raw=Prime3WiiCommand.PING, request_id=8, payload=b"bad-magic", magic=b"XP3W"),
            8,
            Prime3WiiCommand.PING,
            "timeout",
        ),
        Scenario(
            "bad_crc",
            _encode_raw_request(command_raw=Prime3WiiCommand.PING, request_id=9, payload=b"bad-crc", corrupt_crc=True),
            9,
            Prime3WiiCommand.PING,
            "timeout",
        ),
        Scenario(
            "final_ping_zero_bytes",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.PING, 0xFFFFFFFF, b"\x00after\x00hello\x00")),
            0xFFFFFFFF,
            Prime3WiiCommand.PING,
            "pong",
            b"\x00after\x00hello\x00",
        ),
    ]


def _expect_no_reply(udp_socket: socket.socket, timeout_seconds: float) -> None:
    udp_socket.settimeout(timeout_seconds)
    try:
        packet, address = udp_socket.recvfrom(4096)
    except TimeoutError:
        return
    raise RuntimeError(f"Unexpected reply from {address[0]}:{address[1]}: {packet.hex()}")


def _validate_hello_response(
    scenario: Scenario,
    decoded: Prime3WiiResponse | Prime3WiiErrorResponse,
    expected_session_id: int | None,
) -> tuple[int, int, int, int]:
    if not isinstance(decoded, Prime3WiiResponse):
        raise RuntimeError(f"Expected HELLO success for {scenario.name}, got {decoded!r}")
    if decoded.command is not Prime3WiiCommand.HELLO:
        raise RuntimeError(f"Expected HELLO command for {scenario.name}, got {decoded.command.name}")
    if decoded.status is not Prime3WiiResponseStatus.OK:
        raise RuntimeError(f"Expected OK status for {scenario.name}, got {decoded.status.name}")
    payload = decode_hello_response_payload(decoded.payload)
    accepted_capabilities = compute_accepted_capabilities(CLIENT_CAPABILITIES, HELLO_RUNTIME_CAPABILITIES)
    derived_session_id = derive_session_id(
        selected_protocol_version=1,
        client_nonce=CLIENT_NONCE,
        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
        runtime_capabilities=HELLO_RUNTIME_CAPABILITIES,
        accepted_client_capabilities=accepted_capabilities,
    )
    if payload.selected_protocol_version != 1:
        raise RuntimeError(f"Expected selected protocol 1 for {scenario.name}, got {payload.selected_protocol_version}")
    if payload.runtime_capabilities != HELLO_RUNTIME_CAPABILITIES:
        raise RuntimeError(
            f"Unexpected runtime capability mask for {scenario.name}: {int(payload.runtime_capabilities)}"
        )
    if payload.accepted_client_capabilities != accepted_capabilities:
        raise RuntimeError(
            f"Unexpected accepted capability mask for {scenario.name}: {int(payload.accepted_client_capabilities)}"
        )
    if payload.runtime_build_id != DEFAULT_RUNTIME_BUILD_ID:
        raise RuntimeError(f"Unexpected runtime build ID for {scenario.name}: 0x{payload.runtime_build_id:08X}")
    if payload.runtime_mode != EXPECTED_RUNTIME_MODE:
        raise RuntimeError(f"Unexpected runtime mode for {scenario.name}: {payload.runtime_mode}")
    if payload.runtime_name != DEFAULT_RUNTIME_NAME:
        raise RuntimeError(f"Unexpected runtime name for {scenario.name}: {payload.runtime_name!r}")
    if payload.session_id != derived_session_id:
        raise RuntimeError(f"Unexpected session ID for {scenario.name}: 0x{payload.session_id:08X}")
    if expected_session_id is not None and payload.session_id != expected_session_id:
        raise RuntimeError(f"Expected repeated session ID 0x{expected_session_id:08X} for {scenario.name}")
    return (
        payload.session_id,
        int(payload.accepted_client_capabilities),
        int(payload.runtime_capabilities),
        payload.runtime_build_id,
    )


def _validate_error_response(
    scenario: Scenario,
    decoded: Prime3WiiResponse | Prime3WiiErrorResponse,
) -> tuple[str, str]:
    if not isinstance(decoded, Prime3WiiErrorResponse):
        raise RuntimeError(f"Expected structured error response for {scenario.name}, got {decoded!r}")
    expected_map = {
        "not_negotiated": (Prime3WiiErrorCode.NOT_NEGOTIATED, NOT_NEGOTIATED_MESSAGE),
        "unsupported_version": (Prime3WiiErrorCode.UNSUPPORTED_VERSION, UNSUPPORTED_VERSION_MESSAGE),
        "invalid_state": (Prime3WiiErrorCode.INVALID_STATE, INVALID_STATE_MESSAGE),
        "unknown_command": (Prime3WiiErrorCode.UNKNOWN_COMMAND, UNKNOWN_COMMAND_MESSAGE),
    }
    expected_code, expected_message = expected_map[scenario.expected_kind]
    if decoded.command.value != scenario.request_command:
        raise RuntimeError(f"Unexpected error command for {scenario.name}: {decoded.command.name}")
    if decoded.error_code is not expected_code:
        raise RuntimeError(f"Unexpected error code for {scenario.name}: {decoded.error_code.name}")
    if decoded.message != expected_message:
        raise RuntimeError(f"Unexpected error message for {scenario.name}: {decoded.message!r}")
    return decoded.error_code.name, decoded.message


def _validate_pong_response(
    scenario: Scenario,
    decoded: Prime3WiiResponse | Prime3WiiErrorResponse,
) -> tuple[str, str | None]:
    if not isinstance(decoded, Prime3WiiResponse):
        raise RuntimeError(f"Expected PING response for {scenario.name}, got {decoded!r}")
    if decoded.command is not Prime3WiiCommand.PING:
        raise RuntimeError(f"Expected PING response command for {scenario.name}, got {decoded.command.name}")
    if decoded.status is not Prime3WiiResponseStatus.OK:
        raise RuntimeError(f"Expected OK status for {scenario.name}, got {decoded.status.name}")
    if decoded.payload != scenario.expected_payload:
        raise RuntimeError(f"Unexpected echoed payload for {scenario.name}: {decoded.payload!r}")
    return decoded.payload.hex(), _decode_ascii_if_possible(decoded.payload)


def _run_scenario(
    udp_socket: socket.socket,
    host: str,
    port: int,
    scenario: Scenario,
    timeout_seconds: float,
    expected_session_id: int | None,
) -> tuple[ScenarioResult, int | None]:
    started = time.perf_counter()
    udp_socket.sendto(scenario.packet, (host, port))
    result = ScenarioResult(
        name=scenario.name,
        expected_kind=scenario.expected_kind,
        request_command=Prime3WiiCommand(scenario.request_command).name,
        request_id=scenario.request_id,
        packet_hex=scenario.packet.hex(),
        result="pending",
    )

    if scenario.expected_kind == "timeout":
        _expect_no_reply(udp_socket, timeout_seconds)
        result.result = "timeout_expected"
        return result, expected_session_id

    udp_socket.settimeout(timeout_seconds)
    response_packet, address = udp_socket.recvfrom(4096)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    decoded = decode_response(response_packet, expected_request_id=scenario.request_id)
    result.result = "reply_received"
    result.endpoint = f"{address[0]}:{address[1]}"
    result.round_trip_ms = elapsed_ms
    result.response_hex = response_packet.hex()

    if scenario.expected_kind in {"hello_success", "hello_duplicate"}:
        session_id, accepted_capabilities, runtime_capabilities, runtime_build_id = _validate_hello_response(
            scenario, decoded, expected_session_id
        )
        result.response_command = Prime3WiiCommand.HELLO.name
        result.response_status = Prime3WiiResponseStatus.OK.name
        result.session_id = session_id
        result.accepted_capabilities = accepted_capabilities
        result.runtime_capabilities = runtime_capabilities
        result.runtime_build_id = runtime_build_id
        expected_session_id = session_id
    elif scenario.expected_kind == "pong":
        payload_hex, payload_ascii = _validate_pong_response(scenario, decoded)
        result.response_command = Prime3WiiCommand.PING.name
        result.response_status = Prime3WiiResponseStatus.OK.name
        result.response_payload_hex = payload_hex
        result.response_payload_ascii = payload_ascii
    else:
        error_code, message = _validate_error_response(scenario, decoded)
        result.response_command = Prime3WiiCommand(scenario.request_command).name
        result.response_status = Prime3WiiResponseStatus.ERROR.name
        result.response_error_code = error_code
        result.response_message = message

    _expect_no_reply(udp_socket, EXTRA_REPLY_TIMEOUT_SECONDS)
    return result, expected_session_id


def run_validation(*, host: str, port: int, timeout_seconds: float) -> dict[str, object]:
    scenarios = build_scenarios()
    results: list[ScenarioResult] = []
    expected_session_id: int | None = None
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind(("127.0.0.1", 0))
        local_endpoint = f"{udp_socket.getsockname()[0]}:{udp_socket.getsockname()[1]}"
        for scenario in scenarios:
            result, expected_session_id = _run_scenario(
                udp_socket,
                host,
                port,
                scenario,
                timeout_seconds,
                expected_session_id,
            )
            results.append(result)
        _expect_no_reply(udp_socket, EXTRA_REPLY_TIMEOUT_SECONDS)
    return {
        "host": host,
        "port": port,
        "timeout_seconds": timeout_seconds,
        "local_endpoint": local_endpoint,
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
