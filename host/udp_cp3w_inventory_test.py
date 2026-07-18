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
    INVENTORY_ITEM_IDS,
    INVENTORY_PAYLOAD_SIZE,
    PROTOCOL_MAGIC,
    PROTOCOL_VERSION,
    GameIdentityPayload,
    HelloRequestPayload,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiErrorResponse,
    Prime3WiiInventorySnapshot,
    Prime3WiiPacketKind,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    decode_game_identity_payload,
    decode_hello_response_payload,
    decode_inventory_payload,
    decode_response,
    encode_hello_request_payload,
    encode_request,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 43674
DEFAULT_TIMEOUT = 1.0
EXTRA_REPLY_TIMEOUT = 0.25
CLIENT_NONCE = 0x494E5631
CLIENT_NAME = "inventory-validator"
REQUESTED_CAPABILITIES = (
    Prime3WiiCapability.HELLO_NEGOTIATION
    | Prime3WiiCapability.PING
    | Prime3WiiCapability.STRUCTURED_ERRORS
    | Prime3WiiCapability.DETERMINISTIC_SESSION_ID
    | Prime3WiiCapability.GAME_IDENTITY
    | Prime3WiiCapability.INVENTORY_STATE
)


@dataclasses.dataclass(frozen=True)
class Scenario:
    name: str
    packet: bytes
    request_id: int | None
    command: Prime3WiiCommand
    expected: str
    expected_payload: bytes | None = None


def _raw_request(
    command: int,
    request_id: int,
    payload: bytes = b"",
    *,
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
    return encode_hello_request_payload(HelloRequestPayload(minimum, maximum, capabilities, CLIENT_NONCE, CLIENT_NAME))


def build_primary_scenarios() -> list[Scenario]:
    request = lambda command, request_id, payload=b"": encode_request(  # noqa: E731
        Prime3WiiRequest(command, request_id, payload)
    )
    return [
        Scenario(
            "pre_hello_inventory",
            request(Prime3WiiCommand.GET_INVENTORY, 1),
            1,
            Prime3WiiCommand.GET_INVENTORY,
            "not_negotiated",
        ),
        Scenario(
            "unsupported_version_hello",
            request(Prime3WiiCommand.HELLO, 2, _hello(REQUESTED_CAPABILITIES, minimum=2, maximum=3)),
            2,
            Prime3WiiCommand.HELLO,
            "unsupported_version",
        ),
        Scenario(
            "valid_hello",
            request(Prime3WiiCommand.HELLO, 3, _hello(REQUESTED_CAPABILITIES)),
            3,
            Prime3WiiCommand.HELLO,
            "hello",
        ),
        Scenario(
            "game_identity",
            request(Prime3WiiCommand.GET_GAME_IDENTITY, 4),
            4,
            Prime3WiiCommand.GET_GAME_IDENTITY,
            "identity",
        ),
        Scenario(
            "inventory_1", request(Prime3WiiCommand.GET_INVENTORY, 5), 5, Prime3WiiCommand.GET_INVENTORY, "inventory"
        ),
        Scenario(
            "inventory_2", request(Prime3WiiCommand.GET_INVENTORY, 6), 6, Prime3WiiCommand.GET_INVENTORY, "inventory"
        ),
        Scenario(
            "ping",
            request(Prime3WiiCommand.PING, 7, b"inventory-ping"),
            7,
            Prime3WiiCommand.PING,
            "pong",
            b"inventory-ping",
        ),
        Scenario(
            "invalid_inventory_payload",
            request(Prime3WiiCommand.GET_INVENTORY, 8, b"\x01"),
            8,
            Prime3WiiCommand.GET_INVENTORY,
            "invalid_payload",
        ),
        Scenario(
            "unsupported_command",
            request(Prime3WiiCommand.RESERVED_MAILBOX, 9),
            9,
            Prime3WiiCommand.RESERVED_MAILBOX,
            "unknown_command",
        ),
        Scenario(
            "invalid_magic",
            _raw_request(Prime3WiiCommand.GET_INVENTORY, 10, magic=b"NOPE"),
            None,
            Prime3WiiCommand.GET_INVENTORY,
            "timeout",
        ),
        Scenario(
            "bad_crc",
            _raw_request(Prime3WiiCommand.GET_INVENTORY, 11, corrupt_crc=True),
            None,
            Prime3WiiCommand.GET_INVENTORY,
            "timeout",
        ),
        Scenario(
            "binary_ping", request(Prime3WiiCommand.PING, 12, b"A\0B"), 12, Prime3WiiCommand.PING, "pong", b"A\0B"
        ),
        Scenario(
            "inventory_3", request(Prime3WiiCommand.GET_INVENTORY, 13), 13, Prime3WiiCommand.GET_INVENTORY, "inventory"
        ),
        Scenario(
            "inventory_final",
            request(Prime3WiiCommand.GET_INVENTORY, 14),
            14,
            Prime3WiiCommand.GET_INVENTORY,
            "inventory",
        ),
    ]


def build_capability_omission_scenarios() -> list[Scenario]:
    capabilities = REQUESTED_CAPABILITIES & ~Prime3WiiCapability.INVENTORY_STATE
    return [
        Scenario(
            "hello_without_inventory",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.HELLO, 1, _hello(capabilities))),
            1,
            Prime3WiiCommand.HELLO,
            "hello_without_inventory",
        ),
        Scenario(
            "inventory_capability_rejected",
            encode_request(Prime3WiiRequest(Prime3WiiCommand.GET_INVENTORY, 2)),
            2,
            Prime3WiiCommand.GET_INVENTORY,
            "capability_not_negotiated",
        ),
    ]


def decode_inventory_response(packet: bytes, request_id: int) -> Prime3WiiInventorySnapshot:
    response = decode_response(packet, expected_request_id=request_id)
    if not isinstance(response, Prime3WiiResponse):
        raise ValueError(f"Expected GET_INVENTORY success, received {response.error_code.name}.")
    if response.command is not Prime3WiiCommand.GET_INVENTORY or response.status is not Prime3WiiResponseStatus.OK:
        raise ValueError("Unexpected GET_INVENTORY response command or status.")
    if len(response.payload) != INVENTORY_PAYLOAD_SIZE:
        raise ValueError(f"Expected {INVENTORY_PAYLOAD_SIZE} payload bytes, got {len(response.payload)}.")
    return decode_inventory_payload(response.payload)


def assert_selected_records(snapshot: Prime3WiiInventorySnapshot, expected: dict[int, tuple[int, int]]) -> None:
    for item_id, values in expected.items():
        record = snapshot.record_for_item_id(item_id)
        if (record.amount, record.capacity) != values:
            raise ValueError(f"Item ID {item_id} was {(record.amount, record.capacity)}, expected {values}.")


def _expect_error(response: Prime3WiiResponse | Prime3WiiErrorResponse, code: Prime3WiiErrorCode) -> None:
    if not isinstance(response, Prime3WiiErrorResponse) or response.error_code is not code:
        raise ValueError(f"Expected {code.name}, received {response!r}.")


def _summarize_snapshot(snapshot: Prime3WiiInventorySnapshot) -> dict[str, object]:
    nonzero = [
        {"index": index, "item_id": INVENTORY_ITEM_IDS[index], "amount": record.amount, "capacity": record.capacity}
        for index, record in enumerate(snapshot.records)
        if record.amount or record.capacity
    ]
    return {
        "schema_version": snapshot.schema_version,
        "availability": int(snapshot.availability_flags),
        "sequence": snapshot.snapshot_sequence,
        "record_count": len(snapshot.records),
        "nonzero_records": nonzero,
    }


def _validate_response(scenario: Scenario, packet: bytes) -> dict[str, object]:
    assert scenario.request_id is not None
    response = decode_response(packet, expected_request_id=scenario.request_id)
    if response.command is not scenario.command:
        raise ValueError(f"Expected {scenario.command.name}, received {response.command.name}.")
    if scenario.expected == "not_negotiated":
        _expect_error(response, Prime3WiiErrorCode.NOT_NEGOTIATED)
    elif scenario.expected == "unsupported_version":
        _expect_error(response, Prime3WiiErrorCode.UNSUPPORTED_VERSION)
    elif scenario.expected == "capability_not_negotiated":
        _expect_error(response, Prime3WiiErrorCode.CAPABILITY_NOT_NEGOTIATED)
    elif scenario.expected == "invalid_payload":
        _expect_error(response, Prime3WiiErrorCode.INVALID_PAYLOAD_LENGTH)
    elif scenario.expected == "unknown_command":
        _expect_error(response, Prime3WiiErrorCode.UNKNOWN_COMMAND)
    elif scenario.expected.startswith("hello"):
        if not isinstance(response, Prime3WiiResponse):
            raise ValueError(f"HELLO failed: {response!r}")
        hello = decode_hello_response_payload(response.payload)
        if (
            scenario.expected == "hello"
            and not hello.accepted_client_capabilities & Prime3WiiCapability.INVENTORY_STATE
        ):
            raise ValueError("Runtime omitted requested INVENTORY_STATE capability.")
        if (
            scenario.expected == "hello_without_inventory"
            and hello.accepted_client_capabilities & Prime3WiiCapability.INVENTORY_STATE
        ):
            raise ValueError("Runtime accepted omitted INVENTORY_STATE capability.")
        return {"accepted_capabilities": int(hello.accepted_client_capabilities), "runtime_mode": hello.runtime_mode}
    elif scenario.expected == "identity":
        if not isinstance(response, Prime3WiiResponse):
            raise ValueError(f"Identity failed: {response!r}")
        identity: GameIdentityPayload = decode_game_identity_payload(response.payload)
        return {"profile_id": identity.profile_id, "availability": int(identity.availability_flags)}
    elif scenario.expected == "inventory":
        snapshot = decode_inventory_response(packet, scenario.request_id)
        return _summarize_snapshot(snapshot)
    elif scenario.expected == "pong":
        if not isinstance(response, Prime3WiiResponse) or response.payload != scenario.expected_payload:
            raise ValueError("PING response was not an exact payload echo.")
    return {}


def _run_sequence(host: str, port: int, scenarios: list[Scenario], timeout: float, delay: float) -> dict[str, object]:
    results: list[dict[str, object]] = []
    seen_packets: set[bytes] = set()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind((DEFAULT_HOST, 0))
        local_endpoint = f"{udp_socket.getsockname()[0]}:{udp_socket.getsockname()[1]}"
        for scenario in scenarios:
            started = time.perf_counter()
            udp_socket.sendto(scenario.packet, (host, port))
            if scenario.expected == "timeout":
                udp_socket.settimeout(timeout)
                try:
                    packet, endpoint = udp_socket.recvfrom(2048)
                except TimeoutError:
                    results.append({"name": scenario.name, "result": "timeout", "rtt_ms": None})
                else:
                    raise ValueError(f"Unexpected response from {endpoint}: {packet.hex()}")
            else:
                udp_socket.settimeout(timeout)
                packet, endpoint = udp_socket.recvfrom(2048)
                if packet in seen_packets:
                    raise ValueError(f"Duplicate response detected for {scenario.name}.")
                seen_packets.add(packet)
                details = _validate_response(scenario, packet)
                results.append(
                    {
                        "name": scenario.name,
                        "result": "ok",
                        "endpoint": f"{endpoint[0]}:{endpoint[1]}",
                        "rtt_ms": (time.perf_counter() - started) * 1000,
                        **details,
                    }
                )
            if delay:
                time.sleep(delay)
        udp_socket.settimeout(EXTRA_REPLY_TIMEOUT)
        try:
            packet, endpoint = udp_socket.recvfrom(2048)
        except TimeoutError:
            stray = False
        else:
            raise ValueError(f"Stray response after terminal sequence from {endpoint}: {packet.hex()}")
    return {
        "local_endpoint": local_endpoint,
        "remote_endpoint": f"{host}:{port}",
        "stray_response": stray,
        "results": results,
    }


def run_validation(
    host: str, port: int, timeout: float, delay: float, *, only_capability_omission: bool
) -> dict[str, object]:
    scenarios = build_capability_omission_scenarios() if only_capability_omission else build_primary_scenarios()
    return _run_sequence(host, port, scenarios, timeout, delay)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate CP3W GET_INVENTORY against a live Prime 3 Wii runtime.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--inter-packet-delay", type=float, default=0.05)
    parser.add_argument("--only-capability-omission", action="store_true")
    parser.add_argument("--json-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_validation(
        args.host,
        args.port,
        args.timeout,
        args.inter_packet_delay,
        only_capability_omission=args.only_capability_omission,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
    if args.json_output is not None:
        args.json_output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
