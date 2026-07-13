from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from randovania.games.prime3.exporter import probe_delivery, runtime_payload
from randovania.games.prime3.exporter.dol_patcher import Prime3DolPatchError, parse_dol_header
from test.games.prime3.exporter.test_dol_patcher import _build_synthetic_dol, _make_fake_version


def _make_manifest(payload_bytes: bytes) -> runtime_payload.Prime3RuntimePayloadManifest:
    return runtime_payload.Prime3RuntimePayloadManifest(
        schema_version=runtime_payload.PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION,
        target_architecture=runtime_payload.PRIME3_RUNTIME_TARGET_ARCHITECTURE,
        target_endianness=runtime_payload.PRIME3_RUNTIME_TARGET_ENDIANNESS,
        target_abi=runtime_payload.PRIME3_RUNTIME_TARGET_ABI,
        compiler_identity="synthetic",
        compiler_version="1.0",
        linker_identity="synthetic",
        linker_version="1.0",
        payload_sha256=probe_delivery._sha256_bytes(payload_bytes),
        payload_size=len(payload_bytes),
        required_alignment=runtime_payload.PRIME3_RUNTIME_REQUIRED_ALIGNMENT,
        entry_symbol_name=runtime_payload.PRIME3_RUNTIME_ENTRY_SYMBOL,
        entry_symbol_offset=0,
        source_digest="deadbeef",
        protocol_artifact_version=1,
        unresolved_relocation_count=0,
        dynamic_section_count=0,
        canary_start_offset=0x10,
        canary_size=0x10,
        counter_offset=0x20,
        counter_size=4,
    )


def _make_bootstrap_manifest(payload_bytes: bytes, *, mode: str) -> runtime_payload.Prime3RuntimePayloadManifest:
    manifest = _make_manifest(payload_bytes)
    raw = manifest.to_json_dict()
    raw["payload_mode"] = mode
    raw["entry_bootstrap"] = {
        "mode": mode,
        "staging_address": 0x806843C0,
        "staging_save_area_offset": 0x20,
        "staging_save_area_size": 0x10,
        "halt_loop_address": 0x806843E0 if mode.endswith("halt") else None,
        "reserved_boundary": 0x817E0000,
        "reserved_range_start": 0x817E0000,
        "reserved_range_end": 0x817FE3A0,
        "diagnostic_address": 0x817E0100,
        "diagnostic_block_size": 0x40,
        "canary_address": 0x817E0100,
        "canary_size": 0x10,
        "canary_sha256": probe_delivery._sha256_bytes(b"P3BOOTSTRAPCANRY"),
        "marker_address": 0x817E0114,
        "marker_value": 0x50334254,
        "counter_address": 0x817E0118,
        "counter_size": 4,
        "original_80000034_address": 0x817E011C,
        "original_80003110_address": 0x817E0120,
        "replacement_value_address": 0x817E0124,
        "replacement_value": 0x817E0000,
        "status_address": 0x817E0128,
        "status_value": 0xB0070001 if mode.endswith("halt") else 0xB0070002,
        "original_entry_instruction": probe_delivery.EXPECTED_ENTRY_WORD,
        "original_branch_target": 0x8000648C,
        "original_continuation_address": 0x80006324,
    }
    return runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def _make_relocated_manifest(
    payload_bytes: bytes,
    *,
    mode: str,
    enable_ios_udp_diagnostic: bool = False,
) -> runtime_payload.Prime3RuntimePayloadManifest:
    raw = _make_manifest(payload_bytes).to_json_dict()
    raw["payload_mode"] = mode
    raw["entry_bootstrap"] = {
        "mode": mode,
        "staging_address": 0x806843C0,
        "staging_save_area_offset": 0x20,
        "staging_save_area_size": 0x10,
        "halt_loop_address": 0x806843E0 if "halt" in mode else None,
        "reserved_boundary": 0x817E0000,
        "reserved_range_start": 0x817E0000,
        "reserved_range_end": 0x817FE3A0,
        "diagnostic_address": 0x817E0100,
        "diagnostic_block_size": 0x40,
        "canary_address": 0x817E0100,
        "canary_size": 0x10,
        "canary_sha256": probe_delivery._sha256_bytes(b"P3BOOTSTRAPCANRY"),
        "marker_address": 0x817E0114,
        "marker_value": 0x50334254,
        "counter_address": 0x817E0118,
        "counter_size": 4,
        "original_80000034_address": 0x817E011C,
        "original_80003110_address": 0x817E0120,
        "replacement_value_address": 0x817E0124,
        "replacement_value": 0x817E0000,
        "status_address": 0x817E0128,
        "status_value": (
            0xB0071001
            if mode == runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT
            else 0xB0071002
        ),
        "original_entry_instruction": probe_delivery.EXPECTED_ENTRY_WORD,
        "original_branch_target": 0x8000648C,
        "original_continuation_address": 0x80006324,
    }
    raw["relocated_runtime"] = {
        "mode": mode,
        "low_bootstrap_address": 0x806843C0,
        "low_bootstrap_size": 0x60,
        "low_bootstrap_sha256": probe_delivery._sha256_bytes(payload_bytes[:0x60]),
        "embedded_runtime_blob_offset": 0x60,
        "embedded_runtime_blob_size": 0x260,
        "embedded_runtime_blob_sha256": probe_delivery._sha256_bytes(payload_bytes[0x60:0x2C0]),
        "runtime_destination_address": 0x817E1000,
        "runtime_entry_address": 0x817E1000,
        "runtime_poll_entry_address": 0x817E1004,
        "runtime_poll_hook_wrapper_address": 0x817E1014,
        "runtime_code_start": 0x817E1000,
        "runtime_code_end": 0x817E102C,
        "runtime_state_start": 0x817E1030,
        "runtime_state_end": 0x817E1260,
        "runtime_stack_start": None,
        "runtime_stack_end": None,
        "required_source_alignment": runtime_payload.PRIME3_RUNTIME_REQUIRED_ALIGNMENT,
        "required_destination_alignment": runtime_payload.PRIME3_RUNTIME_REQUIRED_ALIGNMENT,
        "cache_line_size": 0x20,
        "cache_range_start": 0x817E1000,
        "cache_range_size": 0x260,
        "runtime_canary_address": 0x817E1030,
        "runtime_canary_size": 0x04,
        "runtime_canary_sha256": probe_delivery._sha256_bytes(payload_bytes[0x70:0x74]),
        "copy_complete_marker_address": 0x817E1034,
        "copy_complete_marker_value": 0x434F5059,
        "runtime_executed_marker_address": 0x817E1038,
        "runtime_executed_marker_value": 0x52554E21,
        "runtime_execution_counter_address": 0x817E103C,
        "runtime_execution_counter_size": 4,
        "runtime_status_address": 0x817E1040,
        "runtime_success_status_value": 0x52544F4B,
        "bootstrap_return_marker_address": 0x817E1044,
        "bootstrap_return_marker_value": 0x4252544E,
        "runtime_poll_counter_address": 0x817E1048,
        "runtime_poll_counter_size": 4,
        "runtime_poll_heartbeat_address": 0x817E104C,
        "runtime_poll_heartbeat_size": 4,
        "runtime_poll_last_sequence_address": 0x817E1050,
        "runtime_poll_last_sequence_size": 4,
        "ios_udp_diagnostic_enabled": enable_ios_udp_diagnostic,
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
            "phase_address": 0x817E1054,
            "phase_size": 4,
            "last_error_address": 0x817E1058,
            "last_error_size": 4,
            "last_socket_error_address": 0x817E105C,
            "last_socket_error_size": 4,
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
            "rejected_callback_count_address": 0x817E1074,
            "rejected_callback_count_size": 4,
            "callback_pending_address": 0x817E1078,
            "callback_pending_size": 4,
            "open_kd_submit_count_address": 0x817E107C,
            "open_kd_submit_count_size": 4,
            "open_kd_callback_count_address": 0x817E1080,
            "open_kd_callback_count_size": 4,
            "nwc24_output_buffer_address": 0x817E10A0,
            "nwc24_output_buffer_size": 0x20,
            "nwc24_output_buffer_alignment": 0x20,
            "nwc24_submit_count_address": 0x817E1084,
            "nwc24_submit_count_size": 4,
            "nwc24_callback_count_address": 0x817E1088,
            "nwc24_callback_count_size": 4,
            "nwc24_synchronous_result_address": 0x817E10C0,
            "nwc24_synchronous_result_size": 4,
            "nwc24_callback_result_address": 0x817E10C4,
            "nwc24_callback_result_size": 4,
            "nwc24_output_digest_address": 0x817E10C8,
            "nwc24_output_digest_size": 4,
            "open_ip_submit_count_address": 0x817E10CC,
            "open_ip_submit_count_size": 4,
            "open_ip_callback_count_address": 0x817E10D0,
            "open_ip_callback_count_size": 4,
            "kd_close_submit_count_address": 0x817E10D4,
            "kd_close_submit_count_size": 4,
            "kd_close_callback_count_address": 0x817E10D8,
            "kd_close_callback_count_size": 4,
            "startup_submit_count_address": 0x817E10DC,
            "startup_submit_count_size": 4,
            "startup_callback_count_address": 0x817E10E0,
            "startup_callback_count_size": 4,
            "get_host_id_submit_count_address": 0x817E10E4,
            "get_host_id_submit_count_size": 4,
            "get_host_id_callback_count_address": 0x817E10E8,
            "get_host_id_callback_count_size": 4,
            "socket_submit_count_address": 0x817E10EC,
            "socket_submit_count_size": 4,
            "socket_callback_count_address": 0x817E10F0,
            "socket_callback_count_size": 4,
            "bind_submit_count_address": 0x817E10F4,
            "bind_submit_count_size": 4,
            "bind_callback_count_address": 0x817E10F8,
            "bind_callback_count_size": 4,
            "kd_fd_address": 0x817E10FC,
            "kd_fd_size": 4,
            "kd_closed_address": 0x817E1100,
            "kd_closed_size": 4,
            "ip_fd_address": 0x817E1104,
            "ip_fd_size": 4,
            "socket_fd_address": 0x817E1108,
            "socket_fd_size": 4,
            "host_id_address": 0x817E110C,
            "host_id_size": 4,
            "bound_port_address": 0x817E1110,
            "bound_port_size": 4,
            "receive_submit_count_address": 0x817E1114,
            "receive_submit_count_size": 4,
            "send_submit_count_address": 0x817E1118,
            "send_submit_count_size": 4,
            "ip_close_submit_count_address": 0x817E111C,
            "ip_close_submit_count_size": 4,
            "socket_close_submit_count_address": 0x817E1120,
            "socket_close_submit_count_size": 4,
            "receive_count_address": 0x817E1124,
            "receive_count_size": 4,
            "receive_bytes_address": 0x817E1128,
            "receive_bytes_size": 4,
            "send_count_address": 0x817E112C,
            "send_count_size": 4,
            "send_bytes_address": 0x817E1130,
            "send_bytes_size": 4,
            "last_receive_length_address": 0x817E1134,
            "last_receive_length_size": 4,
            "last_send_length_address": 0x817E1138,
            "last_send_length_size": 4,
            "last_peer_ipv4_address": 0x817E113C,
            "last_peer_ipv4_size": 4,
            "last_peer_port_address": 0x817E1140,
            "last_peer_port_size": 4,
            "last_peer_family_address": 0x817E1144,
            "last_peer_family_size": 4,
            "last_poll_action_address": 0x817E1148,
            "last_poll_action_size": 4,
            "last_submit_result_address": 0x817E114C,
            "last_submit_result_size": 4,
            "last_receive_preview_address": 0x817E1150,
            "last_receive_preview_size": 16,
            "last_send_preview_address": 0x817E1160,
            "last_send_preview_size": 16,
        } if enable_ios_udp_diagnostic else None,
    }
    return runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)


def _write_inputs(tmp_path: Path, *, extracted_bytes: bytes | None = None) -> tuple[Path, Path, Path, Path, Path]:
    version = _make_fake_version()
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + b"\x00" * 0x10 + b"\x00" * 4
    manifest = _make_manifest(payload_bytes)
    original_bytes = _build_synthetic_dol(version)
    built = probe_delivery.build_unhooked_probe_dol(original_bytes, payload_bytes, manifest)
    original_path = tmp_path.joinpath("original.dol")
    probe_path = tmp_path.joinpath("probe.dol")
    extracted_path = tmp_path.joinpath("extracted.dol")
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    original_path.write_bytes(original_bytes)
    probe_path.write_bytes(built.probe_dol_bytes)
    extracted_path.write_bytes(built.probe_dol_bytes if extracted_bytes is None else extracted_bytes)
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")
    return original_path, probe_path, extracted_path, payload_path, manifest_path


def _entry_gate_version():
    return _make_fake_version(address=0x80006340, build_string=b"!#$MetroidBuildInfo!#$FAKE")


def _entry_gate_original() -> bytes:
    version = _entry_gate_version()
    contents = (
        probe_delivery.EXPECTED_ENTRY_WORD.to_bytes(4, "big")
        + b"\x60\x00\x00\x00" * 7
        + version.build_string
        + b"\x00" * 0x20
    )
    return _build_synthetic_dol(
        version,
        include_build_string=False,
        text_sections=[(0x100, probe_delivery.EXPECTED_ENTRYPOINT, contents)],
        entry_point=probe_delivery.EXPECTED_ENTRYPOINT,
    )


def _recurring_hook_original() -> bytes:
    version = _entry_gate_version()
    entry_contents = (
        probe_delivery.EXPECTED_ENTRY_WORD.to_bytes(4, "big")
        + b"\x60\x00\x00\x00" * 7
        + version.build_string
        + b"\x00" * 0x20
    )
    hook_contents = (
        probe_delivery.RECURRING_POLL_HOOK_EXPECTED_WORD.to_bytes(4, "big")
        + b"\x4E\x80\x00\x20"
        + b"\x00" * 0x18
    )
    return _build_synthetic_dol(
        version,
        include_build_string=False,
        text_sections=[
            (0x100, probe_delivery.EXPECTED_ENTRYPOINT, entry_contents),
            (0x200, probe_delivery.RECURRING_POLL_HOOK_ADDRESS, hook_contents),
        ],
        entry_point=probe_delivery.EXPECTED_ENTRYPOINT,
    )


def _entry_gate_variant(
    *,
    instruction_word: int | None = None,
    entry_point: int = probe_delivery.EXPECTED_ENTRYPOINT,
    use_data_section: bool = False,
    map_entrypoint: bool = True,
) -> bytes:
    version = _entry_gate_version()
    if map_entrypoint:
        entry_contents = (
            (probe_delivery.EXPECTED_ENTRY_WORD if instruction_word is None else instruction_word).to_bytes(4, "big")
            + b"\x60\x00\x00\x00" * 7
            + version.build_string
            + b"\x00" * 0x20
        )
        return _build_synthetic_dol(
            version,
            include_build_string=False,
            text_sections=[] if use_data_section else [(0x100, probe_delivery.EXPECTED_ENTRYPOINT, entry_contents)],
            data_sections=[(0x100, probe_delivery.EXPECTED_ENTRYPOINT, entry_contents)] if use_data_section else None,
            entry_point=entry_point,
        )
    return _build_synthetic_dol(version, include_build_string=False, entry_point=entry_point)


def _load_build_probe_module():
    module_path = Path(__file__).resolve().parents[4].joinpath("tools", "prime3_wii_runtime", "build_probe_dol.py")
    spec = importlib.util.spec_from_file_location("prime3_build_probe_dol_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_unhooked_probe_dol_uses_first_free_text_slot() -> None:
    version = _make_fake_version()
    payload_bytes = b"\xaa" * 0x40
    manifest = _make_manifest(payload_bytes)

    result = probe_delivery.build_unhooked_probe_dol(_build_synthetic_dol(version), payload_bytes, manifest)
    header = parse_dol_header(result.probe_dol_bytes)

    assert result.probe_section.text_kind_index == 1
    assert header.sections[result.probe_section.text_slot_index].address == result.probe_section.virtual_address
    assert result.probe_section.virtual_address % manifest.required_alignment == 0


def test_build_unhooked_probe_dol_gate_disabled_by_default() -> None:
    payload_bytes = b"\xaa" * 0x40
    manifest = _make_manifest(payload_bytes)

    result = probe_delivery.build_unhooked_probe_dol(_entry_gate_original(), payload_bytes, manifest)

    assert result.checkpoint_gate is None


def test_build_unhooked_probe_dol_low_and_high_gated_output() -> None:
    payload_bytes = b"\xaa" * 0x40
    manifest = _make_manifest(payload_bytes)

    low = probe_delivery.build_unhooked_probe_dol(
        _entry_gate_original(),
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        halt_at_entry=True,
        versions=(_entry_gate_version(),),
    )
    high = probe_delivery.build_unhooked_probe_dol(
        _entry_gate_original(),
        payload_bytes,
        manifest,
        payload_virtual_address=0x817E0000,
        halt_at_entry=True,
        versions=(_entry_gate_version(),),
    )

    assert low.checkpoint_gate is not None
    assert low.probe_section.virtual_address == 0x806843C0
    assert high.checkpoint_gate is not None
    assert high.probe_section.virtual_address == 0x817E0000


def test_build_unhooked_probe_dol_supports_explicit_checkpoint_gate() -> None:
    payload_bytes = b"\xaa" * 0x40
    manifest = _make_manifest(payload_bytes)

    result = probe_delivery.build_unhooked_probe_dol(
        _entry_gate_original(),
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        halt_at_address=probe_delivery.ENTRY_GATE_ADDRESS,
        expected_halt_word=probe_delivery.EXPECTED_ENTRY_WORD,
        checkpoint_name="startup-entry",
        versions=(_entry_gate_version(),),
    )

    assert result.checkpoint_gate is not None
    assert result.checkpoint_gate.checkpoint_name == "startup-entry"
    assert result.checkpoint_gate.text_section_name == "text0"


def test_decode_entry_branch_plan_reports_expected_target_and_continuation() -> None:
    decoded = probe_delivery.decode_entry_branch_plan(_entry_gate_original())

    assert decoded.target_address == 0x8000648C
    assert decoded.continuation_address == 0x80006324
    assert decoded.absolute is False
    assert decoded.link is True


def test_build_unhooked_probe_dol_supports_entry_bootstrap_install() -> None:
    payload_bytes = b"\xaa" * 0x60
    manifest = _make_bootstrap_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT,
    )

    result = probe_delivery.build_unhooked_probe_dol(
        _entry_gate_original(),
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        install_entry_bootstrap=True,
        versions=(_entry_gate_version(),),
    )

    assert result.entry_bootstrap is not None
    assert result.entry_bootstrap.original_branch_target == 0x8000648C
    assert result.entry_bootstrap.original_continuation_address == 0x80006324
    assert result.entry_bootstrap.bootstrap_address == result.probe_section.entry_address
    assert result.entry_bootstrap.halt_loop_address == 0x806843E0
    assert result.entry_bootstrap.reserved_high == 0x817E0000


def test_build_unhooked_probe_dol_supports_relocated_runtime_install() -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT,
    )

    result = probe_delivery.build_unhooked_probe_dol(
        _entry_gate_original(),
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        install_relocated_runtime=True,
        versions=(_entry_gate_version(),),
    )

    assert result.relocated_runtime is not None
    assert result.relocated_runtime.bootstrap_mode == runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT
    assert result.relocated_runtime.runtime_destination == 0x817E1000
    assert result.relocated_runtime.runtime_entry == 0x817E1000
    assert result.relocated_runtime.runtime_blob_offset == 0x60
    assert result.relocated_runtime.runtime_blob_size == 0x260
    assert result.relocated_runtime.cache_range_start == 0x817E1000
    assert result.relocated_runtime.cache_range_size == 0x260


def test_build_unhooked_probe_dol_supports_recurring_poll_hook_install() -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT,
    )

    result = probe_delivery.build_unhooked_probe_dol(
        _recurring_hook_original(),
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        install_recurring_poll_hook=True,
        versions=(_entry_gate_version(),),
    )

    assert result.recurring_poll_hook is not None
    assert result.recurring_poll_hook.hook_address == probe_delivery.RECURRING_POLL_HOOK_ADDRESS
    assert result.recurring_poll_hook.expected_hook_instruction == probe_delivery.RECURRING_POLL_HOOK_EXPECTED_WORD
    assert result.recurring_poll_hook.wrapper_address == 0x817E1014
    assert result.recurring_poll_hook.poll_entry_address == 0x817E1004
    assert result.recurring_poll_hook.return_address == probe_delivery.RECURRING_POLL_HOOK_CONTINUATION_ADDRESS


def test_build_unhooked_probe_dol_accepts_explicit_ios_udp_transport_enable() -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
        enable_ios_udp_diagnostic=True,
    )

    result = probe_delivery.build_unhooked_probe_dol(
        _recurring_hook_original(),
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        install_recurring_poll_hook=True,
        enable_ios_udp_diagnostic=True,
        versions=(_entry_gate_version(),),
    )

    assert result.recurring_poll_hook is not None


def test_build_unhooked_probe_dol_rejects_ios_udp_transport_without_recurring_hook() -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
        enable_ios_udp_diagnostic=True,
    )

    with pytest.raises(Prime3DolPatchError, match="requires recurring poll hook installation"):
        probe_delivery.build_unhooked_probe_dol(
            _entry_gate_original(),
            payload_bytes,
            manifest,
            payload_virtual_address=0x806843C0,
            install_relocated_runtime=True,
            enable_ios_udp_diagnostic=True,
            versions=(_entry_gate_version(),),
        )


def test_build_unhooked_probe_dol_rejects_ios_udp_transport_when_manifest_disabled() -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
    )

    with pytest.raises(Prime3DolPatchError, match="Manifest does not enable the IOS UDP diagnostic transport"):
        probe_delivery.build_unhooked_probe_dol(
            _recurring_hook_original(),
            payload_bytes,
            manifest,
            payload_virtual_address=0x806843C0,
            install_recurring_poll_hook=True,
            enable_ios_udp_diagnostic=True,
            versions=(_entry_gate_version(),),
        )


def test_build_unhooked_probe_dol_rejects_high_address_outside_mem1() -> None:
    payload_bytes = b"\xaa" * 0x40
    manifest = _make_manifest(payload_bytes)

    with pytest.raises(Prime3DolPatchError, match="exceeds MEM1"):
        probe_delivery.build_unhooked_probe_dol(
            _entry_gate_original(),
            payload_bytes,
            manifest,
            payload_virtual_address=0x817FFFC8,
        )


def test_install_entry_gate_success() -> None:
    patched, result = probe_delivery.install_entry_gate(
        _entry_gate_original(),
        versions=(_entry_gate_version(),),
    )

    header = parse_dol_header(patched)
    file_offset = header.offset_for_address(probe_delivery.ENTRY_GATE_ADDRESS)
    assert file_offset is not None
    assert patched[file_offset : file_offset + 4] == probe_delivery.ENTRY_GATE_WORD.to_bytes(4, "big")
    assert result.checkpoint_name == probe_delivery.ENTRY_CHECKPOINT_NAME
    assert result.gate_address == probe_delivery.ENTRY_GATE_ADDRESS
    assert result.original_instruction == probe_delivery.EXPECTED_ENTRY_WORD
    assert result.replacement_instruction == probe_delivery.ENTRY_GATE_WORD
    assert result.entrypoint == probe_delivery.EXPECTED_ENTRYPOINT
    assert result.text_section_name == "text0"


def test_install_checkpoint_gate_success() -> None:
    patched, result = probe_delivery.install_checkpoint_gate(
        _entry_gate_original(),
        gate_address=probe_delivery.ENTRY_GATE_ADDRESS,
        expected_original_word=probe_delivery.EXPECTED_ENTRY_WORD,
        checkpoint_name="startup-entry",
        versions=(_entry_gate_version(),),
    )

    header = parse_dol_header(patched)
    file_offset = header.offset_for_address(probe_delivery.ENTRY_GATE_ADDRESS)
    assert file_offset is not None
    assert patched[file_offset : file_offset + 4] == probe_delivery.ENTRY_GATE_WORD.to_bytes(4, "big")
    assert result.checkpoint_name == "startup-entry"


def test_install_entry_gate_rejects_wrong_entrypoint() -> None:
    with pytest.raises(Prime3DolPatchError, match="Unexpected Corruption DOL entrypoint"):
        probe_delivery.install_entry_gate(
            _entry_gate_variant(entry_point=0x80004000),
            versions=(_entry_gate_version(),),
        )


def test_install_entry_gate_rejects_wrong_original_instruction() -> None:
    with pytest.raises(Prime3DolPatchError, match="expected 0x4800016d"):
        probe_delivery.install_entry_gate(
            _entry_gate_variant(instruction_word=0x60000000),
            versions=(_entry_gate_version(),),
        )


def test_install_entry_gate_rejects_already_gated_instruction() -> None:
    with pytest.raises(Prime3DolPatchError, match="already contains the replacement"):
        probe_delivery.install_entry_gate(
            _entry_gate_variant(instruction_word=probe_delivery.ENTRY_GATE_WORD),
            versions=(_entry_gate_version(),),
        )


def test_install_checkpoint_gate_rejects_unaligned_address() -> None:
    with pytest.raises(Prime3DolPatchError, match="not 4-byte aligned"):
        probe_delivery.install_checkpoint_gate(
            _entry_gate_original(),
            gate_address=probe_delivery.ENTRY_GATE_ADDRESS + 2,
            expected_original_word=probe_delivery.EXPECTED_ENTRY_WORD,
            checkpoint_name="unaligned",
            versions=(_entry_gate_version(),),
        )


def test_build_unhooked_probe_dol_rejects_incomplete_explicit_checkpoint_gate() -> None:
    payload_bytes = b"\xaa" * 0x40
    manifest = _make_manifest(payload_bytes)

    with pytest.raises(Prime3DolPatchError, match="explicit expected halt word"):
        probe_delivery.build_unhooked_probe_dol(
            _entry_gate_original(),
            payload_bytes,
            manifest,
            halt_at_address=probe_delivery.ENTRY_GATE_ADDRESS,
            checkpoint_name="missing-word",
        )


def test_build_unhooked_probe_dol_rejects_alias_and_explicit_checkpoint_mix() -> None:
    payload_bytes = b"\xaa" * 0x40
    manifest = _make_manifest(payload_bytes)

    with pytest.raises(Prime3DolPatchError, match="either --halt-at-entry or the explicit checkpoint"):
        probe_delivery.build_unhooked_probe_dol(
            _entry_gate_original(),
            payload_bytes,
            manifest,
            halt_at_entry=True,
            halt_at_address=probe_delivery.ENTRY_GATE_ADDRESS,
            expected_halt_word=probe_delivery.EXPECTED_ENTRY_WORD,
            checkpoint_name="mixed",
        )


def test_build_unhooked_probe_dol_rejects_entry_bootstrap_with_checkpoint_gate() -> None:
    payload_bytes = b"\xaa" * 0x40
    manifest = _make_bootstrap_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT,
    )

    with pytest.raises(Prime3DolPatchError, match="cannot be combined with a checkpoint gate"):
        probe_delivery.build_unhooked_probe_dol(
            _entry_gate_original(),
            payload_bytes,
            manifest,
            payload_virtual_address=0x806843C0,
            install_entry_bootstrap=True,
            halt_at_entry=True,
            versions=(_entry_gate_version(),),
        )


def test_build_unhooked_probe_dol_rejects_relocated_runtime_with_checkpoint_gate() -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT,
    )

    with pytest.raises(Prime3DolPatchError, match="cannot be combined with a checkpoint gate"):
        probe_delivery.build_unhooked_probe_dol(
            _entry_gate_original(),
            payload_bytes,
            manifest,
            payload_virtual_address=0x806843C0,
            install_relocated_runtime=True,
            halt_at_entry=True,
            versions=(_entry_gate_version(),),
        )


def test_build_unhooked_probe_dol_rejects_dual_bootstrap_install_modes() -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT,
    )

    with pytest.raises(Prime3DolPatchError, match="only one bootstrap installation mode"):
        probe_delivery.build_unhooked_probe_dol(
            _entry_gate_original(),
            payload_bytes,
            manifest,
            payload_virtual_address=0x806843C0,
            install_entry_bootstrap=True,
            install_relocated_runtime=True,
            versions=(_entry_gate_version(),),
        )


def test_build_unhooked_probe_dol_rejects_recurring_hook_with_checkpoint_gate() -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT,
    )

    with pytest.raises(Prime3DolPatchError, match="cannot be combined with a checkpoint gate"):
        probe_delivery.build_unhooked_probe_dol(
            _entry_gate_original(),
            payload_bytes,
            manifest,
            payload_virtual_address=0x806843C0,
            install_recurring_poll_hook=True,
            halt_at_entry=True,
            versions=(_entry_gate_version(),),
        )


def test_build_unhooked_probe_dol_rejects_recurring_hook_with_other_bootstrap_mode() -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT,
    )

    with pytest.raises(Prime3DolPatchError, match="only one bootstrap installation mode"):
        probe_delivery.build_unhooked_probe_dol(
            _entry_gate_original(),
            payload_bytes,
            manifest,
            payload_virtual_address=0x806843C0,
            install_relocated_runtime=True,
            install_recurring_poll_hook=True,
            versions=(_entry_gate_version(),),
        )


def test_install_entry_gate_rejects_unmapped_entrypoint() -> None:
    with pytest.raises(Prime3DolPatchError, match="not mapped"):
        probe_delivery.install_entry_gate(
            _entry_gate_variant(map_entrypoint=False),
            versions=(_entry_gate_version(),),
        )


def test_install_entry_gate_rejects_data_section_entrypoint() -> None:
    with pytest.raises(Prime3DolPatchError, match="not text"):
        probe_delivery.install_entry_gate(
            _entry_gate_variant(use_data_section=True),
            versions=(_entry_gate_version(),),
        )


def test_install_entry_gate_changes_only_one_word() -> None:
    original = _entry_gate_original()
    patched, _ = probe_delivery.install_entry_gate(
        original,
        versions=(_entry_gate_version(),),
    )

    diff_offsets = [index for index, (a, b) in enumerate(zip(original, patched, strict=True)) if a != b]
    assert diff_offsets == [0x100 + 2, 0x100 + 3]


def test_verify_probe_delivery_accepts_identical_probe_chain(tmp_path: Path) -> None:
    original_path, probe_path, extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)

    report = probe_delivery.verify_probe_delivery(
        original_dol_path=original_path,
        probe_dol_path=probe_path,
        extracted_final_dol_path=extracted_path,
        payload_bin_path=payload_path,
        payload_manifest_path=manifest_path,
    )

    assert report.delivery_chain_byte_identical is True
    assert report.original_contains_probe_section is False
    assert report.manifest_offsets_valid is True
    assert report.comparisons[1].classification == "byte-identical"


def test_verify_probe_delivery_accepts_gated_probe_chain(tmp_path: Path) -> None:
    payload_bytes = b"\xaa" * 0x40
    manifest = _make_manifest(payload_bytes)
    original_bytes = _entry_gate_original()
    built = probe_delivery.build_unhooked_probe_dol(
        original_bytes,
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        halt_at_entry=True,
        versions=(_entry_gate_version(),),
    )
    original_path = tmp_path.joinpath("original.dol")
    probe_path = tmp_path.joinpath("probe.dol")
    extracted_path = tmp_path.joinpath("extracted.dol")
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    original_path.write_bytes(original_bytes)
    probe_path.write_bytes(built.probe_dol_bytes)
    extracted_path.write_bytes(built.probe_dol_bytes)
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")

    report = probe_delivery.verify_probe_delivery(
        original_dol_path=original_path,
        probe_dol_path=probe_path,
        extracted_final_dol_path=extracted_path,
        payload_bin_path=payload_path,
        payload_manifest_path=manifest_path,
        payload_virtual_address=0x806843C0,
        halt_at_entry=True,
        versions=(_entry_gate_version(),),
    )

    assert report.checkpoint_gate is not None
    assert report.checkpoint_gate.replacement_instruction == probe_delivery.ENTRY_GATE_WORD


def test_verify_probe_delivery_accepts_entry_bootstrap_chain(tmp_path: Path) -> None:
    payload_bytes = b"\xaa" * 0x60
    manifest = _make_bootstrap_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT,
    )
    original_bytes = _entry_gate_original()
    built = probe_delivery.build_unhooked_probe_dol(
        original_bytes,
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        install_entry_bootstrap=True,
        versions=(_entry_gate_version(),),
    )
    original_path = tmp_path.joinpath("original.dol")
    probe_path = tmp_path.joinpath("probe.dol")
    extracted_path = tmp_path.joinpath("extracted.dol")
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    original_path.write_bytes(original_bytes)
    probe_path.write_bytes(built.probe_dol_bytes)
    extracted_path.write_bytes(built.probe_dol_bytes)
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")

    report = probe_delivery.verify_probe_delivery(
        original_dol_path=original_path,
        probe_dol_path=probe_path,
        extracted_final_dol_path=extracted_path,
        payload_bin_path=payload_path,
        payload_manifest_path=manifest_path,
        payload_virtual_address=0x806843C0,
        install_entry_bootstrap=True,
        versions=(_entry_gate_version(),),
    )

    assert report.entry_bootstrap is not None
    assert report.entry_bootstrap.replacement_instruction != probe_delivery.ENTRY_GATE_WORD


def test_verify_probe_delivery_accepts_relocated_runtime_chain(tmp_path: Path) -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
    )
    original_bytes = _entry_gate_original()
    built = probe_delivery.build_unhooked_probe_dol(
        original_bytes,
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        install_relocated_runtime=True,
        versions=(_entry_gate_version(),),
    )
    original_path = tmp_path.joinpath("original.dol")
    probe_path = tmp_path.joinpath("probe.dol")
    extracted_path = tmp_path.joinpath("extracted.dol")
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    original_path.write_bytes(original_bytes)
    probe_path.write_bytes(built.probe_dol_bytes)
    extracted_path.write_bytes(built.probe_dol_bytes)
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")

    report = probe_delivery.verify_probe_delivery(
        original_dol_path=original_path,
        probe_dol_path=probe_path,
        extracted_final_dol_path=extracted_path,
        payload_bin_path=payload_path,
        payload_manifest_path=manifest_path,
        payload_virtual_address=0x806843C0,
        install_relocated_runtime=True,
        versions=(_entry_gate_version(),),
    )

    assert report.relocated_runtime is not None
    assert report.relocated_runtime.runtime_destination == 0x817E1000
    assert report.relocated_runtime.runtime_entry == 0x817E1000
    assert report.relocated_runtime.replacement_instruction != probe_delivery.ENTRY_GATE_WORD


def test_verify_probe_delivery_accepts_recurring_poll_hook_chain(tmp_path: Path) -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
    )
    original_bytes = _recurring_hook_original()
    built = probe_delivery.build_unhooked_probe_dol(
        original_bytes,
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        install_recurring_poll_hook=True,
        versions=(_entry_gate_version(),),
    )
    original_path = tmp_path.joinpath("original.dol")
    probe_path = tmp_path.joinpath("probe.dol")
    extracted_path = tmp_path.joinpath("extracted.dol")
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    original_path.write_bytes(original_bytes)
    probe_path.write_bytes(built.probe_dol_bytes)
    extracted_path.write_bytes(built.probe_dol_bytes)
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")

    report = probe_delivery.verify_probe_delivery(
        original_dol_path=original_path,
        probe_dol_path=probe_path,
        extracted_final_dol_path=extracted_path,
        payload_bin_path=payload_path,
        payload_manifest_path=manifest_path,
        payload_virtual_address=0x806843C0,
        install_recurring_poll_hook=True,
        versions=(_entry_gate_version(),),
    )

    assert report.recurring_poll_hook is not None
    assert report.recurring_poll_hook.wrapper_address == 0x817E1014
    assert report.recurring_poll_hook.hook_replacement_instruction != probe_delivery.RECURRING_POLL_HOOK_EXPECTED_WORD


def test_verify_probe_delivery_accepts_explicit_ios_udp_transport_chain(tmp_path: Path) -> None:
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
        enable_ios_udp_diagnostic=True,
    )
    original_bytes = _recurring_hook_original()
    built = probe_delivery.build_unhooked_probe_dol(
        original_bytes,
        payload_bytes,
        manifest,
        payload_virtual_address=0x806843C0,
        install_recurring_poll_hook=True,
        enable_ios_udp_diagnostic=True,
        versions=(_entry_gate_version(),),
    )
    original_path = tmp_path.joinpath("original.dol")
    probe_path = tmp_path.joinpath("probe.dol")
    extracted_path = tmp_path.joinpath("extracted.dol")
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    original_path.write_bytes(original_bytes)
    probe_path.write_bytes(built.probe_dol_bytes)
    extracted_path.write_bytes(built.probe_dol_bytes)
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")

    report = probe_delivery.verify_probe_delivery(
        original_dol_path=original_path,
        probe_dol_path=probe_path,
        extracted_final_dol_path=extracted_path,
        payload_bin_path=payload_path,
        payload_manifest_path=manifest_path,
        payload_virtual_address=0x806843C0,
        install_recurring_poll_hook=True,
        enable_ios_udp_diagnostic=True,
        versions=(_entry_gate_version(),),
    )

    assert report.recurring_poll_hook is not None


def test_verify_probe_delivery_rejects_missing_appended_section(tmp_path: Path) -> None:
    original_path, _probe_path, extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    probe_path = tmp_path.joinpath("missing-probe.dol")
    probe_path.write_bytes(original_path.read_bytes())

    with pytest.raises(Prime3DolPatchError, match="does not match the expected unhooked probe-section image"):
        probe_delivery.verify_probe_delivery(
            original_dol_path=original_path,
            probe_dol_path=probe_path,
            extracted_final_dol_path=extracted_path,
            payload_bin_path=payload_path,
            payload_manifest_path=manifest_path,
        )


def test_verify_probe_delivery_rejects_changed_section_address(tmp_path: Path) -> None:
    original_path, probe_path, extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    data = bytearray(probe_path.read_bytes())
    text_slot_index = 1
    base = 0x48 + (text_slot_index * 4)
    address = int.from_bytes(data[base : base + 4], "big")
    data[base : base + 4] = (address + 0x20).to_bytes(4, "big")
    probe_path.write_bytes(bytes(data))

    with pytest.raises(Prime3DolPatchError, match="does not match the expected unhooked probe-section image"):
        probe_delivery.verify_probe_delivery(
            original_dol_path=original_path,
            probe_dol_path=probe_path,
            extracted_final_dol_path=extracted_path,
            payload_bin_path=payload_path,
            payload_manifest_path=manifest_path,
        )


def test_verify_probe_delivery_rejects_changed_payload_bytes(tmp_path: Path) -> None:
    original_path, probe_path, extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    data = bytearray(probe_path.read_bytes())
    header = parse_dol_header(data)
    slot = header.sections[1]
    data[slot.file_offset] ^= 0x01
    probe_path.write_bytes(bytes(data))

    with pytest.raises(Prime3DolPatchError, match="does not match the expected unhooked probe-section image"):
        probe_delivery.verify_probe_delivery(
            original_dol_path=original_path,
            probe_dol_path=probe_path,
            extracted_final_dol_path=extracted_path,
            payload_bin_path=payload_path,
            payload_manifest_path=manifest_path,
        )


def test_verify_probe_delivery_rejects_changed_payload_length(tmp_path: Path) -> None:
    original_path, probe_path, extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    probe_path.write_bytes(probe_path.read_bytes()[:-4])

    with pytest.raises(Prime3DolPatchError):
        probe_delivery.verify_probe_delivery(
            original_dol_path=original_path,
            probe_dol_path=probe_path,
            extracted_final_dol_path=extracted_path,
            payload_bin_path=payload_path,
            payload_manifest_path=manifest_path,
        )


def test_verify_probe_delivery_rejects_wrong_payload_hash(tmp_path: Path) -> None:
    original_path, probe_path, extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    manifest = runtime_payload.Prime3RuntimePayloadManifest.from_json_text(manifest_path.read_text(encoding="utf-8"))
    raw = manifest.to_json_dict()
    raw["payload_sha256"] = "0" * 64
    json_text = json.dumps(raw, indent=2, sort_keys=True) + "\n"
    manifest_path.write_text(json_text, encoding="utf-8")
    assert json_text

    with pytest.raises(Prime3DolPatchError, match="Payload hash mismatch"):
        probe_delivery.verify_probe_delivery(
            original_dol_path=original_path,
            probe_dol_path=probe_path,
            extracted_final_dol_path=extracted_path,
            payload_bin_path=payload_path,
            payload_manifest_path=manifest_path,
        )


def test_verify_probe_delivery_rejects_malformed_manifest(tmp_path: Path) -> None:
    original_path, probe_path, extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    manifest_path.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(Prime3DolPatchError, match="Invalid Prime 3 runtime payload manifest JSON"):
        probe_delivery.verify_probe_delivery(
            original_dol_path=original_path,
            probe_dol_path=probe_path,
            extracted_final_dol_path=extracted_path,
            payload_bin_path=payload_path,
            payload_manifest_path=manifest_path,
        )


def test_verify_probe_delivery_rejects_malformed_dol(tmp_path: Path) -> None:
    original_path, probe_path, extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    extracted_path.write_bytes(b"\x00" * 0x10)

    with pytest.raises(Prime3DolPatchError, match="truncated before the header"):
        probe_delivery.verify_probe_delivery(
            original_dol_path=original_path,
            probe_dol_path=probe_path,
            extracted_final_dol_path=extracted_path,
            payload_bin_path=payload_path,
            payload_manifest_path=manifest_path,
        )


def test_verify_probe_delivery_reports_structurally_related_but_non_identical_dol(tmp_path: Path) -> None:
    original_path, probe_path, _extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    extracted_bytes = bytearray(probe_path.read_bytes())
    extracted_bytes[-1] ^= 0x01
    extracted_path = tmp_path.joinpath("extracted-related.dol")
    extracted_path.write_bytes(bytes(extracted_bytes))

    report = probe_delivery.verify_probe_delivery(
        original_dol_path=original_path,
        probe_dol_path=probe_path,
        extracted_final_dol_path=extracted_path,
        payload_bin_path=payload_path,
        payload_manifest_path=manifest_path,
    )

    assert report.delivery_chain_byte_identical is False
    assert report.comparisons[1].classification == "structurally identical with expected unrelated differences"


def test_verify_probe_delivery_json_is_deterministic(tmp_path: Path) -> None:
    original_path, probe_path, extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)

    first = probe_delivery.verify_probe_delivery(
        original_dol_path=original_path,
        probe_dol_path=probe_path,
        extracted_final_dol_path=extracted_path,
        payload_bin_path=payload_path,
        payload_manifest_path=manifest_path,
    ).to_json_text()
    second = probe_delivery.verify_probe_delivery(
        original_dol_path=original_path,
        probe_dol_path=probe_path,
        extracted_final_dol_path=extracted_path,
        payload_bin_path=payload_path,
        payload_manifest_path=manifest_path,
    ).to_json_text()

    assert first == second


def test_build_probe_dol_script_writes_report(tmp_path: Path) -> None:
    module = _load_build_probe_module()
    original_path, _probe_path, _extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    output_dol = tmp_path.joinpath("script-probe.dol")
    report_path = tmp_path.joinpath("script-probe.json")

    sys.argv = [
        "build_probe_dol.py",
        "--original-dol",
        str(original_path),
        "--output-dol",
        str(output_dol),
        "--payload-bin",
        str(payload_path),
        "--payload-manifest",
        str(manifest_path),
        "--report",
        str(report_path),
    ]
    module.main()

    assert output_dol.is_file()
    assert report_path.is_file()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert "checkpoint_gate" not in payload


def test_build_probe_dol_script_rejects_input_output_collision(tmp_path: Path) -> None:
    module = _load_build_probe_module()
    original_path, _probe_path, _extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    report_path = tmp_path.joinpath("script-probe.json")

    sys.argv = [
        "build_probe_dol.py",
        "--original-dol",
        str(original_path),
        "--output-dol",
        str(original_path),
        "--payload-bin",
        str(payload_path),
        "--payload-manifest",
        str(manifest_path),
        "--report",
        str(report_path),
    ]
    with pytest.raises(RuntimeError, match="must differ"):
        module.main()


def test_build_probe_dol_script_rejects_partial_explicit_checkpoint_gate(tmp_path: Path) -> None:
    module = _load_build_probe_module()
    original_path, _probe_path, _extracted_path, payload_path, manifest_path = _write_inputs(tmp_path)
    output_dol = tmp_path.joinpath("script-probe.dol")
    report_path = tmp_path.joinpath("script-probe.json")

    sys.argv = [
        "build_probe_dol.py",
        "--original-dol",
        str(original_path),
        "--output-dol",
        str(output_dol),
        "--payload-bin",
        str(payload_path),
        "--payload-manifest",
        str(manifest_path),
        "--report",
        str(report_path),
        "--halt-at-address",
        hex(probe_delivery.ENTRY_GATE_ADDRESS),
        "--checkpoint-name",
        "missing-word",
    ]
    with pytest.raises(Prime3DolPatchError, match="explicit expected halt word"):
        module.main()


def test_build_probe_dol_script_writes_entry_bootstrap_report(tmp_path: Path) -> None:
    module = _load_build_probe_module()
    payload_bytes = b"\xaa" * 0x60
    manifest = _make_bootstrap_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT,
    )
    original_path = tmp_path.joinpath("original.dol")
    output_dol = tmp_path.joinpath("bootstrap-probe.dol")
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    report_path = tmp_path.joinpath("bootstrap-probe.json")
    original_path.write_bytes(_entry_gate_original())
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")
    original_build_unhooked_probe_dol = module.build_unhooked_probe_dol

    def _patched_build_unhooked_probe_dol(*args, **kwargs):
        kwargs.setdefault("versions", (_entry_gate_version(),))
        return original_build_unhooked_probe_dol(*args, **kwargs)

    module.build_unhooked_probe_dol = _patched_build_unhooked_probe_dol

    sys.argv = [
        "build_probe_dol.py",
        "--original-dol",
        str(original_path),
        "--output-dol",
        str(output_dol),
        "--payload-bin",
        str(payload_path),
        "--payload-manifest",
        str(manifest_path),
        "--report",
        str(report_path),
        "--payload-address",
        "0x806843C0",
        "--install-entry-bootstrap",
    ]
    module.main()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["entry_bootstrap"]["original_branch_target"] == 0x8000648C


def test_build_probe_dol_script_writes_relocated_runtime_report(tmp_path: Path) -> None:
    module = _load_build_probe_module()
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT,
    )
    original_path = tmp_path.joinpath("original.dol")
    output_dol = tmp_path.joinpath("relocated-probe.dol")
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    report_path = tmp_path.joinpath("relocated-probe.json")
    original_path.write_bytes(_entry_gate_original())
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")
    original_build_unhooked_probe_dol = module.build_unhooked_probe_dol

    def _patched_build_unhooked_probe_dol(*args, **kwargs):
        kwargs.setdefault("versions", (_entry_gate_version(),))
        return original_build_unhooked_probe_dol(*args, **kwargs)

    module.build_unhooked_probe_dol = _patched_build_unhooked_probe_dol

    sys.argv = [
        "build_probe_dol.py",
        "--original-dol",
        str(original_path),
        "--output-dol",
        str(output_dol),
        "--payload-bin",
        str(payload_path),
        "--payload-manifest",
        str(manifest_path),
        "--report",
        str(report_path),
        "--payload-address",
        "0x806843C0",
        "--install-relocated-runtime",
    ]
    module.main()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["relocated_runtime"]["runtime_destination"] == 0x817E1000
    assert payload["relocated_runtime"]["runtime_blob_size"] == 0x260


def test_build_probe_dol_script_writes_recurring_poll_hook_report(tmp_path: Path) -> None:
    module = _load_build_probe_module()
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT,
    )
    original_path = tmp_path.joinpath("original.dol")
    output_dol = tmp_path.joinpath("recurring-hook-probe.dol")
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    report_path = tmp_path.joinpath("recurring-hook-probe.json")
    original_path.write_bytes(_recurring_hook_original())
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")
    original_build_unhooked_probe_dol = module.build_unhooked_probe_dol

    def _patched_build_unhooked_probe_dol(*args, **kwargs):
        kwargs.setdefault("versions", (_entry_gate_version(),))
        return original_build_unhooked_probe_dol(*args, **kwargs)

    module.build_unhooked_probe_dol = _patched_build_unhooked_probe_dol

    sys.argv = [
        "build_probe_dol.py",
        "--original-dol",
        str(original_path),
        "--output-dol",
        str(output_dol),
        "--payload-bin",
        str(payload_path),
        "--payload-manifest",
        str(manifest_path),
        "--report",
        str(report_path),
        "--payload-address",
        "0x806843C0",
        "--install-recurring-poll-hook",
    ]
    module.main()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["recurring_poll_hook"]["hook_address"] == probe_delivery.RECURRING_POLL_HOOK_ADDRESS
    assert payload["recurring_poll_hook"]["wrapper_address"] == 0x817E1014


def test_build_probe_dol_script_reports_explicit_ios_udp_transport_enable(tmp_path: Path) -> None:
    module = _load_build_probe_module()
    payload_bytes = b"\xaa" * 0x60 + b"\xbb" * 0x260
    manifest = _make_relocated_manifest(
        payload_bytes,
        mode=runtime_payload.PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
        enable_ios_udp_diagnostic=True,
    )
    original_path = tmp_path.joinpath("original.dol")
    output_dol = tmp_path.joinpath("transport-probe.dol")
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    report_path = tmp_path.joinpath("transport-probe.json")
    original_path.write_bytes(_recurring_hook_original())
    payload_path.write_bytes(payload_bytes)
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")
    original_build_unhooked_probe_dol = module.build_unhooked_probe_dol

    def _patched_build_unhooked_probe_dol(*args, **kwargs):
        kwargs.setdefault("versions", (_entry_gate_version(),))
        return original_build_unhooked_probe_dol(*args, **kwargs)

    module.build_unhooked_probe_dol = _patched_build_unhooked_probe_dol

    sys.argv = [
        "build_probe_dol.py",
        "--original-dol",
        str(original_path),
        "--output-dol",
        str(output_dol),
        "--payload-bin",
        str(payload_path),
        "--payload-manifest",
        str(manifest_path),
        "--report",
        str(report_path),
        "--payload-address",
        "0x806843C0",
        "--install-recurring-poll-hook",
        "--enable-ios-udp-diagnostic",
    ]
    module.main()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["ios_udp_diagnostic_enabled"] is True
