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
