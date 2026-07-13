from __future__ import annotations

import dataclasses
import hashlib
import json
from typing import TYPE_CHECKING, Any

from randovania.games.prime3.exporter.dol_patcher import (
    DolHeader,
    Prime3DolPatchError,
    align_up,
    append_executable_text_section,
    parse_dol_header,
)
from randovania.games.prime3.exporter.runtime_payload import Prime3RuntimePayloadManifest

if TYPE_CHECKING:
    from pathlib import Path


@dataclasses.dataclass(frozen=True)
class Prime3ProbeSection:
    text_slot_index: int
    text_kind_index: int
    file_offset: int
    virtual_address: int
    payload_size: int
    entry_address: int
    canary_address: int | None
    canary_size: int | None
    counter_address: int | None
    counter_size: int | None
    payload_sha256: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "text_slot_index": self.text_slot_index,
            "text_kind_index": self.text_kind_index,
            "file_offset": self.file_offset,
            "virtual_address": self.virtual_address,
            "payload_size": self.payload_size,
            "entry_address": self.entry_address,
            "canary_address": self.canary_address,
            "canary_size": self.canary_size,
            "counter_address": self.counter_address,
            "counter_size": self.counter_size,
            "payload_sha256": self.payload_sha256,
        }


@dataclasses.dataclass(frozen=True)
class ProbeDolBuildResult:
    probe_dol_bytes: bytes
    probe_section: Prime3ProbeSection


@dataclasses.dataclass(frozen=True)
class FileIdentity:
    label: str
    path: str
    size: int
    sha256: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "path": self.path,
            "size": self.size,
            "sha256": self.sha256,
        }


@dataclasses.dataclass(frozen=True)
class ChangedRange:
    file_offset: int
    length: int
    classification: str
    section_name: str | None
    virtual_address: int | None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "file_offset": self.file_offset,
            "length": self.length,
            "classification": self.classification,
            "section_name": self.section_name,
            "virtual_address": self.virtual_address,
        }


@dataclasses.dataclass(frozen=True)
class DolComparison:
    left_label: str
    right_label: str
    left_sha256: str
    right_sha256: str
    byte_identical: bool
    section_table_identical: bool
    classification: str
    changed_ranges: tuple[ChangedRange, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "left_label": self.left_label,
            "right_label": self.right_label,
            "left_sha256": self.left_sha256,
            "right_sha256": self.right_sha256,
            "byte_identical": self.byte_identical,
            "section_table_identical": self.section_table_identical,
            "classification": self.classification,
            "changed_ranges": [item.to_json_dict() for item in self.changed_ranges],
        }


@dataclasses.dataclass(frozen=True)
class ProbeDeliveryVerification:
    original_dol: FileIdentity
    probe_dol: FileIdentity
    extracted_final_dol: FileIdentity
    payload_bin: FileIdentity
    payload_manifest: FileIdentity
    probe_section: Prime3ProbeSection
    original_contains_probe_section: bool
    manifest_offsets_valid: bool
    comparisons: tuple[DolComparison, ...]
    delivery_chain_byte_identical: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "original_dol": self.original_dol.to_json_dict(),
            "probe_dol": self.probe_dol.to_json_dict(),
            "extracted_final_dol": self.extracted_final_dol.to_json_dict(),
            "payload_bin": self.payload_bin.to_json_dict(),
            "payload_manifest": self.payload_manifest.to_json_dict(),
            "probe_section": self.probe_section.to_json_dict(),
            "original_contains_probe_section": self.original_contains_probe_section,
            "manifest_offsets_valid": self.manifest_offsets_valid,
            "comparisons": [item.to_json_dict() for item in self.comparisons],
            "delivery_chain_byte_identical": self.delivery_chain_byte_identical,
        }

    def to_json_text(self) -> str:
        return json.dumps(self.to_json_dict(), indent=2, sort_keys=True) + "\n"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identify_probe_virtual_address(header: DolHeader, required_alignment: int) -> int:
    highest_mapped_end = max(
        [section.end_address for section in header.sections if section.size > 0],
        default=header.bss_end_address,
    )
    return align_up(max(highest_mapped_end, header.bss_end_address), required_alignment)


def build_unhooked_probe_dol(
    original_dol_bytes: bytes,
    payload_bytes: bytes,
    manifest: Prime3RuntimePayloadManifest,
) -> ProbeDolBuildResult:
    manifest.validate()
    if len(payload_bytes) != manifest.payload_size:
        raise Prime3DolPatchError(
            f"Payload size mismatch: manifest expects {manifest.payload_size}, got {len(payload_bytes)}."
        )
    actual_sha256 = _sha256_bytes(payload_bytes)
    if actual_sha256 != manifest.payload_sha256:
        raise Prime3DolPatchError(
            f"Payload hash mismatch: manifest expects {manifest.payload_sha256}, got {actual_sha256}."
        )

    header = parse_dol_header(original_dol_bytes)
    payload_virtual_address = identify_probe_virtual_address(header, manifest.required_alignment)
    probe_dol_bytes, insert_result = append_executable_text_section(
        original_dol_bytes,
        payload_bytes=payload_bytes,
        payload_virtual_address=payload_virtual_address,
        required_alignment=manifest.required_alignment,
        entry_symbol_offset=manifest.entry_symbol_offset,
    )

    probe_section = Prime3ProbeSection(
        text_slot_index=insert_result.text_slot_index,
        text_kind_index=insert_result.text_kind_index,
        file_offset=insert_result.file_offset,
        virtual_address=insert_result.virtual_address,
        payload_size=insert_result.payload_size,
        entry_address=insert_result.entry_symbol_address or payload_virtual_address,
        canary_address=(
            payload_virtual_address + manifest.canary_start_offset if manifest.canary_start_offset is not None else None
        ),
        canary_size=manifest.canary_size,
        counter_address=(
            payload_virtual_address + manifest.counter_offset if manifest.counter_offset is not None else None
        ),
        counter_size=manifest.counter_size,
        payload_sha256=manifest.payload_sha256,
    )
    return ProbeDolBuildResult(probe_dol_bytes=probe_dol_bytes, probe_section=probe_section)


def verify_probe_delivery(
    *,
    original_dol_path: Path,
    probe_dol_path: Path,
    extracted_final_dol_path: Path,
    payload_bin_path: Path,
    payload_manifest_path: Path,
) -> ProbeDeliveryVerification:
    original_dol_bytes = original_dol_path.read_bytes()
    probe_dol_bytes = probe_dol_path.read_bytes()
    extracted_dol_bytes = extracted_final_dol_path.read_bytes()
    payload_bytes = payload_bin_path.read_bytes()
    manifest_text = payload_manifest_path.read_text(encoding="utf-8")
    manifest = Prime3RuntimePayloadManifest.from_json_text(manifest_text)

    build_result = build_unhooked_probe_dol(original_dol_bytes, payload_bytes, manifest)
    if build_result.probe_dol_bytes != probe_dol_bytes:
        raise Prime3DolPatchError(
            "Probe DOL does not match the expected unhooked probe-section image for the given original DOL and payload."
        )

    probe_section = build_result.probe_section
    original_header = parse_dol_header(original_dol_bytes)
    probe_header = parse_dol_header(probe_dol_bytes)
    extracted_header = parse_dol_header(extracted_dol_bytes)

    original_slot = original_header.sections[probe_section.text_slot_index]
    if not original_slot.is_empty:
        raise Prime3DolPatchError(
            f"Original DOL already uses text slot {probe_section.text_kind_index}, expected it to be empty."
        )

    probe_slot = probe_header.sections[probe_section.text_slot_index]
    if probe_slot.address != probe_section.virtual_address:
        raise Prime3DolPatchError(
            f"Probe DOL text slot address 0x{probe_slot.address:08x} does not match expected "
            f"0x{probe_section.virtual_address:08x}."
        )
    if probe_slot.file_offset != probe_section.file_offset:
        raise Prime3DolPatchError(
            f"Probe DOL text slot file offset 0x{probe_slot.file_offset:08x} does not match expected "
            f"0x{probe_section.file_offset:08x}."
        )
    if probe_slot.size != probe_section.payload_size:
        raise Prime3DolPatchError(
            f"Probe DOL text slot size 0x{probe_slot.size:x} does not match expected 0x{probe_section.payload_size:x}."
        )
    observed_probe_payload = probe_dol_bytes[
        probe_section.file_offset : probe_section.file_offset + probe_section.payload_size
    ]
    if observed_probe_payload != payload_bytes:
        raise Prime3DolPatchError("Probe DOL payload bytes do not match the supplied payload binary.")

    manifest_offsets_valid = _manifest_offsets_valid(manifest, probe_section)
    original_contains_probe_section = _original_contains_probe_section(
        original_dol_bytes,
        original_header,
        probe_section,
    )

    comparisons = (
        _compare_dols("original", original_dol_bytes, original_header, "probe", probe_dol_bytes, probe_header),
        _compare_dols("probe", probe_dol_bytes, probe_header, "extracted_final", extracted_dol_bytes, extracted_header),
        _compare_dols(
            "original",
            original_dol_bytes,
            original_header,
            "extracted_final",
            extracted_dol_bytes,
            extracted_header,
        ),
    )

    return ProbeDeliveryVerification(
        original_dol=_file_identity("original", original_dol_path, original_dol_bytes),
        probe_dol=_file_identity("probe", probe_dol_path, probe_dol_bytes),
        extracted_final_dol=_file_identity("extracted_final", extracted_final_dol_path, extracted_dol_bytes),
        payload_bin=_file_identity("payload_bin", payload_bin_path, payload_bytes),
        payload_manifest=_file_identity("payload_manifest", payload_manifest_path, manifest_text.encode("utf-8")),
        probe_section=probe_section,
        original_contains_probe_section=original_contains_probe_section,
        manifest_offsets_valid=manifest_offsets_valid,
        comparisons=comparisons,
        delivery_chain_byte_identical=(
            comparisons[1].byte_identical
            and comparisons[1].section_table_identical
            and extracted_dol_bytes[probe_section.file_offset : probe_section.file_offset + probe_section.payload_size]
            == payload_bytes
        ),
    )


def _file_identity(label: str, path: Path, data: bytes) -> FileIdentity:
    return FileIdentity(label=label, path=str(path), size=len(data), sha256=_sha256_bytes(data))


def _manifest_offsets_valid(manifest: Prime3RuntimePayloadManifest, probe_section: Prime3ProbeSection) -> bool:
    if manifest.canary_start_offset is not None:
        expected_canary = probe_section.virtual_address + manifest.canary_start_offset
        if probe_section.canary_address != expected_canary or probe_section.canary_size != manifest.canary_size:
            return False
    if manifest.counter_offset is not None:
        expected_counter = probe_section.virtual_address + manifest.counter_offset
        if probe_section.counter_address != expected_counter or probe_section.counter_size != manifest.counter_size:
            return False
    return True


def _original_contains_probe_section(
    original_dol_bytes: bytes,
    original_header: DolHeader,
    probe_section: Prime3ProbeSection,
) -> bool:
    slot = original_header.sections[probe_section.text_slot_index]
    if slot.size == probe_section.payload_size and slot.address == probe_section.virtual_address:
        payload_bytes = original_dol_bytes[slot.file_offset : slot.file_offset + slot.size]
        return _sha256_bytes(payload_bytes) == probe_section.payload_sha256
    return False


def _header_signature(header: DolHeader) -> tuple[tuple[int, int, int], ...]:
    return tuple((section.file_offset, section.address, section.size) for section in header.sections)


def _compare_dols(
    left_label: str,
    left_bytes: bytes,
    left_header: DolHeader,
    right_label: str,
    right_bytes: bytes,
    right_header: DolHeader,
) -> DolComparison:
    changed_ranges = _changed_ranges(left_bytes, right_bytes, left_header)
    byte_identical = left_bytes == right_bytes
    section_table_identical = _header_signature(left_header) == _header_signature(right_header)
    if byte_identical:
        classification = "byte-identical"
    elif section_table_identical:
        classification = "structurally identical with expected unrelated differences"
    else:
        classification = "materially different"
    return DolComparison(
        left_label=left_label,
        right_label=right_label,
        left_sha256=_sha256_bytes(left_bytes),
        right_sha256=_sha256_bytes(right_bytes),
        byte_identical=byte_identical,
        section_table_identical=section_table_identical,
        classification=classification,
        changed_ranges=changed_ranges,
    )


def _changed_ranges(left_bytes: bytes, right_bytes: bytes, left_header: DolHeader) -> tuple[ChangedRange, ...]:
    max_size = max(len(left_bytes), len(right_bytes))
    ranges: list[ChangedRange] = []
    start: int | None = None
    for offset in range(max_size):
        left_byte = left_bytes[offset] if offset < len(left_bytes) else None
        right_byte = right_bytes[offset] if offset < len(right_bytes) else None
        if left_byte != right_byte:
            if start is None:
                start = offset
        elif start is not None:
            ranges.append(_build_changed_range(start, offset, left_header, len(left_bytes)))
            start = None
    if start is not None:
        ranges.append(_build_changed_range(start, max_size, left_header, len(left_bytes)))
    return tuple(ranges)


def _build_changed_range(start: int, end: int, left_header: DolHeader, left_size: int) -> ChangedRange:
    classification, section_name, virtual_address = _classify_offset(start, left_header, left_size)
    return ChangedRange(
        file_offset=start,
        length=end - start,
        classification=classification,
        section_name=section_name,
        virtual_address=virtual_address,
    )


def _classify_offset(offset: int, header: DolHeader, original_size: int) -> tuple[str, str | None, int | None]:
    if offset < 0x100:
        return "header", None, None
    if offset >= original_size:
        return "newly appended region", None, None
    section = header.section_for_offset(offset)
    if section is None:
        return "unmapped file region", None, None
    return section.kind, section.name, header.address_for_offset(offset)
