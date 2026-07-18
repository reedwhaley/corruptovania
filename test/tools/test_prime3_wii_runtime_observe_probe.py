from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from randovania.game_connection.executor.prime3_wii_protocol import PROTOCOL_VERSION
from randovania.games.prime3.exporter.runtime_payload import Prime3RuntimePayloadManifest


def _load_module():
    module_path = Path(__file__).resolve().parents[2].joinpath("tools", "prime3_wii_runtime", "observe_probe.py")
    spec = importlib.util.spec_from_file_location("prime3_wii_runtime_observe_probe_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeBackend:
    def __init__(
        self,
        memory: dict[int, bytes] | list[dict[int, bytes]],
        *,
        hooked: bool = True,
        hook_success: bool = True,
    ):
        self.memory = memory
        self._hooked = hooked
        self._hook_success = hook_success
        self._cycle = 0

    def is_hooked(self) -> bool:
        return self._hooked

    def hook(self) -> None:
        self._hooked = self._hook_success

    def un_hook(self) -> None:
        self._hooked = False

    def read_bytes(self, address: int, size: int) -> bytes:
        source = self.memory
        if isinstance(source, list):
            index = min(self._cycle, len(source) - 1)
            source = source[index]
        data = source.get(address, b"")
        return data[:size]

    def advance_cycle(self) -> None:
        self._cycle += 1


def _manifest(payload_bytes: bytes) -> Prime3RuntimePayloadManifest:
    return Prime3RuntimePayloadManifest(
        schema_version=3,
        target_architecture="powerpc",
        target_endianness="big",
        target_abi="eabi",
        compiler_identity="synthetic",
        compiler_version="1.0",
        linker_identity="synthetic",
        linker_version="1.0",
        payload_sha256=__import__("hashlib").sha256(payload_bytes).hexdigest(),
        payload_size=len(payload_bytes),
        required_alignment=0x20,
        entry_symbol_name="payload_entry",
        entry_symbol_offset=0,
        source_digest="deadbeef",
        protocol_artifact_version=PROTOCOL_VERSION,
        unresolved_relocation_count=0,
        dynamic_section_count=0,
        canary_start_offset=0x10,
        canary_size=0x10,
        counter_offset=0x20,
        counter_size=4,
    )


def _bootstrap_manifest(payload_bytes: bytes) -> Prime3RuntimePayloadManifest:
    raw = _manifest(payload_bytes).to_json_dict()
    raw["payload_mode"] = "entry_bootstrap_halt"
    raw["entry_bootstrap"] = {
        "mode": "entry_bootstrap_halt",
        "staging_address": 0x806843C0,
        "staging_save_area_offset": 0x20,
        "staging_save_area_size": 0x10,
        "halt_loop_address": 0x806843D8,
        "reserved_boundary": 0x817E0000,
        "reserved_range_start": 0x817E0000,
        "reserved_range_end": 0x817FE3A0,
        "diagnostic_address": 0x817E0100,
        "diagnostic_block_size": 0x40,
        "canary_address": 0x817E0100,
        "canary_size": 0x10,
        "canary_sha256": __import__("hashlib").sha256(b"P3BOOTSTRAPCANRY").hexdigest(),
        "marker_address": 0x817E0114,
        "marker_value": 0x50334254,
        "counter_address": 0x817E0118,
        "counter_size": 4,
        "original_80000034_address": 0x817E011C,
        "original_80003110_address": 0x817E0120,
        "replacement_value_address": 0x817E0124,
        "replacement_value": 0x817E0000,
        "status_address": 0x817E0128,
        "status_value": 0xB0070001,
        "original_entry_instruction": 0x4800016D,
        "original_branch_target": 0x8000648C,
        "original_continuation_address": 0x80006324,
    }
    return Prime3RuntimePayloadManifest.from_json_dict(raw)


def _relocated_manifest(payload_bytes: bytes) -> Prime3RuntimePayloadManifest:
    raw = _bootstrap_manifest(payload_bytes).to_json_dict()
    raw["payload_mode"] = "relocated_continue"
    raw["entry_bootstrap"]["mode"] = "relocated_continue"
    raw["entry_bootstrap"]["status_value"] = 0xB0071003
    raw["entry_bootstrap"]["halt_loop_address"] = None
    raw["relocated_runtime"] = {
        "mode": "relocated_continue",
        "low_bootstrap_address": 0x806843C0,
        "low_bootstrap_size": 0x20,
        "low_bootstrap_sha256": __import__("hashlib").sha256(payload_bytes[:0x20]).hexdigest(),
        "embedded_runtime_blob_offset": 0x20,
        "embedded_runtime_blob_size": 0x2F0,
        "embedded_runtime_blob_sha256": __import__("hashlib").sha256(payload_bytes[0x20:0x310]).hexdigest(),
        "runtime_destination_address": 0x817E1000,
        "runtime_entry_address": 0x817E1000,
        "runtime_poll_entry_address": 0x817E1004,
        "runtime_poll_hook_wrapper_address": 0x817E1014,
        "runtime_code_start": 0x817E1000,
        "runtime_code_end": 0x817E1028,
        "runtime_state_start": 0x817E1028,
        "runtime_state_end": 0x817E12F0,
        "runtime_stack_start": None,
        "runtime_stack_end": None,
        "required_source_alignment": 0x20,
        "required_destination_alignment": 0x20,
        "cache_line_size": 0x20,
        "cache_range_start": 0x817E1000,
        "cache_range_size": 0x300,
        "runtime_canary_address": 0x817E1028,
        "runtime_canary_size": 0x10,
        "runtime_canary_sha256": __import__("hashlib").sha256(b"R" * 0x10).hexdigest(),
        "copy_complete_marker_address": 0x817E1038,
        "copy_complete_marker_value": 0x434F5059,
        "runtime_executed_marker_address": 0x817E103C,
        "runtime_executed_marker_value": 0x52554E21,
        "runtime_execution_counter_address": 0x817E1040,
        "runtime_execution_counter_size": 4,
        "runtime_status_address": 0x817E1044,
        "runtime_success_status_value": 0x52544F4B,
        "bootstrap_return_marker_address": 0x817E1048,
        "bootstrap_return_marker_value": 0x4252544E,
        "runtime_poll_counter_address": 0x817E104C,
        "runtime_poll_counter_size": 4,
        "runtime_poll_heartbeat_address": 0x817E1050,
        "runtime_poll_heartbeat_size": 4,
        "runtime_poll_last_sequence_address": 0x817E1054,
        "runtime_poll_last_sequence_size": 4,
        "ios_udp_diagnostic_enabled": True,
        "diagnostics": {
            "mode": "normal",
            "hook_wrapper_entry_count_address": 0x817E10E0,
            "hook_wrapper_entry_count_size": 4,
            "hook_wrapper_before_poll_count_address": 0x817E10E4,
            "hook_wrapper_before_poll_count_size": 4,
            "runtime_poll_entry_count_address": 0x817E10E8,
            "runtime_poll_entry_count_size": 4,
            "runtime_poll_exit_count_address": 0x817E10EC,
            "runtime_poll_exit_count_size": 4,
            "state_machine_entry_count_address": 0x817E10F0,
            "state_machine_entry_count_size": 4,
            "state_machine_exit_count_address": 0x817E10F4,
            "state_machine_exit_count_size": 4,
            "c_before_veneer_call_count_address": 0x817E1124,
            "c_before_veneer_call_count_size": 4,
            "retail_veneer_entry_count_address": 0x817E1128,
            "retail_veneer_entry_count_size": 4,
            "retail_target_return_count_address": 0x817E112C,
            "retail_target_return_count_size": 4,
            "retail_veneer_exit_count_address": 0x817E1130,
            "retail_veneer_exit_count_size": 4,
            "c_after_veneer_call_count_address": 0x817E1134,
            "c_after_veneer_call_count_size": 4,
            "ios_submit_attempt_count_address": 0x817E10F8,
            "ios_submit_attempt_count_size": 4,
            "ios_submit_return_count_address": 0x817E10FC,
            "ios_submit_return_count_size": 4,
            "ios_submit_return_value_address": 0x817E1100,
            "ios_submit_return_value_size": 4,
            "callback_entry_count_address": 0x817E1104,
            "callback_entry_count_size": 4,
            "callback_exit_count_address": 0x817E1108,
            "callback_exit_count_size": 4,
            "hook_wrapper_after_poll_count_address": 0x817E110C,
            "hook_wrapper_after_poll_count_size": 4,
            "hook_wrapper_exit_count_address": 0x817E1110,
            "hook_wrapper_exit_count_size": 4,
            "last_execution_marker_address": 0x817E1114,
            "last_execution_marker_size": 4,
            "last_transport_phase_before_step_address": 0x817E1118,
            "last_transport_phase_before_step_size": 4,
            "last_transport_phase_after_step_address": 0x817E111C,
            "last_transport_phase_after_step_size": 4,
            "callback_result_address": 0x817E1120,
            "callback_result_size": 4,
        },
        "transport": {
            "mode": "normal",
            "initialization_enabled": True,
            "receive_enabled": False,
            "send_enabled": False,
            "nwc24_startup_enabled": True,
            "kd_close_enabled": True,
            "ip_close_on_success": False,
            "socket_close_on_success": False,
            "terminal_phase_value": 17,
            "terminal_phase_name": "BOUND_NO_RECV",
            "phase_address": 0x817E1140,
            "phase_size": 4,
            "last_error_address": 0x817E1144,
            "last_error_size": 4,
            "last_socket_error_address": 0x817E1148,
            "last_socket_error_size": 4,
            "last_ios_result_address": 0x817E114C,
            "last_ios_result_size": 4,
            "pending_operation_address": 0x817E1150,
            "pending_operation_size": 4,
            "pending_generation_address": 0x817E1154,
            "pending_generation_size": 4,
            "callback_generation_address": 0x817E1158,
            "callback_generation_size": 4,
            "callback_count_address": 0x817E115C,
            "callback_count_size": 4,
            "rejected_callback_count_address": 0x817E1160,
            "rejected_callback_count_size": 4,
            "callback_pending_address": 0x817E1164,
            "callback_pending_size": 4,
            "open_kd_submit_count_address": 0x817E1168,
            "open_kd_submit_count_size": 4,
            "open_kd_callback_count_address": 0x817E116C,
            "open_kd_callback_count_size": 4,
            "nwc24_output_buffer_address": 0x817E1180,
            "nwc24_output_buffer_size": 0x20,
            "nwc24_output_buffer_alignment": 0x20,
            "nwc24_submit_count_address": 0x817E1170,
            "nwc24_submit_count_size": 4,
            "nwc24_callback_count_address": 0x817E1174,
            "nwc24_callback_count_size": 4,
            "nwc24_synchronous_result_address": 0x817E11A0,
            "nwc24_synchronous_result_size": 4,
            "nwc24_callback_result_address": 0x817E11A4,
            "nwc24_callback_result_size": 4,
            "nwc24_output_digest_address": 0x817E11A8,
            "nwc24_output_digest_size": 4,
            "open_ip_submit_count_address": 0x817E11AC,
            "open_ip_submit_count_size": 4,
            "open_ip_callback_count_address": 0x817E11B0,
            "open_ip_callback_count_size": 4,
            "kd_close_submit_count_address": 0x817E11B4,
            "kd_close_submit_count_size": 4,
            "kd_close_callback_count_address": 0x817E11B8,
            "kd_close_callback_count_size": 4,
            "startup_submit_count_address": 0x817E11BC,
            "startup_submit_count_size": 4,
            "startup_callback_count_address": 0x817E11C0,
            "startup_callback_count_size": 4,
            "get_host_id_submit_count_address": 0x817E11C4,
            "get_host_id_submit_count_size": 4,
            "get_host_id_callback_count_address": 0x817E11C8,
            "get_host_id_callback_count_size": 4,
            "socket_submit_count_address": 0x817E11CC,
            "socket_submit_count_size": 4,
            "socket_callback_count_address": 0x817E11D0,
            "socket_callback_count_size": 4,
            "bind_submit_count_address": 0x817E11D4,
            "bind_submit_count_size": 4,
            "bind_callback_count_address": 0x817E11D8,
            "bind_callback_count_size": 4,
            "kd_fd_address": 0x817E11DC,
            "kd_fd_size": 4,
            "kd_closed_address": 0x817E11E0,
            "kd_closed_size": 4,
            "ip_fd_address": 0x817E11E4,
            "ip_fd_size": 4,
            "socket_fd_address": 0x817E11E8,
            "socket_fd_size": 4,
            "host_id_address": 0x817E11EC,
            "host_id_size": 4,
            "bound_port_address": 0x817E11F0,
            "bound_port_size": 4,
            "receive_submit_count_address": 0x817E11F4,
            "receive_submit_count_size": 4,
            "send_submit_count_address": 0x817E11F8,
            "send_submit_count_size": 4,
            "ip_close_submit_count_address": 0x817E11FC,
            "ip_close_submit_count_size": 4,
            "socket_close_submit_count_address": 0x817E1200,
            "socket_close_submit_count_size": 4,
            "receive_count_address": 0x817E1204,
            "receive_count_size": 4,
            "receive_bytes_address": 0x817E1208,
            "receive_bytes_size": 4,
            "send_count_address": 0x817E120C,
            "send_count_size": 4,
            "send_bytes_address": 0x817E1210,
            "send_bytes_size": 4,
            "last_receive_length_address": 0x817E1214,
            "last_receive_length_size": 4,
            "last_send_length_address": 0x817E1218,
            "last_send_length_size": 4,
            "last_peer_ipv4_address": 0x817E121C,
            "last_peer_ipv4_size": 4,
            "last_peer_port_address": 0x817E1220,
            "last_peer_port_size": 4,
            "last_peer_family_address": 0x817E1224,
            "last_peer_family_size": 4,
            "last_poll_action_address": 0x817E1228,
            "last_poll_action_size": 4,
            "last_submit_result_address": 0x817E122C,
            "last_submit_result_size": 4,
            "last_receive_preview_address": 0x817E1234,
            "last_receive_preview_size": 16,
            "last_send_preview_address": 0x817E1244,
            "last_send_preview_size": 16,
        },
        "abi_probe": {
            "mode": "retail_wrapper_ioctl_async_abi_probe",
            "supplied_args_address": 0x817E1260,
            "supplied_args_size": 0x20,
            "pre_call_args_address": 0x817E1280,
            "pre_call_args_size": 0x20,
            "target_args_address": 0x817E12A0,
            "target_args_size": 0x20,
            "return_value_address": 0x817E12C0,
            "return_value_size": 4,
            "expected_return_value": 0x13579BDF,
            "result_flags_address": 0x817E12C4,
            "result_flags_size": 4,
            "stack_pointer_before_address": 0x817E12C8,
            "stack_pointer_before_size": 4,
            "stack_pointer_after_address": 0x817E12CC,
            "stack_pointer_after_size": 4,
            "saved_lr_address": 0x817E12D0,
            "saved_lr_size": 4,
            "restored_lr_address": 0x817E12D4,
            "restored_lr_size": 4,
            "saved_r2_address": 0x817E12D8,
            "saved_r2_size": 4,
            "restored_r2_address": 0x817E12DC,
            "restored_r2_size": 4,
            "saved_r13_address": 0x817E12E0,
            "saved_r13_size": 4,
            "restored_r13_address": 0x817E12E4,
            "restored_r13_size": 4,
            "target_ctr_address": 0x817E12E8,
            "target_ctr_size": 4,
            "after_call_flag_address": 0x817E12EC,
            "after_call_flag_size": 4,
        },
    }
    return Prime3RuntimePayloadManifest.from_json_dict(raw)


def _write_u32(blob: bytearray, offset: int, value: int) -> None:
    blob[offset : offset + 4] = value.to_bytes(4, "big")


def _write_s32(blob: bytearray, offset: int, value: int) -> None:
    blob[offset : offset + 4] = value.to_bytes(4, "big", signed=True)


def _install_transport_state(
    blob: bytearray,
    *,
    phase: int,
    last_error: int = 0,
    last_socket_error: int = 0,
    last_ios_result: int = 0,
    pending_operation: int = 0,
    pending_generation: int = 0,
    callback_generation: int = 0,
    callback_count: int = 0,
    rejected_callback_count: int = 0,
    callback_pending: int = 0,
    open_kd_submit_count: int = 0,
    open_kd_callback_count: int = 0,
    nwc24_submit_count: int = 0,
    nwc24_callback_count: int = 0,
    nwc24_synchronous_result: int = 0,
    nwc24_callback_result: int = 0,
    nwc24_output_digest: int = 0,
    nwc24_output_buffer_hex: str = "00" * 32,
    open_ip_submit_count: int = 0,
    open_ip_callback_count: int = 0,
    kd_close_submit_count: int = 0,
    kd_close_callback_count: int = 0,
    startup_submit_count: int = 0,
    startup_callback_count: int = 0,
    get_host_id_submit_count: int = 0,
    get_host_id_callback_count: int = 0,
    socket_submit_count: int = 0,
    socket_callback_count: int = 0,
    bind_submit_count: int = 0,
    bind_callback_count: int = 0,
    kd_fd: int = -1,
    kd_closed: int = 0,
    ip_fd: int = -1,
    socket_fd: int = -1,
    host_id: int = 0,
    service_started: int = 0,
    bound_port: int = 43674,
    receive_submit_count: int = 0,
    send_submit_count: int = 0,
    ip_close_submit_count: int = 0,
    socket_close_submit_count: int = 0,
    receive_count: int = 0,
    receive_bytes: int = 0,
    send_count: int = 0,
    send_bytes: int = 0,
    receive_arm_count: int = 0,
    receive_rearm_count: int = 0,
    configured_exchange_limit: int = 0,
    completed_exchange_count: int = 0,
    current_exchange_index: int = 0,
    last_completed_exchange_index: int = 0,
    previous_peer_ipv4: int = 0,
    previous_peer_port: int = 0,
    rearm_submission_failure_count: int = 0,
    loop_complete_transition_count: int = 0,
    cleanup_deferred_count: int = 0,
    last_receive_length: int = 0,
    last_send_length: int = 0,
    last_peer_ipv4: int = 0,
    last_peer_port: int = 0,
    last_peer_family: int = 0,
    last_poll_action: int = 0,
    last_submit_result: int = 0,
    polls_while_receive_pending: int = 0,
    polls_after_loop_complete: int = 0,
    last_receive_preview_hex: str = "00" * 16,
    last_send_preview_hex: str = "00" * 16,
) -> None:
    _write_u32(blob, 0x140, phase)
    _write_s32(blob, 0x144, last_error)
    _write_s32(blob, 0x148, last_socket_error)
    _write_s32(blob, 0x14C, last_ios_result)
    _write_u32(blob, 0x150, pending_operation)
    _write_u32(blob, 0x154, pending_generation)
    _write_u32(blob, 0x158, callback_generation)
    _write_u32(blob, 0x15C, callback_count)
    _write_u32(blob, 0x160, rejected_callback_count)
    _write_u32(blob, 0x164, callback_pending)
    _write_u32(blob, 0x168, open_kd_submit_count)
    _write_u32(blob, 0x16C, open_kd_callback_count)
    _write_u32(blob, 0x170, nwc24_submit_count)
    _write_u32(blob, 0x174, nwc24_callback_count)
    blob[0x180:0x1A0] = bytes.fromhex(nwc24_output_buffer_hex)
    _write_s32(blob, 0x1A0, nwc24_synchronous_result)
    _write_s32(blob, 0x1A4, nwc24_callback_result)
    _write_u32(blob, 0x1A8, nwc24_output_digest)
    _write_u32(blob, 0x1AC, open_ip_submit_count)
    _write_u32(blob, 0x1B0, open_ip_callback_count)
    _write_u32(blob, 0x1B4, kd_close_submit_count)
    _write_u32(blob, 0x1B8, kd_close_callback_count)
    _write_u32(blob, 0x1BC, startup_submit_count)
    _write_u32(blob, 0x1C0, startup_callback_count)
    _write_u32(blob, 0x1C4, get_host_id_submit_count)
    _write_u32(blob, 0x1C8, get_host_id_callback_count)
    _write_u32(blob, 0x1CC, socket_submit_count)
    _write_u32(blob, 0x1D0, socket_callback_count)
    _write_u32(blob, 0x1D4, bind_submit_count)
    _write_u32(blob, 0x1D8, bind_callback_count)
    _write_s32(blob, 0x1DC, kd_fd)
    _write_u32(blob, 0x1E0, kd_closed)
    _write_s32(blob, 0x1E4, ip_fd)
    _write_s32(blob, 0x1E8, socket_fd)
    _write_u32(blob, 0x1EC, host_id)
    _write_u32(blob, 0x250, service_started)
    _write_u32(blob, 0x1F0, bound_port)
    _write_u32(blob, 0x1F4, receive_submit_count)
    _write_u32(blob, 0x1F8, send_submit_count)
    _write_u32(blob, 0x1FC, ip_close_submit_count)
    _write_u32(blob, 0x200, socket_close_submit_count)
    _write_u32(blob, 0x204, receive_count)
    _write_u32(blob, 0x208, receive_bytes)
    _write_u32(blob, 0x20C, send_count)
    _write_u32(blob, 0x210, send_bytes)
    _write_u32(blob, 0x2C0, receive_arm_count)
    _write_u32(blob, 0x2C4, receive_rearm_count)
    _write_u32(blob, 0x2C8, configured_exchange_limit)
    _write_u32(blob, 0x2CC, completed_exchange_count)
    _write_u32(blob, 0x2D0, current_exchange_index)
    _write_u32(blob, 0x2D4, last_completed_exchange_index)
    _write_u32(blob, 0x2D8, previous_peer_ipv4)
    _write_u32(blob, 0x2DC, previous_peer_port)
    _write_u32(blob, 0x2E0, rearm_submission_failure_count)
    _write_u32(blob, 0x2E4, loop_complete_transition_count)
    _write_u32(blob, 0x2E8, cleanup_deferred_count)
    _write_u32(blob, 0x2EC, polls_while_receive_pending)
    _write_u32(blob, 0x214, last_receive_length)
    _write_u32(blob, 0x218, last_send_length)
    _write_u32(blob, 0x21C, last_peer_ipv4)
    _write_u32(blob, 0x220, last_peer_port)
    _write_u32(blob, 0x224, last_peer_family)
    _write_u32(blob, 0x228, last_poll_action)
    _write_s32(blob, 0x22C, last_submit_result)
    _write_u32(blob, 0x230, polls_after_loop_complete)
    blob[0x234:0x244] = bytes.fromhex(last_receive_preview_hex)
    blob[0x244:0x254] = bytes.fromhex(last_send_preview_hex)


def _install_abi_probe_state(
    blob: bytearray,
    *,
    supplied_args: tuple[int, ...] = (),
    pre_call_args: tuple[int, ...] = (),
    target_args: tuple[int, ...] = (),
    return_value: int = 0,
    result_flags: int = 0,
    stack_pointer_before: int = 0,
    stack_pointer_after: int = 0,
    saved_lr: int = 0,
    restored_lr: int = 0,
    saved_r2: int = 0,
    restored_r2: int = 0,
    saved_r13: int = 0,
    restored_r13: int = 0,
    target_ctr: int = 0,
    after_call_flag: int = 0,
) -> None:
    for index, value in enumerate(supplied_args):
        _write_u32(blob, 0x260 + (index * 4), value)
    for index, value in enumerate(pre_call_args):
        _write_u32(blob, 0x280 + (index * 4), value)
    for index, value in enumerate(target_args):
        _write_u32(blob, 0x2A0 + (index * 4), value)
    _write_s32(blob, 0x2C0, return_value)
    _write_u32(blob, 0x2C4, result_flags)
    _write_u32(blob, 0x2C8, stack_pointer_before)
    _write_u32(blob, 0x2CC, stack_pointer_after)
    _write_u32(blob, 0x2D0, saved_lr)
    _write_u32(blob, 0x2D4, restored_lr)
    _write_u32(blob, 0x2D8, saved_r2)
    _write_u32(blob, 0x2DC, restored_r2)
    _write_u32(blob, 0x2E0, saved_r13)
    _write_u32(blob, 0x2E4, restored_r13)
    _write_u32(blob, 0x2E8, target_ctr)
    _write_u32(blob, 0x2EC, after_call_flag)


def _install_diagnostics(
    blob: bytearray,
    *,
    mode: str = "normal",
    hook_wrapper_entry_count: int,
    hook_wrapper_before_poll_count: int,
    runtime_poll_entry_count: int,
    runtime_poll_exit_count: int,
    state_machine_entry_count: int,
    state_machine_exit_count: int,
    c_before_veneer_call_count: int = 0,
    retail_veneer_entry_count: int = 0,
    retail_target_return_count: int = 0,
    retail_veneer_exit_count: int = 0,
    c_after_veneer_call_count: int = 0,
    ios_submit_attempt_count: int,
    ios_submit_return_count: int,
    ios_submit_return_value: int,
    callback_entry_count: int,
    callback_exit_count: int,
    hook_wrapper_after_poll_count: int,
    hook_wrapper_exit_count: int,
    last_execution_marker: int,
    last_transport_phase_before_step: int,
    last_transport_phase_after_step: int,
    callback_result: int,
) -> None:
    del mode
    _write_u32(blob, 0xE0, hook_wrapper_entry_count)
    _write_u32(blob, 0xE4, hook_wrapper_before_poll_count)
    _write_u32(blob, 0xE8, runtime_poll_entry_count)
    _write_u32(blob, 0xEC, runtime_poll_exit_count)
    _write_u32(blob, 0xF0, state_machine_entry_count)
    _write_u32(blob, 0xF4, state_machine_exit_count)
    _write_u32(blob, 0xF8, ios_submit_attempt_count)
    _write_u32(blob, 0xFC, ios_submit_return_count)
    _write_s32(blob, 0x100, ios_submit_return_value)
    _write_u32(blob, 0x104, callback_entry_count)
    _write_u32(blob, 0x108, callback_exit_count)
    _write_u32(blob, 0x10C, hook_wrapper_after_poll_count)
    _write_u32(blob, 0x110, hook_wrapper_exit_count)
    _write_u32(blob, 0x114, last_execution_marker)
    _write_u32(blob, 0x118, last_transport_phase_before_step)
    _write_u32(blob, 0x11C, last_transport_phase_after_step)
    _write_s32(blob, 0x120, callback_result)
    _write_u32(blob, 0x124, c_before_veneer_call_count)
    _write_u32(blob, 0x128, retail_veneer_entry_count)
    _write_u32(blob, 0x12C, retail_target_return_count)
    _write_u32(blob, 0x130, retail_veneer_exit_count)
    _write_u32(blob, 0x134, c_after_veneer_call_count)


def _install_bootstrap_diagnostic(memory: dict[int, bytes], *, status_value: int = 0xB0071003) -> None:
    diagnostic = bytearray(b"\x00" * 0x40)
    diagnostic[0x00:0x10] = b"P3BOOTSTRAPCANRY"
    diagnostic[0x14:0x18] = (0x50334254).to_bytes(4, "big")
    diagnostic[0x18:0x1C] = (1).to_bytes(4, "big")
    diagnostic[0x1C:0x20] = (0x817FE3A0).to_bytes(4, "big")
    diagnostic[0x20:0x24] = (0x817FE3A0).to_bytes(4, "big")
    diagnostic[0x24:0x28] = (0x817E0000).to_bytes(4, "big")
    diagnostic[0x28:0x2C] = status_value.to_bytes(4, "big")
    memory[0x817E0100] = bytes(diagnostic)
    memory[0x80000034] = (0x817E0000).to_bytes(4, "big")
    memory[0x80003110] = (0x817E0000).to_bytes(4, "big")


def _config(module, payload_address: int = 0x817F0000, startup_word: int = 0x38000000):
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + b"\x00" * 0x10 + b"\x00\x00\x00\x00"
    return module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=payload_address,
        payload_bytes=payload_bytes,
        manifest=_manifest(payload_bytes),
        startup_words=(
            module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),
            module.StartupWordExpectation(address=0x8000633C, expected_word=startup_word),
        ),
    )


def _memory_for_config(module, config, *, startup_word: int = 0x38000000, short_payload: bool = False):
    payload_bytes = config.payload_bytes[:-1] if short_payload else config.payload_bytes
    return {
        module.GAME_ID_ADDRESS: b"RM3E01",
        0x80006320: (0x48000000).to_bytes(4, "big"),
        0x8000633C: startup_word.to_bytes(4, "big"),
        config.payload_address: payload_bytes,
        module.BOOT_INFO_POINTER_ADDRESS: (0x817FC3A0).to_bytes(4, "big"),
        0x80000034: (0x817FEC60).to_bytes(4, "big"),
        0x80003110: (0x81800000).to_bytes(4, "big"),
        0x817FC3A8: (0).to_bytes(4, "big"),
    }


def test_observe_probe_reads_complete_payload() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend(_memory_for_config(module, config))

    result = module.observe_probe_memory(backend, config)

    assert result["payload_matches_expected"] is True
    assert result["counter"]["value"] == 0
    assert result["entry_gate_active"] is True
    assert result["checkpoint_name"] == "entry"
    assert result["halt_active"] is True
    assert result["live_halt_word"] == 0x48000000


def test_observe_probe_reports_wrong_startup_word() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend(_memory_for_config(module, config, startup_word=0x60000000))

    result = module.observe_probe_memory(backend, config)

    assert result["startup_words"]["0x8000633C"]["matches"] is False


def test_observe_probe_reports_wrong_halt_word() -> None:
    module = _load_module()
    config = _config(module)
    memory = _memory_for_config(module, config)
    memory[0x80006320] = (0x60000000).to_bytes(4, "big")
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["halt_active"] is False
    assert result["live_halt_word"] == 0x60000000


def test_observe_probe_reads_bootstrap_diagnostic_block() -> None:
    module = _load_module()
    base_config = _config(module, payload_address=0x806843C0)
    config = module.ProbeObservationConfig(
        checkpoint_name=base_config.checkpoint_name,
        halt_address=base_config.halt_address,
        expected_halt_word=base_config.expected_halt_word,
        expected_game_id=base_config.expected_game_id,
        payload_address=base_config.payload_address,
        payload_bytes=base_config.payload_bytes,
        manifest=_bootstrap_manifest(base_config.payload_bytes),
        startup_words=base_config.startup_words,
        repeat_delay_seconds=base_config.repeat_delay_seconds,
        iso_path=base_config.iso_path,
        iso_sha256=base_config.iso_sha256,
        dolphin_command_line=base_config.dolphin_command_line,
    )
    memory = _memory_for_config(module, config)
    diagnostic = bytearray(b"\x00" * 0x40)
    diagnostic[0x00:0x10] = b"P3BOOTSTRAPCANRY"
    diagnostic[0x14:0x18] = (0x50334254).to_bytes(4, "big")
    diagnostic[0x18:0x1C] = (1).to_bytes(4, "big")
    diagnostic[0x1C:0x20] = (0x817FE3A0).to_bytes(4, "big")
    diagnostic[0x20:0x24] = (0x817FE3A0).to_bytes(4, "big")
    diagnostic[0x24:0x28] = (0x817E0000).to_bytes(4, "big")
    diagnostic[0x28:0x2C] = (0xB0070001).to_bytes(4, "big")
    memory[0x817E0100] = bytes(diagnostic)
    memory[0x80000034] = (0x817E0000).to_bytes(4, "big")
    memory[0x80003110] = (0x817E0000).to_bytes(4, "big")
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["bootstrap_diagnostic"]["canary_matches_expected"] is True
    assert result["bootstrap_diagnostic"]["marker_matches_expected"] is True
    assert result["bootstrap_halt_loop_address"] == 0x806843D8
    assert result["bootstrap_diagnostic"]["counter_value"] == 1
    assert result["bootstrap_diagnostic"]["replacement_matches_expected"] is True


def test_observe_probe_reads_relocated_runtime_state() -> None:
    module = _load_module()
    runtime_blob = bytearray(b"R" * 0x2F0)
    _write_u32(runtime_blob, 0x38, 0x434F5059)
    _write_u32(runtime_blob, 0x3C, 0x52554E21)
    _write_u32(runtime_blob, 0x40, 1)
    _write_u32(runtime_blob, 0x44, 0x52544F4B)
    _write_u32(runtime_blob, 0x48, 0x4252544E)
    _write_u32(runtime_blob, 0x4C, 7)
    _write_u32(runtime_blob, 0x50, 7)
    _write_u32(runtime_blob, 0x54, 7)
    _install_transport_state(
        runtime_blob,
        phase=17,
        callback_count=1,
        open_kd_submit_count=1,
        open_kd_callback_count=1,
        nwc24_submit_count=1,
        nwc24_callback_count=1,
        nwc24_output_buffer_hex="11" * 32,
        nwc24_output_digest=0xA5A5A5A5,
        open_ip_submit_count=1,
        open_ip_callback_count=1,
        kd_close_submit_count=1,
        kd_close_callback_count=1,
        startup_submit_count=1,
        startup_callback_count=1,
        get_host_id_submit_count=1,
        get_host_id_callback_count=1,
        socket_submit_count=1,
        socket_callback_count=1,
        bind_submit_count=1,
        bind_callback_count=1,
        kd_fd=-1,
        kd_closed=1,
        ip_fd=3,
        socket_fd=4,
        host_id=0xC0A80164,
        bound_port=43674,
        last_receive_preview_hex="0102030405060708090a0b0c0d0e0f10",
        last_send_preview_hex="50335544000000010000000700000007",
    )
    _install_diagnostics(
        runtime_blob,
        hook_wrapper_entry_count=7,
        hook_wrapper_before_poll_count=7,
        runtime_poll_entry_count=7,
        runtime_poll_exit_count=7,
        state_machine_entry_count=7,
        state_machine_exit_count=7,
        ios_submit_attempt_count=1,
        ios_submit_return_count=1,
        ios_submit_return_value=0,
        callback_entry_count=1,
        callback_exit_count=1,
        hook_wrapper_after_poll_count=7,
        hook_wrapper_exit_count=7,
        last_execution_marker=0xC0DE000D,
        last_transport_phase_before_step=17,
        last_transport_phase_after_step=17,
        callback_result=0,
    )
    _install_abi_probe_state(runtime_blob)
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob)
    manifest = _relocated_manifest(payload_bytes)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(
            module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),
            module.StartupWordExpectation(address=0x8000633C, expected_word=0x38000000),
        ),
    )
    memory = _memory_for_config(module, config)
    diagnostic = bytearray(b"\x00" * 0x40)
    diagnostic[0x00:0x10] = b"P3BOOTSTRAPCANRY"
    diagnostic[0x14:0x18] = (0x50334254).to_bytes(4, "big")
    diagnostic[0x18:0x1C] = (1).to_bytes(4, "big")
    diagnostic[0x1C:0x20] = (0x817FE3A0).to_bytes(4, "big")
    diagnostic[0x20:0x24] = (0x817FE3A0).to_bytes(4, "big")
    diagnostic[0x24:0x28] = (0x817E0000).to_bytes(4, "big")
    diagnostic[0x28:0x2C] = (0xB0071002).to_bytes(4, "big")
    memory[0x817E0100] = bytes(diagnostic)
    runtime_state = bytearray(payload_bytes[0x20:0x310])
    memory[0x817E1000] = bytes(runtime_state)
    memory[0x80000034] = (0x817E0000).to_bytes(4, "big")
    memory[0x80003110] = (0x817E0000).to_bytes(4, "big")
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["relocated_runtime"]["matches_expected"] is True
    assert result["relocated_runtime"]["classification"] == "exact payload match"
    assert result["relocated_runtime"]["copy_complete_matches_expected"] is True
    assert result["relocated_runtime"]["runtime_executed_matches_expected"] is True
    assert result["relocated_runtime"]["runtime_execution_counter_value"] == 1
    assert result["relocated_runtime"]["runtime_status_matches_expected"] is True
    assert result["relocated_runtime"]["bootstrap_return_matches_expected"] is True
    assert result["relocated_runtime"]["runtime_poll_counter_value"] == 7
    assert result["relocated_runtime"]["runtime_poll_heartbeat_value"] == 7
    assert result["relocated_runtime"]["runtime_poll_last_sequence_value"] == 7
    assert result["relocated_runtime"]["diagnostics"]["wrapper_counts_balanced"] is True
    assert result["relocated_runtime"]["diagnostics"]["last_execution_marker_name"] == "wrapper_returning_to_game"
    assert result["relocated_runtime"]["transport"]["phase"] == 17
    assert result["relocated_runtime"]["transport"]["kd_closed"] == 1
    assert result["relocated_runtime"]["transport"]["nwc24_output_buffer_hex"] == "11" * 32
    assert result["relocated_runtime"]["transport"]["host_id"] == 0xC0A80164
    assert result["relocated_runtime"]["transport"]["last_receive_preview_hex"] == "0102030405060708090a0b0c0d0e0f10"
    assert result["probable_stop_boundary"] == "bound_no_recv"


def test_observe_probe_reports_recurring_hook_and_poll_progress() -> None:
    module = _load_module()
    runtime_blob_first = bytearray(b"R" * 0x2F0)
    _write_u32(runtime_blob_first, 0x38, 0x434F5059)
    _write_u32(runtime_blob_first, 0x3C, 0x52554E21)
    _write_u32(runtime_blob_first, 0x40, 1)
    _write_u32(runtime_blob_first, 0x44, 0x52544F4B)
    _write_u32(runtime_blob_first, 0x48, 0x4252544E)
    _write_u32(runtime_blob_first, 0x4C, 7)
    _write_u32(runtime_blob_first, 0x50, 7)
    _write_u32(runtime_blob_first, 0x54, 7)
    _install_transport_state(
        runtime_blob_first,
        phase=17,
        kd_fd=-1,
        kd_closed=1,
        ip_fd=3,
        socket_fd=4,
        host_id=0xC0A80164,
        bound_port=43674,
    )
    _install_diagnostics(
        runtime_blob_first,
        hook_wrapper_entry_count=7,
        hook_wrapper_before_poll_count=7,
        runtime_poll_entry_count=7,
        runtime_poll_exit_count=7,
        state_machine_entry_count=7,
        state_machine_exit_count=7,
        ios_submit_attempt_count=0,
        ios_submit_return_count=0,
        ios_submit_return_value=0,
        callback_entry_count=0,
        callback_exit_count=0,
        hook_wrapper_after_poll_count=7,
        hook_wrapper_exit_count=7,
        last_execution_marker=0xC0DE000D,
        last_transport_phase_before_step=17,
        last_transport_phase_after_step=17,
        callback_result=0,
    )
    _install_abi_probe_state(runtime_blob_first)
    runtime_blob_second = bytearray(runtime_blob_first)
    _write_u32(runtime_blob_second, 0x4C, 11)
    _write_u32(runtime_blob_second, 0x50, 11)
    _write_u32(runtime_blob_second, 0x54, 11)
    _install_diagnostics(
        runtime_blob_second,
        hook_wrapper_entry_count=11,
        hook_wrapper_before_poll_count=11,
        runtime_poll_entry_count=11,
        runtime_poll_exit_count=11,
        state_machine_entry_count=11,
        state_machine_exit_count=11,
        ios_submit_attempt_count=0,
        ios_submit_return_count=0,
        ios_submit_return_value=0,
        callback_entry_count=0,
        callback_exit_count=0,
        hook_wrapper_after_poll_count=11,
        hook_wrapper_exit_count=11,
        last_execution_marker=0xC0DE000D,
        last_transport_phase_before_step=17,
        last_transport_phase_after_step=17,
        callback_result=0,
    )

    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob_first)
    manifest = _relocated_manifest(payload_bytes)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(
            module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),
        ),
        hook_address=0x800BB71C,
        expected_hook_word=0x48000005,
        repeat_delay_seconds=0.25,
    )

    first_memory = _memory_for_config(module, config)
    second_memory = _memory_for_config(module, config)
    first_memory[0x800BB71C] = (0x48000005).to_bytes(4, "big")
    second_memory[0x800BB71C] = (0x48000005).to_bytes(4, "big")
    first_memory[0x817E1000] = bytes(runtime_blob_first)
    second_memory[0x817E1000] = bytes(runtime_blob_second)
    for memory in (first_memory, second_memory):
        diagnostic = bytearray(b"\x00" * 0x40)
        diagnostic[0x00:0x10] = b"P3BOOTSTRAPCANRY"
        diagnostic[0x14:0x18] = (0x50334254).to_bytes(4, "big")
        diagnostic[0x18:0x1C] = (1).to_bytes(4, "big")
        diagnostic[0x1C:0x20] = (0x817FE3A0).to_bytes(4, "big")
        diagnostic[0x20:0x24] = (0x817FE3A0).to_bytes(4, "big")
        diagnostic[0x24:0x28] = (0x817E0000).to_bytes(4, "big")
        diagnostic[0x28:0x2C] = (0xB0071002).to_bytes(4, "big")
        memory[0x817E0100] = bytes(diagnostic)
        memory[0x80000034] = (0x817E0000).to_bytes(4, "big")
        memory[0x80003110] = (0x817E0000).to_bytes(4, "big")

    backend = FakeBackend([first_memory, second_memory])

    result = module.observe_probe_memory(backend, config)

    assert result["live_hook_word"] == 0x48000005
    assert result["hook_word_matches_expected"] is True
    assert result["poll_counter_delta"] == 4
    assert result["poll_counter_monotonic"] is True
    assert result["heartbeat_updated"] is True
    assert result["approximate_calls_per_second"] == 16.0
    assert result["recurring_execution_continuing"] is True
    assert result["probable_stop_boundary"] == "bound_no_recv_stable"


def test_observe_probe_reports_waiting_for_callback_boundary() -> None:
    module = _load_module()
    runtime_blob = bytearray(b"R" * 0x2F0)
    _write_u32(runtime_blob, 0x38, 0x434F5059)
    _write_u32(runtime_blob, 0x3C, 0x52554E21)
    _write_u32(runtime_blob, 0x40, 1)
    _write_u32(runtime_blob, 0x44, 0x52544F4B)
    _write_u32(runtime_blob, 0x48, 0x4252544E)
    _write_u32(runtime_blob, 0x4C, 1)
    _write_u32(runtime_blob, 0x50, 1)
    _write_u32(runtime_blob, 0x54, 1)
    _install_transport_state(
        runtime_blob,
        phase=4,
        last_ios_result=0,
        pending_operation=4,
        pending_generation=1,
        callback_generation=0,
        callback_count=0,
    )
    _install_diagnostics(
        runtime_blob,
        hook_wrapper_entry_count=1,
        hook_wrapper_before_poll_count=1,
        runtime_poll_entry_count=1,
        runtime_poll_exit_count=1,
        state_machine_entry_count=1,
        state_machine_exit_count=1,
        ios_submit_attempt_count=1,
        ios_submit_return_count=1,
        ios_submit_return_value=0,
        callback_entry_count=0,
        callback_exit_count=0,
        hook_wrapper_after_poll_count=1,
        hook_wrapper_exit_count=1,
        c_before_veneer_call_count=1,
        retail_veneer_entry_count=1,
        retail_target_return_count=1,
        retail_veneer_exit_count=1,
        c_after_veneer_call_count=1,
        last_execution_marker=0xC0DE000A,
        last_transport_phase_before_step=7,
        last_transport_phase_after_step=8,
        callback_result=0,
    )
    _install_abi_probe_state(runtime_blob)
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob)
    manifest = _relocated_manifest(payload_bytes)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
    )
    memory = _memory_for_config(module, config)
    _install_bootstrap_diagnostic(memory)
    memory[0x817E1000] = bytes(runtime_blob)
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["relocated_runtime"]["diagnostics"]["ios_submission_returned"] is True
    assert result["relocated_runtime"]["diagnostics"]["callback_observed"] is False
    assert result["probable_stop_boundary"] == "waiting_nwc24_callback"


def test_observe_probe_reports_abi_probe_pass_boundary() -> None:
    module = _load_module()
    runtime_blob = bytearray(b"R" * 0x2F0)
    _write_u32(runtime_blob, 0x38, 0x434F5059)
    _write_u32(runtime_blob, 0x3C, 0x52554E21)
    _write_u32(runtime_blob, 0x40, 1)
    _write_u32(runtime_blob, 0x44, 0x52544F4B)
    _write_u32(runtime_blob, 0x48, 0x4252544E)
    _write_u32(runtime_blob, 0x4C, 4)
    _write_u32(runtime_blob, 0x50, 4)
    _write_u32(runtime_blob, 0x54, 4)
    _install_transport_state(runtime_blob, phase=0xFE)
    _install_diagnostics(
        runtime_blob,
        hook_wrapper_entry_count=4,
        hook_wrapper_before_poll_count=4,
        runtime_poll_entry_count=4,
        runtime_poll_exit_count=4,
        state_machine_entry_count=4,
        state_machine_exit_count=4,
        ios_submit_attempt_count=0,
        ios_submit_return_count=0,
        ios_submit_return_value=0,
        callback_entry_count=0,
        callback_exit_count=0,
        hook_wrapper_after_poll_count=4,
        hook_wrapper_exit_count=4,
        last_execution_marker=0xC0DE000D,
        last_transport_phase_before_step=0xFE,
        last_transport_phase_after_step=0xFE,
        callback_result=0,
    )
    expected_args = (
        0x11111111,
        0x22222222,
        0x33333333,
        0x44444444,
        0x55555555,
        0x66666666,
        0x77777777,
        0x88888888,
    )
    _install_abi_probe_state(
        runtime_blob,
        supplied_args=expected_args,
        pre_call_args=expected_args,
        target_args=expected_args,
        return_value=0x13579BDF,
        result_flags=0x003FFFFF,
        stack_pointer_before=0x817E3F00,
        stack_pointer_after=0x817E3F00,
        saved_lr=0x80001234,
        restored_lr=0x80001234,
        saved_r2=0x80400000,
        restored_r2=0x80400000,
        saved_r13=0x80500000,
        restored_r13=0x80500000,
        target_ctr=0x817E1800,
        after_call_flag=1,
    )
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob)
    manifest = _relocated_manifest(payload_bytes)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
    )
    memory = _memory_for_config(module, config)
    _install_bootstrap_diagnostic(memory)
    memory[0x817E1000] = bytes(runtime_blob)
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["probable_stop_boundary"] == "abi_probe_passed"
    assert result["relocated_runtime"]["abi_probe"]["pass"] is True
    assert result["relocated_runtime"]["abi_probe"]["target_called"] is True
    assert result["relocated_runtime"]["abi_probe"]["supplied_args"] == list(expected_args)


def test_observe_probe_reports_contradictory_diagnostic_counters() -> None:
    module = _load_module()
    runtime_blob = bytearray(b"R" * 0x2F0)
    _write_u32(runtime_blob, 0x38, 0x434F5059)
    _write_u32(runtime_blob, 0x3C, 0x52554E21)
    _write_u32(runtime_blob, 0x40, 1)
    _write_u32(runtime_blob, 0x44, 0x52544F4B)
    _write_u32(runtime_blob, 0x48, 0x4252544E)
    _write_u32(runtime_blob, 0x4C, 1)
    _write_u32(runtime_blob, 0x50, 1)
    _write_u32(runtime_blob, 0x54, 1)
    _install_transport_state(runtime_blob, phase=0)
    _install_diagnostics(
        runtime_blob,
        hook_wrapper_entry_count=1,
        hook_wrapper_before_poll_count=1,
        runtime_poll_entry_count=1,
        runtime_poll_exit_count=2,
        state_machine_entry_count=1,
        state_machine_exit_count=1,
        ios_submit_attempt_count=0,
        ios_submit_return_count=0,
        ios_submit_return_value=0,
        callback_entry_count=0,
        callback_exit_count=0,
        hook_wrapper_after_poll_count=1,
        hook_wrapper_exit_count=1,
        last_execution_marker=0xC0DE000B,
        last_transport_phase_before_step=0,
        last_transport_phase_after_step=0,
        callback_result=0,
    )
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob)
    manifest = _relocated_manifest(payload_bytes)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
    )
    memory = _memory_for_config(module, config)
    _install_bootstrap_diagnostic(memory)
    memory[0x817E1000] = bytes(runtime_blob)
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["relocated_runtime"]["diagnostics"]["counter_consistency"] == "contradictory"
    assert result["probable_stop_boundary"] == "contradictory_counters"


def test_observe_probe_reports_terminal_ip_open_state() -> None:
    module = _load_module()
    runtime_blob_first = bytearray(b"R" * 0x360)
    runtime_blob_second = bytearray(b"R" * 0x360)
    for runtime_blob, poll_value in ((runtime_blob_first, 7), (runtime_blob_second, 11)):
        _write_u32(runtime_blob, 0x38, 0x434F5059)
        _write_u32(runtime_blob, 0x3C, 0x52554E21)
        _write_u32(runtime_blob, 0x40, 1)
        _write_u32(runtime_blob, 0x44, 0x52544F4B)
        _write_u32(runtime_blob, 0x48, 0x4252544E)
        _write_u32(runtime_blob, 0x4C, poll_value)
        _write_u32(runtime_blob, 0x50, poll_value)
        _write_u32(runtime_blob, 0x54, poll_value)
        _install_transport_state(
            runtime_blob,
            phase=0xFE,
            pending_operation=0,
            open_kd_submit_count=1,
            open_kd_callback_count=1,
            nwc24_submit_count=1,
            nwc24_callback_count=1,
            nwc24_synchronous_result=0,
            nwc24_callback_result=0,
            open_ip_submit_count=1,
            open_ip_callback_count=1,
            kd_close_submit_count=1,
            kd_close_callback_count=1,
            kd_fd=-1,
            kd_closed=1,
            ip_fd=7,
            startup_submit_count=0,
            get_host_id_submit_count=0,
            socket_submit_count=0,
            bind_submit_count=0,
            receive_count=0,
            send_count=0,
        )
        _write_u32(runtime_blob, 0x254, 0x817E12C0)
        _write_u32(runtime_blob, 0x258, 15)
        _write_u32(runtime_blob, 0x25C, 0)
        _write_u32(runtime_blob, 0x260, 0x817E1010)
        _write_u32(runtime_blob, 0x264, 0x817E1280)
        _write_u32(runtime_blob, 0x268, 1)
        _write_u32(runtime_blob, 0x26C, 0)
        _write_u32(runtime_blob, 0x270, 0)
        _write_s32(runtime_blob, 0x274, -1)
        _write_s32(runtime_blob, 0x278, 11)
        _write_s32(runtime_blob, 0x27C, 11)
        _write_s32(runtime_blob, 0x280, -1)
        _write_s32(runtime_blob, 0x284, 0)
        _write_s32(runtime_blob, 0x288, 7)
        _write_u32(runtime_blob, 0x28C, 1)
        _write_u32(runtime_blob, 0x290, 1)
        _write_s32(runtime_blob, 0x294, 0)
        _write_s32(runtime_blob, 0x298, 0)
        _write_u32(runtime_blob, 0x29C, 1)
        _write_u32(runtime_blob, 0x2A0, 1)
        _install_diagnostics(
            runtime_blob,
            hook_wrapper_entry_count=poll_value,
            hook_wrapper_before_poll_count=poll_value,
            runtime_poll_entry_count=poll_value,
            runtime_poll_exit_count=poll_value,
            state_machine_entry_count=poll_value,
            state_machine_exit_count=poll_value,
            ios_submit_attempt_count=3,
            ios_submit_return_count=3,
            ios_submit_return_value=0,
            callback_entry_count=3,
            callback_exit_count=3,
            hook_wrapper_after_poll_count=poll_value,
            hook_wrapper_exit_count=poll_value,
            last_execution_marker=0xC0DE000D,
            last_transport_phase_before_step=0xFE,
            last_transport_phase_after_step=0xFE,
            callback_result=7,
        )
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob_first)
    raw = _relocated_manifest(payload_bytes).to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_nwc24_close_open_ip_once"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_nwc24_close_open_ip_once"
    transport["terminal_phase_value"] = 0xFE
    transport["terminal_phase_name"] = "IP_OPEN"
    transport["open_ip_path_pointer_address"] = 0x817E1254
    transport["open_ip_path_pointer_size"] = 4
    transport["open_ip_path_length_address"] = 0x817E1258
    transport["open_ip_path_length_size"] = 4
    transport["open_ip_mode_value_address"] = 0x817E125C
    transport["open_ip_mode_value_size"] = 4
    transport["open_ip_callback_pointer_address"] = 0x817E1260
    transport["open_ip_callback_pointer_size"] = 4
    transport["open_ip_context_pointer_address"] = 0x817E1264
    transport["open_ip_context_pointer_size"] = 4
    transport["open_ip_callback_exit_count_address"] = 0x817E1268
    transport["open_ip_callback_exit_count_size"] = 4
    transport["open_ip_stale_callback_count_address"] = 0x817E126C
    transport["open_ip_stale_callback_count_size"] = 4
    transport["open_ip_duplicate_callback_count_address"] = 0x817E1270
    transport["open_ip_duplicate_callback_count_size"] = 4
    transport["ip_fd_before_open_ip_address"] = 0x817E1274
    transport["ip_fd_before_open_ip_size"] = 4
    transport["kd_close_submitted_fd_address"] = 0x817E1278
    transport["kd_close_submitted_fd_size"] = 4
    transport["kd_fd_before_close_address"] = 0x817E127C
    transport["kd_fd_before_close_size"] = 4
    transport["kd_fd_after_close_address"] = 0x817E1280
    transport["kd_fd_after_close_size"] = 4
    transport["open_ip_submit_result_address"] = 0x817E1284
    transport["open_ip_submit_result_size"] = 4
    transport["open_ip_callback_result_address"] = 0x817E1288
    transport["open_ip_callback_result_size"] = 4
    transport["open_ip_submit_generation_address"] = 0x817E128C
    transport["open_ip_submit_generation_size"] = 4
    transport["open_ip_callback_generation_address"] = 0x817E1290
    transport["open_ip_callback_generation_size"] = 4
    transport["kd_close_submit_result_address"] = 0x817E1294
    transport["kd_close_submit_result_size"] = 4
    transport["kd_close_callback_result_address"] = 0x817E1298
    transport["kd_close_callback_result_size"] = 4
    transport["kd_close_submit_generation_address"] = 0x817E129C
    transport["kd_close_submit_generation_size"] = 4
    transport["kd_close_callback_generation_address"] = 0x817E12A0
    transport["kd_close_callback_generation_size"] = 4
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated
    manifest = Prime3RuntimePayloadManifest.from_json_dict(raw)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
        repeat_delay_seconds=0.25,
    )
    first_memory = _memory_for_config(module, config)
    second_memory = _memory_for_config(module, config)
    for memory, runtime_blob in ((first_memory, runtime_blob_first), (second_memory, runtime_blob_second)):
        _install_bootstrap_diagnostic(memory)
        memory[0x817E1000] = bytes(runtime_blob)
        memory[0x817E12C0] = b"/dev/net/ip/top\x00"
    backend = FakeBackend([first_memory, second_memory])

    result = module.observe_probe_memory(backend, config)

    assert result["probable_stop_boundary"] == "ip_open"
    assert result["poll_counter_delta"] == 4
    assert result["recurring_execution_continuing"] is True
    assert result["relocated_runtime"]["transport"]["open_ip_path_address"] == 0x817E12C0
    assert result["relocated_runtime"]["transport"]["open_ip_path_length"] == 15
    assert result["relocated_runtime"]["transport"]["open_ip_path_bounded_string"] == "/dev/net/ip/top"
    assert result["relocated_runtime"]["transport"]["open_ip_mode"] == 0
    assert result["relocated_runtime"]["transport"]["open_ip_callback_pointer"] == 0x817E1010
    assert result["relocated_runtime"]["transport"]["open_ip_context_pointer"] == 0x817E1280
    assert result["relocated_runtime"]["transport"]["open_ip_callback_exit_count"] == 1
    assert result["relocated_runtime"]["transport"]["ip_fd_before_open_ip"] == -1
    assert result["relocated_runtime"]["transport"]["kd_close_submitted_fd"] == 11
    assert result["relocated_runtime"]["transport"]["kd_fd_before_close"] == 11
    assert result["relocated_runtime"]["transport"]["kd_fd_after_close"] == -1


def test_observe_probe_reports_terminal_so_started_state() -> None:
    module = _load_module()
    runtime_blob_first = bytearray(b"R" * 0x360)
    runtime_blob_second = bytearray(b"R" * 0x360)
    for runtime_blob, poll_value in ((runtime_blob_first, 7), (runtime_blob_second, 11)):
        _write_u32(runtime_blob, 0x38, 0x434F5059)
        _write_u32(runtime_blob, 0x3C, 0x52554E21)
        _write_u32(runtime_blob, 0x40, 1)
        _write_u32(runtime_blob, 0x44, 0x52544F4B)
        _write_u32(runtime_blob, 0x48, 0x4252544E)
        _write_u32(runtime_blob, 0x4C, poll_value)
        _write_u32(runtime_blob, 0x50, poll_value)
        _write_u32(runtime_blob, 0x54, poll_value)
        _install_transport_state(
            runtime_blob,
            phase=18,
            pending_operation=0,
            open_kd_submit_count=1,
            open_kd_callback_count=1,
            nwc24_submit_count=1,
            nwc24_callback_count=1,
            nwc24_synchronous_result=0,
            nwc24_callback_result=0,
            open_ip_submit_count=1,
            open_ip_callback_count=1,
            kd_close_submit_count=1,
            kd_close_callback_count=1,
            startup_submit_count=1,
            startup_callback_count=1,
            kd_fd=-1,
            kd_closed=1,
            ip_fd=11,
            service_started=1,
            get_host_id_submit_count=0,
            socket_submit_count=0,
            bind_submit_count=0,
            receive_count=0,
            send_count=0,
        )
        _write_u32(runtime_blob, 0x254, 0x80504FE0)
        _write_u32(runtime_blob, 0x258, 31)
        _write_s32(runtime_blob, 0x25C, 11)
        _write_u32(runtime_blob, 0x260, 0x817E1010)
        _write_u32(runtime_blob, 0x264, 0x817E1280)
        _write_u32(runtime_blob, 0x268, 1)
        _write_u32(runtime_blob, 0x26C, 0)
        _write_u32(runtime_blob, 0x270, 0)
        _write_u32(runtime_blob, 0x274, 0)
        _write_u32(runtime_blob, 0x278, 1)
        _write_s32(runtime_blob, 0x27C, 11)
        _write_s32(runtime_blob, 0x280, 11)
        _write_u32(runtime_blob, 0x284, 0)
        _write_u32(runtime_blob, 0x288, 0)
        _write_u32(runtime_blob, 0x28C, 9)
        _write_u32(runtime_blob, 0x290, 10)
        for offset, value in enumerate((11, 31, 0, 0, 0, 0, 0x817E1010, 0x817E1280)):
            _write_u32(runtime_blob, 0x2A4 + offset * 4, value)
        _write_u32(runtime_blob, 0x2C4, 1)
        _write_s32(runtime_blob, 0x294, 0)
        _write_s32(runtime_blob, 0x298, 0)
        _write_u32(runtime_blob, 0x29C, 1)
        _write_u32(runtime_blob, 0x2A0, 1)
        _install_diagnostics(
            runtime_blob,
            hook_wrapper_entry_count=poll_value,
            hook_wrapper_before_poll_count=poll_value,
            runtime_poll_entry_count=poll_value,
            runtime_poll_exit_count=poll_value,
            state_machine_entry_count=poll_value,
            state_machine_exit_count=poll_value,
            ios_submit_attempt_count=4,
            ios_submit_return_count=4,
            ios_submit_return_value=0,
            callback_entry_count=4,
            callback_exit_count=4,
            hook_wrapper_after_poll_count=poll_value,
            hook_wrapper_exit_count=poll_value,
            last_execution_marker=0xC0DE000D,
            last_transport_phase_before_step=18,
            last_transport_phase_after_step=18,
            callback_result=0,
        )
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob_first)
    raw = _relocated_manifest(payload_bytes).to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_nwc24_close_open_ip_startup_once"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_nwc24_close_open_ip_startup_once"
    transport["terminal_phase_value"] = 18
    transport["terminal_phase_name"] = "SO_STARTED"
    transport["service_started_address"] = 0x817E12C4
    transport["service_started_size"] = 4
    transport["startup_target_address"] = 0x817E1254
    transport["startup_target_size"] = 4
    transport["startup_command_address"] = 0x817E1258
    transport["startup_command_size"] = 4
    transport["startup_submitted_fd_address"] = 0x817E125C
    transport["startup_submitted_fd_size"] = 4
    transport["startup_callback_pointer_address"] = 0x817E1260
    transport["startup_callback_pointer_size"] = 4
    transport["startup_context_pointer_address"] = 0x817E1264
    transport["startup_context_pointer_size"] = 4
    transport["startup_callback_exit_count_address"] = 0x817E1268
    transport["startup_callback_exit_count_size"] = 4
    transport["startup_stale_callback_count_address"] = 0x817E126C
    transport["startup_stale_callback_count_size"] = 4
    transport["startup_duplicate_callback_count_address"] = 0x817E1270
    transport["startup_duplicate_callback_count_size"] = 4
    transport["startup_service_started_before_submit_address"] = 0x817E1274
    transport["startup_service_started_before_submit_size"] = 4
    transport["startup_service_started_after_completion_address"] = 0x817E1278
    transport["startup_service_started_after_completion_size"] = 4
    transport["ip_fd_before_startup_address"] = 0x817E127C
    transport["ip_fd_before_startup_size"] = 4
    transport["ip_fd_after_startup_address"] = 0x817E1280
    transport["ip_fd_after_startup_size"] = 4
    transport["startup_pending_before_submit_address"] = 0x817E1284
    transport["startup_pending_before_submit_size"] = 4
    transport["startup_pending_after_completion_address"] = 0x817E1288
    transport["startup_pending_after_completion_size"] = 4
    transport["startup_phase_before_submit_address"] = 0x817E128C
    transport["startup_phase_before_submit_size"] = 4
    transport["startup_phase_after_completion_address"] = 0x817E1290
    transport["startup_phase_after_completion_size"] = 4
    transport["startup_submit_result_address"] = 0x817E1294
    transport["startup_submit_result_size"] = 4
    transport["startup_callback_result_address"] = 0x817E1298
    transport["startup_callback_result_size"] = 4
    transport["startup_submit_generation_address"] = 0x817E129C
    transport["startup_submit_generation_size"] = 4
    transport["startup_callback_generation_address"] = 0x817E12A0
    transport["startup_callback_generation_size"] = 4
    transport["startup_pre_call_args_address"] = 0x817E12A4
    transport["startup_pre_call_args_size"] = 0x20
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated
    manifest = Prime3RuntimePayloadManifest.from_json_dict(raw)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
        repeat_delay_seconds=0.25,
    )
    first_memory = _memory_for_config(module, config)
    second_memory = _memory_for_config(module, config)
    for memory, runtime_blob in ((first_memory, runtime_blob_first), (second_memory, runtime_blob_second)):
        _install_bootstrap_diagnostic(memory)
        memory[0x817E1000] = bytes(runtime_blob)
    backend = FakeBackend([first_memory, second_memory])

    result = module.observe_probe_memory(backend, config)

    assert result["probable_stop_boundary"] == "so_started"
    assert result["recurring_execution_continuing"] is True
    assert result["relocated_runtime"]["transport"]["startup_target_address"] == 0x80504FE0
    assert result["relocated_runtime"]["transport"]["startup_command"] == 31
    assert result["relocated_runtime"]["transport"]["startup_pre_call_args"] == [
        11,
        31,
        0,
        0,
        0,
        0,
        0x817E1010,
        0x817E1280,
    ]


def test_observe_probe_reports_host_id_ready_for_high_bit_ipv4() -> None:
    module = _load_module()
    runtime_blob_first = bytearray(b"R" * 0x360)
    runtime_blob_second = bytearray(b"R" * 0x360)
    for runtime_blob, poll_value in ((runtime_blob_first, 7), (runtime_blob_second, 11)):
        _write_u32(runtime_blob, 0x38, 0x434F5059)
        _write_u32(runtime_blob, 0x3C, 0x52554E21)
        _write_u32(runtime_blob, 0x40, 1)
        _write_u32(runtime_blob, 0x44, 0x52544F4B)
        _write_u32(runtime_blob, 0x48, 0x4252544E)
        _write_u32(runtime_blob, 0x4C, poll_value)
        _write_u32(runtime_blob, 0x50, poll_value)
        _write_u32(runtime_blob, 0x54, poll_value)
        _install_transport_state(
            runtime_blob,
            phase=19,
            pending_operation=0,
            open_kd_submit_count=1,
            open_kd_callback_count=1,
            nwc24_submit_count=1,
            nwc24_callback_count=1,
            nwc24_synchronous_result=0,
            nwc24_callback_result=0,
            open_ip_submit_count=1,
            open_ip_callback_count=1,
            kd_close_submit_count=1,
            kd_close_callback_count=1,
            startup_submit_count=1,
            startup_callback_count=1,
            get_host_id_submit_count=1,
            get_host_id_callback_count=1,
            kd_fd=-1,
            kd_closed=1,
            ip_fd=11,
            host_id=0xC0A80164,
            service_started=1,
        )
        _write_u32(runtime_blob, 0x254, 0x80504FE0)
        _write_u32(runtime_blob, 0x258, 16)
        _write_s32(runtime_blob, 0x25C, 11)
        _write_u32(runtime_blob, 0x260, 0x817E1010)
        _write_u32(runtime_blob, 0x264, 0x817E12A0)
        _write_u32(runtime_blob, 0x268, 1)
        _write_u32(runtime_blob, 0x26C, 0)
        _write_u32(runtime_blob, 0x270, 0)
        _write_u32(runtime_blob, 0x274, 1)
        _write_u32(runtime_blob, 0x278, 1)
        _write_s32(runtime_blob, 0x27C, 11)
        _write_s32(runtime_blob, 0x280, 11)
        _write_u32(runtime_blob, 0x284, 0)
        _write_u32(runtime_blob, 0x288, 0)
        _write_u32(runtime_blob, 0x28C, 11)
        _write_u32(runtime_blob, 0x290, 12)
        for offset, value in enumerate((11, 16, 0, 0, 0, 0, 0x817E1010, 0x817E12A0)):
            _write_u32(runtime_blob, 0x294 + offset * 4, value)
        _write_u32(runtime_blob, 0x2CC, 1)
        _write_u32(runtime_blob, 0x2D0, 1)
        _write_u32(runtime_blob, 0x2D4, 1)
        _write_s32(runtime_blob, 0x2D8, 0)
        _write_s32(runtime_blob, 0x2DC, -1062731420)
        _write_u32(runtime_blob, 0x2E0, 1)
        _write_u32(runtime_blob, 0x2E4, 1)
        _install_diagnostics(
            runtime_blob,
            hook_wrapper_entry_count=poll_value,
            hook_wrapper_before_poll_count=poll_value,
            runtime_poll_entry_count=poll_value,
            runtime_poll_exit_count=poll_value,
            state_machine_entry_count=poll_value,
            state_machine_exit_count=poll_value,
            ios_submit_attempt_count=5,
            ios_submit_return_count=5,
            ios_submit_return_value=0,
            callback_entry_count=5,
            callback_exit_count=5,
            hook_wrapper_after_poll_count=poll_value,
            hook_wrapper_exit_count=poll_value,
            last_execution_marker=0xC0DE000D,
            last_transport_phase_before_step=19,
            last_transport_phase_after_step=19,
            callback_result=-1062731420,
        )
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob_first)
    raw = _relocated_manifest(payload_bytes).to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_get_host_id_once"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_get_host_id_once"
    transport["terminal_phase_value"] = 19
    transport["terminal_phase_name"] = "HOST_ID_READY"
    transport["service_started_address"] = 0x817E12CC
    transport["service_started_size"] = 4
    transport["host_id_available_address"] = 0x817E12D0
    transport["host_id_available_size"] = 4
    transport["host_id_ready_address"] = 0x817E12D4
    transport["host_id_ready_size"] = 4
    transport["get_host_id_target_address"] = 0x817E1254
    transport["get_host_id_target_size"] = 4
    transport["get_host_id_command_address"] = 0x817E1258
    transport["get_host_id_command_size"] = 4
    transport["get_host_id_submitted_fd_address"] = 0x817E125C
    transport["get_host_id_submitted_fd_size"] = 4
    transport["get_host_id_callback_pointer_address"] = 0x817E1260
    transport["get_host_id_callback_pointer_size"] = 4
    transport["get_host_id_context_pointer_address"] = 0x817E1264
    transport["get_host_id_context_pointer_size"] = 4
    transport["get_host_id_callback_exit_count_address"] = 0x817E1268
    transport["get_host_id_callback_exit_count_size"] = 4
    transport["get_host_id_stale_callback_count_address"] = 0x817E126C
    transport["get_host_id_stale_callback_count_size"] = 4
    transport["get_host_id_duplicate_callback_count_address"] = 0x817E1270
    transport["get_host_id_duplicate_callback_count_size"] = 4
    transport["get_host_id_service_started_before_submit_address"] = 0x817E1274
    transport["get_host_id_service_started_before_submit_size"] = 4
    transport["get_host_id_service_started_after_completion_address"] = 0x817E1278
    transport["get_host_id_service_started_after_completion_size"] = 4
    transport["ip_fd_before_get_host_id_address"] = 0x817E127C
    transport["ip_fd_before_get_host_id_size"] = 4
    transport["ip_fd_after_get_host_id_address"] = 0x817E1280
    transport["ip_fd_after_get_host_id_size"] = 4
    transport["get_host_id_pending_before_submit_address"] = 0x817E1284
    transport["get_host_id_pending_before_submit_size"] = 4
    transport["get_host_id_pending_after_completion_address"] = 0x817E1288
    transport["get_host_id_pending_after_completion_size"] = 4
    transport["get_host_id_phase_before_submit_address"] = 0x817E128C
    transport["get_host_id_phase_before_submit_size"] = 4
    transport["get_host_id_phase_after_completion_address"] = 0x817E1290
    transport["get_host_id_phase_after_completion_size"] = 4
    transport["get_host_id_pre_call_args_address"] = 0x817E1294
    transport["get_host_id_pre_call_args_size"] = 0x20
    transport["get_host_id_submit_result_address"] = 0x817E12D8
    transport["get_host_id_submit_result_size"] = 4
    transport["get_host_id_callback_result_address"] = 0x817E12DC
    transport["get_host_id_callback_result_size"] = 4
    transport["get_host_id_submit_generation_address"] = 0x817E12E0
    transport["get_host_id_submit_generation_size"] = 4
    transport["get_host_id_callback_generation_address"] = 0x817E12E4
    transport["get_host_id_callback_generation_size"] = 4
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated
    manifest = Prime3RuntimePayloadManifest.from_json_dict(raw)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
        repeat_delay_seconds=0.25,
    )
    first_memory = _memory_for_config(module, config)
    second_memory = _memory_for_config(module, config)
    for memory, runtime_blob in ((first_memory, runtime_blob_first), (second_memory, runtime_blob_second)):
        _install_bootstrap_diagnostic(memory)
        memory[0x817E1000] = bytes(runtime_blob)
    backend = FakeBackend([first_memory, second_memory])

    result = module.observe_probe_memory(backend, config)

    assert result["probable_stop_boundary"] == "host_id_ready"
    assert result["poll_counter_delta"] == 4
    assert result["recurring_execution_continuing"] is True
    assert result["relocated_runtime"]["transport"]["host_id"] == 0xC0A80164
    assert result["relocated_runtime"]["transport"]["host_id_callback_result"] == -1062731420
    assert result["relocated_runtime"]["transport"]["host_id_callback_result_u32"] == 0xC0A80164
    assert result["relocated_runtime"]["transport"]["host_id_dotted_ipv4"] == "192.168.1.100"
    assert result["relocated_runtime"]["transport"]["get_host_id_pre_call_args"] == [
        11,
        16,
        0,
        0,
        0,
        0,
        0x817E1010,
        0x817E12A0,
    ]


def test_observe_probe_reports_get_host_id_unavailable() -> None:
    module = _load_module()
    runtime_blob = bytearray(b"R" * 0x2F0)
    _write_u32(runtime_blob, 0x38, 0x434F5059)
    _write_u32(runtime_blob, 0x3C, 0x52554E21)
    _write_u32(runtime_blob, 0x40, 1)
    _write_u32(runtime_blob, 0x44, 0x52544F4B)
    _write_u32(runtime_blob, 0x48, 0x4252544E)
    _write_u32(runtime_blob, 0x4C, 7)
    _write_u32(runtime_blob, 0x50, 7)
    _write_u32(runtime_blob, 0x54, 7)
    _install_transport_state(
        runtime_blob,
        phase=0xFF,
        pending_operation=0,
        open_kd_submit_count=1,
        open_kd_callback_count=1,
        nwc24_submit_count=1,
        nwc24_callback_count=1,
        open_ip_submit_count=1,
        open_ip_callback_count=1,
        kd_close_submit_count=1,
        kd_close_callback_count=1,
        startup_submit_count=1,
        startup_callback_count=1,
        get_host_id_submit_count=1,
        get_host_id_callback_count=1,
        kd_fd=-1,
        kd_closed=1,
        ip_fd=11,
        host_id=0,
        service_started=1,
    )
    _install_diagnostics(
        runtime_blob,
        hook_wrapper_entry_count=7,
        hook_wrapper_before_poll_count=7,
        runtime_poll_entry_count=7,
        runtime_poll_exit_count=7,
        state_machine_entry_count=7,
        state_machine_exit_count=7,
        ios_submit_attempt_count=5,
        ios_submit_return_count=5,
        ios_submit_return_value=0,
        callback_entry_count=5,
        callback_exit_count=5,
        hook_wrapper_after_poll_count=7,
        hook_wrapper_exit_count=7,
        last_execution_marker=0xC0DE000D,
        last_transport_phase_before_step=0xFF,
        last_transport_phase_after_step=0xFF,
        callback_result=0,
    )
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob)
    raw = _relocated_manifest(payload_bytes).to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_get_host_id_once"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_get_host_id_once"
    transport["terminal_phase_value"] = 19
    transport["terminal_phase_name"] = "HOST_ID_READY"
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated
    manifest = Prime3RuntimePayloadManifest.from_json_dict(raw)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
    )
    memory = _memory_for_config(module, config)
    _install_bootstrap_diagnostic(memory)
    memory[0x817E1000] = bytes(runtime_blob)
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["probable_stop_boundary"] == "get_host_id_unavailable"


@pytest.mark.parametrize(
    ("diagnostics", "expected"),
    [
        (
            {
                "counter_consistency": "consistent",
                "c_before_veneer_call_count": 1,
                "retail_veneer_entry_count": 0,
                "retail_target_return_count": 0,
                "retail_veneer_exit_count": 0,
                "c_after_veneer_call_count": 0,
                "callback_entry_count": 0,
                "callback_exit_count": 0,
                "runtime_poll_entry_count": 1,
                "runtime_poll_exit_count": 1,
                "state_machine_entry_count": 1,
                "state_machine_exit_count": 1,
                "ios_submit_return_count": 0,
                "last_execution_marker_name": "c_before_veneer_call",
            },
            "before_veneer",
        ),
        (
            {
                "counter_consistency": "consistent",
                "c_before_veneer_call_count": 1,
                "retail_veneer_entry_count": 1,
                "retail_target_return_count": 0,
                "retail_veneer_exit_count": 0,
                "c_after_veneer_call_count": 0,
                "callback_entry_count": 0,
                "callback_exit_count": 0,
                "runtime_poll_entry_count": 1,
                "runtime_poll_exit_count": 1,
                "state_machine_entry_count": 1,
                "state_machine_exit_count": 1,
                "ios_submit_return_count": 0,
                "last_execution_marker_name": "retail_veneer_entered",
            },
            "inside_veneer_before_target",
        ),
        (
            {
                "counter_consistency": "consistent",
                "c_before_veneer_call_count": 1,
                "retail_veneer_entry_count": 1,
                "retail_target_return_count": 1,
                "retail_veneer_exit_count": 0,
                "c_after_veneer_call_count": 0,
                "callback_entry_count": 0,
                "callback_exit_count": 0,
                "runtime_poll_entry_count": 1,
                "runtime_poll_exit_count": 1,
                "state_machine_entry_count": 1,
                "state_machine_exit_count": 1,
                "ios_submit_return_count": 0,
                "last_execution_marker_name": "retail_target_returned",
            },
            "target_returned_veneer_stuck",
        ),
        (
            {
                "counter_consistency": "consistent",
                "c_before_veneer_call_count": 1,
                "retail_veneer_entry_count": 1,
                "retail_target_return_count": 1,
                "retail_veneer_exit_count": 1,
                "c_after_veneer_call_count": 0,
                "callback_entry_count": 0,
                "callback_exit_count": 0,
                "runtime_poll_entry_count": 1,
                "runtime_poll_exit_count": 1,
                "state_machine_entry_count": 1,
                "state_machine_exit_count": 1,
                "ios_submit_return_count": 0,
                "last_execution_marker_name": "retail_before_veneer_blr",
            },
            "veneer_returned_c_stuck",
        ),
    ],
)
def test_diagnostic_stop_boundary_classifies_new_veneer_boundaries(
    diagnostics: dict[str, object],
    expected: str,
) -> None:
    module = _load_module()

    result = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport=None,
        abi_probe=None,
        recurring_execution_continuing=False,
    )

    assert result == expected


def test_diagnostic_stop_boundary_classifies_abi_probe_states() -> None:
    module = _load_module()
    diagnostics = {
        "counter_consistency": "consistent",
        "last_execution_marker_name": "wrapper_returning_to_game",
    }

    passed = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport=None,
        abi_probe={"pass": True, "target_called": True},
        recurring_execution_continuing=True,
    )
    failed = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport=None,
        abi_probe={"pass": False, "target_called": True},
        recurring_execution_continuing=True,
    )
    incomplete = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport=None,
        abi_probe={"pass": False, "target_called": False, "result_flags": 1},
        recurring_execution_continuing=True,
    )

    assert passed == "abi_probe_passed"
    assert failed == "abi_probe_failed"
    assert incomplete == "abi_probe_incomplete"


def test_diagnostic_stop_boundary_classifies_create_socket_states() -> None:
    module = _load_module()
    diagnostics = {
        "counter_consistency": "consistent",
        "last_execution_marker_name": "wrapper_returning_to_game",
    }
    transport_common = {
        "mode": "retail_wrapper_create_socket_once",
        "open_kd_callback_count": 1,
        "nwc24_callback_count": 1,
        "kd_close_callback_count": 1,
        "open_ip_callback_count": 1,
        "startup_callback_count": 1,
        "get_host_id_callback_count": 1,
        "socket_submit_count": 1,
        "socket_callback_count": 1,
        "socket_callback_exit_count": 1,
        "socket_target_address": 0x80504FE0,
        "socket_command": 15,
        "socket_submitted_fd": 11,
        "ip_fd": 11,
        "socket_callback_pointer": 0x817E1010,
        "socket_context_pointer": 0x817E1320,
        "socket_pre_call_args": [11, 15, 0x817E1300, 12, 0, 0, 0x817E1010, 0x817E1320],
        "socket_request_address": 0x817E1300,
        "socket_submit_result": 0,
        "socket_submit_generation": 7,
        "socket_callback_generation": 7,
        "socket_request_logical_size": 12,
        "socket_request_alignment": 0x20,
        "socket_family_value": 2,
        "socket_type_value": 2,
        "socket_protocol_value": 0,
        "socket_request_bytes_hex": "000000020000000200000000",
        "socket_callback_result": 0,
        "socket_fd": 0,
        "socket_descriptor_valid": 1,
        "socket_ready": 1,
        "pending_operation": 0,
        "kd_fd": -1,
        "kd_closed": 1,
        "service_started": 1,
        "host_id_ready": 1,
        "bind_submit_count": 0,
        "receive_count": 0,
        "send_count": 0,
    }

    ready = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 20, **transport_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    submission_failed = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 0xFF, **transport_common, "socket_submit_result": 1},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    callback_failed = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 0xFF, **transport_common, "socket_callback_count": 1, "socket_callback_result": -1},
        abi_probe=None,
        recurring_execution_continuing=True,
    )

    assert ready == "socket_ready"
    assert submission_failed == "create_socket_submission_failed"
    assert callback_failed == "create_socket_callback_failed"


def test_diagnostic_stop_boundary_classifies_bind_and_cleanup_states() -> None:
    module = _load_module()
    diagnostics = {
        "counter_consistency": "consistent",
        "last_execution_marker_name": "wrapper_returning_to_game",
    }
    bind_common = {
        "mode": "retail_wrapper_bind_once",
        "open_kd_callback_count": 1,
        "nwc24_callback_count": 1,
        "kd_close_callback_count": 1,
        "open_ip_callback_count": 1,
        "startup_callback_count": 1,
        "get_host_id_callback_count": 1,
        "socket_submit_count": 1,
        "socket_callback_count": 1,
        "socket_callback_exit_count": 1,
        "socket_target_address": 0x80504FE0,
        "socket_command": 15,
        "socket_submitted_fd": 11,
        "ip_fd": 11,
        "socket_callback_pointer": 0x817E1010,
        "socket_context_pointer": 0x817E1320,
        "socket_pre_call_args": [11, 15, 0x817E1300, 12, 0, 0, 0x817E1010, 0x817E1320],
        "socket_request_address": 0x817E1300,
        "socket_submit_result": 0,
        "socket_submit_generation": 7,
        "socket_callback_generation": 7,
        "socket_request_logical_size": 12,
        "socket_request_alignment": 0x20,
        "socket_family_value": 2,
        "socket_type_value": 2,
        "socket_protocol_value": 0,
        "socket_request_bytes_hex": "000000020000000200000000",
        "socket_callback_result": 0,
        "socket_fd": 0,
        "socket_descriptor_valid": 1,
        "socket_ready": 1,
        "pending_operation": 0,
        "kd_fd": -1,
        "kd_closed": 1,
        "service_started": 1,
        "host_id_ready": 1,
        "bind_submit_count": 0,
        "receive_count": 0,
        "send_count": 0,
        "callback_pending": 0,
        "receive_submit_count": 0,
        "send_submit_count": 0,
        "ip_close_submit_count": 0,
        "socket_close_submit_count": 0,
        "bound_port": 43674,
        "bound_flag": 1,
        "bound_address": 0,
    }

    socket_ready = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 20, **bind_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    waiting_bind_submission = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 15, "last_submit_result": 0, **bind_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    bind_submission_failed_cleanup_pending = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={**bind_common, "phase": 15, "last_submit_result": -1, "bind_submit_count": 1},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    waiting_bind_callback = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={**bind_common, "phase": 16, "pending_operation": 8, "bind_submit_count": 1},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    bind_callback_failed_cleanup_pending = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={**bind_common, "phase": 21, "bind_callback_result": 1, "bind_submit_count": 1},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    waiting_bind_failure_close_submission = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={**bind_common, "phase": 21, "bind_callback_result": 0, "bind_submit_count": 1},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    waiting_bind_failure_close_callback = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={**bind_common, "phase": 22, "pending_operation": 9, "bind_submit_count": 1},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    bind_failed_cleaned = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={**bind_common, "phase": 23, "socket_fd": -1, "socket_ready": 0, "bind_submit_count": 1},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    failed_socket_leak = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={**bind_common, "phase": 24, "socket_leak_detected": 1, "bind_submit_count": 1},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    bound_no_recv_stable = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 17, "socket_fd": 0, **bind_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )

    assert socket_ready == "socket_ready"
    assert waiting_bind_submission == "waiting_bind_submission"
    assert bind_submission_failed_cleanup_pending == "bind_submission_failed_cleanup_pending"
    assert waiting_bind_callback == "waiting_bind_callback"
    assert bind_callback_failed_cleanup_pending == "bind_callback_failed_cleanup_pending"
    assert waiting_bind_failure_close_submission == "waiting_bind_failure_close_submission"
    assert waiting_bind_failure_close_callback == "waiting_bind_failure_close_callback"
    assert bind_failed_cleaned == "bind_failed_cleaned"
    assert failed_socket_leak == "failed_socket_leak"
    assert bound_no_recv_stable == "bound_no_recv_stable"


def test_diagnostic_stop_boundary_classifies_recvfrom_once_states() -> None:
    module = _load_module()
    diagnostics = {
        "counter_consistency": "consistent",
        "last_execution_marker_name": "wrapper_returning_to_game",
    }
    recv_common = {
        "mode": "retail_wrapper_recvfrom_once",
        "receive_submit_count": 1,
        "receive_count": 1,
        "send_count": 0,
        "send_submit_count": 0,
        "ip_close_submit_count": 0,
        "socket_close_submit_count": 0,
        "pending_operation": 0,
        "callback_pending": 0,
        "last_receive_length": 32,
    }

    waiting_receive_submission_transport = dict(recv_common)
    waiting_receive_submission_transport["receive_submit_count"] = 0
    waiting_receive_submission = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 25, "last_submit_result": 0, **waiting_receive_submission_transport},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    waiting_receive_callback_transport = dict(recv_common)
    waiting_receive_callback_transport["pending_operation"] = 10
    waiting_receive_callback = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 26, **waiting_receive_callback_transport},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    received_datagram = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 27, **recv_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    receive_submit_failed = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 28, **recv_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    receive_async_failed = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 29, **recv_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    receive_invalid_positive = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 30, **recv_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    receive_oversized_result = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 31, **recv_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    receive_stale_callback = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 32, **recv_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    receive_duplicate_callback = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 33, **recv_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )
    receive_cleanup_deferred = module._diagnostic_stop_boundary(
        diagnostics=diagnostics,
        transport={"phase": 34, **recv_common},
        abi_probe=None,
        recurring_execution_continuing=True,
    )

    assert waiting_receive_submission == "waiting_receive_submission"
    assert waiting_receive_callback == "waiting_receive_callback"
    assert received_datagram == "received_datagram"
    assert receive_submit_failed == "receive_submit_failed"
    assert receive_async_failed == "receive_async_failed"
    assert receive_invalid_positive == "receive_invalid_positive"
    assert receive_oversized_result == "receive_oversized_result"
    assert receive_stale_callback == "receive_stale_callback"
    assert receive_duplicate_callback == "receive_duplicate_callback"
    assert receive_cleanup_deferred == "receive_cleanup_deferred"


def test_observe_probe_rejects_short_payload_read() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend(_memory_for_config(module, config, short_payload=True))

    with pytest.raises(module.ProbeObservationError, match="Short read for payload bytes"):
        module.observe_probe_memory(backend, config)


def test_observe_probe_reports_canary_match() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend(_memory_for_config(module, config))

    result = module.observe_probe_memory(backend, config)

    assert result["canary"]["matches_expected"] is True


def test_observe_probe_reports_canary_mismatch() -> None:
    module = _load_module()
    config = _config(module)
    memory = _memory_for_config(module, config)
    corrupted = bytearray(config.payload_bytes)
    corrupted[0x10] ^= 0x01
    memory[config.payload_address] = bytes(corrupted)
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["canary"]["matches_expected"] is False


def test_observe_probe_reports_all_zero_payload() -> None:
    module = _load_module()
    config = _config(module)
    memory = _memory_for_config(module, config)
    memory[config.payload_address] = b"\x00" * len(config.payload_bytes)
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["payload_classification"] == "all zero"
    assert result["payload_all_zero"] is True


def test_observe_probe_reports_altered_payload() -> None:
    module = _load_module()
    config = _config(module)
    memory = _memory_for_config(module, config)
    altered = bytearray(config.payload_bytes)
    altered[0] ^= 0x01
    memory[config.payload_address] = bytes(altered)
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["payload_classification"] == "payload present but altered"


def test_observe_probe_rejects_wrong_game_build() -> None:
    module = _load_module()
    config = _config(module)
    memory = _memory_for_config(module, config)
    memory[module.GAME_ID_ADDRESS] = b"RM3P01"
    backend = FakeBackend(memory)

    with pytest.raises(module.ProbeObservationError, match="Unexpected game ID"):
        module.observe_probe_memory(backend, config)


def test_observe_probe_rejects_disconnected_emulator() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend({}, hooked=False, hook_success=False)

    with pytest.raises(module.ProbeObservationError, match="Unable to connect to Dolphin"):
        module.observe_probe_memory(backend, config)


def test_observe_probe_module_exposes_no_write_api() -> None:
    module = _load_module()

    assert not hasattr(module, "write_bytes")


def test_observe_probe_reports_stable_repeated_reads() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend(_memory_for_config(module, config))

    result = module.observe_probe_memory(backend, config)

    assert result["repeated_read_stable"] is True


def test_observe_probe_reports_changing_repeated_reads() -> None:
    module = _load_module()
    config = _config(module)
    first = _memory_for_config(module, config)
    second = _memory_for_config(module, config)
    second[config.payload_address] = b"\x00" * len(config.payload_bytes)
    backend = FakeBackend([first, second])

    result = module.observe_probe_memory(backend, config)

    assert result["repeated_read_stable"] is False


def test_observe_probe_rejects_invalid_pointer_dereference() -> None:
    module = _load_module()
    config = _config(module)
    memory = _memory_for_config(module, config)
    memory[module.BOOT_INFO_POINTER_ADDRESS] = (0x90000000).to_bytes(4, "big")
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["invalid_boot_info_pointer"] == 0x90000000
    assert "boot_info_plus_8" not in result


def test_observe_probe_cli_writes_json_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    config = _config(module)
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    report_path = tmp_path.joinpath("report.json")
    payload_path.write_bytes(config.payload_bytes)
    manifest_path.write_text(config.manifest.to_json_text(), encoding="utf-8")
    memory = _memory_for_config(module, config)
    memory[0x800BB71C] = (0x48000005).to_bytes(4, "big")
    monkeypatch.setattr(module, "dolphin_memory_engine", FakeBackend(memory))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "observe_probe.py",
            "--payload-address",
            hex(config.payload_address),
            "--payload-bin",
            str(payload_path),
            "--payload-manifest",
            str(manifest_path),
            "--checkpoint-name",
            "entry",
            "--halt-address",
            "0x80006320",
            "--expected-halt-word",
            "0x48000000",
            "--report",
            str(report_path),
            "--startup-word",
            "0x80006320=0x48000000",
            "--startup-word",
            "0x8000633C=0x38000000",
            "--hook-address",
            "0x800BB71C",
            "--expected-hook-word",
            "0x48000005",
            "--iso-path",
            "X:\\probe.iso",
            "--iso-sha256",
            "abc123",
            "--dolphin-command-line",
            "Dolphin.exe --exec X:\\probe.iso",
        ],
    )

    module.main()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["payload_matches_expected"] is True
    assert payload["checkpoint_name"] == "entry"
    assert payload["hook_address"] == 0x800BB71C
    assert payload["expected_hook_word"] == 0x48000005
    assert payload["iso_path"] == "X:\\probe.iso"


def test_observe_probe_cli_requires_checkpoint_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    config = _config(module)
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    report_path = tmp_path.joinpath("report.json")
    payload_path.write_bytes(config.payload_bytes)
    manifest_path.write_text(config.manifest.to_json_text(), encoding="utf-8")
    monkeypatch.setattr(module, "dolphin_memory_engine", FakeBackend(_memory_for_config(module, config)))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "observe_probe.py",
            "--payload-address",
            hex(config.payload_address),
            "--payload-bin",
            str(payload_path),
            "--payload-manifest",
            str(manifest_path),
            "--halt-address",
            "0x80006320",
            "--expected-halt-word",
            "0x48000000",
            "--report",
            str(report_path),
        ],
    )

    with pytest.raises(module.ProbeObservationError, match="non-empty --checkpoint-name"):
        module.main()


def test_observe_probe_cli_allows_payload_only_without_checkpoint_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    config = _config(module)
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    report_path = tmp_path.joinpath("report.json")
    payload_path.write_bytes(config.payload_bytes)
    manifest_path.write_text(config.manifest.to_json_text(), encoding="utf-8")
    monkeypatch.setattr(module, "dolphin_memory_engine", FakeBackend(_memory_for_config(module, config)))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "observe_probe.py",
            "--payload-address",
            hex(config.payload_address),
            "--payload-bin",
            str(payload_path),
            "--payload-manifest",
            str(manifest_path),
            "--report",
            str(report_path),
        ],
    )

    module.main()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["checkpoint_name"] is None
    assert payload["entry_gate_active"] is False


def test_observe_probe_reports_recv_send_loop_transport_fields() -> None:
    module = _load_module()
    runtime_blob_first = bytearray(b"R" * 0x2F0)
    runtime_blob_second = bytearray(b"R" * 0x2F0)
    for runtime_blob, poll_value in ((runtime_blob_first, 9), (runtime_blob_second, 29)):
        _write_u32(runtime_blob, 0x38, 0x434F5059)
        _write_u32(runtime_blob, 0x3C, 0x52554E21)
        _write_u32(runtime_blob, 0x40, 1)
        _write_u32(runtime_blob, 0x44, 0x52544F4B)
        _write_u32(runtime_blob, 0x48, 0x4252544E)
        _write_u32(runtime_blob, 0x4C, poll_value)
        _write_u32(runtime_blob, 0x50, poll_value)
        _write_u32(runtime_blob, 0x54, poll_value)
        _install_transport_state(
            runtime_blob,
            phase=45,
            open_kd_submit_count=1,
            open_kd_callback_count=1,
            nwc24_submit_count=1,
            nwc24_callback_count=1,
            open_ip_submit_count=1,
            open_ip_callback_count=1,
            kd_close_submit_count=1,
            kd_close_callback_count=1,
            startup_submit_count=1,
            startup_callback_count=1,
            get_host_id_submit_count=1,
            get_host_id_callback_count=1,
            socket_submit_count=1,
            socket_callback_count=1,
            bind_submit_count=1,
            bind_callback_count=1,
            receive_submit_count=3,
            send_submit_count=3,
            receive_count=3,
            receive_bytes=72,
            send_count=3,
            send_bytes=87,
            receive_arm_count=3,
            receive_rearm_count=2,
            configured_exchange_limit=3,
            completed_exchange_count=3,
            current_exchange_index=3,
            last_completed_exchange_index=3,
            previous_peer_ipv4=0x1AD38AB6,
            previous_peer_port=43675,
            loop_complete_transition_count=1,
            polls_while_receive_pending=25,
            polls_after_loop_complete=poll_value,
            last_receive_length=24,
            last_send_length=29,
            last_peer_ipv4=0x1AD38AB6,
            last_peer_port=43675,
        )
        _install_diagnostics(
            runtime_blob,
            hook_wrapper_entry_count=poll_value,
            hook_wrapper_before_poll_count=poll_value,
            runtime_poll_entry_count=poll_value,
            runtime_poll_exit_count=poll_value,
            state_machine_entry_count=poll_value,
            state_machine_exit_count=poll_value,
            ios_submit_attempt_count=10,
            ios_submit_return_count=10,
            ios_submit_return_value=0,
            callback_entry_count=10,
            callback_exit_count=10,
            hook_wrapper_after_poll_count=poll_value,
            hook_wrapper_exit_count=poll_value,
            last_execution_marker=0xC0DE000D,
            last_transport_phase_before_step=45,
            last_transport_phase_after_step=45,
            callback_result=0,
        )
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob_first)
    raw = _relocated_manifest(payload_bytes).to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_recv_send_loop"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_recv_send_loop"
    transport["receive_enabled"] = True
    transport["send_enabled"] = True
    transport["terminal_phase_value"] = 45
    transport["terminal_phase_name"] = "LOOP_COMPLETE"
    transport["receive_arm_count_address"] = 0x817E12C0
    transport["receive_arm_count_size"] = 4
    transport["receive_rearm_count_address"] = 0x817E12C4
    transport["receive_rearm_count_size"] = 4
    transport["configured_exchange_limit_address"] = 0x817E12C8
    transport["configured_exchange_limit_size"] = 4
    transport["completed_exchange_count_address"] = 0x817E12CC
    transport["completed_exchange_count_size"] = 4
    transport["current_exchange_index_address"] = 0x817E12D0
    transport["current_exchange_index_size"] = 4
    transport["last_completed_exchange_index_address"] = 0x817E12D4
    transport["last_completed_exchange_index_size"] = 4
    transport["previous_peer_ipv4_address"] = 0x817E12D8
    transport["previous_peer_ipv4_size"] = 4
    transport["previous_peer_port_address"] = 0x817E12DC
    transport["previous_peer_port_size"] = 4
    transport["rearm_submission_failure_count_address"] = 0x817E12E0
    transport["rearm_submission_failure_count_size"] = 4
    transport["loop_complete_transition_count_address"] = 0x817E12E4
    transport["loop_complete_transition_count_size"] = 4
    transport["cleanup_deferred_count_address"] = 0x817E12E8
    transport["cleanup_deferred_count_size"] = 4
    transport["polls_while_receive_pending_address"] = 0x817E12EC
    transport["polls_while_receive_pending_size"] = 4
    transport["polls_after_loop_complete_address"] = 0x817E1230
    transport["polls_after_loop_complete_size"] = 4
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated
    manifest = Prime3RuntimePayloadManifest.from_json_dict(raw)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
        repeat_delay_seconds=0.5,
    )
    first_memory = _memory_for_config(module, config)
    second_memory = _memory_for_config(module, config)
    for memory, runtime_blob in ((first_memory, runtime_blob_first), (second_memory, runtime_blob_second)):
        _install_bootstrap_diagnostic(memory)
        memory[0x817E1000] = bytes(runtime_blob)
    backend = FakeBackend([first_memory, second_memory])

    result = module.observe_probe_memory(backend, config)

    assert result["probable_stop_boundary"] == "recurring_execution_continues"
    assert result["poll_counter_delta"] == 20
    assert result["first_observed_at_utc"]
    assert result["second_observed_at_utc"]
    assert result["relocated_runtime"]["transport"]["phase_name"] == "LOOP_COMPLETE"
    assert result["relocated_runtime"]["transport"]["receive_arm_count"] == 3
    assert result["relocated_runtime"]["transport"]["receive_rearm_count"] == 2
    assert result["relocated_runtime"]["transport"]["completed_exchange_count"] == 3
    assert result["relocated_runtime"]["transport"]["polls_after_loop_complete"] == 9


def test_observe_probe_reports_cp3w_frame_validation_transport_fields() -> None:
    module = _load_module()
    runtime_blob_first = bytearray(b"R" * 0x2F0)
    runtime_blob_second = bytearray(b"R" * 0x2F0)
    for runtime_blob, poll_value in ((runtime_blob_first, 15), (runtime_blob_second, 35)):
        _write_u32(runtime_blob, 0x38, 0x434F5059)
        _write_u32(runtime_blob, 0x3C, 0x52554E21)
        _write_u32(runtime_blob, 0x40, 1)
        _write_u32(runtime_blob, 0x44, 0x52544F4B)
        _write_u32(runtime_blob, 0x48, 0x4252544E)
        _write_u32(runtime_blob, 0x4C, poll_value)
        _write_u32(runtime_blob, 0x50, poll_value)
        _write_u32(runtime_blob, 0x54, poll_value)
        _install_transport_state(
            runtime_blob,
            phase=55,
            open_kd_submit_count=1,
            open_kd_callback_count=1,
            nwc24_submit_count=1,
            nwc24_callback_count=1,
            open_ip_submit_count=1,
            open_ip_callback_count=1,
            kd_close_submit_count=1,
            kd_close_callback_count=1,
            startup_submit_count=1,
            startup_callback_count=1,
            get_host_id_submit_count=1,
            get_host_id_callback_count=1,
            socket_submit_count=1,
            socket_callback_count=1,
            bind_submit_count=1,
            bind_callback_count=1,
            receive_submit_count=7,
            send_submit_count=2,
            receive_count=7,
            receive_bytes=212,
            send_count=2,
            send_bytes=82,
            configured_exchange_limit=7,
            completed_exchange_count=2,
            current_exchange_index=7,
            last_completed_exchange_index=2,
            last_receive_length=20,
            last_send_length=41,
            last_peer_ipv4=0x1AD38AB6,
            last_peer_port=43675,
            last_peer_family=2,
            polls_after_loop_complete=poll_value,
            last_receive_preview_hex=("43" "50" "33" "57" "01" "01" "7F" "00" "00" "00" "00" "2A" "00" "00" "00" "16"),
            last_send_preview_hex=("43" "50" "33" "57" "01" "02" "7F" "00" "00" "00" "00" "2A" "00" "00" "00" "15"),
        )
        _write_u32(runtime_blob, 0x254, 41)
        _write_u32(runtime_blob, 0x258, 7)
        _write_u32(runtime_blob, 0x25C, 2)
        _write_u32(runtime_blob, 0x260, 5)
        _write_u32(runtime_blob, 0x264, 1)
        _write_u32(runtime_blob, 0x268, 1)
        _write_u32(runtime_blob, 0x26C, 1)
        _write_u32(runtime_blob, 0x270, 1)
        _write_u32(runtime_blob, 0x274, 1)
        _write_u32(runtime_blob, 0x278, 1)
        _write_u32(runtime_blob, 0x27C, 0)
        _write_u32(runtime_blob, 0x280, 1)
        _write_u32(runtime_blob, 0x284, 2)
        _write_u32(runtime_blob, 0x288, 2)
        _write_u32(runtime_blob, 0x28C, 2)
        _write_u32(runtime_blob, 0x290, 0x2A)
        _write_u32(runtime_blob, 0x294, 0x2A)
        _write_u32(runtime_blob, 0x298, 1)
        _write_u32(runtime_blob, 0x29C, 22)
        _write_u32(runtime_blob, 0x2A0, 22)
        _write_u32(runtime_blob, 0x2A4, 1)
        _write_u32(runtime_blob, 0x2A8, 7)
        _install_diagnostics(
            runtime_blob,
            hook_wrapper_entry_count=poll_value,
            hook_wrapper_before_poll_count=poll_value,
            runtime_poll_entry_count=poll_value,
            runtime_poll_exit_count=poll_value,
            state_machine_entry_count=poll_value,
            state_machine_exit_count=poll_value,
            ios_submit_attempt_count=11,
            ios_submit_return_count=11,
            ios_submit_return_value=0,
            callback_entry_count=11,
            callback_exit_count=11,
            hook_wrapper_after_poll_count=poll_value,
            hook_wrapper_exit_count=poll_value,
            last_execution_marker=0xC0DE0011,
            last_transport_phase_before_step=55,
            last_transport_phase_after_step=55,
            callback_result=0,
        )
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob_first)
    raw = _relocated_manifest(payload_bytes).to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "cp3w_frame_validation"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "cp3w_frame_validation"
    transport["receive_enabled"] = True
    transport["send_enabled"] = True
    transport["terminal_phase_value"] = 55
    transport["terminal_phase_name"] = "CP3W_FRAME_LOOP_COMPLETE"
    transport["cp3w_magic_hex"] = "43503357"
    transport["cp3w_protocol_version"] = 1
    transport["cp3w_header_size"] = 16
    transport["cp3w_crc_size"] = 4
    transport["cp3w_crc_initial_value"] = 0xFFFFFFFF
    transport["cp3w_crc_final_xor_value"] = 0xFFFFFFFF
    transport["cp3w_crc_polynomial"] = 0xEDB88320
    transport["cp3w_crc_reflected"] = True
    transport["cp3w_packet_kind_request"] = 1
    transport["cp3w_packet_kind_response"] = 2
    transport["cp3w_command_reserved_mailbox"] = 127
    transport["cp3w_packet_kind_offset"] = 5
    transport["cp3w_command_offset"] = 6
    transport["cp3w_response_status_offset"] = 7
    transport["cp3w_request_id_offset"] = 8
    transport["cp3w_payload_length_offset"] = 12
    transport["cp3w_request_payload_ascii"] = "P3_FRAME_TEST_20260717"
    transport["cp3w_response_payload_ascii"] = "P3_FRAME_ACK_20260717"
    transport["cp3w_request_payload_length"] = 22
    transport["cp3w_response_payload_length"] = 21
    transport["prepared_send_length_address"] = 0x817E1254
    transport["prepared_send_length_size"] = 4
    transport["cp3w_datagrams_processed_address"] = 0x817E1258
    transport["cp3w_datagrams_processed_size"] = 4
    transport["cp3w_frames_valid_address"] = 0x817E125C
    transport["cp3w_frames_valid_size"] = 4
    transport["cp3w_frames_invalid_address"] = 0x817E1260
    transport["cp3w_frames_invalid_size"] = 4
    transport["cp3w_frames_too_short_address"] = 0x817E1264
    transport["cp3w_frames_too_short_size"] = 4
    transport["cp3w_frames_invalid_magic_address"] = 0x817E1268
    transport["cp3w_frames_invalid_magic_size"] = 4
    transport["cp3w_frames_invalid_version_address"] = 0x817E126C
    transport["cp3w_frames_invalid_version_size"] = 4
    transport["cp3w_frames_unsupported_type_address"] = 0x817E1270
    transport["cp3w_frames_unsupported_type_size"] = 4
    transport["cp3w_frames_nonzero_flags_address"] = 0x817E1274
    transport["cp3w_frames_nonzero_flags_size"] = 4
    transport["cp3w_frames_length_mismatch_address"] = 0x817E1278
    transport["cp3w_frames_length_mismatch_size"] = 4
    transport["cp3w_frames_payload_too_large_address"] = 0x817E127C
    transport["cp3w_frames_payload_too_large_size"] = 4
    transport["cp3w_frames_invalid_payload_address"] = 0x817E1280
    transport["cp3w_frames_invalid_payload_size"] = 4
    transport["cp3w_frames_malformed_address"] = 0x817E1284
    transport["cp3w_frames_malformed_size"] = 4
    transport["cp3w_framed_responses_submitted_address"] = 0x817E1288
    transport["cp3w_framed_responses_submitted_size"] = 4
    transport["cp3w_framed_responses_completed_address"] = 0x817E128C
    transport["cp3w_framed_responses_completed_size"] = 4
    transport["cp3w_last_request_id_address"] = 0x817E1290
    transport["cp3w_last_request_id_size"] = 4
    transport["cp3w_last_response_id_address"] = 0x817E1294
    transport["cp3w_last_response_id_size"] = 4
    transport["cp3w_last_message_type_address"] = 0x817E1298
    transport["cp3w_last_message_type_size"] = 4
    transport["cp3w_last_declared_payload_length_address"] = 0x817E129C
    transport["cp3w_last_declared_payload_length_size"] = 4
    transport["cp3w_last_actual_payload_length_address"] = 0x817E12A0
    transport["cp3w_last_actual_payload_length_size"] = 4
    transport["cp3w_last_frame_result_address"] = 0x817E12A4
    transport["cp3w_last_frame_result_size"] = 4
    transport["cp3w_final_datagram_index_address"] = 0x817E12A8
    transport["cp3w_final_datagram_index_size"] = 4
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated
    manifest = Prime3RuntimePayloadManifest.from_json_dict(raw)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
        repeat_delay_seconds=0.5,
    )
    first_memory = _memory_for_config(module, config)
    second_memory = _memory_for_config(module, config)
    for memory, runtime_blob in ((first_memory, runtime_blob_first), (second_memory, runtime_blob_second)):
        _install_bootstrap_diagnostic(memory)
        memory[0x817E1000] = bytes(runtime_blob)
    backend = FakeBackend([first_memory, second_memory])

    result = module.observe_probe_memory(backend, config)

    assert result["probable_stop_boundary"] == "recurring_execution_continues"
    assert result["poll_counter_delta"] == 20
    assert result["relocated_runtime"]["transport"]["phase_name"] == "CP3W_FRAME_LOOP_COMPLETE"
    assert result["relocated_runtime"]["transport"]["prepared_send_length"] == 41
    assert result["relocated_runtime"]["transport"]["cp3w_magic_hex"] == "43503357"
    assert result["relocated_runtime"]["transport"]["cp3w_frames_valid"] == 2
    assert result["relocated_runtime"]["transport"]["cp3w_frames_invalid"] == 5
    assert result["relocated_runtime"]["transport"]["cp3w_frames_invalid_magic"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_frames_length_mismatch"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_framed_responses_submitted"] == 2
    assert result["relocated_runtime"]["transport"]["cp3w_framed_responses_completed"] == 2
    assert result["relocated_runtime"]["transport"]["cp3w_last_request_id"] == 0x2A
    assert result["relocated_runtime"]["transport"]["cp3w_last_response_id"] == 0x2A
    assert result["relocated_runtime"]["transport"]["cp3w_last_message_type"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_last_declared_payload_length"] == 22
    assert result["relocated_runtime"]["transport"]["cp3w_last_actual_payload_length"] == 22
    assert result["relocated_runtime"]["transport"]["cp3w_last_frame_result"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_final_datagram_index"] == 7


def test_observe_probe_reports_cp3w_ping_pong_transport_fields() -> None:
    module = _load_module()
    runtime_blob_first = bytearray(b"R" * 0x2F0)
    runtime_blob_second = bytearray(b"R" * 0x2F0)
    for runtime_blob, poll_value in ((runtime_blob_first, 20), (runtime_blob_second, 40)):
        _write_u32(runtime_blob, 0x38, 0x434F5059)
        _write_u32(runtime_blob, 0x3C, 0x52554E21)
        _write_u32(runtime_blob, 0x40, 1)
        _write_u32(runtime_blob, 0x44, 0x52544F4B)
        _write_u32(runtime_blob, 0x48, 0x4252544E)
        _write_u32(runtime_blob, 0x4C, poll_value)
        _write_u32(runtime_blob, 0x50, poll_value)
        _write_u32(runtime_blob, 0x54, poll_value)
        _install_transport_state(
            runtime_blob,
            phase=61,
            open_kd_submit_count=1,
            open_kd_callback_count=1,
            nwc24_submit_count=1,
            nwc24_callback_count=1,
            open_ip_submit_count=1,
            open_ip_callback_count=1,
            kd_close_submit_count=1,
            kd_close_callback_count=1,
            startup_submit_count=1,
            startup_callback_count=1,
            get_host_id_submit_count=1,
            get_host_id_callback_count=1,
            socket_submit_count=1,
            socket_callback_count=1,
            bind_submit_count=1,
            bind_callback_count=1,
            receive_submit_count=8,
            send_submit_count=2,
            receive_count=8,
            receive_bytes=204,
            send_count=2,
            send_bytes=43,
            configured_exchange_limit=8,
            completed_exchange_count=2,
            current_exchange_index=8,
            last_completed_exchange_index=2,
            last_receive_length=28,
            last_send_length=28,
            last_peer_ipv4=0x1AD38AB6,
            last_peer_port=43675,
            last_peer_family=2,
            polls_after_loop_complete=poll_value,
            last_receive_preview_hex=("43" "50" "33" "57" "01" "01" "03" "00" "00" "00" "00" "11" "00" "00" "00" "0D"),
            last_send_preview_hex=("43" "50" "33" "57" "01" "02" "04" "01" "00" "00" "00" "12" "00" "00" "00" "1C"),
        )
        _write_u32(runtime_blob, 0x254, 28)
        _write_u32(runtime_blob, 0x258, 8)
        _write_u32(runtime_blob, 0x25C, 2)
        _write_u32(runtime_blob, 0x260, 6)
        _write_u32(runtime_blob, 0x264, 0)
        _write_u32(runtime_blob, 0x268, 0)
        _write_u32(runtime_blob, 0x26C, 0)
        _write_u32(runtime_blob, 0x270, 0)
        _write_u32(runtime_blob, 0x274, 0)
        _write_u32(runtime_blob, 0x278, 0)
        _write_u32(runtime_blob, 0x27C, 0)
        _write_u32(runtime_blob, 0x280, 0)
        _write_u32(runtime_blob, 0x284, 0)
        _write_u32(runtime_blob, 0x288, 0)
        _write_u32(runtime_blob, 0x28C, 0)
        _write_u32(runtime_blob, 0x290, 0x12)
        _write_u32(runtime_blob, 0x294, 0x12)
        _write_u32(runtime_blob, 0x298, 4)
        _write_u32(runtime_blob, 0x29C, 0)
        _write_u32(runtime_blob, 0x2A0, 0)
        _write_u32(runtime_blob, 0x2A4, 1)
        _write_u32(runtime_blob, 0x2A8, 8)
        _write_u32(runtime_blob, 0x2AC, 2)
        _write_u32(runtime_blob, 0x2B0, 1)
        _write_u32(runtime_blob, 0x2B4, 1)
        _write_u32(runtime_blob, 0x2B8, 1)
        _write_u32(runtime_blob, 0x2BC, 1)
        _write_u32(runtime_blob, 0x2C0, 1)
        _write_u32(runtime_blob, 0x2C4, 1)
        _write_u32(runtime_blob, 0x2C8, 4)
        _write_u32(runtime_blob, 0x2CC, 1)
        _write_u32(runtime_blob, 0x2D0, 0)
        _write_u32(runtime_blob, 0x2D4, 1)
        _install_diagnostics(
            runtime_blob,
            hook_wrapper_entry_count=poll_value,
            hook_wrapper_before_poll_count=poll_value,
            runtime_poll_entry_count=poll_value,
            runtime_poll_exit_count=poll_value,
            state_machine_entry_count=poll_value,
            state_machine_exit_count=poll_value,
            ios_submit_attempt_count=12,
            ios_submit_return_count=12,
            ios_submit_return_value=0,
            callback_entry_count=12,
            callback_exit_count=12,
            hook_wrapper_after_poll_count=poll_value,
            hook_wrapper_exit_count=poll_value,
            last_execution_marker=0xC0DE0011,
            last_transport_phase_before_step=61,
            last_transport_phase_after_step=61,
            callback_result=0,
        )
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob_first)
    raw = _relocated_manifest(payload_bytes).to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "cp3w_ping_pong"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "cp3w_ping_pong"
    transport["receive_enabled"] = True
    transport["send_enabled"] = True
    transport["terminal_phase_value"] = 61
    transport["terminal_phase_name"] = "CP3W_PING_PONG_LOOP_COMPLETE"
    transport["cp3w_magic_hex"] = "43503357"
    transport["cp3w_protocol_version"] = 1
    transport["cp3w_header_size"] = 16
    transport["cp3w_crc_size"] = 4
    transport["cp3w_crc_initial_value"] = 0xFFFFFFFF
    transport["cp3w_crc_final_xor_value"] = 0xFFFFFFFF
    transport["cp3w_crc_polynomial"] = 0xEDB88320
    transport["cp3w_crc_reflected"] = True
    transport["cp3w_packet_kind_request"] = 1
    transport["cp3w_packet_kind_response"] = 2
    transport["cp3w_response_status_error"] = 1
    transport["cp3w_command_ping"] = 3
    transport["cp3w_pong_command"] = 3
    transport["cp3w_pong_uses_ping_command"] = True
    transport["cp3w_command_reserved_mailbox"] = 127
    transport["cp3w_error_code_unknown_command"] = 4
    transport["cp3w_packet_kind_offset"] = 5
    transport["cp3w_command_offset"] = 6
    transport["cp3w_response_status_offset"] = 7
    transport["cp3w_request_id_offset"] = 8
    transport["cp3w_payload_length_offset"] = 12
    transport["cp3w_ping_max_payload_length"] = 1472
    transport["cp3w_unsupported_message_ascii"] = "Command is unsupported"
    transport["prepared_send_length_address"] = 0x817E1254
    transport["prepared_send_length_size"] = 4
    transport["cp3w_datagrams_processed_address"] = 0x817E1258
    transport["cp3w_datagrams_processed_size"] = 4
    transport["cp3w_frames_valid_address"] = 0x817E125C
    transport["cp3w_frames_valid_size"] = 4
    transport["cp3w_frames_invalid_address"] = 0x817E1260
    transport["cp3w_frames_invalid_size"] = 4
    transport["cp3w_frames_too_short_address"] = 0x817E1264
    transport["cp3w_frames_too_short_size"] = 4
    transport["cp3w_frames_invalid_magic_address"] = 0x817E1268
    transport["cp3w_frames_invalid_magic_size"] = 4
    transport["cp3w_frames_invalid_version_address"] = 0x817E126C
    transport["cp3w_frames_invalid_version_size"] = 4
    transport["cp3w_frames_unsupported_type_address"] = 0x817E1270
    transport["cp3w_frames_unsupported_type_size"] = 4
    transport["cp3w_frames_nonzero_flags_address"] = 0x817E1274
    transport["cp3w_frames_nonzero_flags_size"] = 4
    transport["cp3w_frames_length_mismatch_address"] = 0x817E1278
    transport["cp3w_frames_length_mismatch_size"] = 4
    transport["cp3w_frames_payload_too_large_address"] = 0x817E127C
    transport["cp3w_frames_payload_too_large_size"] = 4
    transport["cp3w_frames_invalid_payload_address"] = 0x817E1280
    transport["cp3w_frames_invalid_payload_size"] = 4
    transport["cp3w_frames_malformed_address"] = 0x817E1284
    transport["cp3w_frames_malformed_size"] = 4
    transport["cp3w_framed_responses_submitted_address"] = 0x817E1288
    transport["cp3w_framed_responses_submitted_size"] = 4
    transport["cp3w_framed_responses_completed_address"] = 0x817E128C
    transport["cp3w_framed_responses_completed_size"] = 4
    transport["cp3w_last_request_id_address"] = 0x817E1290
    transport["cp3w_last_request_id_size"] = 4
    transport["cp3w_last_response_id_address"] = 0x817E1294
    transport["cp3w_last_response_id_size"] = 4
    transport["cp3w_last_message_type_address"] = 0x817E1298
    transport["cp3w_last_message_type_size"] = 4
    transport["cp3w_last_declared_payload_length_address"] = 0x817E129C
    transport["cp3w_last_declared_payload_length_size"] = 4
    transport["cp3w_last_actual_payload_length_address"] = 0x817E12A0
    transport["cp3w_last_actual_payload_length_size"] = 4
    transport["cp3w_last_frame_result_address"] = 0x817E12A4
    transport["cp3w_last_frame_result_size"] = 4
    transport["cp3w_final_datagram_index_address"] = 0x817E12A8
    transport["cp3w_final_datagram_index_size"] = 4
    transport["cp3w_requests_dispatched_address"] = 0x817E12AC
    transport["cp3w_requests_dispatched_size"] = 4
    transport["cp3w_ping_requests_received_address"] = 0x817E12B0
    transport["cp3w_ping_requests_received_size"] = 4
    transport["cp3w_pong_responses_submitted_address"] = 0x817E12B4
    transport["cp3w_pong_responses_submitted_size"] = 4
    transport["cp3w_pong_responses_completed_address"] = 0x817E12B8
    transport["cp3w_pong_responses_completed_size"] = 4
    transport["cp3w_unsupported_commands_received_address"] = 0x817E12BC
    transport["cp3w_unsupported_commands_received_size"] = 4
    transport["cp3w_unsupported_responses_submitted_address"] = 0x817E12C0
    transport["cp3w_unsupported_responses_submitted_size"] = 4
    transport["cp3w_unsupported_responses_completed_address"] = 0x817E12C4
    transport["cp3w_unsupported_responses_completed_size"] = 4
    transport["cp3w_last_command_address"] = 0x817E12C8
    transport["cp3w_last_command_size"] = 4
    transport["cp3w_last_response_status_address"] = 0x817E12CC
    transport["cp3w_last_response_status_size"] = 4
    transport["cp3w_last_ping_payload_length_address"] = 0x817E12D0
    transport["cp3w_last_ping_payload_length_size"] = 4
    transport["cp3w_last_dispatch_result_address"] = 0x817E12D4
    transport["cp3w_last_dispatch_result_size"] = 4
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated
    manifest = Prime3RuntimePayloadManifest.from_json_dict(raw)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
        repeat_delay_seconds=0.5,
    )
    first_memory = _memory_for_config(module, config)
    second_memory = _memory_for_config(module, config)
    for memory, runtime_blob in ((first_memory, runtime_blob_first), (second_memory, runtime_blob_second)):
        _install_bootstrap_diagnostic(memory)
        memory[0x817E1000] = bytes(runtime_blob)
    backend = FakeBackend([first_memory, second_memory])

    result = module.observe_probe_memory(backend, config)

    assert result["probable_stop_boundary"] == "recurring_execution_continues"
    assert result["poll_counter_delta"] == 20
    assert result["relocated_runtime"]["transport"]["phase_name"] == "CP3W_PING_PONG_LOOP_COMPLETE"
    assert result["relocated_runtime"]["transport"]["prepared_send_length"] == 28
    assert result["relocated_runtime"]["transport"]["cp3w_response_status_error"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_command_ping"] == 3
    assert result["relocated_runtime"]["transport"]["cp3w_pong_command"] == 3
    assert result["relocated_runtime"]["transport"]["cp3w_pong_uses_ping_command"] is True
    assert result["relocated_runtime"]["transport"]["cp3w_error_code_unknown_command"] == 4
    assert result["relocated_runtime"]["transport"]["cp3w_unsupported_message_ascii"] == "Command is unsupported"
    assert result["relocated_runtime"]["transport"]["cp3w_requests_dispatched"] == 2
    assert result["relocated_runtime"]["transport"]["cp3w_ping_requests_received"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_pong_responses_submitted"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_pong_responses_completed"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_unsupported_commands_received"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_unsupported_responses_submitted"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_unsupported_responses_completed"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_last_command"] == 4
    assert result["relocated_runtime"]["transport"]["cp3w_last_response_status"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_last_ping_payload_length"] == 0
    assert result["relocated_runtime"]["transport"]["cp3w_last_dispatch_result"] == 1


def test_observe_probe_reports_cp3w_hello_session_transport_fields() -> None:
    module = _load_module()
    runtime_blob_first = bytearray(b"R" * 0x360)
    runtime_blob_second = bytearray(b"R" * 0x360)
    for runtime_blob, poll_value in ((runtime_blob_first, 25), (runtime_blob_second, 45)):
        _write_u32(runtime_blob, 0x38, 0x434F5059)
        _write_u32(runtime_blob, 0x3C, 0x52554E21)
        _write_u32(runtime_blob, 0x40, 1)
        _write_u32(runtime_blob, 0x44, 0x52544F4B)
        _write_u32(runtime_blob, 0x48, 0x4252544E)
        _write_u32(runtime_blob, 0x4C, poll_value)
        _write_u32(runtime_blob, 0x50, poll_value)
        _write_u32(runtime_blob, 0x54, poll_value)
        _install_transport_state(
            runtime_blob,
            phase=69,
            open_kd_submit_count=1,
            open_kd_callback_count=1,
            nwc24_submit_count=1,
            nwc24_callback_count=1,
            open_ip_submit_count=1,
            open_ip_callback_count=1,
            kd_close_submit_count=1,
            kd_close_callback_count=1,
            startup_submit_count=1,
            startup_callback_count=1,
            get_host_id_submit_count=1,
            get_host_id_callback_count=1,
            socket_submit_count=1,
            socket_callback_count=1,
            bind_submit_count=1,
            bind_callback_count=1,
            receive_submit_count=10,
            send_submit_count=8,
            receive_count=10,
            receive_bytes=330,
            send_count=8,
            send_bytes=404,
            configured_exchange_limit=10,
            completed_exchange_count=8,
            current_exchange_index=10,
            last_completed_exchange_index=8,
            last_receive_length=33,
            last_send_length=33,
            last_peer_ipv4=0x7F000001,
            last_peer_port=62909,
            last_peer_family=2,
            polls_after_loop_complete=poll_value,
            last_receive_preview_hex=("43" "50" "33" "57" "01" "01" "03" "00" "FF" "FF" "FF" "FF" "00" "00" "00" "0D"),
            last_send_preview_hex=("43" "50" "33" "57" "01" "02" "03" "00" "FF" "FF" "FF" "FF" "00" "00" "00" "0D"),
        )
        _write_u32(runtime_blob, 0x254, 33)
        _write_u32(runtime_blob, 0x258, 10)
        _write_u32(runtime_blob, 0x25C, 8)
        _write_u32(runtime_blob, 0x260, 2)
        _write_u32(runtime_blob, 0x264, 0)
        _write_u32(runtime_blob, 0x268, 1)
        _write_u32(runtime_blob, 0x26C, 0)
        _write_u32(runtime_blob, 0x270, 0)
        _write_u32(runtime_blob, 0x274, 0)
        _write_u32(runtime_blob, 0x278, 0)
        _write_u32(runtime_blob, 0x27C, 0)
        _write_u32(runtime_blob, 0x280, 0)
        _write_u32(runtime_blob, 0x284, 1)
        _write_u32(runtime_blob, 0x288, 4)
        _write_u32(runtime_blob, 0x28C, 4)
        _write_u32(runtime_blob, 0x290, 0xFFFFFFFF)
        _write_u32(runtime_blob, 0x294, 0xFFFFFFFF)
        _write_u32(runtime_blob, 0x298, 1)
        _write_u32(runtime_blob, 0x29C, 13)
        _write_u32(runtime_blob, 0x2A0, 13)
        _write_u32(runtime_blob, 0x2A4, 1)
        _write_u32(runtime_blob, 0x2A8, 10)
        _write_u32(runtime_blob, 0x2AC, 8)
        _write_u32(runtime_blob, 0x2B0, 2)
        _write_u32(runtime_blob, 0x2B4, 2)
        _write_u32(runtime_blob, 0x30C, 0x50335731)
        _write_u32(runtime_blob, 0x310, 0x99B67873)
        _write_u32(runtime_blob, 0x314, 0x0F)
        _write_u32(runtime_blob, 0x318, 0x0F)
        _write_u32(runtime_blob, 0x31C, 0x1F)
        _write_u32(runtime_blob, 0x320, 0x43503357)
        _write_u32(runtime_blob, 0x324, 1)
        _write_u32(runtime_blob, 0x328, 1)
        _write_u32(runtime_blob, 0x32C, 1)
        _write_u32(runtime_blob, 0x330, 1)
        _write_u32(runtime_blob, 0x334, 1)
        _write_u32(runtime_blob, 0x338, 1)
        _write_u32(runtime_blob, 0x33C, 1)
        _write_u32(runtime_blob, 0x340, 4)
        _write_u32(runtime_blob, 0x344, 4)
        _write_u32(runtime_blob, 0x348, 1)
        _write_u32(runtime_blob, 0x34C, 1)
        _write_u32(runtime_blob, 0x350, 4)
        _install_diagnostics(
            runtime_blob,
            hook_wrapper_entry_count=poll_value,
            hook_wrapper_before_poll_count=poll_value,
            runtime_poll_entry_count=poll_value,
            runtime_poll_exit_count=poll_value,
            state_machine_entry_count=poll_value,
            state_machine_exit_count=poll_value,
            ios_submit_attempt_count=26,
            ios_submit_return_count=26,
            ios_submit_return_value=0,
            callback_entry_count=26,
            callback_exit_count=26,
            hook_wrapper_after_poll_count=poll_value,
            hook_wrapper_exit_count=poll_value,
            last_execution_marker=0xC0DE0011,
            last_transport_phase_before_step=69,
            last_transport_phase_after_step=69,
            callback_result=33,
        )
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + bytes(runtime_blob_first)
    raw = _relocated_manifest(payload_bytes).to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    relocated["embedded_runtime_blob_size"] = len(runtime_blob_first)
    relocated["embedded_runtime_blob_sha256"] = __import__("hashlib").sha256(bytes(runtime_blob_first)).hexdigest()
    relocated["cache_range_size"] = 0x360
    relocated["runtime_state_end"] = 0x817E1360
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "cp3w_hello_session"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "cp3w_hello_session"
    transport["receive_enabled"] = True
    transport["send_enabled"] = True
    transport["terminal_phase_value"] = 69
    transport["terminal_phase_name"] = "CP3W_HELLO_SESSION_LOOP_COMPLETE"
    transport["cp3w_magic_hex"] = "43503357"
    transport["cp3w_protocol_version"] = 1
    transport["cp3w_header_size"] = 16
    transport["cp3w_crc_size"] = 4
    transport["cp3w_crc_initial_value"] = 0xFFFFFFFF
    transport["cp3w_crc_final_xor_value"] = 0xFFFFFFFF
    transport["cp3w_crc_polynomial"] = 0xEDB88320
    transport["cp3w_crc_reflected"] = True
    transport["cp3w_packet_kind_request"] = 1
    transport["cp3w_packet_kind_response"] = 2
    transport["cp3w_response_status_error"] = 1
    transport["cp3w_command_ping"] = 3
    transport["cp3w_pong_command"] = 3
    transport["cp3w_pong_uses_ping_command"] = True
    transport["cp3w_command_reserved_mailbox"] = 127
    transport["cp3w_error_code_unknown_command"] = 4
    transport["cp3w_packet_kind_offset"] = 5
    transport["cp3w_command_offset"] = 6
    transport["cp3w_response_status_offset"] = 7
    transport["cp3w_request_id_offset"] = 8
    transport["cp3w_payload_length_offset"] = 12
    transport["cp3w_ping_max_payload_length"] = 44
    transport["cp3w_unsupported_message_ascii"] = "Command is unsupported"
    transport["prepared_send_length_address"] = 0x817E1254
    transport["prepared_send_length_size"] = 4
    transport["cp3w_datagrams_processed_address"] = 0x817E1258
    transport["cp3w_datagrams_processed_size"] = 4
    transport["cp3w_frames_valid_address"] = 0x817E125C
    transport["cp3w_frames_valid_size"] = 4
    transport["cp3w_frames_invalid_address"] = 0x817E1260
    transport["cp3w_frames_invalid_size"] = 4
    transport["cp3w_frames_invalid_magic_address"] = 0x817E1268
    transport["cp3w_frames_invalid_magic_size"] = 4
    transport["cp3w_frames_invalid_payload_address"] = 0x817E1280
    transport["cp3w_frames_invalid_payload_size"] = 4
    transport["cp3w_frames_malformed_address"] = 0x817E1284
    transport["cp3w_frames_malformed_size"] = 4
    transport["cp3w_last_request_id_address"] = 0x817E1290
    transport["cp3w_last_request_id_size"] = 4
    transport["cp3w_last_response_id_address"] = 0x817E1294
    transport["cp3w_last_response_id_size"] = 4
    transport["cp3w_last_message_type_address"] = 0x817E1298
    transport["cp3w_last_message_type_size"] = 4
    transport["cp3w_last_declared_payload_length_address"] = 0x817E129C
    transport["cp3w_last_declared_payload_length_size"] = 4
    transport["cp3w_last_actual_payload_length_address"] = 0x817E12A0
    transport["cp3w_last_actual_payload_length_size"] = 4
    transport["cp3w_last_frame_result_address"] = 0x817E12A4
    transport["cp3w_last_frame_result_size"] = 4
    transport["cp3w_final_datagram_index_address"] = 0x817E12A8
    transport["cp3w_final_datagram_index_size"] = 4
    transport["cp3w_requests_dispatched_address"] = 0x817E12AC
    transport["cp3w_requests_dispatched_size"] = 4
    transport["cp3w_ping_requests_received_address"] = 0x817E12B0
    transport["cp3w_ping_requests_received_size"] = 4
    transport["cp3w_pong_responses_submitted_address"] = 0x817E12B4
    transport["cp3w_pong_responses_submitted_size"] = 4
    transport["cp3w_pong_responses_completed_address"] = 0x817E12B8
    transport["cp3w_pong_responses_completed_size"] = 4
    transport["cp3w_unsupported_commands_received_address"] = 0x817E12BC
    transport["cp3w_unsupported_commands_received_size"] = 4
    transport["cp3w_unsupported_responses_submitted_address"] = 0x817E12C0
    transport["cp3w_unsupported_responses_submitted_size"] = 4
    transport["cp3w_unsupported_responses_completed_address"] = 0x817E12C4
    transport["cp3w_unsupported_responses_completed_size"] = 4
    transport["cp3w_last_command_address"] = 0x817E12C8
    transport["cp3w_last_command_size"] = 4
    transport["cp3w_last_response_status_address"] = 0x817E12CC
    transport["cp3w_last_response_status_size"] = 4
    transport["cp3w_last_ping_payload_length_address"] = 0x817E12D0
    transport["cp3w_last_ping_payload_length_size"] = 4
    transport["cp3w_last_dispatch_result_address"] = 0x817E12D4
    transport["cp3w_last_dispatch_result_size"] = 4
    transport["cp3w_hello_requests_received_address"] = 0x817E1350
    transport["cp3w_hello_requests_received_size"] = 4
    transport["cp3w_hello_successes_address"] = 0x817E134C
    transport["cp3w_hello_successes_size"] = 4
    transport["cp3w_hello_version_rejections_address"] = 0x817E1348
    transport["cp3w_hello_version_rejections_size"] = 4
    transport["cp3w_hello_responses_submitted_address"] = 0x817E1344
    transport["cp3w_hello_responses_submitted_size"] = 4
    transport["cp3w_hello_responses_completed_address"] = 0x817E1340
    transport["cp3w_hello_responses_completed_size"] = 4
    transport["cp3w_hello_duplicate_requests_address"] = 0x817E133C
    transport["cp3w_hello_duplicate_requests_size"] = 4
    transport["cp3w_hello_renegotiation_rejections_address"] = 0x817E1338
    transport["cp3w_hello_renegotiation_rejections_size"] = 4
    transport["cp3w_pre_hello_gated_commands_address"] = 0x817E1334
    transport["cp3w_pre_hello_gated_commands_size"] = 4
    transport["cp3w_not_negotiated_responses_submitted_address"] = 0x817E1330
    transport["cp3w_not_negotiated_responses_submitted_size"] = 4
    transport["cp3w_not_negotiated_responses_completed_address"] = 0x817E132C
    transport["cp3w_not_negotiated_responses_completed_size"] = 4
    transport["cp3w_negotiated_flag_address"] = 0x817E1328
    transport["cp3w_negotiated_flag_size"] = 4
    transport["cp3w_selected_protocol_version_address"] = 0x817E1324
    transport["cp3w_selected_protocol_version_size"] = 4
    transport["cp3w_client_nonce_address"] = 0x817E1320
    transport["cp3w_client_nonce_size"] = 4
    transport["cp3w_client_capabilities_address"] = 0x817E131C
    transport["cp3w_client_capabilities_size"] = 4
    transport["cp3w_runtime_capabilities_address"] = 0x817E1318
    transport["cp3w_runtime_capabilities_size"] = 4
    transport["cp3w_accepted_capabilities_address"] = 0x817E1314
    transport["cp3w_accepted_capabilities_size"] = 4
    transport["cp3w_session_id_address"] = 0x817E1310
    transport["cp3w_session_id_size"] = 4
    transport["cp3w_runtime_build_id_address"] = 0x817E130C
    transport["cp3w_runtime_build_id_size"] = 4
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated
    manifest = Prime3RuntimePayloadManifest.from_json_dict(raw)
    config = module.ProbeObservationConfig(
        checkpoint_name="entry",
        halt_address=0x80006320,
        expected_halt_word=0x48000000,
        expected_game_id=b"RM3E01",
        payload_address=0x806843C0,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=(module.StartupWordExpectation(address=0x80006320, expected_word=0x48000000),),
        repeat_delay_seconds=0.5,
    )
    first_memory = _memory_for_config(module, config)
    second_memory = _memory_for_config(module, config)
    for memory, runtime_blob in ((first_memory, runtime_blob_first), (second_memory, runtime_blob_second)):
        _install_bootstrap_diagnostic(memory)
        memory[0x817E1000] = bytes(runtime_blob)
    backend = FakeBackend([first_memory, second_memory])

    result = module.observe_probe_memory(backend, config)

    assert result["probable_stop_boundary"] == "recurring_execution_continues"
    assert result["poll_counter_delta"] == 20
    assert result["relocated_runtime"]["transport"]["phase_name"] == "CP3W_HELLO_SESSION_LOOP_COMPLETE"
    assert result["relocated_runtime"]["transport"]["cp3w_hello_requests_received"] == 4
    assert result["relocated_runtime"]["transport"]["cp3w_hello_successes"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_hello_version_rejections"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_hello_responses_submitted"] == 4
    assert result["relocated_runtime"]["transport"]["cp3w_hello_responses_completed"] == 4
    assert result["relocated_runtime"]["transport"]["cp3w_hello_duplicate_requests"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_hello_renegotiation_rejections"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_pre_hello_gated_commands"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_not_negotiated_responses_submitted"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_not_negotiated_responses_completed"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_negotiated_flag"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_selected_protocol_version"] == 1
    assert result["relocated_runtime"]["transport"]["cp3w_client_nonce"] == 0x43503357
    assert result["relocated_runtime"]["transport"]["cp3w_client_capabilities"] == 0x1F
    assert result["relocated_runtime"]["transport"]["cp3w_runtime_capabilities"] == 0x0F
    assert result["relocated_runtime"]["transport"]["cp3w_accepted_capabilities"] == 0x0F
    assert result["relocated_runtime"]["transport"]["cp3w_session_id"] == 0x99B67873
    assert result["relocated_runtime"]["transport"]["cp3w_runtime_build_id"] == 0x50335731


def test_observe_probe_main_rejects_poll_ms_below_minimum(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "observe_probe.py",
            "--payload-address",
            "0x806843C0",
            "--payload-bin",
            "ignored.bin",
            "--payload-manifest",
            "ignored.json",
            "--report",
            "ignored-report.json",
            "--poll-ms",
            "9",
        ],
    )

    with pytest.raises(module.ProbeObservationError, match="at least 10 ms"):
        module.main()
