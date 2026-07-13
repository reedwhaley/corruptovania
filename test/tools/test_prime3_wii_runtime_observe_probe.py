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
        "embedded_runtime_blob_size": 0x140,
        "embedded_runtime_blob_sha256": __import__("hashlib").sha256(payload_bytes[0x20:0x160]).hexdigest(),
        "runtime_destination_address": 0x817E1000,
        "runtime_entry_address": 0x817E1000,
        "runtime_poll_entry_address": 0x817E1004,
        "runtime_poll_hook_wrapper_address": 0x817E1014,
        "runtime_code_start": 0x817E1000,
        "runtime_code_end": 0x817E1028,
        "runtime_state_start": 0x817E1028,
        "runtime_state_end": 0x817E1140,
        "runtime_stack_start": None,
        "runtime_stack_end": None,
        "required_source_alignment": 0x20,
        "required_destination_alignment": 0x20,
        "cache_line_size": 0x20,
        "cache_range_start": 0x817E1000,
        "cache_range_size": 0x140,
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
            "phase_address": 0x817E1058,
            "phase_size": 4,
            "last_error_address": 0x817E105C,
            "last_error_size": 4,
            "last_ios_result_address": 0x817E1060,
            "last_ios_result_size": 4,
            "pending_operation_address": 0x817E1064,
            "pending_operation_size": 4,
            "pending_generation_address": 0x817E1068,
            "pending_generation_size": 4,
            "callback_generation_address": 0x817E106C,
            "callback_generation_size": 4,
            "callback_count_address": 0x817E1070,
            "callback_count_size": 4,
            "callback_pending_address": 0x817E1074,
            "callback_pending_size": 4,
            "kd_fd_address": 0x817E1078,
            "kd_fd_size": 4,
            "ip_fd_address": 0x817E107C,
            "ip_fd_size": 4,
            "socket_fd_address": 0x817E1080,
            "socket_fd_size": 4,
            "host_id_address": 0x817E1084,
            "host_id_size": 4,
            "bound_port_address": 0x817E1088,
            "bound_port_size": 4,
            "receive_count_address": 0x817E108C,
            "receive_count_size": 4,
            "receive_bytes_address": 0x817E1090,
            "receive_bytes_size": 4,
            "send_count_address": 0x817E1094,
            "send_count_size": 4,
            "send_bytes_address": 0x817E1098,
            "send_bytes_size": 4,
            "last_receive_length_address": 0x817E109C,
            "last_receive_length_size": 4,
            "last_send_length_address": 0x817E10A0,
            "last_send_length_size": 4,
            "last_peer_ipv4_address": 0x817E10A4,
            "last_peer_ipv4_size": 4,
            "last_peer_port_address": 0x817E10A8,
            "last_peer_port_size": 4,
            "last_peer_family_address": 0x817E10AC,
            "last_peer_family_size": 4,
            "last_poll_action_address": 0x817E10B0,
            "last_poll_action_size": 4,
            "last_submit_result_address": 0x817E10B4,
            "last_submit_result_size": 4,
            "last_receive_preview_address": 0x817E10C0,
            "last_receive_preview_size": 16,
            "last_send_preview_address": 0x817E10D0,
            "last_send_preview_size": 16,
        },
    }
    return Prime3RuntimePayloadManifest.from_json_dict(raw)


def _write_u32(blob: bytearray, offset: int, value: int) -> None:
    blob[offset : offset + 4] = value.to_bytes(4, "big")


def _write_s32(blob: bytearray, offset: int, value: int) -> None:
    blob[offset : offset + 4] = value.to_bytes(4, "big", signed=True)


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
    runtime_blob = bytearray(b"R" * 0x140)
    _write_u32(runtime_blob, 0x38, 0x434F5059)
    _write_u32(runtime_blob, 0x3C, 0x52554E21)
    _write_u32(runtime_blob, 0x40, 1)
    _write_u32(runtime_blob, 0x44, 0x52544F4B)
    _write_u32(runtime_blob, 0x48, 0x4252544E)
    _write_u32(runtime_blob, 0x4C, 7)
    _write_u32(runtime_blob, 0x50, 7)
    _write_u32(runtime_blob, 0x54, 7)
    _write_u32(runtime_blob, 0x58, 21)
    _write_s32(runtime_blob, 0x5C, 0)
    _write_s32(runtime_blob, 0x60, 0)
    _write_u32(runtime_blob, 0x64, 0)
    _write_u32(runtime_blob, 0x68, 7)
    _write_u32(runtime_blob, 0x6C, 7)
    _write_u32(runtime_blob, 0x70, 2)
    _write_u32(runtime_blob, 0x74, 0)
    _write_s32(runtime_blob, 0x78, -1)
    _write_s32(runtime_blob, 0x7C, 3)
    _write_s32(runtime_blob, 0x80, 4)
    _write_u32(runtime_blob, 0x84, 0xC0A80164)
    _write_u32(runtime_blob, 0x88, 43674)
    _write_u32(runtime_blob, 0x8C, 1)
    _write_u32(runtime_blob, 0x90, 24)
    _write_u32(runtime_blob, 0x94, 1)
    _write_u32(runtime_blob, 0x98, 48)
    _write_u32(runtime_blob, 0x9C, 24)
    _write_u32(runtime_blob, 0xA0, 48)
    _write_u32(runtime_blob, 0xA4, 0xC0A80102)
    _write_u32(runtime_blob, 0xA8, 0xABAA)
    _write_u32(runtime_blob, 0xAC, 2)
    _write_u32(runtime_blob, 0xB0, 4)
    _write_s32(runtime_blob, 0xB4, 0)
    runtime_blob[0xC0:0xD0] = bytes.fromhex("0102030405060708090a0b0c0d0e0f10")
    runtime_blob[0xD0:0xE0] = bytes.fromhex("50335544000000010000000700000007")
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
        last_transport_phase_before_step=21,
        last_transport_phase_after_step=21,
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
    runtime_state = bytearray(payload_bytes[0x20:0x160])
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
    assert result["relocated_runtime"]["transport"]["phase"] == 21
    assert result["relocated_runtime"]["transport"]["host_id"] == 0xC0A80164
    assert result["relocated_runtime"]["transport"]["last_receive_preview_hex"] == "0102030405060708090a0b0c0d0e0f10"


def test_observe_probe_reports_recurring_hook_and_poll_progress() -> None:
    module = _load_module()
    runtime_blob_first = bytearray(b"R" * 0x140)
    _write_u32(runtime_blob_first, 0x38, 0x434F5059)
    _write_u32(runtime_blob_first, 0x3C, 0x52554E21)
    _write_u32(runtime_blob_first, 0x40, 1)
    _write_u32(runtime_blob_first, 0x44, 0x52544F4B)
    _write_u32(runtime_blob_first, 0x48, 0x4252544E)
    _write_u32(runtime_blob_first, 0x4C, 7)
    _write_u32(runtime_blob_first, 0x50, 7)
    _write_u32(runtime_blob_first, 0x54, 7)
    _write_u32(runtime_blob_first, 0x58, 21)
    _write_u32(runtime_blob_first, 0x90, 24)
    _write_u32(runtime_blob_first, 0x98, 48)
    _write_u32(runtime_blob_first, 0xB0, 4)
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
        last_transport_phase_before_step=21,
        last_transport_phase_after_step=21,
        callback_result=0,
    )
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
        last_transport_phase_before_step=21,
        last_transport_phase_after_step=21,
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
    assert result["probable_stop_boundary"] == "recurring_execution_continues"


def test_observe_probe_reports_waiting_for_callback_boundary() -> None:
    module = _load_module()
    runtime_blob = bytearray(b"R" * 0x140)
    _write_u32(runtime_blob, 0x38, 0x434F5059)
    _write_u32(runtime_blob, 0x3C, 0x52554E21)
    _write_u32(runtime_blob, 0x40, 1)
    _write_u32(runtime_blob, 0x44, 0x52544F4B)
    _write_u32(runtime_blob, 0x48, 0x4252544E)
    _write_u32(runtime_blob, 0x4C, 1)
    _write_u32(runtime_blob, 0x50, 1)
    _write_u32(runtime_blob, 0x54, 1)
    _write_u32(runtime_blob, 0x58, 2)
    _write_u32(runtime_blob, 0x64, 1)
    _write_u32(runtime_blob, 0x68, 1)
    _write_u32(runtime_blob, 0x6C, 0)
    _write_u32(runtime_blob, 0x70, 0)
    _write_s32(runtime_blob, 0xB4, 0)
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
        last_transport_phase_before_step=1,
        last_transport_phase_after_step=2,
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

    assert result["relocated_runtime"]["diagnostics"]["ios_submission_returned"] is True
    assert result["relocated_runtime"]["diagnostics"]["callback_observed"] is False
    assert result["probable_stop_boundary"] == "callback_pending"


def test_observe_probe_reports_contradictory_diagnostic_counters() -> None:
    module = _load_module()
    runtime_blob = bytearray(b"R" * 0x140)
    _write_u32(runtime_blob, 0x38, 0x434F5059)
    _write_u32(runtime_blob, 0x3C, 0x52554E21)
    _write_u32(runtime_blob, 0x40, 1)
    _write_u32(runtime_blob, 0x44, 0x52544F4B)
    _write_u32(runtime_blob, 0x48, 0x4252544E)
    _write_u32(runtime_blob, 0x4C, 1)
    _write_u32(runtime_blob, 0x50, 1)
    _write_u32(runtime_blob, 0x54, 1)
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
        recurring_execution_continuing=False,
    )

    assert result == expected


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
