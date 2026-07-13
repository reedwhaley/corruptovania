from __future__ import annotations

import argparse
import json
import os
import secrets
import socket
import struct
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__ in {None, ""}:
    _repository_root = Path(__file__).resolve().parents[2]
    _repository_root_str = os.fspath(_repository_root)
    if _repository_root_str not in sys.path:
        sys.path.insert(0, _repository_root_str)

REQUEST_MAGIC = b"P3UD"
RESPONSE_MAGIC = b"P3UD"
PROTOCOL_VERSION = 1
DEFAULT_PORT = 43674
REQUEST_STRUCT = struct.Struct(">4sIII")
RESPONSE_STRUCT = struct.Struct(">4sIIIIIII16s")


@dataclass(frozen=True)
class DiagnosticRequest:
    sequence: int

    def to_bytes(self) -> bytes:
        return REQUEST_STRUCT.pack(REQUEST_MAGIC, PROTOCOL_VERSION, self.sequence, 0)


@dataclass(frozen=True)
class DiagnosticResponse:
    responding_address: str
    responding_port: int
    sequence: int
    heartbeat: int
    recurring_poll_counter: int
    transport_state: int
    host_id: int
    receive_count: int
    last_receive_length: int
    echoed_request_preview_hex: str
    round_trip_ms: float

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
    if len(data) != RESPONSE_STRUCT.size:
        raise ValueError(f"Expected {RESPONSE_STRUCT.size} response bytes, got {len(data)}.")
    (
        magic,
        version,
        response_sequence,
        recurring_poll_counter,
        transport_state,
        host_id,
        receive_count,
        last_receive_length,
        echoed_preview,
    ) = RESPONSE_STRUCT.unpack(data)
    if magic != RESPONSE_MAGIC:
        raise ValueError(f"Wrong response magic: expected {RESPONSE_MAGIC!r}, got {magic!r}.")
    if version != PROTOCOL_VERSION:
        raise ValueError(f"Wrong response protocol version: expected {PROTOCOL_VERSION}, got {version}.")
    if last_receive_length > 0xFFFFFFFF:
        raise ValueError(f"Malformed last_receive_length value {last_receive_length}.")
    echoed_sequence = int.from_bytes(echoed_preview[8:12], "big")
    if echoed_sequence != expected_sequence:
        raise ValueError(f"Wrong echoed request sequence: expected {expected_sequence}, got {echoed_sequence}.")
    return DiagnosticResponse(
        responding_address=responding_address[0],
        responding_port=responding_address[1],
        sequence=response_sequence,
        heartbeat=recurring_poll_counter,
        recurring_poll_counter=recurring_poll_counter,
        transport_state=transport_state,
        host_id=host_id,
        receive_count=receive_count,
        last_receive_length=last_receive_length,
        echoed_request_preview_hex=echoed_preview.hex(),
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
        for _attempt in range(retries):
            started = time.perf_counter()
            udp_socket.sendto(request_bytes, (host, port))
            try:
                response_bytes, responding_address = udp_socket.recvfrom(RESPONSE_STRUCT.size + 32)
            except (TimeoutError, ConnectionResetError) as exc:
                last_error = exc
                continue
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            return parse_response(
                response_bytes,
                expected_sequence=request.sequence,
                responding_address=responding_address,
                round_trip_ms=elapsed_ms,
            )
    assert last_error is not None
    raise TimeoutError(f"No diagnostic response from {host}:{port} after {retries} attempts.") from last_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--sequence", type=lambda value: int(value, 0))
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = query_runtime(
        args.host,
        port=args.port,
        sequence=args.sequence,
        timeout=args.timeout,
        retries=args.retries,
    )
    text = result.to_json_text()
    if args.output is None:
        sys.stdout.write(text)
        return
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
