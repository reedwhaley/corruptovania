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
        "embedded_runtime_blob_size": 0x1E0,
        "embedded_runtime_blob_sha256": hashlib.sha256(payload_bytes[0x1A0:0x380]).hexdigest(),
        "runtime_destination_address": 0x817E1000,
        "runtime_entry_address": 0x817E1000,
        "runtime_poll_entry_address": 0x817E1020,
        "runtime_poll_hook_wrapper_address": 0x817E1030,
        "runtime_code_start": 0x817E1000,
        "runtime_code_end": 0x817E104C,
        "runtime_state_start": 0x817E1050,
        "runtime_state_end": 0x817E11C4,
        "runtime_stack_start": None,
        "runtime_stack_end": None,
        "required_source_alignment": 0x20,
        "required_destination_alignment": 0x20,
        "cache_line_size": 0x20,
        "cache_range_start": 0x817E1000,
        "cache_range_size": 0x1E0,
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
            "phase_address": 0x817E1144,
            "phase_size": 4,
            "last_error_address": 0x817E1148,
            "last_error_size": 4,
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
            "callback_pending_address": 0x817E1160,
            "callback_pending_size": 4,
            "kd_fd_address": 0x817E1164,
            "kd_fd_size": 4,
            "ip_fd_address": 0x817E1168,
            "ip_fd_size": 4,
            "socket_fd_address": 0x817E116C,
            "socket_fd_size": 4,
            "host_id_address": 0x817E1170,
            "host_id_size": 4,
            "bound_port_address": 0x817E1174,
            "bound_port_size": 4,
            "receive_count_address": 0x817E1178,
            "receive_count_size": 4,
            "receive_bytes_address": 0x817E117C,
            "receive_bytes_size": 4,
            "send_count_address": 0x817E1180,
            "send_count_size": 4,
            "send_bytes_address": 0x817E1184,
            "send_bytes_size": 4,
            "last_receive_length_address": 0x817E1188,
            "last_receive_length_size": 4,
            "last_send_length_address": 0x817E118C,
            "last_send_length_size": 4,
            "last_peer_ipv4_address": 0x817E1190,
            "last_peer_ipv4_size": 4,
            "last_peer_port_address": 0x817E1194,
            "last_peer_port_size": 4,
            "last_peer_family_address": 0x817E1198,
            "last_peer_family_size": 4,
            "last_poll_action_address": 0x817E119C,
            "last_poll_action_size": 4,
            "last_submit_result_address": 0x817E11A0,
            "last_submit_result_size": 4,
            "last_receive_preview_address": 0x817E11A4,
            "last_receive_preview_size": 16,
            "last_send_preview_address": 0x817E11B4,
            "last_send_preview_size": 16,
        },
        "retail_ios_wrapper": {
            "supported_dol_sha256": "6b550f221602074747a2e61b0aa064203fd493f6865dfb3b1a912682065e6104",
            "open_async_address": 0x80504668,
            "open_address": 0x80504780,
            "close_async_address": 0x805048A0,
            "close_address": 0x80504960,
            "ioctl_async_address": 0x80504A08,
            "ioctl_address": 0x80504B08,
            "ioctlv_async_address": 0x80504C10,
            "ioctlv_address": 0x80504D10,
            "open_async_guard_words": [0x9421FFD0, 0x7C0802A6, 0x90010034, 0x39610030],
            "callback_signature": "s32 callback(s32 result, void *userdata)",
            "preserved_registers": ["r2", "r13"],
            "submit_helper_address": 0x8050441C,
            "request_allocator_address": 0x80505960,
            "evidence_source": "prime3-ntsc retail DOL cluster + callsite analysis",
            "confidence": "verified",
        },
    }
    return runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_json_is_deterministic() -> None:
    manifest = _make_manifest(b"\x4e\x80\x00\x20")
    assert manifest.to_json_text() == manifest.to_json_text()


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
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 240)

    parsed = runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(manifest.to_json_dict())

    assert parsed.relocated_runtime is not None
    assert parsed.relocated_runtime.runtime_destination_address == 0x817E1000
    assert parsed.relocated_runtime.cache_range_size == 0x1E0
    assert parsed.relocated_runtime.runtime_poll_hook_wrapper_address == 0x817E1030
    assert parsed.relocated_runtime.runtime_poll_last_sequence_address == 0x817E107C
    assert parsed.relocated_runtime.diagnostics is not None
    assert parsed.relocated_runtime.diagnostics.last_execution_marker_address == 0x817E1134
    assert parsed.relocated_runtime.ios_udp_diagnostic_enabled is True
    assert parsed.relocated_runtime.transport is not None
    assert parsed.relocated_runtime.transport.last_receive_preview_size == 16
    assert parsed.relocated_runtime.retail_ios_wrapper is not None
    assert parsed.relocated_runtime.retail_ios_wrapper.ioctlv_async_address == 0x80504C10


def test_runtime_payload_manifest_accepts_disabled_relocated_transport_metadata() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 240)
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
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 240)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    relocated["ios_udp_diagnostic_enabled"] = False
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="requires ios_udp_diagnostic_enabled"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_retail_wrapper_wrong_callback_signature() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 240)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    wrapper = dict(relocated["retail_ios_wrapper"])
    wrapper["callback_signature"] = "void callback(void)"
    relocated["retail_ios_wrapper"] = wrapper
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="callback signature metadata is unexpected"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_enabled_transport_outside_relocated_continue() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 240)
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


def test_runtime_payload_manifest_rejects_relocated_runtime_overlap_with_bootstrap_diagnostic() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 240)
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
        if key.endswith("_address"):
            transport[key] = value - 0xF00
    relocated["transport"] = transport
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="overlaps the bootstrap diagnostic block"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_partial_runtime_stack_range() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 240)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    relocated["runtime_stack_start"] = 0x817E1050
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="provide both start and end together"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_runtime_poll_range_outside_state() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 240)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    relocated["runtime_poll_last_sequence_address"] = 0x817E11C4
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="runtime_poll_last_sequence is outside the runtime state range"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_overlapping_diagnostic_fields() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 240)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    diagnostics = dict(relocated["diagnostics"])
    diagnostics["runtime_poll_exit_count_address"] = diagnostics["runtime_poll_entry_count_address"]
    relocated["diagnostics"] = diagnostics
    raw["relocated_runtime"] = relocated

    with pytest.raises(Prime3DolPatchError, match="overlap"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def test_runtime_payload_manifest_rejects_transport_preview_outside_state() -> None:
    manifest = _make_relocated_manifest(b"\x4e\x80\x00\x20" * 240)
    raw = manifest.to_json_dict()
    relocated = dict(raw["relocated_runtime"])
    transport = dict(relocated["transport"])
    transport["last_send_preview_address"] = 0x817E11C0
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
