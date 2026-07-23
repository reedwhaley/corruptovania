from __future__ import annotations

import dataclasses
import struct
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

DIAGNOSTICS_MAGIC = 0x43503344  # CP3D
DIAGNOSTICS_VERSION = 1
DIAGNOSTICS_WORD_COUNT = 64
DIAGNOSTICS_SIZE = DIAGNOSTICS_WORD_COUNT * 4
CP3W_UDP_PORT = 43674
HEARTBEAT_PREFIX = b"CP3W-DIAG-HEARTBEAT"
NATIVE_EXECUTION_CANARY = 0x4E415431  # NAT1

DIAGNOSTIC_FIELDS = (
    "magic",
    "version",
    "size",
    "build_id",
    "current_phase",
    "previous_phase",
    "transition_count",
    "ios_version",
    "ios_revision",
    "initialization_attempt_count",
    "successful_initialization_count",
    "restart_request_count",
    "socket_recovery_count",
    "initial_delay_polls",
    "retry_delay_polls",
    "network_initialization_result",
    "nwc24_result",
    "host_id_result",
    "host_ip",
    "socket_descriptor",
    "socket_creation_result",
    "bind_result",
    "getsockname_result",
    "last_socket_error",
    "last_error_phase",
    "requested_bind_address",
    "requested_bind_port",
    "actual_bind_address",
    "actual_bind_port",
    "byte_order_applied",
    "listening",
    "receive_loop_active",
    "receive_call_count",
    "packets_received",
    "malformed_packets_received",
    "transient_receive_errors",
    "fatal_receive_errors",
    "send_call_count",
    "packets_sent",
    "send_failures",
    "close_call_count",
    "shutdown_call_count",
    "cleanup_call_count",
    "network_device_close_count",
    "last_close_descriptor",
    "last_shutdown_descriptor",
    "last_received_command",
    "last_received_packet_size",
    "last_sender_ip",
    "last_sender_port",
    "last_heartbeat_result",
    "uptime_polls",
    "last_successful_bind_poll",
    "last_packet_receive_poll",
    "last_packet_send_poll",
    "restart_request",
    "heartbeat_request",
    "overlay_enabled",
    "overlay_page",
    "auto_retry_enabled",
    "reset_counters_request",
    "socket_lost_count",
    "getsockname_call_count",
    "receive_loop_iteration_count",
)

_SIGNED_FIELDS = {
    "network_initialization_result",
    "nwc24_result",
    "host_id_result",
    "socket_descriptor",
    "socket_creation_result",
    "bind_result",
    "getsockname_result",
    "last_socket_error",
    "last_close_descriptor",
    "last_shutdown_descriptor",
    "last_heartbeat_result",
}
_STRUCT = struct.Struct(">" + "I" * DIAGNOSTICS_WORD_COUNT)


class NetworkPhase(IntEnum):
    OPEN_IP = 7
    SO_STARTUP = 9
    GET_HOST_ID = 11
    CREATE_SOCKET = 13
    RETRY_DELAY = 100
    SOCKET_LOST = 102
    CLOSE_SOCKET_FOR_RECOVERY = 103
    FATAL_ERROR = 107


class EndpointVerification(IntEnum):
    ADVISORY_UNVERIFIED = 0
    VERIFIED = 1
    WRONG_NONZERO_PORT = 2


@dataclasses.dataclass(frozen=True)
class Prime3WiiRuntimeDiagnostics:
    values: Mapping[str, int]

    def __getitem__(self, field: str) -> int:
        return self.values[field]

    @property
    def build_id_text(self) -> str:
        return self.values["build_id"].to_bytes(4, "big").decode("ascii", errors="replace")

    @property
    def native_execution_canary(self) -> int:
        return self.values["ios_version"]

    @property
    def native_execution_stage(self) -> int:
        return self.values["ios_revision"]

    @property
    def native_recurring_hook_count(self) -> int:
        return self.values["shutdown_call_count"]

    @property
    def native_post_copy_hook_result(self) -> int:
        return _as_signed(self.values["overlay_page"])


def _as_signed(value: int) -> int:
    return value - 0x1_0000_0000 if value & 0x8000_0000 else value


def parse_diagnostics(data: bytes) -> Prime3WiiRuntimeDiagnostics:
    if len(data) != DIAGNOSTICS_SIZE:
        raise ValueError(f"Expected {DIAGNOSTICS_SIZE} diagnostic bytes, got {len(data)}.")
    raw_values = _STRUCT.unpack(data)
    values = {
        field: _as_signed(value) if field in _SIGNED_FIELDS else value
        for field, value in zip(DIAGNOSTIC_FIELDS, raw_values, strict=True)
    }
    if values["magic"] != DIAGNOSTICS_MAGIC:
        raise ValueError(f"Wrong diagnostics magic 0x{values['magic']:08X}.")
    if values["version"] != DIAGNOSTICS_VERSION:
        raise ValueError(f"Unsupported diagnostics version {values['version']}.")
    if values["size"] != DIAGNOSTICS_SIZE:
        raise ValueError(f"Diagnostics structure reports invalid size {values['size']}.")
    if values["requested_bind_port"] != CP3W_UDP_PORT:
        raise ValueError(f"Diagnostics structure reports unexpected UDP port {values['requested_bind_port']}.")
    return Prime3WiiRuntimeDiagnostics(values)


def encode_heartbeat(*, build_id: int, phase: int) -> bytes:
    if not 0 <= build_id <= 0xFFFF_FFFF:
        raise ValueError("build_id must be a 32-bit unsigned integer.")
    if not 0 <= phase <= 0xFFFF_FFFF:
        raise ValueError("phase must be a 32-bit unsigned integer.")
    return HEARTBEAT_PREFIX + b"\0" + struct.pack(">II", build_id, phase)


def encode_wii_sockaddr(*, address: int = 0, port: int = CP3W_UDP_PORT) -> bytes:
    if not 0 <= address <= 0xFFFF_FFFF:
        raise ValueError("address must be a 32-bit unsigned integer.")
    if port != CP3W_UDP_PORT:
        raise ValueError(f"Prime 3 CP3W must bind UDP port {CP3W_UDP_PORT}.")
    return struct.pack(">BBHI", 8, 2, port, address)


def classify_bound_endpoint(result: int, sockaddr: bytes) -> tuple[EndpointVerification, int, int]:
    if result != 0 or len(sockaddr) != 8 or sockaddr[0] != 8 or sockaddr[1] != 2:
        return EndpointVerification.ADVISORY_UNVERIFIED, 0, 0
    _length, _family, port, address = struct.unpack(">BBHI", sockaddr)
    if port == 0:
        return EndpointVerification.ADVISORY_UNVERIFIED, 0, 0
    if port != CP3W_UDP_PORT:
        return EndpointVerification.WRONG_NONZERO_PORT, address, port
    return EndpointVerification.VERIFIED, address, port


def phase_after_failure(*, socket_descriptor: int, auto_retry: bool, socket_lost: bool) -> NetworkPhase:
    if not auto_retry:
        return NetworkPhase.FATAL_ERROR
    if socket_lost:
        return NetworkPhase.SOCKET_LOST
    if socket_descriptor >= 0:
        return NetworkPhase.CLOSE_SOCKET_FOR_RECOVERY
    return NetworkPhase.RETRY_DELAY


def phase_after_retry_delay(*, ip_open: bool, service_started: bool, host_id_ready: bool) -> NetworkPhase:
    if not ip_open:
        return NetworkPhase.OPEN_IP
    if not service_started:
        return NetworkPhase.SO_STARTUP
    if not host_id_ready:
        return NetworkPhase.GET_HOST_ID
    return NetworkPhase.CREATE_SOCKET


assert len(DIAGNOSTIC_FIELDS) == DIAGNOSTICS_WORD_COUNT
