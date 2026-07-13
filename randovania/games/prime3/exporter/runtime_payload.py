from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game_connection.executor.prime3_wii_protocol import PROTOCOL_VERSION
from randovania.games.prime3.exporter.dol_patcher import Prime3DolPatchError, Prime3PayloadArtifact

if TYPE_CHECKING:
    from collections.abc import Iterable

PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION = 3
PRIME3_RUNTIME_TARGET_ARCHITECTURE = "powerpc"
PRIME3_RUNTIME_TARGET_ENDIANNESS = "big"
PRIME3_RUNTIME_TARGET_ABI = "eabi"
PRIME3_RUNTIME_REQUIRED_ALIGNMENT = 0x20
PRIME3_RUNTIME_ENTRY_SYMBOL = "payload_entry"
PRIME3_RUNTIME_PAYLOAD_MODE_NORMAL = "normal"
PRIME3_RUNTIME_PAYLOAD_MODE_PROBE = "probe"
PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT = "entry_bootstrap_halt"
PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_CONTINUE = "entry_bootstrap_continue"
PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT = "relocated_copy_halt"
PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT = "relocated_return_halt"
PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE = "relocated_continue"
PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES = (
    PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT,
    PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_CONTINUE,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
)
PRIME3_RUNTIME_RELOCATED_MODES = (
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
)
PRIME3_RUNTIME_HALT_MODES = (
    PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT,
)
PRIME3_RUNTIME_CONTINUE_MODES = (
    PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_CONTINUE,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
)


def compute_cache_range(*, address: int, size: int, cache_line_size: int) -> tuple[int, int]:
    if cache_line_size <= 0 or cache_line_size & (cache_line_size - 1) != 0:
        raise Prime3DolPatchError(f"Cache line size must be a positive power of two, got {cache_line_size}.")
    if address < 0:
        raise Prime3DolPatchError(f"Cache range address must be non-negative, got {address}.")
    if size <= 0:
        raise Prime3DolPatchError(f"Cache range size must be positive, got {size}.")
    try:
        end = address + size
    except OverflowError as exc:
        raise Prime3DolPatchError("Cache range overflowed the integer address space.") from exc
    if end <= address:
        raise Prime3DolPatchError("Cache range end must be above the start address.")
    aligned_start = address & ~(cache_line_size - 1)
    aligned_end = (end + cache_line_size - 1) & ~(cache_line_size - 1)
    if aligned_end <= aligned_start:
        raise Prime3DolPatchError("Cache-aligned range must be non-empty.")
    return aligned_start, aligned_end - aligned_start


@dataclasses.dataclass(frozen=True)
class Prime3EntryBootstrapMetadata:
    mode: str
    staging_address: int
    staging_save_area_offset: int
    staging_save_area_size: int
    halt_loop_address: int | None
    reserved_boundary: int
    reserved_range_start: int
    reserved_range_end: int
    diagnostic_address: int
    diagnostic_block_size: int
    canary_address: int
    canary_size: int
    canary_sha256: str
    marker_address: int
    marker_value: int
    counter_address: int
    counter_size: int
    original_80000034_address: int
    original_80003110_address: int
    replacement_value_address: int
    replacement_value: int
    status_address: int
    status_value: int
    original_entry_instruction: int
    original_branch_target: int
    original_continuation_address: int

    def validate(self, *, payload_size: int) -> None:
        if self.mode not in PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES:
            raise Prime3DolPatchError(f"Unsupported Prime 3 entry bootstrap mode {self.mode!r}.")
        _validate_optional_range(
            payload_size=payload_size,
            field_name="staging_save_area_offset",
            start=self.staging_save_area_offset,
            size=self.staging_save_area_size,
        )
        if self.halt_loop_address is not None and not (
            self.staging_address <= self.halt_loop_address < self.staging_address + payload_size
        ):
            raise Prime3DolPatchError("Entry bootstrap halt loop address is outside the staged payload range.")
        if self.mode in PRIME3_RUNTIME_HALT_MODES and self.halt_loop_address is None:
            raise Prime3DolPatchError("Entry bootstrap halt modes require a halt loop address.")
        if self.mode in PRIME3_RUNTIME_CONTINUE_MODES and self.halt_loop_address is not None:
            raise Prime3DolPatchError("Entry bootstrap continue modes must not define a halt loop address.")
        if self.reserved_range_start != self.reserved_boundary:
            raise Prime3DolPatchError("Entry bootstrap reserved range must start at the reserved boundary.")
        if self.reserved_range_end <= self.reserved_range_start:
            raise Prime3DolPatchError("Entry bootstrap reserved range end must be above the reserved range start.")
        if not (self.reserved_range_start <= self.diagnostic_address < self.reserved_range_end):
            raise Prime3DolPatchError("Entry bootstrap diagnostic block address is outside the reserved range.")
        if self.diagnostic_address + self.diagnostic_block_size > self.reserved_range_end:
            raise Prime3DolPatchError("Entry bootstrap diagnostic block exceeds the reserved range.")

        occupied_ranges = (
            ("canary", self.canary_address, self.canary_size),
            ("marker", self.marker_address, 4),
            ("counter", self.counter_address, self.counter_size),
            ("original_80000034", self.original_80000034_address, 4),
            ("original_80003110", self.original_80003110_address, 4),
            ("replacement_value", self.replacement_value_address, 4),
            ("status", self.status_address, 4),
        )
        for name, start, size in occupied_ranges:
            if not (self.reserved_range_start <= start < self.reserved_range_end):
                raise Prime3DolPatchError(f"Entry bootstrap field {name} is outside the reserved range.")
            if start + size > self.reserved_range_end:
                raise Prime3DolPatchError(f"Entry bootstrap field {name} exceeds the reserved range.")
        _validate_non_overlapping_ranges(tuple((name, start, size) for name, start, size in occupied_ranges))

    def to_json_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)

    @classmethod
    def from_json_dict(cls, data: dict[str, object], *, payload_size: int) -> Prime3EntryBootstrapMetadata:
        metadata = cls(
            mode=_json_string(data, "mode"),
            staging_address=_json_int(data, "staging_address"),
            staging_save_area_offset=_json_int(data, "staging_save_area_offset"),
            staging_save_area_size=_json_int(data, "staging_save_area_size"),
            halt_loop_address=_json_optional_int(data, "halt_loop_address"),
            reserved_boundary=_json_int(data, "reserved_boundary"),
            reserved_range_start=_json_int(data, "reserved_range_start"),
            reserved_range_end=_json_int(data, "reserved_range_end"),
            diagnostic_address=_json_int(data, "diagnostic_address"),
            diagnostic_block_size=_json_int(data, "diagnostic_block_size"),
            canary_address=_json_int(data, "canary_address"),
            canary_size=_json_int(data, "canary_size"),
            canary_sha256=_json_string(data, "canary_sha256"),
            marker_address=_json_int(data, "marker_address"),
            marker_value=_json_int(data, "marker_value"),
            counter_address=_json_int(data, "counter_address"),
            counter_size=_json_int(data, "counter_size"),
            original_80000034_address=_json_int(data, "original_80000034_address"),
            original_80003110_address=_json_int(data, "original_80003110_address"),
            replacement_value_address=_json_int(data, "replacement_value_address"),
            replacement_value=_json_int(data, "replacement_value"),
            status_address=_json_int(data, "status_address"),
            status_value=_json_int(data, "status_value"),
            original_entry_instruction=_json_int(data, "original_entry_instruction"),
            original_branch_target=_json_int(data, "original_branch_target"),
            original_continuation_address=_json_int(data, "original_continuation_address"),
        )
        metadata.validate(payload_size=payload_size)
        return metadata


@dataclasses.dataclass(frozen=True)
class Prime3RuntimeTransportMetadata:
    phase_address: int
    phase_size: int
    last_error_address: int
    last_error_size: int
    last_ios_result_address: int
    last_ios_result_size: int
    pending_operation_address: int
    pending_operation_size: int
    pending_generation_address: int
    pending_generation_size: int
    callback_generation_address: int
    callback_generation_size: int
    callback_count_address: int
    callback_count_size: int
    callback_pending_address: int
    callback_pending_size: int
    kd_fd_address: int
    kd_fd_size: int
    ip_fd_address: int
    ip_fd_size: int
    socket_fd_address: int
    socket_fd_size: int
    host_id_address: int
    host_id_size: int
    bound_port_address: int
    bound_port_size: int
    receive_count_address: int
    receive_count_size: int
    receive_bytes_address: int
    receive_bytes_size: int
    send_count_address: int
    send_count_size: int
    send_bytes_address: int
    send_bytes_size: int
    last_receive_length_address: int
    last_receive_length_size: int
    last_send_length_address: int
    last_send_length_size: int
    last_peer_ipv4_address: int
    last_peer_ipv4_size: int
    last_peer_port_address: int
    last_peer_port_size: int
    last_peer_family_address: int
    last_peer_family_size: int
    last_poll_action_address: int
    last_poll_action_size: int
    last_submit_result_address: int
    last_submit_result_size: int
    last_receive_preview_address: int
    last_receive_preview_size: int
    last_send_preview_address: int
    last_send_preview_size: int

    def validate(self, *, runtime_state_start: int, runtime_state_end: int) -> tuple[tuple[str, int, int], ...]:
        ranges = (
            ("transport_phase", self.phase_address, self.phase_size),
            ("transport_last_error", self.last_error_address, self.last_error_size),
            ("transport_last_ios_result", self.last_ios_result_address, self.last_ios_result_size),
            ("transport_pending_operation", self.pending_operation_address, self.pending_operation_size),
            ("transport_pending_generation", self.pending_generation_address, self.pending_generation_size),
            ("transport_callback_generation", self.callback_generation_address, self.callback_generation_size),
            ("transport_callback_count", self.callback_count_address, self.callback_count_size),
            ("transport_callback_pending", self.callback_pending_address, self.callback_pending_size),
            ("transport_kd_fd", self.kd_fd_address, self.kd_fd_size),
            ("transport_ip_fd", self.ip_fd_address, self.ip_fd_size),
            ("transport_socket_fd", self.socket_fd_address, self.socket_fd_size),
            ("transport_host_id", self.host_id_address, self.host_id_size),
            ("transport_bound_port", self.bound_port_address, self.bound_port_size),
            ("transport_receive_count", self.receive_count_address, self.receive_count_size),
            ("transport_receive_bytes", self.receive_bytes_address, self.receive_bytes_size),
            ("transport_send_count", self.send_count_address, self.send_count_size),
            ("transport_send_bytes", self.send_bytes_address, self.send_bytes_size),
            ("transport_last_receive_length", self.last_receive_length_address, self.last_receive_length_size),
            ("transport_last_send_length", self.last_send_length_address, self.last_send_length_size),
            ("transport_last_peer_ipv4", self.last_peer_ipv4_address, self.last_peer_ipv4_size),
            ("transport_last_peer_port", self.last_peer_port_address, self.last_peer_port_size),
            ("transport_last_peer_family", self.last_peer_family_address, self.last_peer_family_size),
            ("transport_last_poll_action", self.last_poll_action_address, self.last_poll_action_size),
            ("transport_last_submit_result", self.last_submit_result_address, self.last_submit_result_size),
            ("transport_last_receive_preview", self.last_receive_preview_address, self.last_receive_preview_size),
            ("transport_last_send_preview", self.last_send_preview_address, self.last_send_preview_size),
        )
        for name, start, size in ranges:
            if size <= 0:
                raise Prime3DolPatchError(f"Relocated runtime transport field {name} size must be positive.")
            if not (runtime_state_start <= start < runtime_state_end):
                raise Prime3DolPatchError(
                    f"Relocated runtime transport field {name} is outside the runtime state range."
                )
            if start + size > runtime_state_end:
                raise Prime3DolPatchError(f"Relocated runtime transport field {name} exceeds the runtime state range.")
        _validate_non_overlapping_ranges(ranges)
        return ranges

    def to_json_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> Prime3RuntimeTransportMetadata:
        return cls(
            phase_address=_json_int(data, "phase_address"),
            phase_size=_json_int(data, "phase_size"),
            last_error_address=_json_int(data, "last_error_address"),
            last_error_size=_json_int(data, "last_error_size"),
            last_ios_result_address=_json_int(data, "last_ios_result_address"),
            last_ios_result_size=_json_int(data, "last_ios_result_size"),
            pending_operation_address=_json_int(data, "pending_operation_address"),
            pending_operation_size=_json_int(data, "pending_operation_size"),
            pending_generation_address=_json_int(data, "pending_generation_address"),
            pending_generation_size=_json_int(data, "pending_generation_size"),
            callback_generation_address=_json_int(data, "callback_generation_address"),
            callback_generation_size=_json_int(data, "callback_generation_size"),
            callback_count_address=_json_int(data, "callback_count_address"),
            callback_count_size=_json_int(data, "callback_count_size"),
            callback_pending_address=_json_int(data, "callback_pending_address"),
            callback_pending_size=_json_int(data, "callback_pending_size"),
            kd_fd_address=_json_int(data, "kd_fd_address"),
            kd_fd_size=_json_int(data, "kd_fd_size"),
            ip_fd_address=_json_int(data, "ip_fd_address"),
            ip_fd_size=_json_int(data, "ip_fd_size"),
            socket_fd_address=_json_int(data, "socket_fd_address"),
            socket_fd_size=_json_int(data, "socket_fd_size"),
            host_id_address=_json_int(data, "host_id_address"),
            host_id_size=_json_int(data, "host_id_size"),
            bound_port_address=_json_int(data, "bound_port_address"),
            bound_port_size=_json_int(data, "bound_port_size"),
            receive_count_address=_json_int(data, "receive_count_address"),
            receive_count_size=_json_int(data, "receive_count_size"),
            receive_bytes_address=_json_int(data, "receive_bytes_address"),
            receive_bytes_size=_json_int(data, "receive_bytes_size"),
            send_count_address=_json_int(data, "send_count_address"),
            send_count_size=_json_int(data, "send_count_size"),
            send_bytes_address=_json_int(data, "send_bytes_address"),
            send_bytes_size=_json_int(data, "send_bytes_size"),
            last_receive_length_address=_json_int(data, "last_receive_length_address"),
            last_receive_length_size=_json_int(data, "last_receive_length_size"),
            last_send_length_address=_json_int(data, "last_send_length_address"),
            last_send_length_size=_json_int(data, "last_send_length_size"),
            last_peer_ipv4_address=_json_int(data, "last_peer_ipv4_address"),
            last_peer_ipv4_size=_json_int(data, "last_peer_ipv4_size"),
            last_peer_port_address=_json_int(data, "last_peer_port_address"),
            last_peer_port_size=_json_int(data, "last_peer_port_size"),
            last_peer_family_address=_json_int(data, "last_peer_family_address"),
            last_peer_family_size=_json_int(data, "last_peer_family_size"),
            last_poll_action_address=_json_int(data, "last_poll_action_address"),
            last_poll_action_size=_json_int(data, "last_poll_action_size"),
            last_submit_result_address=_json_int(data, "last_submit_result_address"),
            last_submit_result_size=_json_int(data, "last_submit_result_size"),
            last_receive_preview_address=_json_int(data, "last_receive_preview_address"),
            last_receive_preview_size=_json_int(data, "last_receive_preview_size"),
            last_send_preview_address=_json_int(data, "last_send_preview_address"),
            last_send_preview_size=_json_int(data, "last_send_preview_size"),
        )


@dataclasses.dataclass(frozen=True)
class Prime3RetailIosWrapperMetadata:
    supported_dol_sha256: str
    open_async_address: int
    open_address: int
    close_async_address: int
    close_address: int
    ioctl_async_address: int
    ioctl_address: int
    ioctlv_async_address: int
    ioctlv_address: int
    open_async_guard_words: tuple[int, ...]
    callback_signature: str
    preserved_registers: tuple[str, ...]
    submit_helper_address: int
    request_allocator_address: int
    evidence_source: str
    confidence: str

    def validate(self) -> None:
        if len(self.supported_dol_sha256) != 64:
            raise Prime3DolPatchError("Retail IOS wrapper metadata requires a SHA-256 DOL fingerprint.")
        addresses = (
            self.open_async_address,
            self.open_address,
            self.close_async_address,
            self.close_address,
            self.ioctl_async_address,
            self.ioctl_address,
            self.ioctlv_async_address,
            self.ioctlv_address,
            self.submit_helper_address,
            self.request_allocator_address,
        )
        for address in addresses:
            if address <= 0 or address > 0xFFFFFFFF:
                raise Prime3DolPatchError(f"Retail IOS wrapper address is outside the 32-bit range: {address!r}")
        if len(self.open_async_guard_words) < 2:
            raise Prime3DolPatchError("Retail IOS wrapper metadata requires at least two guarded entry words.")
        if self.callback_signature != "s32 callback(s32 result, void *userdata)":
            raise Prime3DolPatchError("Retail IOS wrapper callback signature metadata is unexpected.")
        if tuple(self.preserved_registers) != ("r2", "r13"):
            raise Prime3DolPatchError("Retail IOS wrapper metadata must document preserved game SDA registers.")
        if not self.evidence_source:
            raise Prime3DolPatchError("Retail IOS wrapper metadata requires an evidence source.")
        if self.confidence not in {"candidate", "verified"}:
            raise Prime3DolPatchError(f"Unsupported retail IOS wrapper confidence {self.confidence!r}.")

    def to_json_dict(self) -> dict[str, object]:
        return {
            **dataclasses.asdict(self),
            "open_async_guard_words": list(self.open_async_guard_words),
            "preserved_registers": list(self.preserved_registers),
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> Prime3RetailIosWrapperMetadata:
        metadata = cls(
            supported_dol_sha256=_json_string(data, "supported_dol_sha256"),
            open_async_address=_json_int(data, "open_async_address"),
            open_address=_json_int(data, "open_address"),
            close_async_address=_json_int(data, "close_async_address"),
            close_address=_json_int(data, "close_address"),
            ioctl_async_address=_json_int(data, "ioctl_async_address"),
            ioctl_address=_json_int(data, "ioctl_address"),
            ioctlv_async_address=_json_int(data, "ioctlv_async_address"),
            ioctlv_address=_json_int(data, "ioctlv_address"),
            open_async_guard_words=tuple(_json_int_list(data, "open_async_guard_words")),
            callback_signature=_json_string(data, "callback_signature"),
            preserved_registers=tuple(_json_string_list(data, "preserved_registers")),
            submit_helper_address=_json_int(data, "submit_helper_address"),
            request_allocator_address=_json_int(data, "request_allocator_address"),
            evidence_source=_json_string(data, "evidence_source"),
            confidence=_json_string(data, "confidence"),
        )
        metadata.validate()
        return metadata


@dataclasses.dataclass(frozen=True)
class Prime3RuntimeDiagnosticMetadata:
    mode: str
    hook_wrapper_entry_count_address: int
    hook_wrapper_entry_count_size: int
    hook_wrapper_before_poll_count_address: int
    hook_wrapper_before_poll_count_size: int
    runtime_poll_entry_count_address: int
    runtime_poll_entry_count_size: int
    runtime_poll_exit_count_address: int
    runtime_poll_exit_count_size: int
    state_machine_entry_count_address: int
    state_machine_entry_count_size: int
    state_machine_exit_count_address: int
    state_machine_exit_count_size: int
    c_before_veneer_call_count_address: int
    c_before_veneer_call_count_size: int
    retail_veneer_entry_count_address: int
    retail_veneer_entry_count_size: int
    retail_target_return_count_address: int
    retail_target_return_count_size: int
    retail_veneer_exit_count_address: int
    retail_veneer_exit_count_size: int
    c_after_veneer_call_count_address: int
    c_after_veneer_call_count_size: int
    ios_submit_attempt_count_address: int
    ios_submit_attempt_count_size: int
    ios_submit_return_count_address: int
    ios_submit_return_count_size: int
    ios_submit_return_value_address: int
    ios_submit_return_value_size: int
    callback_entry_count_address: int
    callback_entry_count_size: int
    callback_exit_count_address: int
    callback_exit_count_size: int
    hook_wrapper_after_poll_count_address: int
    hook_wrapper_after_poll_count_size: int
    hook_wrapper_exit_count_address: int
    hook_wrapper_exit_count_size: int
    last_execution_marker_address: int
    last_execution_marker_size: int
    last_transport_phase_before_step_address: int
    last_transport_phase_before_step_size: int
    last_transport_phase_after_step_address: int
    last_transport_phase_after_step_size: int
    callback_result_address: int
    callback_result_size: int

    def validate(self, *, runtime_state_start: int, runtime_state_end: int) -> tuple[tuple[str, int, int], ...]:
        ranges = (
            ("hook_wrapper_entry_count", self.hook_wrapper_entry_count_address, self.hook_wrapper_entry_count_size),
            (
                "hook_wrapper_before_poll_count",
                self.hook_wrapper_before_poll_count_address,
                self.hook_wrapper_before_poll_count_size,
            ),
            ("runtime_poll_entry_count", self.runtime_poll_entry_count_address, self.runtime_poll_entry_count_size),
            ("runtime_poll_exit_count", self.runtime_poll_exit_count_address, self.runtime_poll_exit_count_size),
            ("state_machine_entry_count", self.state_machine_entry_count_address, self.state_machine_entry_count_size),
            ("state_machine_exit_count", self.state_machine_exit_count_address, self.state_machine_exit_count_size),
            (
                "c_before_veneer_call_count",
                self.c_before_veneer_call_count_address,
                self.c_before_veneer_call_count_size,
            ),
            (
                "retail_veneer_entry_count",
                self.retail_veneer_entry_count_address,
                self.retail_veneer_entry_count_size,
            ),
            (
                "retail_target_return_count",
                self.retail_target_return_count_address,
                self.retail_target_return_count_size,
            ),
            (
                "retail_veneer_exit_count",
                self.retail_veneer_exit_count_address,
                self.retail_veneer_exit_count_size,
            ),
            (
                "c_after_veneer_call_count",
                self.c_after_veneer_call_count_address,
                self.c_after_veneer_call_count_size,
            ),
            ("ios_submit_attempt_count", self.ios_submit_attempt_count_address, self.ios_submit_attempt_count_size),
            ("ios_submit_return_count", self.ios_submit_return_count_address, self.ios_submit_return_count_size),
            ("ios_submit_return_value", self.ios_submit_return_value_address, self.ios_submit_return_value_size),
            ("callback_entry_count", self.callback_entry_count_address, self.callback_entry_count_size),
            ("callback_exit_count", self.callback_exit_count_address, self.callback_exit_count_size),
            (
                "hook_wrapper_after_poll_count",
                self.hook_wrapper_after_poll_count_address,
                self.hook_wrapper_after_poll_count_size,
            ),
            ("hook_wrapper_exit_count", self.hook_wrapper_exit_count_address, self.hook_wrapper_exit_count_size),
            ("last_execution_marker", self.last_execution_marker_address, self.last_execution_marker_size),
            (
                "last_transport_phase_before_step",
                self.last_transport_phase_before_step_address,
                self.last_transport_phase_before_step_size,
            ),
            (
                "last_transport_phase_after_step",
                self.last_transport_phase_after_step_address,
                self.last_transport_phase_after_step_size,
            ),
            ("callback_result", self.callback_result_address, self.callback_result_size),
        )
        for name, start, size in ranges:
            if size <= 0:
                raise Prime3DolPatchError(f"Relocated runtime diagnostic field {name} size must be positive.")
            if not (runtime_state_start <= start < runtime_state_end):
                raise Prime3DolPatchError(
                    f"Relocated runtime diagnostic field {name} is outside the runtime state range."
                )
            if start + size > runtime_state_end:
                raise Prime3DolPatchError(
                    f"Relocated runtime diagnostic field {name} exceeds the runtime state range."
                )
        _validate_non_overlapping_ranges(ranges)
        return ranges

    def to_json_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> Prime3RuntimeDiagnosticMetadata:
        return cls(
            mode=_json_string(data, "mode"),
            hook_wrapper_entry_count_address=_json_int(data, "hook_wrapper_entry_count_address"),
            hook_wrapper_entry_count_size=_json_int(data, "hook_wrapper_entry_count_size"),
            hook_wrapper_before_poll_count_address=_json_int(data, "hook_wrapper_before_poll_count_address"),
            hook_wrapper_before_poll_count_size=_json_int(data, "hook_wrapper_before_poll_count_size"),
            runtime_poll_entry_count_address=_json_int(data, "runtime_poll_entry_count_address"),
            runtime_poll_entry_count_size=_json_int(data, "runtime_poll_entry_count_size"),
            runtime_poll_exit_count_address=_json_int(data, "runtime_poll_exit_count_address"),
            runtime_poll_exit_count_size=_json_int(data, "runtime_poll_exit_count_size"),
            state_machine_entry_count_address=_json_int(data, "state_machine_entry_count_address"),
            state_machine_entry_count_size=_json_int(data, "state_machine_entry_count_size"),
            state_machine_exit_count_address=_json_int(data, "state_machine_exit_count_address"),
            state_machine_exit_count_size=_json_int(data, "state_machine_exit_count_size"),
            c_before_veneer_call_count_address=_json_int(data, "c_before_veneer_call_count_address"),
            c_before_veneer_call_count_size=_json_int(data, "c_before_veneer_call_count_size"),
            retail_veneer_entry_count_address=_json_int(data, "retail_veneer_entry_count_address"),
            retail_veneer_entry_count_size=_json_int(data, "retail_veneer_entry_count_size"),
            retail_target_return_count_address=_json_int(data, "retail_target_return_count_address"),
            retail_target_return_count_size=_json_int(data, "retail_target_return_count_size"),
            retail_veneer_exit_count_address=_json_int(data, "retail_veneer_exit_count_address"),
            retail_veneer_exit_count_size=_json_int(data, "retail_veneer_exit_count_size"),
            c_after_veneer_call_count_address=_json_int(data, "c_after_veneer_call_count_address"),
            c_after_veneer_call_count_size=_json_int(data, "c_after_veneer_call_count_size"),
            ios_submit_attempt_count_address=_json_int(data, "ios_submit_attempt_count_address"),
            ios_submit_attempt_count_size=_json_int(data, "ios_submit_attempt_count_size"),
            ios_submit_return_count_address=_json_int(data, "ios_submit_return_count_address"),
            ios_submit_return_count_size=_json_int(data, "ios_submit_return_count_size"),
            ios_submit_return_value_address=_json_int(data, "ios_submit_return_value_address"),
            ios_submit_return_value_size=_json_int(data, "ios_submit_return_value_size"),
            callback_entry_count_address=_json_int(data, "callback_entry_count_address"),
            callback_entry_count_size=_json_int(data, "callback_entry_count_size"),
            callback_exit_count_address=_json_int(data, "callback_exit_count_address"),
            callback_exit_count_size=_json_int(data, "callback_exit_count_size"),
            hook_wrapper_after_poll_count_address=_json_int(data, "hook_wrapper_after_poll_count_address"),
            hook_wrapper_after_poll_count_size=_json_int(data, "hook_wrapper_after_poll_count_size"),
            hook_wrapper_exit_count_address=_json_int(data, "hook_wrapper_exit_count_address"),
            hook_wrapper_exit_count_size=_json_int(data, "hook_wrapper_exit_count_size"),
            last_execution_marker_address=_json_int(data, "last_execution_marker_address"),
            last_execution_marker_size=_json_int(data, "last_execution_marker_size"),
            last_transport_phase_before_step_address=_json_int(data, "last_transport_phase_before_step_address"),
            last_transport_phase_before_step_size=_json_int(data, "last_transport_phase_before_step_size"),
            last_transport_phase_after_step_address=_json_int(data, "last_transport_phase_after_step_address"),
            last_transport_phase_after_step_size=_json_int(data, "last_transport_phase_after_step_size"),
            callback_result_address=_json_int(data, "callback_result_address"),
            callback_result_size=_json_int(data, "callback_result_size"),
        )


@dataclasses.dataclass(frozen=True)
class Prime3RelocatedRuntimeMetadata:
    mode: str
    low_bootstrap_address: int
    low_bootstrap_size: int
    low_bootstrap_sha256: str
    embedded_runtime_blob_offset: int
    embedded_runtime_blob_size: int
    embedded_runtime_blob_sha256: str
    runtime_destination_address: int
    runtime_entry_address: int
    runtime_poll_entry_address: int
    runtime_poll_hook_wrapper_address: int
    runtime_code_start: int
    runtime_code_end: int
    runtime_state_start: int
    runtime_state_end: int
    runtime_stack_start: int | None
    runtime_stack_end: int | None
    required_source_alignment: int
    required_destination_alignment: int
    cache_line_size: int
    cache_range_start: int
    cache_range_size: int
    runtime_canary_address: int
    runtime_canary_size: int
    runtime_canary_sha256: str
    copy_complete_marker_address: int
    copy_complete_marker_value: int
    runtime_executed_marker_address: int
    runtime_executed_marker_value: int
    runtime_execution_counter_address: int
    runtime_execution_counter_size: int
    runtime_status_address: int
    runtime_success_status_value: int
    bootstrap_return_marker_address: int
    bootstrap_return_marker_value: int
    runtime_poll_counter_address: int
    runtime_poll_counter_size: int
    runtime_poll_heartbeat_address: int
    runtime_poll_heartbeat_size: int
    runtime_poll_last_sequence_address: int
    runtime_poll_last_sequence_size: int
    diagnostics: Prime3RuntimeDiagnosticMetadata | None = None
    ios_udp_diagnostic_enabled: bool = False
    transport: Prime3RuntimeTransportMetadata | None = None
    retail_ios_wrapper: Prime3RetailIosWrapperMetadata | None = None

    def _validate_diagnostic_configuration(self) -> tuple[tuple[str, int, int], ...]:
        if self.diagnostics is None:
            return ()
        return self.diagnostics.validate(
            runtime_state_start=self.runtime_state_start,
            runtime_state_end=self.runtime_state_end,
        )

    def _validate_transport_configuration(self) -> tuple[tuple[str, int, int], ...]:
        if self.ios_udp_diagnostic_enabled:
            if self.mode != PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE:
                raise Prime3DolPatchError("IOS UDP diagnostic transport requires relocated_continue mode.")
            if self.transport is None:
                raise Prime3DolPatchError("IOS UDP diagnostic transport metadata is missing.")
        elif self.transport is not None:
            raise Prime3DolPatchError("Relocated runtime transport metadata requires ios_udp_diagnostic_enabled.")

        if self.transport is None:
            return ()
        return self.transport.validate(
            runtime_state_start=self.runtime_state_start,
            runtime_state_end=self.runtime_state_end,
        )

    def _validate_retail_wrapper_configuration(self) -> None:
        if self.retail_ios_wrapper is None:
            return
        self.retail_ios_wrapper.validate()

    def validate(
        self,
        *,
        payload_size: int,
        reserved_range_start: int,
        reserved_range_end: int,
        bootstrap_diagnostic_start: int,
        bootstrap_diagnostic_size: int,
    ) -> None:
        if self.mode not in PRIME3_RUNTIME_RELOCATED_MODES:
            raise Prime3DolPatchError(f"Unsupported Prime 3 relocated runtime mode {self.mode!r}.")
        if self.low_bootstrap_size <= 0 or self.low_bootstrap_size > payload_size:
            raise Prime3DolPatchError("Low bootstrap size is outside the compound payload size.")
        _validate_optional_range(
            payload_size=payload_size,
            field_name="embedded_runtime_blob_offset",
            start=self.embedded_runtime_blob_offset,
            size=self.embedded_runtime_blob_size,
        )
        if self.embedded_runtime_blob_offset < self.low_bootstrap_size:
            raise Prime3DolPatchError("Embedded runtime blob overlaps the low bootstrap bytes.")
        if self.required_source_alignment <= 0 or self.required_destination_alignment <= 0:
            raise Prime3DolPatchError("Relocated runtime alignments must be positive.")
        if self.embedded_runtime_blob_offset % self.required_source_alignment != 0:
            raise Prime3DolPatchError("Embedded runtime blob offset does not meet source alignment.")
        if self.runtime_destination_address % self.required_destination_alignment != 0:
            raise Prime3DolPatchError("Runtime destination does not meet destination alignment.")
        if self.runtime_destination_address < reserved_range_start:
            raise Prime3DolPatchError("Runtime destination is below the reserved range.")
        runtime_end = self.runtime_destination_address + self.embedded_runtime_blob_size
        if runtime_end > reserved_range_end or runtime_end <= self.runtime_destination_address:
            raise Prime3DolPatchError("Runtime destination range exceeds the reserved range.")
        if not (self.runtime_code_start <= self.runtime_entry_address < self.runtime_code_end):
            raise Prime3DolPatchError("Runtime entry address is outside the runtime code range.")
        if not (self.runtime_code_start <= self.runtime_poll_entry_address < self.runtime_code_end):
            raise Prime3DolPatchError("Runtime poll entry address is outside the runtime code range.")
        if not (self.runtime_code_start <= self.runtime_poll_hook_wrapper_address < self.runtime_code_end):
            raise Prime3DolPatchError("Runtime poll hook wrapper address is outside the runtime code range.")
        if self.runtime_code_start != self.runtime_destination_address:
            raise Prime3DolPatchError("Runtime code must begin at the destination address.")
        if self.runtime_code_end > runtime_end:
            raise Prime3DolPatchError("Runtime code range exceeds the embedded runtime size.")
        if not (self.runtime_code_end <= self.runtime_state_start <= self.runtime_state_end <= runtime_end):
            raise Prime3DolPatchError("Runtime state range is invalid or overlaps runtime code.")
        if (self.runtime_stack_start is None) != (self.runtime_stack_end is None):
            raise Prime3DolPatchError("Runtime stack range must provide both start and end together.")
        if self.runtime_stack_start is not None:
            assert self.runtime_stack_end is not None
            if not (
                self.runtime_state_start
                <= self.runtime_stack_start
                <= self.runtime_stack_end
                <= self.runtime_state_end
            ):
                raise Prime3DolPatchError("Runtime stack range must stay inside the runtime state range.")

        diagnostic_end = bootstrap_diagnostic_start + bootstrap_diagnostic_size
        state_ranges = (
            ("runtime_canary", self.runtime_canary_address, self.runtime_canary_size),
            ("copy_complete_marker", self.copy_complete_marker_address, 4),
            ("runtime_executed_marker", self.runtime_executed_marker_address, 4),
            ("runtime_execution_counter", self.runtime_execution_counter_address, self.runtime_execution_counter_size),
            ("runtime_status", self.runtime_status_address, 4),
            ("bootstrap_return_marker", self.bootstrap_return_marker_address, 4),
            ("runtime_poll_counter", self.runtime_poll_counter_address, self.runtime_poll_counter_size),
            ("runtime_poll_heartbeat", self.runtime_poll_heartbeat_address, self.runtime_poll_heartbeat_size),
            (
                "runtime_poll_last_sequence",
                self.runtime_poll_last_sequence_address,
                self.runtime_poll_last_sequence_size,
            ),
        )
        diagnostic_ranges = self._validate_diagnostic_configuration()
        transport_ranges = self._validate_transport_configuration()
        self._validate_retail_wrapper_configuration()
        for name, start, size in state_ranges:
            if not (self.runtime_state_start <= start < self.runtime_state_end):
                raise Prime3DolPatchError(f"Relocated runtime field {name} is outside the runtime state range.")
            if start + size > self.runtime_state_end:
                raise Prime3DolPatchError(f"Relocated runtime field {name} exceeds the runtime state range.")
            if start < diagnostic_end and start + size > bootstrap_diagnostic_start:
                raise Prime3DolPatchError(f"Relocated runtime field {name} overlaps the bootstrap diagnostic block.")
        _validate_non_overlapping_ranges(state_ranges + diagnostic_ranges + transport_ranges)

        expected_cache_start, expected_cache_size = compute_cache_range(
            address=self.runtime_destination_address,
            size=self.embedded_runtime_blob_size,
            cache_line_size=self.cache_line_size,
        )
        if self.cache_range_start != expected_cache_start or self.cache_range_size != expected_cache_size:
            raise Prime3DolPatchError("Relocated runtime cache range does not match the aligned runtime destination.")

    def to_json_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> Prime3RelocatedRuntimeMetadata:
        return cls(
            mode=_json_string(data, "mode"),
            low_bootstrap_address=_json_int(data, "low_bootstrap_address"),
            low_bootstrap_size=_json_int(data, "low_bootstrap_size"),
            low_bootstrap_sha256=_json_string(data, "low_bootstrap_sha256"),
            embedded_runtime_blob_offset=_json_int(data, "embedded_runtime_blob_offset"),
            embedded_runtime_blob_size=_json_int(data, "embedded_runtime_blob_size"),
            embedded_runtime_blob_sha256=_json_string(data, "embedded_runtime_blob_sha256"),
            runtime_destination_address=_json_int(data, "runtime_destination_address"),
            runtime_entry_address=_json_int(data, "runtime_entry_address"),
            runtime_poll_entry_address=_json_int(data, "runtime_poll_entry_address"),
            runtime_poll_hook_wrapper_address=_json_int(data, "runtime_poll_hook_wrapper_address"),
            runtime_code_start=_json_int(data, "runtime_code_start"),
            runtime_code_end=_json_int(data, "runtime_code_end"),
            runtime_state_start=_json_int(data, "runtime_state_start"),
            runtime_state_end=_json_int(data, "runtime_state_end"),
            runtime_stack_start=_json_optional_int(data, "runtime_stack_start"),
            runtime_stack_end=_json_optional_int(data, "runtime_stack_end"),
            required_source_alignment=_json_int(data, "required_source_alignment"),
            required_destination_alignment=_json_int(data, "required_destination_alignment"),
            cache_line_size=_json_int(data, "cache_line_size"),
            cache_range_start=_json_int(data, "cache_range_start"),
            cache_range_size=_json_int(data, "cache_range_size"),
            runtime_canary_address=_json_int(data, "runtime_canary_address"),
            runtime_canary_size=_json_int(data, "runtime_canary_size"),
            runtime_canary_sha256=_json_string(data, "runtime_canary_sha256"),
            copy_complete_marker_address=_json_int(data, "copy_complete_marker_address"),
            copy_complete_marker_value=_json_int(data, "copy_complete_marker_value"),
            runtime_executed_marker_address=_json_int(data, "runtime_executed_marker_address"),
            runtime_executed_marker_value=_json_int(data, "runtime_executed_marker_value"),
            runtime_execution_counter_address=_json_int(data, "runtime_execution_counter_address"),
            runtime_execution_counter_size=_json_int(data, "runtime_execution_counter_size"),
            runtime_status_address=_json_int(data, "runtime_status_address"),
            runtime_success_status_value=_json_int(data, "runtime_success_status_value"),
            bootstrap_return_marker_address=_json_int(data, "bootstrap_return_marker_address"),
            bootstrap_return_marker_value=_json_int(data, "bootstrap_return_marker_value"),
            runtime_poll_counter_address=_json_int(data, "runtime_poll_counter_address"),
            runtime_poll_counter_size=_json_int(data, "runtime_poll_counter_size"),
            runtime_poll_heartbeat_address=_json_int(data, "runtime_poll_heartbeat_address"),
            runtime_poll_heartbeat_size=_json_int(data, "runtime_poll_heartbeat_size"),
            runtime_poll_last_sequence_address=_json_int(data, "runtime_poll_last_sequence_address"),
            runtime_poll_last_sequence_size=_json_int(data, "runtime_poll_last_sequence_size"),
            diagnostics=_json_optional_runtime_diagnostics(data, "diagnostics"),
            ios_udp_diagnostic_enabled=_json_optional_bool(data, "ios_udp_diagnostic_enabled") or False,
            transport=_json_optional_runtime_transport(data, "transport"),
            retail_ios_wrapper=_json_optional_retail_ios_wrapper(data, "retail_ios_wrapper"),
        )


@dataclasses.dataclass(frozen=True)
class Prime3RuntimePayloadManifest:
    schema_version: int
    target_architecture: str
    target_endianness: str
    target_abi: str
    compiler_identity: str
    compiler_version: str
    linker_identity: str
    linker_version: str
    payload_sha256: str
    payload_size: int
    required_alignment: int
    entry_symbol_name: str
    entry_symbol_offset: int
    source_digest: str
    protocol_artifact_version: int
    unresolved_relocation_count: int
    dynamic_section_count: int
    payload_mode: str = PRIME3_RUNTIME_PAYLOAD_MODE_NORMAL
    canary_start_offset: int | None = None
    canary_size: int | None = None
    counter_offset: int | None = None
    counter_size: int | None = None
    entry_bootstrap: Prime3EntryBootstrapMetadata | None = None
    relocated_runtime: Prime3RelocatedRuntimeMetadata | None = None

    def validate(self) -> None:
        if self.schema_version != PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION:
            raise Prime3DolPatchError(
                f"Unsupported Prime 3 runtime payload schema version {self.schema_version}; "
                f"expected {PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION}."
            )
        if self.target_architecture != PRIME3_RUNTIME_TARGET_ARCHITECTURE:
            raise Prime3DolPatchError(
                f"Unsupported payload architecture {self.target_architecture!r}; "
                f"expected {PRIME3_RUNTIME_TARGET_ARCHITECTURE!r}."
            )
        if self.target_endianness != PRIME3_RUNTIME_TARGET_ENDIANNESS:
            raise Prime3DolPatchError(
                f"Unsupported payload endianness {self.target_endianness!r}; "
                f"expected {PRIME3_RUNTIME_TARGET_ENDIANNESS!r}."
            )
        if self.target_abi != PRIME3_RUNTIME_TARGET_ABI:
            raise Prime3DolPatchError(
                f"Unsupported payload ABI {self.target_abi!r}; expected {PRIME3_RUNTIME_TARGET_ABI!r}."
            )
        if self.payload_size < 0:
            raise Prime3DolPatchError(f"Payload size must be non-negative, got {self.payload_size}.")
        if self.entry_symbol_offset < 0 or self.entry_symbol_offset > self.payload_size:
            raise Prime3DolPatchError(
                f"Payload entry offset {self.entry_symbol_offset} is outside payload size {self.payload_size}."
            )
        if self.unresolved_relocation_count != 0:
            raise Prime3DolPatchError(
                f"Payload manifest reports {self.unresolved_relocation_count} unresolved relocations."
            )
        if self.dynamic_section_count != 0:
            raise Prime3DolPatchError(f"Payload manifest reports {self.dynamic_section_count} dynamic sections.")
        if self.protocol_artifact_version != PROTOCOL_VERSION:
            raise Prime3DolPatchError(
                f"Payload protocol version {self.protocol_artifact_version!r} does not match {PROTOCOL_VERSION!r}."
            )
        if self.payload_mode not in (
            PRIME3_RUNTIME_PAYLOAD_MODE_NORMAL,
            PRIME3_RUNTIME_PAYLOAD_MODE_PROBE,
            *PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES,
        ):
            raise Prime3DolPatchError(f"Unsupported payload mode {self.payload_mode!r}.")
        _validate_optional_range(
            payload_size=self.payload_size,
            field_name="canary_start_offset",
            start=self.canary_start_offset,
            size=self.canary_size,
        )
        _validate_optional_range(
            payload_size=self.payload_size,
            field_name="counter_offset",
            start=self.counter_offset,
            size=self.counter_size,
        )
        if self.entry_bootstrap is None and self.payload_mode in PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES:
            raise Prime3DolPatchError("Entry bootstrap payload mode requires entry bootstrap metadata.")
        if self.entry_bootstrap is not None:
            self.entry_bootstrap.validate(payload_size=self.payload_size)
            if self.payload_mode != self.entry_bootstrap.mode:
                raise Prime3DolPatchError("Payload mode does not match entry bootstrap metadata mode.")
        if self.relocated_runtime is None and self.payload_mode in PRIME3_RUNTIME_RELOCATED_MODES:
            raise Prime3DolPatchError("Relocated runtime payload mode requires relocated runtime metadata.")
        if self.relocated_runtime is not None:
            if self.entry_bootstrap is None:
                raise Prime3DolPatchError("Relocated runtime metadata requires entry bootstrap metadata.")
            self.relocated_runtime.validate(
                payload_size=self.payload_size,
                reserved_range_start=self.entry_bootstrap.reserved_range_start,
                reserved_range_end=self.entry_bootstrap.reserved_range_end,
                bootstrap_diagnostic_start=self.entry_bootstrap.diagnostic_address,
                bootstrap_diagnostic_size=self.entry_bootstrap.diagnostic_block_size,
            )
            if self.payload_mode != self.relocated_runtime.mode:
                raise Prime3DolPatchError("Payload mode does not match relocated runtime metadata mode.")

        Prime3PayloadArtifact.create(
            payload_bytes=b"\x00" * self.payload_size,
            load_address=0,
            entry_symbol_offset=self.entry_symbol_offset,
            required_alignment=self.required_alignment,
            protocol_manifest_version=str(self.protocol_artifact_version),
            build_tool_identity=self.compiler_identity,
            build_tool_version=self.compiler_version,
            source_digest=self.source_digest,
        )

    def to_json_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "compiler_identity": self.compiler_identity,
            "compiler_version": self.compiler_version,
            "dynamic_section_count": self.dynamic_section_count,
            "entry_symbol_name": self.entry_symbol_name,
            "entry_symbol_offset": self.entry_symbol_offset,
            "linker_identity": self.linker_identity,
            "linker_version": self.linker_version,
            "payload_sha256": self.payload_sha256,
            "payload_size": self.payload_size,
            "payload_mode": self.payload_mode,
            "protocol_artifact_version": self.protocol_artifact_version,
            "required_alignment": self.required_alignment,
            "schema_version": self.schema_version,
            "source_digest": self.source_digest,
            "target_abi": self.target_abi,
            "target_architecture": self.target_architecture,
            "target_endianness": self.target_endianness,
            "unresolved_relocation_count": self.unresolved_relocation_count,
        }
        if self.canary_start_offset is not None:
            result["canary_start_offset"] = self.canary_start_offset
            result["canary_size"] = self.canary_size
        if self.counter_offset is not None:
            result["counter_offset"] = self.counter_offset
            result["counter_size"] = self.counter_size
        if self.entry_bootstrap is not None:
            result["entry_bootstrap"] = self.entry_bootstrap.to_json_dict()
        if self.relocated_runtime is not None:
            result["relocated_runtime"] = self.relocated_runtime.to_json_dict()
        return result

    def to_json_text(self) -> str:
        return json.dumps(self.to_json_dict(), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> Prime3RuntimePayloadManifest:
        required_keys = {
            "compiler_identity",
            "compiler_version",
            "dynamic_section_count",
            "entry_symbol_name",
            "entry_symbol_offset",
            "linker_identity",
            "linker_version",
            "payload_sha256",
            "payload_size",
            "payload_mode",
            "protocol_artifact_version",
            "required_alignment",
            "schema_version",
            "source_digest",
            "target_abi",
            "target_architecture",
            "target_endianness",
            "unresolved_relocation_count",
            "canary_start_offset",
            "canary_size",
            "counter_offset",
            "counter_size",
            "entry_bootstrap",
            "relocated_runtime",
        }
        unknown_keys = set(data) - required_keys
        if unknown_keys:
            raise Prime3DolPatchError(f"Unknown Prime 3 runtime payload manifest keys: {sorted(unknown_keys)}")

        payload_size = _json_int(data, "payload_size")
        manifest = cls(
            schema_version=_json_int(data, "schema_version"),
            target_architecture=_json_string(data, "target_architecture"),
            target_endianness=_json_string(data, "target_endianness"),
            target_abi=_json_string(data, "target_abi"),
            compiler_identity=_json_string(data, "compiler_identity"),
            compiler_version=_json_string(data, "compiler_version"),
            linker_identity=_json_string(data, "linker_identity"),
            linker_version=_json_string(data, "linker_version"),
            payload_sha256=_json_string(data, "payload_sha256"),
            payload_size=payload_size,
            payload_mode=_json_string(data, "payload_mode"),
            required_alignment=_json_int(data, "required_alignment"),
            entry_symbol_name=_json_string(data, "entry_symbol_name"),
            entry_symbol_offset=_json_int(data, "entry_symbol_offset"),
            source_digest=_json_string(data, "source_digest"),
            protocol_artifact_version=_json_int(data, "protocol_artifact_version"),
            unresolved_relocation_count=_json_int(data, "unresolved_relocation_count"),
            dynamic_section_count=_json_int(data, "dynamic_section_count"),
            canary_start_offset=_json_optional_int(data, "canary_start_offset"),
            canary_size=_json_optional_int(data, "canary_size"),
            counter_offset=_json_optional_int(data, "counter_offset"),
            counter_size=_json_optional_int(data, "counter_size"),
            entry_bootstrap=_json_optional_entry_bootstrap(data, "entry_bootstrap", payload_size=payload_size),
            relocated_runtime=_json_optional_relocated_runtime(data, "relocated_runtime"),
        )
        manifest.validate()
        return manifest

    @classmethod
    def from_json_text(cls, text: str) -> Prime3RuntimePayloadManifest:
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise Prime3DolPatchError(f"Invalid Prime 3 runtime payload manifest JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise Prime3DolPatchError("Prime 3 runtime payload manifest must be a JSON object.")
        return cls.from_json_dict(raw)


def compute_source_digest(source_root: Path, relative_paths: Iterable[str | Path]) -> str:
    digest = hashlib.sha256()
    for relative_path in sorted((Path(path) for path in relative_paths), key=lambda path: path.as_posix()):
        digest.update(relative_path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(source_root.joinpath(relative_path).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_prime3_runtime_payload_artifact(
    *,
    manifest_path: Path,
    payload_path: Path,
    load_address: int,
) -> Prime3PayloadArtifact:
    manifest = Prime3RuntimePayloadManifest.from_json_text(manifest_path.read_text(encoding="utf-8"))
    payload_bytes = payload_path.read_bytes()
    actual_hash = hashlib.sha256(payload_bytes).hexdigest()
    if actual_hash != manifest.payload_sha256:
        raise Prime3DolPatchError(
            f"Payload hash mismatch for {payload_path}: expected {manifest.payload_sha256}, got {actual_hash}."
        )
    if len(payload_bytes) != manifest.payload_size:
        raise Prime3DolPatchError(
            f"Payload size mismatch for {payload_path}: expected {manifest.payload_size}, got {len(payload_bytes)}."
        )

    build_tool_identity = f"{manifest.compiler_identity} + {manifest.linker_identity}"
    build_tool_version = f"{manifest.compiler_version} / {manifest.linker_version}"
    return Prime3PayloadArtifact.create(
        payload_bytes=payload_bytes,
        load_address=load_address,
        entry_symbol_offset=manifest.entry_symbol_offset,
        required_alignment=manifest.required_alignment,
        protocol_manifest_version=str(manifest.protocol_artifact_version),
        build_tool_identity=build_tool_identity,
        build_tool_version=build_tool_version,
        source_digest=manifest.source_digest,
    )


def _json_int(data: dict[str, object], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be an integer.")
    return value


def _json_string(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be a string.")
    return value


def _json_int_list(data: dict[str, object], key: str) -> list[int]:
    value = data.get(key)
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, int) for item in value):
        raise Prime3DolPatchError(
            f"Prime 3 runtime payload manifest field {key!r} must be a list or tuple of integers."
        )
    return list(value)


def _json_string_list(data: dict[str, object], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise Prime3DolPatchError(
            f"Prime 3 runtime payload manifest field {key!r} must be a list or tuple of strings."
        )
    return list(value)


def _json_optional_int(data: dict[str, object], key: str) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, int):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be an integer when present.")
    return value


def _json_optional_bool(data: dict[str, object], key: str) -> bool | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be a bool when present.")
    return value


def _json_optional_entry_bootstrap(
    data: dict[str, object],
    key: str,
    *,
    payload_size: int,
) -> Prime3EntryBootstrapMetadata | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be an object when present.")
    return Prime3EntryBootstrapMetadata.from_json_dict(value, payload_size=payload_size)


def _json_optional_relocated_runtime(
    data: dict[str, object],
    key: str,
) -> Prime3RelocatedRuntimeMetadata | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be an object when present.")
    return Prime3RelocatedRuntimeMetadata.from_json_dict(value)


def _json_optional_runtime_transport(
    data: dict[str, object],
    key: str,
) -> Prime3RuntimeTransportMetadata | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be an object when present.")
    return Prime3RuntimeTransportMetadata.from_json_dict(value)


def _json_optional_runtime_diagnostics(
    data: dict[str, object],
    key: str,
) -> Prime3RuntimeDiagnosticMetadata | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be an object when present.")
    return Prime3RuntimeDiagnosticMetadata.from_json_dict(value)


def _json_optional_retail_ios_wrapper(
    data: dict[str, object],
    key: str,
) -> Prime3RetailIosWrapperMetadata | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be an object when present.")
    return Prime3RetailIosWrapperMetadata.from_json_dict(value)


def _validate_optional_range(*, payload_size: int, field_name: str, start: int | None, size: int | None) -> None:
    if start is None and size is None:
        return
    if start is None or size is None:
        raise Prime3DolPatchError(f"Payload manifest must provide both {field_name} and its size together.")
    if size <= 0:
        raise Prime3DolPatchError(f"Payload manifest field {field_name!r} size must be positive, got {size}.")
    if start < 0 or start + size > payload_size:
        raise Prime3DolPatchError(
            f"Payload manifest field {field_name!r} range {start}..{start + size} "
            f"is outside payload size {payload_size}."
        )


def _validate_non_overlapping_ranges(ranges: tuple[tuple[str, int, int], ...]) -> None:
    for index, (first_name, first_start, first_size) in enumerate(ranges):
        first_end = first_start + first_size
        for second_name, second_start, second_size in ranges[index + 1 :]:
            second_end = second_start + second_size
            if first_start < second_end and second_start < first_end:
                raise Prime3DolPatchError(f"Fields {first_name} and {second_name} overlap.")
