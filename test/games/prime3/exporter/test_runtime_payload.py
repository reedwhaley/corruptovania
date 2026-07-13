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


def test_runtime_payload_manifest_rejects_partial_probe_metadata() -> None:
    manifest = _make_manifest(b"\x4e\x80\x00\x20" * 16)
    raw = manifest.to_json_dict()
    raw["canary_start_offset"] = 0x10

    with pytest.raises(Prime3DolPatchError, match="provide both canary_start_offset"):
        runtime_payload.Prime3RuntimePayloadManifest.from_json_dict(raw)
