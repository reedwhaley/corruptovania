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
