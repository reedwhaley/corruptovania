from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import pytest

from randovania.game_connection.executor.prime3_wii_protocol import PROTOCOL_VERSION
from randovania.games.prime3.exporter import runtime_payload
from randovania.games.prime3.exporter.dol_patcher import Prime3DolPatchError

if TYPE_CHECKING:
    from pathlib import Path


def _make_manifest(payload_bytes: bytes) -> runtime_payload.Prime3RuntimePayloadManifest:
    return runtime_payload.Prime3RuntimePayloadManifest(
        schema_version=runtime_payload.PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION,
        target_architecture=runtime_payload.PRIME3_RUNTIME_TARGET_ARCHITECTURE,
        target_endianness=runtime_payload.PRIME3_RUNTIME_TARGET_ENDIANNESS,
        target_abi=runtime_payload.PRIME3_RUNTIME_TARGET_ABI,
        compiler_identity="powerpc-eabi-gcc (devkitPPC release 47.1)",
        compiler_version="15.1.0",
        linker_identity="GNU ld",
        linker_version="2.44",
        payload_sha256=hashlib.sha256(payload_bytes).hexdigest(),
        payload_size=len(payload_bytes),
        required_alignment=runtime_payload.PRIME3_RUNTIME_REQUIRED_ALIGNMENT,
        entry_symbol_name=runtime_payload.PRIME3_RUNTIME_ENTRY_SYMBOL,
        entry_symbol_offset=0,
        source_digest="a" * 64,
        protocol_artifact_version=PROTOCOL_VERSION,
        unresolved_relocation_count=0,
        dynamic_section_count=0,
    )


def test_tcp_transport_metadata_round_trip_rejects_legacy_udp_fields() -> None:
    transport = runtime_payload.Prime3RuntimeTransportMetadata(
        transport_kind="tcp",
        protocol_magic_hex="43503357",
        protocol_version=1,
        frame_size=64,
        diagnostics_enabled=False,
        inbound_queue_depth=4,
        outbound_queue_depth=4,
        cp3c_config_offset=0x200,
        cp3c_config_size=0x20,
        server_ipv4_offset=0x20C,
        server_ipv4_size=4,
        server_ipv4_byte_order="big",
        server_port_offset=0x210,
        server_port_size=2,
        server_port_byte_order="big",
        inventory_tracker_capability=True,
        tracker_snapshot_capability=True,
        tracker_delta_capability=True,
        resync_capability=True,
    )

    data = transport.to_json_dict()

    assert "udp_port" not in data
    assert "mode" not in data
    assert data["server_ipv4_size"] == 4
    assert data["server_ipv4_byte_order"] == "big"
    assert data["server_port_size"] == 2
    assert data["server_port_byte_order"] == "big"
    assert data["inventory_tracker_capability"] is True
    assert data["tracker_snapshot_capability"] is True
    assert data["diagnostics_enabled"] is False
    assert runtime_payload.Prime3RuntimeTransportMetadata.from_json_dict(data) == transport

    with pytest.raises(runtime_payload.Prime3DolPatchError, match="Legacy UDP"):
        runtime_payload.Prime3RuntimeTransportMetadata.from_json_dict({**data, "udp_port": 43674})


def _make_bootstrap_manifest(payload_bytes: bytes) -> runtime_payload.Prime3RuntimePayloadManifest:
    manifest = _make_manifest(payload_bytes)
    raw = manifest.to_json_dict()
    raw["payload_mode"] = runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT
    raw["entry_bootstrap"] = {
        "mode": runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT,
        "staging_address": 0x806843C0,
        "staging_save_area_offset": 0x40,
        "staging_save_area_size": 0x10,
        "halt_loop_address": 0x806843F0,
        "reserved_boundary": 0x817E0000,
        "reserved_range_start": 0x817E0000,
        "reserved_range_end": 0x817FE3A0,
        "diagnostic_address": 0x817E0100,
        "diagnostic_block_size": 0x40,
        "canary_address": 0x817E0100,
        "canary_size": 0x10,
        "canary_sha256": hashlib.sha256(b"P3BOOTSTRAPCANRY").hexdigest(),
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
    return runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def _make_relocated_manifest(payload_bytes: bytes) -> runtime_payload.Prime3RuntimePayloadManifest:
    manifest = _make_bootstrap_manifest(payload_bytes)
    raw = manifest.to_json_dict()
    raw["payload_mode"] = runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE
    raw["entry_bootstrap"]["mode"] = runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE
    raw["entry_bootstrap"]["status_value"] = 0xB0071003
    raw["entry_bootstrap"]["halt_loop_address"] = None
    raw["relocated_runtime"] = {
        "mode": runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
        "low_bootstrap_address": 0x806843C0,
        "low_bootstrap_size": 0x1A0,
        "low_bootstrap_sha256": hashlib.sha256(payload_bytes[:0x1A0]).hexdigest(),
        "embedded_runtime_blob_offset": 0x1A0,
        "embedded_runtime_blob_size": 0x2F0,
        "embedded_runtime_blob_sha256": hashlib.sha256(payload_bytes[0x1A0:0x400]).hexdigest(),
        "runtime_destination_address": 0x817E1000,
        "runtime_entry_address": 0x817E1000,
        "runtime_poll_entry_address": 0x817E1020,
        "runtime_poll_hook_wrapper_address": 0x817E1030,
        "runtime_code_start": 0x817E1000,
        "runtime_code_end": 0x817E104C,
        "runtime_state_start": 0x817E1050,
        "runtime_state_end": 0x817E12F0,
        "runtime_stack_start": None,
        "runtime_stack_end": None,
        "required_source_alignment": 0x20,
        "required_destination_alignment": 0x20,
        "cache_line_size": 0x20,
        "cache_range_start": 0x817E1000,
        "cache_range_size": 0x300,
        "runtime_canary_address": 0x817E1050,
        "runtime_canary_size": 0x10,
        "runtime_canary_sha256": hashlib.sha256(b"P3HIRUNTIMECANAR").hexdigest(),
        "copy_complete_marker_address": 0x817E1060,
        "copy_complete_marker_value": 0x434F5059,
        "runtime_executed_marker_address": 0x817E1064,
        "runtime_executed_marker_value": 0x52554E21,
        "runtime_execution_counter_address": 0x817E1068,
        "runtime_execution_counter_size": 4,
        "runtime_status_address": 0x817E106C,
        "runtime_success_status_value": 0x52544F4B,
        "bootstrap_return_marker_address": 0x817E1070,
        "bootstrap_return_marker_value": 0x4252544E,
        "runtime_poll_counter_address": 0x817E1074,
        "runtime_poll_counter_size": 4,
        "runtime_poll_heartbeat_address": 0x817E1078,
        "runtime_poll_heartbeat_size": 4,
        "runtime_poll_last_sequence_address": 0x817E107C,
        "runtime_poll_last_sequence_size": 4,
        "diagnostics": {
            "mode": "normal",
            "c_after_veneer_call_count_address": 0x817E10F0,
            "c_after_veneer_call_count_size": 4,
            "c_before_veneer_call_count_address": 0x817E10EC,
            "c_before_veneer_call_count_size": 4,
            "hook_wrapper_entry_count_address": 0x817E1100,
            "hook_wrapper_entry_count_size": 4,
            "hook_wrapper_before_poll_count_address": 0x817E1104,
            "hook_wrapper_before_poll_count_size": 4,
            "runtime_poll_entry_count_address": 0x817E1108,
            "runtime_poll_entry_count_size": 4,
            "runtime_poll_exit_count_address": 0x817E110C,
            "runtime_poll_exit_count_size": 4,
            "state_machine_entry_count_address": 0x817E1110,
            "state_machine_entry_count_size": 4,
            "state_machine_exit_count_address": 0x817E1114,
            "state_machine_exit_count_size": 4,
            "ios_submit_attempt_count_address": 0x817E1118,
            "ios_submit_attempt_count_size": 4,
            "ios_submit_return_count_address": 0x817E111C,
            "ios_submit_return_count_size": 4,
            "ios_submit_return_value_address": 0x817E1120,
            "ios_submit_return_value_size": 4,
            "callback_entry_count_address": 0x817E1124,
            "callback_entry_count_size": 4,
            "callback_exit_count_address": 0x817E1128,
            "callback_exit_count_size": 4,
            "hook_wrapper_after_poll_count_address": 0x817E112C,
            "hook_wrapper_after_poll_count_size": 4,
            "hook_wrapper_exit_count_address": 0x817E1130,
            "hook_wrapper_exit_count_size": 4,
            "last_execution_marker_address": 0x817E1134,
            "last_execution_marker_size": 4,
            "last_transport_phase_before_step_address": 0x817E1138,
            "last_transport_phase_before_step_size": 4,
            "last_transport_phase_after_step_address": 0x817E113C,
            "last_transport_phase_after_step_size": 4,
            "callback_result_address": 0x817E1140,
            "callback_result_size": 4,
            "retail_target_return_count_address": 0x817E10F8,
            "retail_target_return_count_size": 4,
            "retail_veneer_entry_count_address": 0x817E10F4,
            "retail_veneer_entry_count_size": 4,
            "retail_veneer_exit_count_address": 0x817E10FC,
            "retail_veneer_exit_count_size": 4,
        },
        "ios_udp_diagnostic_enabled": True,
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
            "phase_address": 0x817E1144,
            "phase_size": 4,
            "last_error_address": 0x817E1148,
            "last_error_size": 4,
            "last_socket_error_address": 0x817E114C,
            "last_socket_error_size": 4,
            "last_ios_result_address": 0x817E1150,
            "last_ios_result_size": 4,
            "pending_operation_address": 0x817E1154,
            "pending_operation_size": 4,
            "pending_generation_address": 0x817E1158,
            "pending_generation_size": 4,
            "callback_generation_address": 0x817E115C,
            "callback_generation_size": 4,
            "callback_count_address": 0x817E1160,
            "callback_count_size": 4,
            "rejected_callback_count_address": 0x817E1164,
            "rejected_callback_count_size": 4,
            "callback_pending_address": 0x817E1168,
            "callback_pending_size": 4,
            "open_kd_submit_count_address": 0x817E116C,
            "open_kd_submit_count_size": 4,
            "open_kd_callback_count_address": 0x817E1170,
            "open_kd_callback_count_size": 4,
            "nwc24_output_buffer_address": 0x817E1180,
            "nwc24_output_buffer_size": 0x20,
            "nwc24_output_buffer_alignment": 0x20,
            "nwc24_submit_count_address": 0x817E1174,
            "nwc24_submit_count_size": 4,
            "nwc24_callback_count_address": 0x817E1178,
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
            "service_started_address": 0x817E1250,
            "service_started_size": 4,
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
            "last_receive_preview_address": 0x817E1230,
            "last_receive_preview_size": 16,
            "last_send_preview_address": 0x817E1240,
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
        "retail_ios_wrapper": {
            "supported_dol_sha256": "6b550f221602074747a2e61b0aa064203fd493f6865dfb3b1a912682065e6104",
            "open_async_address": 0x80504668,
            "open_address": 0x80504780,
            "close_async_address": 0x805048A0,
            "close_address": 0x80504960,
            "async_close_address": 0x805048A0,
            "async_close_extent": "0x805048A0..0x80504960",
            "async_close_argument_count": 3,
            "async_close_stack_argument_count": 0,
            "async_close_operation": 2,
            "async_close_fingerprint_sha256": "cad7a4b8950241515a9399d51c69d5680bba41fe060c37f5b6953effcdcb1288",
            "async_close_prototype": "s32 close_async(s32 fd, completion_fn completion, void *userdata)",
            "async_close_register_arguments": ["r3=fd", "r4=completion", "r5=userdata"],
            "async_close_confidence": "verified",
            "read_async_address": 0x80504A08,
            "read_sync_address": 0x80504B08,
            "write_async_address": 0x80504C10,
            "write_sync_address": 0x80504D10,
            "seek_async_address": 0x80504E18,
            "seek_sync_address": 0x80504EF8,
            "confirmed_ioctl_async_address": 0x80504FE0,
            "confirmed_ioctl_sync_address": 0x80505118,
            "confirmed_ioctlv_async_address": 0x80505384,
            "confirmed_ioctlv_sync_address": 0x80505468,
            "async_ioctl_address": 0x80504FE0,
            "async_ioctl_extent": "0x80504FE0..0x80505118",
            "async_ioctl_argument_count": 8,
            "async_ioctl_stack_argument_count": 0,
            "async_ioctl_operation": 6,
            "async_ioctl_confidence": "verified",
            "confirmed_ioctl_async_fingerprint_sha256": (
                "031342395575c5542428b9edfcd4fd3bf9633bfb54bd39726d3766b3e6f3b17b"
            ),
            "confirmed_ioctl_async_prototype": (
                "s32 ioctl_async(s32 fd, u32 command, const void *input, u32 input_length, "
                "void *output, u32 output_length, completion_fn completion, void *userdata)"
            ),
            "confirmed_ioctl_async_register_arguments": [
                "r3=fd",
                "r4=command",
                "r5=input",
                "r6=input_length",
                "r7=output",
                "r8=output_length",
                "r9=completion",
                "r10=userdata",
            ],
            "confirmed_ioctl_async_stack_arguments": [],
            "request_field_offsets": [
                "operation=0x00",
                "result=0x04",
                "fd=0x08",
                "argument_0=0x0c",
                "argument_1=0x10",
                "argument_2=0x14",
                "argument_3=0x18",
                "argument_4=0x1c",
                "completion=0x20",
                "completion_userdata=0x24",
                "special_vector_flag=0x28",
            ],
            "open_async_guard_words": [0x9421FFD0, 0x7C0802A6, 0x90010034, 0x39610030],
            "callback_signature": "s32 callback(s32 result, void *userdata)",
            "preserved_registers": ["r2", "r13"],
            "submit_helper_address": 0x8050441C,
            "request_allocator_address": 0x80505960,
            "evidence_source": (
                "prime3-ntsc retail DOL operation 3-7 request construction, cache handling, "
                "completion fields, and compatible callsite verification"
            ),
            "confidence": "verified",
        },
    }
    return runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_json_is_deterministic() -> None:
    manifest = _make_manifest(b"\x4e\x80\x00\x20")
    assert manifest.to_json_text() == manifest.to_json_text()


def test_game_identity_metadata_round_trip_and_validation() -> None:
    metadata = runtime_payload.Prime3RuntimeGameIdentityMetadata(
        mode_value=20,
        mode_name="cp3w_game_identity",
        command_value=5,
        capability_value=1 << 11,
        schema_version=1,
        payload_size=28,
        field_offsets={"reserved": 24},
        game_id=1,
        platform_id=1,
        region_id=1,
        revision_id=1,
        profile_id=0x50334E41,
        profile_fingerprint=0x67B00CE6,
        fingerprint_derivation="test",
        runtime_build_id=0x50335731,
        availability_flags={"EXECUTABLE_RECOGNIZED": 1},
        phase_names={"LOOP_COMPLETE": 79},
        configured_count=12,
        state_addresses={"requests": 0x817E1100, "successes": 0x817E1104},
    )
    assert metadata.validate(runtime_state_start=0x817E1000, runtime_state_end=0x817E1200)
    assert runtime_payload.Prime3RuntimeGameIdentityMetadata.from_json_dict(metadata.to_json_dict()) == metadata


def test_load_prime3_runtime_payload_artifact(tmp_path: Path) -> None:
    payload_bytes = b"\x4e\x80\x00\x20"
    manifest = _make_manifest(payload_bytes)
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")

    artifact = runtime_payload.load_prime3_runtime_payload_artifact(
        manifest_path=manifest_path,
        payload_path=payload_path,
        load_address=0x80510000,
    )

    assert artifact.load_address == 0x80510000
    assert artifact.entry_symbol_offset == 0
    assert artifact.required_alignment == runtime_payload.PRIME3_RUNTIME_REQUIRED_ALIGNMENT
    assert artifact.protocol_manifest_version == str(PROTOCOL_VERSION)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("target_architecture", "mips", "Unsupported payload architecture"),
        ("target_endianness", "little", "Unsupported payload endianness"),
        ("schema_version", 99, "Unsupported Prime 3 runtime payload schema version"),
        ("unresolved_relocation_count", 1, "unresolved relocations"),
        ("dynamic_section_count", 1, "dynamic sections"),
        ("entry_symbol_offset", 8, "outside payload size"),
    ],
)
def test_runtime_payload_manifest_rejects_invalid_fields(field: str, value: object, match: str) -> None:
    manifest = _make_manifest(b"\x4e\x80\x00\x20")
    raw = manifest.to_json_dict()
    raw[field] = value

    with pytest.raises(Prime3DolPatchError, match=match):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_malformed_json() -> None:
    with pytest.raises(Prime3DolPatchError, match="Invalid Prime 3 runtime payload manifest JSON"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_text("{")


def test_load_prime3_runtime_payload_artifact_rejects_hash_mismatch(tmp_path: Path) -> None:
    payload_bytes = b"\x4e\x80\x00\x20"
    manifest = _make_manifest(payload_bytes)
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    payload_path.write_bytes(payload_bytes)
    raw = manifest.to_json_dict()
    raw["payload_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(Prime3DolPatchError, match="Payload hash mismatch"):
        runtime_payload.load_prime3_runtime_payload_artifact(
            manifest_path=manifest_path,
            payload_path=payload_path,
            load_address=0x80510000,
        )


def test_compute_source_digest_changes_with_source(tmp_path: Path) -> None:
    tmp_path.joinpath("a.txt").write_text("alpha", encoding="utf-8")
    tmp_path.joinpath("b.txt").write_text("beta", encoding="utf-8")
    first = runtime_payload.compute_source_digest(tmp_path, ("a.txt", "b.txt"))
    tmp_path.joinpath("b.txt").write_text("gamma", encoding="utf-8")
    second = runtime_payload.compute_source_digest(tmp_path, ("a.txt", "b.txt"))
    assert first != second


def test_runtime_payload_manifest_accepts_optional_probe_metadata() -> None:
    manifest = _make_manifest(b"\x4e\x80\x00\x20" * 16)
    raw = manifest.to_json_dict()
    raw["canary_start_offset"] = 0x10
    raw["canary_size"] = 0x10
    raw["counter_offset"] = 0x20
    raw["counter_size"] = 4

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.canary_start_offset == 0x10
    assert parsed.canary_size == 0x10
    assert parsed.counter_offset == 0x20
    assert parsed.counter_size == 4


def test_runtime_payload_manifest_accepts_entry_bootstrap_metadata() -> None:
    manifest = _make_bootstrap_manifest(b"\x4e\x80\x00\x20" * 32)

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(manifest.to_json_dict())

    assert parsed.payload_mode == runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT
    assert parsed.entry_bootstrap is not None
    assert parsed.entry_bootstrap.original_branch_target == 0x8000648C
    assert parsed.entry_bootstrap.halt_loop_address == 0x806843F0


def test_runtime_payload_manifest_rejects_bootstrap_diagnostic_outside_reserved_range() -> None:
    manifest = _make_bootstrap_manifest(b"\x4e\x80\x00\x20" * 32)
    raw = manifest.to_json_dict()
    bootstrap = dict(raw["entry_bootstrap"])
    bootstrap["diagnostic_address"] = 0x817FF000
    raw["entry_bootstrap"] = bootstrap

    with pytest.raises(Prime3DolPatchError, match="diagnostic block address is outside the reserved range"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_accepts_relocated_runtime_metadata() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(manifest.to_json_dict())

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.runtime_destination_address == 0x817E1000
    assert parsed.relocated_runtime.cache_range_size == 0x300
    assert parsed.relocated_runtime.runtime_poll_hook_wrapper_address == 0x817E1030
    assert parsed.relocated_runtime.runtime_poll_last_sequence_address == 0x817E107C
    assert parsed.relocated_runtime.diagnostics is not None
    assert parsed.relocated_runtime.diagnostics.last_execution_marker_address == 0x817E1134
    assert parsed.relocated_runtime.ios_udp_diagnostic_enabled is True
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.last_receive_preview_size == 16
    assert parsed.relocated_runtime.abi_probe is not None
    assert parsed.relocated_runtime.abi_probe.expected_return_value == 0x13579BDF
    assert parsed.relocated_runtime.retail_ios_wrapper is not None
    assert parsed.relocated_runtime.retail_ios_wrapper.write_async_address == 0x80504C10
    assert parsed.relocated_runtime.retail_ios_wrapper.confirmed_ioctl_async_address == 0x80504FE0
    assert parsed.relocated_runtime.retail_ios_wrapper.async_ioctl_argument_count == 8


def test_runtime_payload_manifest_accepts_nwc24_ioctl_once_terminal_metadata() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_nwc24_startup_once"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_nwc24_startup_once"
    transport["kd_close_enabled"] = False
    transport["terminal_phase_value"] = 0xFE
    transport["terminal_phase_name"] = "NWC24_COMPLETE"
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.kd_close_enabled is False
    assert parsed.relocated_runtime.transport.terminal_phase_name == "NWC24_COMPLETE"


def test_runtime_payload_manifest_accepts_nwc24_close_open_ip_terminal_metadata() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_nwc24_close_open_ip_once"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_nwc24_close_open_ip_once"
    transport["kd_close_enabled"] = True
    transport["terminal_phase_value"] = 0xFE
    transport["terminal_phase_name"] = "IP_OPEN"
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.kd_close_enabled is True
    assert parsed.relocated_runtime.transport.terminal_phase_name == "IP_OPEN"


def test_runtime_payload_manifest_accepts_nwc24_close_open_ip_startup_terminal_metadata() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_nwc24_close_open_ip_startup_once"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_nwc24_close_open_ip_startup_once"
    transport["kd_close_enabled"] = True
    transport["terminal_phase_value"] = 18
    transport["terminal_phase_name"] = "SO_STARTED"
    transport["service_started_address"] = 0x817E1254
    transport["service_started_size"] = 4
    transport["startup_target_address"] = 0x817E1258
    transport["startup_target_size"] = 4
    transport["startup_command_address"] = 0x817E125C
    transport["startup_command_size"] = 4
    transport["startup_submitted_fd_address"] = 0x817E1260
    transport["startup_submitted_fd_size"] = 4
    transport["startup_callback_pointer_address"] = 0x817E1264
    transport["startup_callback_pointer_size"] = 4
    transport["startup_context_pointer_address"] = 0x817E1268
    transport["startup_context_pointer_size"] = 4
    transport["startup_callback_exit_count_address"] = 0x817E126C
    transport["startup_callback_exit_count_size"] = 4
    transport["startup_stale_callback_count_address"] = 0x817E1270
    transport["startup_stale_callback_count_size"] = 4
    transport["startup_duplicate_callback_count_address"] = 0x817E1274
    transport["startup_duplicate_callback_count_size"] = 4
    transport["startup_service_started_before_submit_address"] = 0x817E1278
    transport["startup_service_started_before_submit_size"] = 4
    transport["startup_service_started_after_completion_address"] = 0x817E127C
    transport["startup_service_started_after_completion_size"] = 4
    transport["ip_fd_before_startup_address"] = 0x817E1280
    transport["ip_fd_before_startup_size"] = 4
    transport["ip_fd_after_startup_address"] = 0x817E1284
    transport["ip_fd_after_startup_size"] = 4
    transport["startup_pending_before_submit_address"] = 0x817E1288
    transport["startup_pending_before_submit_size"] = 4
    transport["startup_pending_after_completion_address"] = 0x817E128C
    transport["startup_pending_after_completion_size"] = 4
    transport["startup_phase_before_submit_address"] = 0x817E1290
    transport["startup_phase_before_submit_size"] = 4
    transport["startup_phase_after_completion_address"] = 0x817E1294
    transport["startup_phase_after_completion_size"] = 4
    transport["startup_pre_call_args_address"] = 0x817E12A8
    transport["startup_pre_call_args_size"] = 0x20
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.terminal_phase_name == "SO_STARTED"
    assert parsed.relocated_runtime.transport.startup_pre_call_args_size == 0x20


def test_runtime_payload_manifest_accepts_get_host_id_terminal_metadata() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_get_host_id_once"
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_get_host_id_once"
    transport["kd_close_enabled"] = True
    transport["terminal_phase_value"] = 19
    transport["terminal_phase_name"] = "HOST_ID_READY"
    transport["service_started_address"] = 0x817E1254
    transport["service_started_size"] = 4
    transport["host_id_available_address"] = 0x817E1258
    transport["host_id_available_size"] = 4
    transport["host_id_ready_address"] = 0x817E125C
    transport["host_id_ready_size"] = 4
    transport["get_host_id_submit_result_address"] = 0x817E1260
    transport["get_host_id_submit_result_size"] = 4
    transport["get_host_id_callback_result_address"] = 0x817E1264
    transport["get_host_id_callback_result_size"] = 4
    transport["get_host_id_submit_generation_address"] = 0x817E1268
    transport["get_host_id_submit_generation_size"] = 4
    transport["get_host_id_callback_generation_address"] = 0x817E126C
    transport["get_host_id_callback_generation_size"] = 4
    transport["get_host_id_target_address"] = 0x817E1270
    transport["get_host_id_target_size"] = 4
    transport["get_host_id_command_address"] = 0x817E1274
    transport["get_host_id_command_size"] = 4
    transport["get_host_id_submitted_fd_address"] = 0x817E1278
    transport["get_host_id_submitted_fd_size"] = 4
    transport["get_host_id_callback_pointer_address"] = 0x817E127C
    transport["get_host_id_callback_pointer_size"] = 4
    transport["get_host_id_context_pointer_address"] = 0x817E1280
    transport["get_host_id_context_pointer_size"] = 4
    transport["get_host_id_callback_exit_count_address"] = 0x817E1284
    transport["get_host_id_callback_exit_count_size"] = 4
    transport["get_host_id_stale_callback_count_address"] = 0x817E1288
    transport["get_host_id_stale_callback_count_size"] = 4
    transport["get_host_id_duplicate_callback_count_address"] = 0x817E128C
    transport["get_host_id_duplicate_callback_count_size"] = 4
    transport["get_host_id_service_started_before_submit_address"] = 0x817E1290
    transport["get_host_id_service_started_before_submit_size"] = 4
    transport["get_host_id_service_started_after_completion_address"] = 0x817E1294
    transport["get_host_id_service_started_after_completion_size"] = 4
    transport["ip_fd_before_get_host_id_address"] = 0x817E1298
    transport["ip_fd_before_get_host_id_size"] = 4
    transport["ip_fd_after_get_host_id_address"] = 0x817E129C
    transport["ip_fd_after_get_host_id_size"] = 4
    transport["get_host_id_pending_before_submit_address"] = 0x817E12A0
    transport["get_host_id_pending_before_submit_size"] = 4
    transport["get_host_id_pending_after_completion_address"] = 0x817E12A4
    transport["get_host_id_pending_after_completion_size"] = 4
    transport["get_host_id_phase_before_submit_address"] = 0x817E12A8
    transport["get_host_id_phase_before_submit_size"] = 4
    transport["get_host_id_phase_after_completion_address"] = 0x817E12AC
    transport["get_host_id_phase_after_completion_size"] = 4
    transport["get_host_id_pre_call_args_address"] = 0x817E12B0
    transport["get_host_id_pre_call_args_size"] = 0x20
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.terminal_phase_name == "HOST_ID_READY"
    assert parsed.relocated_runtime.transport.get_host_id_pre_call_args_size == 0x20


def test_runtime_payload_manifest_accepts_create_socket_terminal_metadata() -> None:
    payload_bytes = b"\x4e\x80\x00\x20" * 320
    manifest = _make_relocated_manifest(payload_bytes)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_create_socket_once"
    relocated["diagnostics"] = diagnostics
    relocated["embedded_runtime_blob_size"] = 0x360
    relocated["embedded_runtime_blob_sha256"] = hashlib.sha256(payload_bytes[0x1A0:0x500]).hexdigest()
    relocated["cache_range_size"] = 0x360
    relocated["runtime_state_end"] = 0x817E1360
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_create_socket_once"
    transport["kd_close_enabled"] = True
    transport["terminal_phase_value"] = 20
    transport["terminal_phase_name"] = "SOCKET_READY"
    transport["socket_target_address"] = 0x817E12B4
    transport["socket_target_size"] = 4
    transport["socket_command_address"] = 0x817E12B8
    transport["socket_command_size"] = 4
    transport["socket_submitted_fd_address"] = 0x817E12BC
    transport["socket_submitted_fd_size"] = 4
    transport["socket_callback_pointer_address"] = 0x817E12C0
    transport["socket_callback_pointer_size"] = 4
    transport["socket_context_pointer_address"] = 0x817E12C4
    transport["socket_context_pointer_size"] = 4
    transport["socket_callback_exit_count_address"] = 0x817E12C8
    transport["socket_callback_exit_count_size"] = 4
    transport["socket_stale_callback_count_address"] = 0x817E12CC
    transport["socket_stale_callback_count_size"] = 4
    transport["socket_duplicate_callback_count_address"] = 0x817E12D0
    transport["socket_duplicate_callback_count_size"] = 4
    transport["socket_fd_before_submit_address"] = 0x817E12D4
    transport["socket_fd_before_submit_size"] = 4
    transport["socket_fd_after_completion_address"] = 0x817E12D8
    transport["socket_fd_after_completion_size"] = 4
    transport["socket_request_address_address"] = 0x817E12DC
    transport["socket_request_address_size"] = 4
    transport["socket_request_storage_size_address"] = 0x817E12E0
    transport["socket_request_storage_size_size"] = 4
    transport["socket_request_logical_size_address"] = 0x817E12E4
    transport["socket_request_logical_size_size"] = 4
    transport["socket_request_alignment_address"] = 0x817E12E8
    transport["socket_request_alignment_size"] = 4
    transport["socket_family_value_address"] = 0x817E12EC
    transport["socket_family_value_size"] = 4
    transport["socket_type_value_address"] = 0x817E12F0
    transport["socket_type_value_size"] = 4
    transport["socket_protocol_value_address"] = 0x817E12F4
    transport["socket_protocol_value_size"] = 4
    transport["socket_descriptor_valid_address"] = 0x817E12F8
    transport["socket_descriptor_valid_size"] = 4
    transport["socket_ready_address"] = 0x817E12FC
    transport["socket_ready_size"] = 4
    transport["socket_request_bytes_address"] = 0x817E1300
    transport["socket_request_bytes_size"] = 12
    transport["socket_pre_call_args_address"] = 0x817E1320
    transport["socket_pre_call_args_size"] = 0x20
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.terminal_phase_name == "SOCKET_READY"
    assert parsed.relocated_runtime.transport.socket_request_bytes_size == 12
    assert parsed.relocated_runtime.transport.socket_pre_call_args_size == 0x20


def test_runtime_payload_manifest_accepts_bind_terminal_metadata() -> None:
    payload_bytes = b"\x4e\x80\x00\x20" * 512
    manifest = _make_relocated_manifest(payload_bytes)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["mode"] = "retail_wrapper_bind_once"
    relocated["diagnostics"] = diagnostics
    relocated["embedded_runtime_blob_size"] = 0x4A0
    relocated["embedded_runtime_blob_sha256"] = hashlib.sha256(payload_bytes[0x1A0:0x620]).hexdigest()
    relocated["cache_range_size"] = 0x4A0
    relocated["runtime_state_end"] = 0x817E14A0
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_bind_once"
    transport["terminal_phase_value"] = 17
    transport["terminal_phase_name"] = "BOUND_NO_RECV"
    transport["bind_target_address"] = 0x817E1360
    transport["bind_target_size"] = 4
    transport["bind_command_address"] = 0x817E1364
    transport["bind_command_size"] = 4
    transport["bind_submitted_fd_address"] = 0x817E1368
    transport["bind_submitted_fd_size"] = 4
    transport["bind_callback_pointer_address"] = 0x817E136C
    transport["bind_callback_pointer_size"] = 4
    transport["bind_context_pointer_address"] = 0x817E1370
    transport["bind_context_pointer_size"] = 4
    transport["bind_callback_exit_count_address"] = 0x817E1374
    transport["bind_callback_exit_count_size"] = 4
    transport["bind_stale_callback_count_address"] = 0x817E1378
    transport["bind_stale_callback_count_size"] = 4
    transport["bind_duplicate_callback_count_address"] = 0x817E137C
    transport["bind_duplicate_callback_count_size"] = 4
    transport["bind_request_address_address"] = 0x817E1380
    transport["bind_request_address_size"] = 4
    transport["bind_request_storage_size_address"] = 0x817E1384
    transport["bind_request_storage_size_size"] = 4
    transport["bind_request_logical_size_address"] = 0x817E1388
    transport["bind_request_logical_size_size"] = 4
    transport["bind_request_alignment_address"] = 0x817E138C
    transport["bind_request_alignment_size"] = 4
    transport["bind_sockaddr_length_address"] = 0x817E1390
    transport["bind_sockaddr_length_size"] = 4
    transport["bind_family_value_address"] = 0x817E1394
    transport["bind_family_value_size"] = 4
    transport["bind_port_value_address"] = 0x817E1398
    transport["bind_port_value_size"] = 4
    transport["bind_address_value_address"] = 0x817E139C
    transport["bind_address_value_size"] = 4
    transport["bind_request_bytes_address"] = 0x817E13A0
    transport["bind_request_bytes_size"] = 36
    transport["bind_pre_call_args_address"] = 0x817E13E0
    transport["bind_pre_call_args_size"] = 0x20
    transport["cleanup_close_callback_count_address"] = 0x817E1400
    transport["cleanup_close_callback_count_size"] = 4
    transport["cleanup_close_submit_result_address"] = 0x817E1404
    transport["cleanup_close_submit_result_size"] = 4
    transport["cleanup_close_callback_result_address"] = 0x817E1408
    transport["cleanup_close_callback_result_size"] = 4
    transport["cleanup_close_submit_generation_address"] = 0x817E140C
    transport["cleanup_close_submit_generation_size"] = 4
    transport["cleanup_close_callback_generation_address"] = 0x817E1410
    transport["cleanup_close_callback_generation_size"] = 4
    transport["cleanup_close_target_address"] = 0x817E1414
    transport["cleanup_close_target_size"] = 4
    transport["cleanup_close_command_address"] = 0x817E1418
    transport["cleanup_close_command_size"] = 4
    transport["cleanup_close_submitted_fd_address"] = 0x817E141C
    transport["cleanup_close_submitted_fd_size"] = 4
    transport["cleanup_close_callback_pointer_address"] = 0x817E1420
    transport["cleanup_close_callback_pointer_size"] = 4
    transport["cleanup_close_context_pointer_address"] = 0x817E1424
    transport["cleanup_close_context_pointer_size"] = 4
    transport["cleanup_close_callback_exit_count_address"] = 0x817E1428
    transport["cleanup_close_callback_exit_count_size"] = 4
    transport["cleanup_close_stale_callback_count_address"] = 0x817E142C
    transport["cleanup_close_stale_callback_count_size"] = 4
    transport["cleanup_close_duplicate_callback_count_address"] = 0x817E1430
    transport["cleanup_close_duplicate_callback_count_size"] = 4
    transport["cleanup_close_request_address_address"] = 0x817E1434
    transport["cleanup_close_request_address_size"] = 4
    transport["cleanup_close_request_storage_size_address"] = 0x817E1438
    transport["cleanup_close_request_storage_size_size"] = 4
    transport["cleanup_close_request_logical_size_address"] = 0x817E143C
    transport["cleanup_close_request_logical_size_size"] = 4
    transport["cleanup_close_request_alignment_address"] = 0x817E1440
    transport["cleanup_close_request_alignment_size"] = 4
    transport["cleanup_close_request_value_address"] = 0x817E1444
    transport["cleanup_close_request_value_size"] = 4
    transport["cleanup_close_request_bytes_address"] = 0x817E1448
    transport["cleanup_close_request_bytes_size"] = 4
    transport["cleanup_close_pre_call_args_address"] = 0x817E1460
    transport["cleanup_close_pre_call_args_size"] = 0x20
    transport["bound_flag_address"] = 0x817E1480
    transport["bound_flag_size"] = 4
    transport["bound_address_address"] = 0x817E1484
    transport["bound_address_size"] = 4
    transport["socket_closed_after_bind_failure_address"] = 0x817E1488
    transport["socket_closed_after_bind_failure_size"] = 4
    transport["socket_leak_detected_address"] = 0x817E148C
    transport["socket_leak_detected_size"] = 4
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.bind_request_bytes_size == 36
    assert parsed.relocated_runtime.transport.cleanup_close_request_bytes_size == 4
    assert parsed.relocated_runtime.transport.bound_flag_size == 4


def test_runtime_payload_manifest_rejects_abi_probe_outside_runtime_state() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    abi_probe = dict(relocated["abi_probe"])
    abi_probe["after_call_flag_address"] = 0x817E12F0
    relocated["abi_probe"] = abi_probe
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="ABI probe field after_call_flag is outside the runtime state range"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_accepts_disabled_relocated_transport_metadata() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    relocated["ios_udp_diagnostic_enabled"] = False
    relocated["transport"] = None
    raw["relocated_runtime"] = relocated

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.ios_udp_diagnostic_enabled is False
    assert parsed.relocated_runtime.transport is None


def test_runtime_payload_manifest_rejects_transport_metadata_when_disabled() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    relocated["ios_udp_diagnostic_enabled"] = False
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="requires ios_udp_diagnostic_enabled"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_retail_wrapper_wrong_callback_signature() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    wrapper = dict(relocated["retail_ios_wrapper"])
    wrapper["callback_signature"] = "void callback(void)"
    relocated["retail_ios_wrapper"] = wrapper
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="callback signature metadata is unexpected"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_legacy_inferred_ioctl_labels() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    wrapper = dict(relocated["retail_ios_wrapper"])
    wrapper["ioctl_async_address"] = wrapper["read_async_address"]
    relocated["retail_ios_wrapper"] = wrapper
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="legacy inferred label"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_wrong_confirmed_ioctl_fingerprint() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    wrapper = dict(relocated["retail_ios_wrapper"])
    wrapper["confirmed_ioctl_async_fingerprint_sha256"] = "0" * 64
    relocated["retail_ios_wrapper"] = wrapper
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="unexpected function fingerprint"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_enabled_transport_outside_relocated_continue() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    raw["payload_mode"] = runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT
    raw["entry_bootstrap"]["mode"] = runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT
    raw["entry_bootstrap"]["status_value"] = 0xB0071002
    raw["entry_bootstrap"]["halt_loop_address"] = 0x80684540
    relocated = dict(raw["relocated_runtime"])
    relocated["mode"] = runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="requires relocated_continue mode"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_accepts_recvfrom_once_transport() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_recvfrom_once"
    transport["receive_enabled"] = True
    transport["terminal_phase_value"] = 27
    transport["terminal_phase_name"] = "RECEIVED_DATAGRAM"
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.mode == "retail_wrapper_recvfrom_once"
    assert parsed.relocated_runtime.transport.receive_enabled is True


def test_runtime_payload_manifest_rejects_recvfrom_once_without_receive_enabled() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_recvfrom_once"
    transport["receive_enabled"] = False
    transport["terminal_phase_value"] = 27
    transport["terminal_phase_name"] = "RECEIVED_DATAGRAM"
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="must enable receive"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_accepts_recv_send_once_transport() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_recv_send_once"
    transport["receive_enabled"] = True
    transport["send_enabled"] = True
    transport["terminal_phase_value"] = 37
    transport["terminal_phase_name"] = "SENT_DATAGRAM"
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.mode == "retail_wrapper_recv_send_once"
    assert parsed.relocated_runtime.transport.receive_enabled is True
    assert parsed.relocated_runtime.transport.send_enabled is True


def test_runtime_payload_manifest_rejects_recv_send_once_without_send_enabled() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_recv_send_once"
    transport["receive_enabled"] = True
    transport["send_enabled"] = False
    transport["terminal_phase_value"] = 37
    transport["terminal_phase_name"] = "SENT_DATAGRAM"
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="must enable send"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_accepts_recv_send_loop_transport() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    transport = dict(relocated["transport"])
    transport["mode"] = "retail_wrapper_recv_send_loop"
    transport["receive_enabled"] = True
    transport["send_enabled"] = True
    transport["terminal_phase_value"] = 45
    transport["terminal_phase_name"] = "LOOP_COMPLETE"
    transport["receive_arm_count_address"] = 0x817E1254
    transport["receive_arm_count_size"] = 4
    transport["receive_rearm_count_address"] = 0x817E1258
    transport["receive_rearm_count_size"] = 4
    transport["configured_exchange_limit_address"] = 0x817E125C
    transport["configured_exchange_limit_size"] = 4
    transport["completed_exchange_count_address"] = 0x817E1260
    transport["completed_exchange_count_size"] = 4
    transport["current_exchange_index_address"] = 0x817E1264
    transport["current_exchange_index_size"] = 4
    transport["last_completed_exchange_index_address"] = 0x817E1268
    transport["last_completed_exchange_index_size"] = 4
    transport["previous_peer_ipv4_address"] = 0x817E126C
    transport["previous_peer_ipv4_size"] = 4
    transport["previous_peer_port_address"] = 0x817E1270
    transport["previous_peer_port_size"] = 4
    transport["rearm_submission_failure_count_address"] = 0x817E1274
    transport["rearm_submission_failure_count_size"] = 4
    transport["loop_complete_transition_count_address"] = 0x817E1278
    transport["loop_complete_transition_count_size"] = 4
    transport["cleanup_deferred_count_address"] = 0x817E127C
    transport["cleanup_deferred_count_size"] = 4
    transport["polls_while_receive_pending_address"] = 0x817E1280
    transport["polls_while_receive_pending_size"] = 4
    transport["polls_after_loop_complete_address"] = 0x817E1284
    transport["polls_after_loop_complete_size"] = 4
    relocated["transport"] = transport
    relocated["abi_probe"] = None
    raw["relocated_runtime"] = relocated

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.mode == "retail_wrapper_recv_send_loop"
    assert parsed.relocated_runtime.transport.completed_exchange_count_address == 0x817E1260
    assert parsed.relocated_runtime.transport.polls_after_loop_complete_address == 0x817E1284


def test_runtime_payload_manifest_accepts_cp3w_frame_validation_transport() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
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

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.mode == "cp3w_frame_validation"
    assert parsed.relocated_runtime.transport.terminal_phase_name == "CP3W_FRAME_LOOP_COMPLETE"
    assert parsed.relocated_runtime.transport.cp3w_magic_hex == "43503357"
    assert parsed.relocated_runtime.transport.prepared_send_length_address == 0x817E1254
    assert parsed.relocated_runtime.transport.cp3w_last_frame_result_address == 0x817E12A4


def test_runtime_payload_manifest_rejects_cp3w_frame_validation_wrong_terminal_phase() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    transport = dict(relocated["transport"])
    transport["mode"] = "cp3w_frame_validation"
    transport["receive_enabled"] = True
    transport["send_enabled"] = True
    transport["terminal_phase_value"] = 45
    transport["terminal_phase_name"] = "LOOP_COMPLETE"
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="CP3W_FRAME_LOOP_COMPLETE"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_accepts_cp3w_ping_pong_transport() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
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

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.mode == "cp3w_ping_pong"
    assert parsed.relocated_runtime.transport.terminal_phase_name == "CP3W_PING_PONG_LOOP_COMPLETE"
    assert parsed.relocated_runtime.transport.cp3w_pong_uses_ping_command is True
    assert parsed.relocated_runtime.transport.cp3w_last_dispatch_result_address == 0x817E12D4


def test_runtime_payload_manifest_rejects_cp3w_ping_pong_wrong_terminal_phase() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    transport = dict(relocated["transport"])
    transport["mode"] = "cp3w_ping_pong"
    transport["receive_enabled"] = True
    transport["send_enabled"] = True
    transport["terminal_phase_value"] = 55
    transport["terminal_phase_name"] = "CP3W_FRAME_LOOP_COMPLETE"
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="CP3W_PING_PONG_LOOP_COMPLETE"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_accepts_cp3w_hello_session_transport() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    relocated["embedded_runtime_blob_size"] = 0x360
    relocated["cache_range_size"] = 0x360
    relocated["runtime_state_end"] = 0x817E1360
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

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.mode == "cp3w_hello_session"
    assert parsed.relocated_runtime.transport.terminal_phase_name == "CP3W_HELLO_SESSION_LOOP_COMPLETE"
    assert parsed.relocated_runtime.transport.cp3w_hello_requests_received_address == 0x817E1350
    assert parsed.relocated_runtime.transport.cp3w_runtime_build_id_address == 0x817E130C


def test_runtime_payload_manifest_rejects_cp3w_hello_session_wrong_terminal_phase() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    transport = dict(relocated["transport"])
    transport["mode"] = "cp3w_hello_session"
    transport["receive_enabled"] = True
    transport["send_enabled"] = True
    transport["terminal_phase_value"] = 61
    transport["terminal_phase_name"] = "CP3W_PING_PONG_LOOP_COMPLETE"
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="CP3W_HELLO_SESSION_LOOP_COMPLETE"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_relocated_runtime_overlap_with_bootstrap_diagnostic() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    relocated["runtime_destination_address"] = 0x817E0100
    relocated["runtime_entry_address"] = 0x817E0100
    relocated["runtime_code_start"] = 0x817E0100
    relocated["runtime_poll_entry_address"] = 0x817E0104
    relocated["runtime_poll_hook_wrapper_address"] = 0x817E0110
    relocated["runtime_code_end"] = 0x817E0118
    relocated["runtime_state_start"] = 0x817E0118
    relocated["runtime_state_end"] = 0x817E02C4
    relocated["runtime_canary_address"] = 0x817E0118
    relocated["copy_complete_marker_address"] = 0x817E0128
    relocated["runtime_executed_marker_address"] = 0x817E012C
    relocated["runtime_execution_counter_address"] = 0x817E0130
    relocated["runtime_status_address"] = 0x817E0134
    relocated["bootstrap_return_marker_address"] = 0x817E0138
    relocated["runtime_poll_counter_address"] = 0x817E013C
    relocated["runtime_poll_heartbeat_address"] = 0x817E0140
    relocated["runtime_poll_last_sequence_address"] = 0x817E0144
    relocated["cache_range_start"] = 0x817E0100
    relocated["cache_range_size"] = 0x2C4
    diagnostics = dict(relocated["diagnostics"])
    for key, value in list(diagnostics.items()):
        if key.endswith("_address"):
            diagnostics[key] = value - 0xF00
    relocated["diagnostics"] = diagnostics
    transport = dict(relocated["transport"])
    for key, value in list(transport.items()):
        if key.endswith("_address") and value is not None:
            transport[key] = value - 0xF00
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    with pytest.raises(
        Prime3DolPatchError,
        match="outside the runtime state range|overlaps the bootstrap diagnostic block",
    ):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_partial_runtime_stack_range() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    relocated["runtime_stack_start"] = 0x817E1050
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="provide both start and end together"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_runtime_poll_range_outside_state() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    relocated["runtime_poll_last_sequence_address"] = 0x817E12F0
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="runtime_poll_last_sequence is outside the runtime state range"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_overlapping_diagnostic_fields() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["runtime_poll_exit_count_address"] = diagnostics["runtime_poll_entry_count_address"]
    relocated["diagnostics"] = diagnostics
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="overlap"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_transport_preview_outside_state() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 320)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    transport = dict(relocated["transport"])
    transport["last_send_preview_address"] = 0x817E12E8
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="transport field transport_last_send_preview exceeds"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


@pytest.mark.parametrize(
    ("address", "size", "line_size", "expected"),
    [
        (0x817E1000, 0x80, 0x20, (0x817E1000, 0x80)),
        (0x817E1001, 0x80, 0x20, (0x817E1000, 0xA0)),
        (0x817E1000, 1, 0x20, (0x817E1000, 0x20)),
    ],
)
def test_compute_cache_range(address: int, size: int, line_size: int, expected: tuple[int, int]) -> None:
    assert runtime_payload.compute_cache_range(address=address, size=size, cache_line_size=line_size) == expected


def test_compute_cache_range_rejects_zero_length() -> None:
    with pytest.raises(Prime3DolPatchError, match="must be positive"):
        runtime_payload.compute_cache_range(address=0x817E1000, size=0, cache_line_size=0x20)


def test_runtime_payload_manifest_rejects_partial_probe_metadata() -> None:
    manifest = _make_manifest(b"\x4e\x80\x00\x20" * 16)
    raw = manifest.to_json_dict()
    raw["canary_start_offset"] = 0x10

    with pytest.raises(Prime3DolPatchError, match="provide both canary_start_offset"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)
