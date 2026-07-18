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
    GAME_IDENTITY_CAPABILITY_MESSAGE,
    GAME_IDENTITY_INVALID_PAYLOAD_MESSAGE,
    GAME_IDENTITY_NOT_NEGOTIATED_MESSAGE,
    GAME_IDENTITY_PAYLOAD_SIZE,
    GAME_IDENTITY_RUNTIME_CAPABILITIES,
    HEADER_FORMAT,
    HELLO_RUNTIME_CAPABILITIES,
    PRIME3_NTSC_RETAIL_PROFILE_FINGERPRINT,
    PRIME3_NTSC_RETAIL_PROFILE_ID,
    PROTOCOL_MAGIC,
    PROTOCOL_VERSION,
    UNKNOWN_COMMAND_MESSAGE,
    UNSUPPORTED_VERSION_MESSAGE,
    GameIdentityPayload,
    HelloRequestPayload,
    Prime3WiiAvailability,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiErrorResponse,
    Prime3WiiGameId,
    Prime3WiiPacketKind,
    Prime3WiiPlatformId,
    Prime3WiiRegionId,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    Prime3WiiRevisionId,
    compute_accepted_capabilities,
    decode_game_identity_payload,
    decode_hello_response_payload,
    decode_response,
    encode_hello_request_payload,
    encode_request,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 43674
DEFAULT_TIMEOUT_SECONDS = 1.0
EXTRA_REPLY_TIMEOUT_SECONDS = 0.25
CLIENT_NONCE = 0x4944454E
CLIENT_NAME = "identity-validator"
EXPECTED_RUNTIME_MODE = 20
BASELINE_CAPABILITIES = HELLO_RUNTIME_CAPABILITIES
IDENTITY_CAPABILITIES = BASELINE_CAPABILITIES | Prime3WiiCapability.GAME_IDENTITY


@dataclasses.dataclass(frozen=True)
class Scenario:
    name: str
    packet: bytes
    request_id: int | None
    command: Prime3WiiCommand
    expected: str
    expected_payload: bytes | None = None


def _raw_request(
    *,
    command: int,
    request_id: int,
    payload: bytes = b"",
    magic: bytes = PROTOCOL_MAGIC,
    corrupt_crc: bool = False,
) -> bytes:
    body = (
        struct.pack(
            HEADER_FORMAT,
            magic,
            PROTOCOL_VERSION,
            Prime3WiiPacketKind.REQUEST,
            command,
            Prime3WiiResponseStatus.OK,
            request_id,
            len(payload),
        )
        + payload
    )
    crc = zlib.crc32(body) & 0xFFFFFFFF
    if corrupt_crc:
        crc ^= 0xFFFFFFFF
    return body + struct.pack(">I", crc)


def _hello(capabilities: Prime3WiiCapability, *, minimum: int = 1, maximum: int = 1) -> bytes:
    return encode_hello_request_payload(
        HelloRequestPayload(
            min_protocol_version=minimum,
            max_protocol_version=maximum,
            capabilities=capabilities,
            client_nonce=CLIENT_NONCE,
            client_name=CLIENT_NAME,
        )
    )


def build_primary_scenarios() -> list[Scenario]:
    return [
        Scenario(
            "pre_hello_identity",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.GET_GAME_IDENTITY, 1)),
            1,
            Prime3WiiCommand.GET_GAME_IDENTITY,
            "not_negotiated",
        ),
        Scenario(
            "unsupported_version_hello",
            encode_request(
                Prime3WiiRequest(Prime3WiiCommand.HELLO, 2, _hello(IDENTITY_CAPABILITIES, minimum=2, maximum=3))
            ),
            2,
            Prime3WiiCommand.HELLO,
            "unsupported_version",
        ),
        Scenario(
            "valid_hello",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.HELLO, 3, _hello(IDENTITY_CAPABILITIES))),
            3,
            Prime3WiiCommand.HELLO,
            "hello",
        ),
        Scenario(
            "first_identity",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.GET_GAME_IDENTITY, 4)),
            4,
            Prime3WiiCommand.GET_GAME_IDENTITY,
            "identity",
        ),
        Scenario(
            "second_identity",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.GET_GAME_IDENTITY, 5)),
            5,
            Prime3WiiCommand.GET_GAME_IDENTITY,
            "identity",
        ),
        Scenario(
            "ping_regression",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.PING, 6, b"identity-ping")),
            6,
            Prime3WiiCommand.PING,
            "pong",
            b"identity-ping",
        ),
        Scenario(
            "invalid_identity_payload",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.GET_GAME_IDENTITY, 7, b"\x01")),
            7,
            Prime3WiiCommand.GET_GAME_IDENTITY,
            "invalid_payload",
        ),
        Scenario(
            "unsupported_command",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.RESERVED_MAILBOX, 8)),
            8,
            Prime3WiiCommand.RESERVED_MAILBOX,
            "unknown_command",
        ),
        Scenario(
            "invalid_magic",
            _raw_request(command=Prime3WiiCommand.PING, request_id=9, magic=b"XP3W"),
            9,
            Prime3WiiCommand.PING,
            "timeout",
        ),
        Scenario(
            "bad_crc",
            _raw_request(command=Prime3WiiCommand.PING, request_id=10, corrupt_crc=True),
            10,
            Prime3WiiCommand.PING,
            "timeout",
        ),
        Scenario(
            "binary_ping",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.PING, 11, b"\x00binary\x00ping")),
            11,
            Prime3WiiCommand.PING,
            "pong",
            b"\x00binary\x00ping",
        ),
        Scenario(
            "final_identity",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.GET_GAME_IDENTITY, 12)),
            12,
            Prime3WiiCommand.GET_GAME_IDENTITY,
            "identity",
        ),
    ]


def build_capability_omission_scenarios() -> list[Scenario]:
    return [
        Scenario(
            "baseline_hello",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.HELLO, 1, _hello(BASELINE_CAPABILITIES))),
            1,
            Prime3WiiCommand.HELLO,
            "hello_without_identity",
        ),
        Scenario(
            "identity_without_capability",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.GET_GAME_IDENTITY, 2)),
            2,
            Prime3WiiCommand.GET_GAME_IDENTITY,
            "capability_not_negotiated",
        ),
    ]


def validate_identity_response(
    decoded: Prime3WiiResponse | Prime3WiiErrorResponse,
    *,
    request_id: int,
) -> GameIdentityPayload:
    if not isinstance(decoded, Prime3WiiResponse):
        raise RuntimeError(f"Expected identity success, got {decoded!r}")
    if decoded.command is not Prime3WiiCommand.GET_GAME_IDENTITY:
        raise RuntimeError(f"Wrong identity response command: {decoded.command.name}")
    if decoded.status is not Prime3WiiResponseStatus.OK:
        raise RuntimeError(f"Wrong identity response status: {decoded.status.name}")
    if decoded.request_id != request_id:
        raise RuntimeError(f"Wrong identity request ID: {decoded.request_id}")
    if len(decoded.payload) != GAME_IDENTITY_PAYLOAD_SIZE:
        raise RuntimeError(f"Wrong identity payload length: {len(decoded.payload)}")
    identity = decode_game_identity_payload(decoded.payload)
    expected = {
        "game_id": (identity.game_id, Prime3WiiGameId.METROID_PRIME_3_CORRUPTION),
        "platform_id": (identity.platform_id, Prime3WiiPlatformId.WII),
        "region_id": (identity.region_id, Prime3WiiRegionId.NTSC_U),
        "revision_id": (identity.revision_id, Prime3WiiRevisionId.WII_NTSC_3_436),
        "profile_id": (identity.profile_id, PRIME3_NTSC_RETAIL_PROFILE_ID),
        "profile_fingerprint": (identity.profile_fingerprint, PRIME3_NTSC_RETAIL_PROFILE_FINGERPRINT),
        "runtime_build_id": (identity.runtime_build_id, DEFAULT_RUNTIME_BUILD_ID),
        "protocol_version": (identity.protocol_version, PROTOCOL_VERSION),
        "runtime_mode": (identity.runtime_mode, EXPECTED_RUNTIME_MODE),
        "reserved": (identity.reserved, 0),
    }
    for name, (actual, wanted) in expected.items():
        if actual != wanted:
            raise RuntimeError(f"Identity {name} mismatch: received {actual!r}, expected {wanted!r}")
    return identity


def _expect_no_reply(udp_socket: socket.socket, timeout: float) -> None:
    udp_socket.settimeout(timeout)
    try:
        packet, endpoint = udp_socket.recvfrom(4096)
    except TimeoutError:
        return
    raise RuntimeError(f"Unexpected duplicate or stray response from {endpoint}: {packet.hex()}")


def _error_expected(kind: str) -> tuple[Prime3WiiErrorCode, str]:
    return {
        "not_negotiated": (Prime3WiiErrorCode.NOT_NEGOTIATED, GAME_IDENTITY_NOT_NEGOTIATED_MESSAGE),
        "unsupported_version": (Prime3WiiErrorCode.UNSUPPORTED_VERSION, UNSUPPORTED_VERSION_MESSAGE),
        "capability_not_negotiated": (
            Prime3WiiErrorCode.CAPABILITY_NOT_NEGOTIATED,
            GAME_IDENTITY_CAPABILITY_MESSAGE,
        ),
        "invalid_payload": (Prime3WiiErrorCode.INVALID_PAYLOAD_LENGTH, GAME_IDENTITY_INVALID_PAYLOAD_MESSAGE),
        "unknown_command": (Prime3WiiErrorCode.UNKNOWN_COMMAND, UNKNOWN_COMMAND_MESSAGE),
    }[kind]


def _run_sequence(
    *,
    host: str,
    port: int,
    timeout: float,
    scenarios: list[Scenario],
    inter_packet_delay: float = 0.0,
) -> dict[str, object]:
    results: list[dict[str, object]] = []
    identities: list[GameIdentityPayload] = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind((DEFAULT_HOST, 0))
        local_endpoint = f"{udp_socket.getsockname()[0]}:{udp_socket.getsockname()[1]}"
        for scenario in scenarios:
            started = time.perf_counter()
            udp_socket.sendto(scenario.packet, (host, port))
            if scenario.expected == "timeout":
                _expect_no_reply(udp_socket, timeout)
                results.append({"name": scenario.name, "result": "expected_timeout", "request_id": scenario.request_id})
                time.sleep(inter_packet_delay)
                continue
            udp_socket.settimeout(timeout)
            packet, endpoint = udp_socket.recvfrom(4096)
            rtt_ms = (time.perf_counter() - started) * 1000.0
            if endpoint != (host, port):
                raise RuntimeError(f"Unexpected response endpoint {endpoint}; expected {(host, port)}")
            decoded = decode_response(packet, expected_request_id=scenario.request_id)
            detail: dict[str, object] = {
                "name": scenario.name,
                "result": "reply_received",
                "request_id": scenario.request_id,
                "response_endpoint": f"{endpoint[0]}:{endpoint[1]}",
                "rtt_ms": rtt_ms,
                "response_hex": packet.hex(),
            }
            if scenario.expected in {"hello", "hello_without_identity"}:
                if not isinstance(decoded, Prime3WiiResponse) or decoded.command is not Prime3WiiCommand.HELLO:
                    raise RuntimeError(f"Expected HELLO success for {scenario.name}, got {decoded!r}")
                hello = decode_hello_response_payload(decoded.payload)
                expected_runtime = GAME_IDENTITY_RUNTIME_CAPABILITIES
                expected_requested = IDENTITY_CAPABILITIES if scenario.expected == "hello" else BASELINE_CAPABILITIES
                expected_accepted = compute_accepted_capabilities(expected_requested, expected_runtime)
                if (
                    hello.runtime_capabilities != expected_runtime
                    or hello.accepted_client_capabilities != expected_accepted
                ):
                    raise RuntimeError(f"Unexpected HELLO capability negotiation for {scenario.name}")
                detail.update(
                    runtime_capabilities=int(hello.runtime_capabilities),
                    accepted_capabilities=int(hello.accepted_client_capabilities),
                    session_id=hello.session_id,
                )
            elif scenario.expected == "identity":
                identity = validate_identity_response(decoded, request_id=scenario.request_id or 0)
                identities.append(identity)
                detail["identity"] = {
                    **dataclasses.asdict(identity),
                    "game_id": identity.game_id.name,
                    "platform_id": identity.platform_id.name,
                    "region_id": identity.region_id.name,
                    "revision_id": identity.revision_id.name,
                    "availability_flags": int(identity.availability_flags),
                    "availability_names": [
                        flag.name for flag in Prime3WiiAvailability if flag in identity.availability_flags
                    ],
                }
            elif scenario.expected == "pong":
                if not isinstance(decoded, Prime3WiiResponse) or decoded.command is not Prime3WiiCommand.PING:
                    raise RuntimeError(f"Expected PING response for {scenario.name}, got {decoded!r}")
                if decoded.payload != scenario.expected_payload:
                    raise RuntimeError(f"PING payload mismatch for {scenario.name}")
                detail["payload_hex"] = decoded.payload.hex()
            else:
                if not isinstance(decoded, Prime3WiiErrorResponse):
                    raise RuntimeError(f"Expected structured error for {scenario.name}, got {decoded!r}")
                expected_code, expected_message = _error_expected(scenario.expected)
                if decoded.error_code is not expected_code or decoded.message != expected_message:
                    raise RuntimeError(f"Wrong structured error for {scenario.name}: {decoded!r}")
                detail.update(error_code=decoded.error_code.name, error_message=decoded.message)
            _expect_no_reply(udp_socket, EXTRA_REPLY_TIMEOUT_SECONDS)
            results.append(detail)
            time.sleep(inter_packet_delay)
        _expect_no_reply(udp_socket, EXTRA_REPLY_TIMEOUT_SECONDS)
    static_payloads = [
        dataclasses.replace(identity, availability_flags=Prime3WiiAvailability(0)) for identity in identities
    ]
    if static_payloads and any(item != static_payloads[0] for item in static_payloads[1:]):
        raise RuntimeError("Static identity fields changed across repeated responses")
    return {
        "local_endpoint": local_endpoint,
        "remote_endpoint": f"{host}:{port}",
        "scenario_order": [item.name for item in scenarios],
        "results": results,
        "identity_response_count": len(identities),
        "duplicate_responses": 0,
        "stray_responses": 0,
    }


def run_validation(
    *,
    host: str,
    port: int,
    timeout_seconds: float,
    include_capability_omission: bool = False,
    only_capability_omission: bool = False,
    inter_packet_delay: float = 0.0,
) -> dict[str, object]:
    report: dict[str, object] = {}
    if not only_capability_omission:
        report["primary"] = _run_sequence(
            host=host,
            port=port,
            timeout=timeout_seconds,
            scenarios=build_primary_scenarios(),
            inter_packet_delay=inter_packet_delay,
        )
    if include_capability_omission or only_capability_omission:
        report["capability_omission"] = _run_sequence(
            host=host,
            port=port,
            timeout=timeout_seconds,
            scenarios=build_capability_omission_scenarios(),
            inter_packet_delay=inter_packet_delay,
        )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--capability-omission", action="store_true")
    parser.add_argument("--only-capability-omission", action="store_true")
    parser.add_argument("--inter-packet-delay", type=float, default=0.0)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_validation(
        host=args.host,
        port=args.port,
        timeout_seconds=args.timeout,
        include_capability_omission=args.capability_omission,
        only_capability_omission=args.only_capability_omission,
        inter_packet_delay=args.inter_packet_delay,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(text)
    else:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
