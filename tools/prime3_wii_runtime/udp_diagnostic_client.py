from __future__ import annotations

import argparse
import json
import os
import secrets
import socket
import sys
import time
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

if __package__ in {None, ""}:
    _repository_root = Path(__file__).resolve().parents[2]
    _repository_root_str = os.fspath(_repository_root)
    if _repository_root_str not in sys.path:
        sys.path.insert(0, _repository_root_str)

from randovania.game_connection.executor.prime3_wii_protocol import (
    INVENTORY_RUNTIME_CAPABILITIES,
    PROTOCOL_VERSION,
    HelloRequestPayload,
    Prime3WiiCommand,
    Prime3WiiErrorResponse,
    Prime3WiiProtocolError,
    Prime3WiiRequest,
    decode_hello_response_payload,
    decode_response,
    encode_hello_request_payload,
    encode_request,
)

DEFAULT_PORT = 43674


@dataclass(frozen=True)
class DiagnosticRequest:
    sequence: int

    def to_bytes(self) -> bytes:
        hello = HelloRequestPayload(
            min_protocol_version=PROTOCOL_VERSION,
            max_protocol_version=PROTOCOL_VERSION,
            capabilities=INVENTORY_RUNTIME_CAPABILITIES,
            client_nonce=self.sequence,
            client_name="CP3W diagnostic probe",
        )
        return encode_request(
            Prime3WiiRequest(
                command=Prime3WiiCommand.HELLO,
                request_id=self.sequence,
                payload=encode_hello_request_payload(hello),
            )
        )


@dataclass(frozen=True)
class DiagnosticResponse:
    responding_address: str
    responding_port: int
    request_id: int
    selected_protocol_version: int
    runtime_capabilities: int
    accepted_client_capabilities: int
    session_id: int
    runtime_build_id: int
    runtime_build_id_text: str
    runtime_mode: int
    runtime_metadata_version: int
    runtime_name: str
    round_trip_ms: float
    attempt_count: int = 1
    attempted_at_utc: str = ""
    local_address: str = ""
    local_port: int = 0
    request_length: int = 0
    request_hex: str = ""
    response_length: int = 0
    response_hex: str = ""

    def to_json_text(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True) + "\n"


def build_request(*, sequence: int | None = None) -> DiagnosticRequest:
    value = secrets.randbits(32) if sequence is None else sequence
    if not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"Sequence must be a 32-bit unsigned integer, got {value}.")
    return DiagnosticRequest(sequence=value)


def parse_response(
    data: bytes,
    *,
    expected_sequence: int,
    responding_address: tuple[str, int],
    round_trip_ms: float,
) -> DiagnosticResponse:
    try:
        response = decode_response(data, expected_request_id=expected_sequence)
    except Prime3WiiProtocolError as exc:
        raise ValueError(f"Malformed CP3W response: {exc}") from exc
    if isinstance(response, Prime3WiiErrorResponse):
        raise ValueError(f"CP3W HELLO failed with {response.error_code.name}: {response.message}")
    if response.command is not Prime3WiiCommand.HELLO:
        raise ValueError(f"Expected CP3W HELLO response, got {response.command.name}.")
    hello = decode_hello_response_payload(response.payload)
    return DiagnosticResponse(
        responding_address=responding_address[0],
        responding_port=responding_address[1],
        request_id=response.request_id,
        selected_protocol_version=hello.selected_protocol_version,
        runtime_capabilities=int(hello.runtime_capabilities),
        accepted_client_capabilities=int(hello.accepted_client_capabilities),
        session_id=hello.session_id,
        runtime_build_id=hello.runtime_build_id,
        runtime_build_id_text=hello.runtime_build_id.to_bytes(4, "big").decode("ascii", errors="replace"),
        runtime_mode=hello.runtime_mode,
        runtime_metadata_version=hello.runtime_metadata_version,
        runtime_name=hello.runtime_name,
        round_trip_ms=round_trip_ms,
    )


def query_runtime(
    host: str,
    *,
    port: int = DEFAULT_PORT,
    sequence: int | None = None,
    timeout: float = 1.0,
    retries: int = 3,
) -> DiagnosticResponse:
    if timeout <= 0:
        raise ValueError(f"Timeout must be positive, got {timeout}.")
    if retries <= 0:
        raise ValueError(f"Retry count must be positive, got {retries}.")

    request = build_request(sequence=sequence)
    request_bytes = request.to_bytes()
    last_error: Exception | None = None
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.settimeout(timeout)
        for attempt in range(1, retries + 1):
            attempted_at_utc = datetime.now(UTC).isoformat()
            started = time.perf_counter()
            udp_socket.sendto(request_bytes, (host, port))
            local_address, local_port = udp_socket.getsockname()
            try:
                response_bytes, responding_address = udp_socket.recvfrom(2048)
            except (TimeoutError, ConnectionResetError) as exc:
                last_error = exc
                continue
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            response = parse_response(
                response_bytes,
                expected_sequence=request.sequence,
                responding_address=responding_address,
                round_trip_ms=elapsed_ms,
            )
            return replace(
                response,
                attempt_count=attempt,
                attempted_at_utc=attempted_at_utc,
                local_address=local_address,
                local_port=local_port,
                request_length=len(request_bytes),
                request_hex=request_bytes.hex(),
                response_length=len(response_bytes),
                response_hex=response_bytes.hex(),
            )
    assert last_error is not None
    raise TimeoutError(f"No diagnostic response from {host}:{port} after {retries} attempts.") from last_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, choices=(DEFAULT_PORT,), default=DEFAULT_PORT)
    parser.add_argument("--sequence", type=lambda value: int(value, 0))
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--output")
    return parser.parse_args()


def _failure_json(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        classification = "timeout"
    elif isinstance(exc, ValueError):
        classification = "malformed_response"
    else:
        classification = "socket_error"
    return (
        json.dumps(
            {
                "classification": classification,
                "error": str(exc),
                "timestamp_utc": datetime.now(UTC).isoformat(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def main() -> int:
    args = parse_args()
    try:
        result = query_runtime(
            args.host,
            port=args.port,
            sequence=args.sequence,
            timeout=args.timeout,
            retries=args.retries,
        )
    except TimeoutError as exc:
        sys.stderr.write(_failure_json(exc))
        return 2
    except ValueError as exc:
        sys.stderr.write(_failure_json(exc))
        return 4
    except OSError as exc:
        sys.stderr.write(_failure_json(exc))
        return 5
    text = result.to_json_text()
    if args.output is None:
        sys.stdout.write(text)
        return 0
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
