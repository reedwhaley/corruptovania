from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

_NUM_TEXT_SECTIONS = 7
_NUM_DATA_SECTIONS = 11
_NUM_SECTIONS = _NUM_TEXT_SECTIONS + _NUM_DATA_SECTIONS
_HEADER_SIZE = 0x100
_ZERO_RUN_THRESHOLD = 32


class DolAnalysisError(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class DolSection:
    kind: str
    index: int
    offset: int
    address: int
    size: int

    @property
    def end_offset(self) -> int:
        return self.offset + self.size

    @property
    def end_address(self) -> int:
        return self.address + self.size

    @property
    def name(self) -> str:
        return f"{self.kind}{self.index}"


@dataclasses.dataclass(frozen=True)
class DolHeader:
    sections: tuple[DolSection, ...]
    bss_address: int
    bss_size: int
    entry_point: int

    def section_for_offset(self, offset: int) -> DolSection | None:
        for section in self.sections:
            if section.offset <= offset < section.end_offset:
                return section
        return None

    def section_for_address(self, address: int) -> DolSection | None:
        for section in self.sections:
            if section.address <= address < section.end_address:
                return section
        return None

    def address_for_offset(self, offset: int) -> int | None:
        section = self.section_for_offset(offset)
        if section is None:
            return None
        return section.address + (offset - section.offset)

    def offset_for_address(self, address: int) -> int | None:
        section = self.section_for_address(address)
        if section is None:
            return None
        return section.offset + (address - section.address)


@dataclasses.dataclass(frozen=True)
class MetadataSpan:
    name: str
    start_address: int
    length: int
    category: str = "metadata"
    description: str | None = None

    @property
    def end_address(self) -> int:
        return self.start_address + self.length


@dataclasses.dataclass(frozen=True)
class RangeAnnotation:
    name: str
    category: str
    start_address: int
    length: int
    description: str | None = None


@dataclasses.dataclass(frozen=True)
class ChangedRange:
    start: int
    end: int
    classification: str
    section_name: str | None
    virtual_address: int | None
    length: int
    annotations: tuple[RangeAnnotation, ...] = ()


@dataclasses.dataclass(frozen=True)
class DecodedBranch:
    instruction_offset: int
    instruction_address: int
    instruction_word: int
    mnemonic: str
    absolute: bool
    link: bool
    target_address: int
    target_classification: str
    target_section_name: str | None
    target_in_changed_region: bool
    target_changed_range_classification: str | None = None
    target_changed_range_section_name: str | None = None
    target_annotations: tuple[RangeAnnotation, ...] = ()


@dataclasses.dataclass(frozen=True)
class ZeroCandidateRegion:
    section_name: str
    file_offset: int
    virtual_address: int
    length: int


@dataclasses.dataclass(frozen=True)
class DolDiffReport:
    original_path: str
    patched_path: str
    original_size: int
    patched_size: int
    original_sha256: str
    patched_sha256: str
    original_header: DolHeader
    patched_header: DolHeader
    section_mappings_changed: bool
    changed_ranges: tuple[ChangedRange, ...]
    decoded_branches: tuple[DecodedBranch, ...]
    zero_candidates: tuple[ZeroCandidateRegion, ...]


@dataclasses.dataclass(frozen=True)
class DolFileIdentity:
    label: str
    path: str
    size: int
    sha256: str
    header: DolHeader


@dataclasses.dataclass(frozen=True)
class ComparisonSummary:
    label: str
    left_label: str
    right_label: str
    report: DolDiffReport
    total_changed_bytes: int
    changed_range_count: int
    changed_bytes_by_classification: tuple[tuple[str, int], ...]
    changed_bytes_by_section: tuple[tuple[str, int], ...]
    has_text_changes: bool
    has_data_changes: bool
    has_header_changes: bool
    has_appended_changes: bool
    has_unmapped_changes: bool
    is_data_only: bool


@dataclasses.dataclass(frozen=True)
class ThreeWayDolDiffReport:
    files: tuple[DolFileIdentity, ...]
    comparisons: tuple[ComparisonSummary, ...]


def _read_u32_be(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_dol_header(data: bytes) -> DolHeader:
    if len(data) < _HEADER_SIZE:
        raise DolAnalysisError(f"DOL header requires {_HEADER_SIZE} bytes, got {len(data)}")

    offsets = [_read_u32_be(data, i * 4) for i in range(_NUM_SECTIONS)]
    addresses = [_read_u32_be(data, 0x48 + (i * 4)) for i in range(_NUM_SECTIONS)]
    sizes = [_read_u32_be(data, 0x90 + (i * 4)) for i in range(_NUM_SECTIONS)]

    sections: list[DolSection] = []
    for i in range(_NUM_SECTIONS):
        offset = offsets[i]
        address = addresses[i]
        size = sizes[i]
        if size == 0:
            if offset != 0 or address != 0:
                raise DolAnalysisError(
                    f"Section slot {i} has zero size but non-zero offset/address: "
                    f"offset=0x{offset:x} address=0x{address:x}"
                )
            continue
        if offset < _HEADER_SIZE:
            raise DolAnalysisError(f"Section slot {i} starts inside the DOL header: 0x{offset:x}")
        if address == 0:
            raise DolAnalysisError(f"Section slot {i} has size 0x{size:x} but zero virtual address")
        if offset + size < offset:
            raise DolAnalysisError(f"Section slot {i} file range overflows")
        if address + size < address:
            raise DolAnalysisError(f"Section slot {i} virtual address range overflows")

        kind = "text" if i < _NUM_TEXT_SECTIONS else "data"
        index = i if kind == "text" else i - _NUM_TEXT_SECTIONS
        sections.append(DolSection(kind=kind, index=index, offset=offset, address=address, size=size))

    sorted_by_offset = sorted(sections, key=lambda item: item.offset)
    for first, second in zip(sorted_by_offset, sorted_by_offset[1:]):
        if second.offset < first.end_offset:
            raise DolAnalysisError(
                f"Overlapping section file ranges: {first.name} 0x{first.offset:x}-0x{first.end_offset:x} and "
                f"{second.name} 0x{second.offset:x}-0x{second.end_offset:x}"
            )

    sorted_by_address = sorted(sections, key=lambda item: item.address)
    for first, second in zip(sorted_by_address, sorted_by_address[1:]):
        if second.address < first.end_address:
            raise DolAnalysisError(
                f"Overlapping section virtual ranges: {first.name} 0x{first.address:x}-0x{first.end_address:x} and "
                f"{second.name} 0x{second.address:x}-0x{second.end_address:x}"
            )

    return DolHeader(
        sections=tuple(sections),
        bss_address=_read_u32_be(data, 0xD8),
        bss_size=_read_u32_be(data, 0xDC),
        entry_point=_read_u32_be(data, 0xE0),
    )


def parse_dol_file(path: Path) -> tuple[DolHeader, bytes]:
    data = path.read_bytes()
    return parse_dol_header(data), data


def _annotations_for_region(
    virtual_address: int | None,
    length: int,
    metadata_spans: Sequence[MetadataSpan],
) -> tuple[RangeAnnotation, ...]:
    if virtual_address is None or length == 0:
        return ()

    end_address = virtual_address + length
    annotations = []
    for span in metadata_spans:
        if virtual_address < span.end_address and span.start_address < end_address:
            annotations.append(
                RangeAnnotation(
                    name=span.name,
                    category=span.category,
                    start_address=span.start_address,
                    length=span.length,
                    description=span.description,
                )
            )
    return tuple(annotations)


def _classify_offset(offset: int, original_header: DolHeader, original_size: int) -> tuple[str, str | None, int | None]:
    if offset < _HEADER_SIZE:
        return "header", None, None
    if offset >= original_size:
        return "newly appended region", None, None
    section = original_header.section_for_offset(offset)
    if section is None:
        return "unmapped file region", None, None
    return section.kind, section.name, original_header.address_for_offset(offset)


def group_changed_ranges(
    original_data: bytes,
    patched_data: bytes,
    original_header: DolHeader,
    metadata_spans: Sequence[MetadataSpan] = (),
) -> tuple[ChangedRange, ...]:
    max_size = max(len(original_data), len(patched_data))
    ranges: list[ChangedRange] = []
    start: int | None = None
    for offset in range(max_size):
        original_byte = original_data[offset] if offset < len(original_data) else None
        patched_byte = patched_data[offset] if offset < len(patched_data) else None
        if original_byte != patched_byte:
            if start is None:
                start = offset
        elif start is not None:
            classification, section_name, virtual_address = _classify_offset(start, original_header, len(original_data))
            length = offset - start
            ranges.append(
                ChangedRange(
                    start=start,
                    end=offset,
                    classification=classification,
                    section_name=section_name,
                    virtual_address=virtual_address,
                    length=length,
                    annotations=_annotations_for_region(virtual_address, length, metadata_spans),
                )
            )
            start = None
    if start is not None:
        classification, section_name, virtual_address = _classify_offset(start, original_header, len(original_data))
        length = max_size - start
        ranges.append(
            ChangedRange(
                start=start,
                end=max_size,
                classification=classification,
                section_name=section_name,
                virtual_address=virtual_address,
                length=length,
                annotations=_annotations_for_region(virtual_address, length, metadata_spans),
            )
        )
    return tuple(ranges)


def _section_signature(header: DolHeader) -> tuple[tuple[str, int, int, int], ...]:
    return tuple((section.name, section.offset, section.address, section.size) for section in header.sections)


def decode_unconditional_branch(instruction_word: int, instruction_address: int) -> DecodedBranch | None:
    opcode = instruction_word >> 26
    if opcode != 18:
        return None

    li_field = instruction_word & 0x03FFFFFC
    if li_field & 0x02000000:
        li_field -= 0x04000000
    absolute = bool(instruction_word & 0x2)
    link = bool(instruction_word & 0x1)
    target_address = li_field if absolute else instruction_address + li_field
    mnemonic = "bl" if link else "b"
    if absolute:
        mnemonic += "a"
    return DecodedBranch(
        instruction_offset=-1,
        instruction_address=instruction_address,
        instruction_word=instruction_word,
        mnemonic=mnemonic,
        absolute=absolute,
        link=link,
        target_address=target_address,
        target_classification="",
        target_section_name=None,
        target_in_changed_region=False,
    )


def _changed_range_for_address(target_address: int, changed_ranges: Sequence[ChangedRange]) -> ChangedRange | None:
    for changed_range in changed_ranges:
        if changed_range.virtual_address is None:
            continue
        if changed_range.virtual_address <= target_address < changed_range.virtual_address + changed_range.length:
            return changed_range
    return None


def _classify_branch_target(
    target_address: int,
    original_header: DolHeader,
    patched_header: DolHeader,
    changed_ranges: Sequence[ChangedRange],
    metadata_spans: Sequence[MetadataSpan],
) -> tuple[str, str | None, bool, str | None, str | None, tuple[RangeAnnotation, ...]]:
    changed_range = _changed_range_for_address(target_address, changed_ranges)
    target_annotations = _annotations_for_region(target_address, 1, metadata_spans)
    if changed_range is not None:
        if changed_range.classification == "text":
            return (
                "inside changed executable region",
                changed_range.section_name,
                True,
                changed_range.classification,
                changed_range.section_name,
                target_annotations,
            )
        if changed_range.classification == "data":
            return (
                "inside changed data region",
                changed_range.section_name,
                True,
                changed_range.classification,
                changed_range.section_name,
                target_annotations,
            )

    original_section = original_header.section_for_address(target_address)
    patched_section = patched_header.section_for_address(target_address)
    if original_section is not None:
        return (
            "inside original mapped section",
            original_section.name,
            changed_range is not None,
            None,
            None,
            target_annotations,
        )
    if patched_section is not None:
        return (
            "inside patched or expanded section",
            patched_section.name,
            changed_range is not None,
            None,
            None,
            target_annotations,
        )
    return "outside mapped DOL memory", None, changed_range is not None, None, None, target_annotations


def detect_changed_branches(
    original_header: DolHeader,
    patched_header: DolHeader,
    original_data: bytes,
    patched_data: bytes,
    changed_ranges: Sequence[ChangedRange],
    metadata_spans: Sequence[MetadataSpan] = (),
) -> tuple[DecodedBranch, ...]:
    branches: list[DecodedBranch] = []
    seen_offsets: set[int] = set()
    for changed_range in changed_ranges:
        if changed_range.classification != "text":
            continue
        section = original_header.section_for_offset(changed_range.start)
        if section is None:
            continue
        range_start = changed_range.start - (changed_range.start % 4)
        range_end = ((changed_range.end + 3) // 4) * 4
        for offset in range(range_start, range_end, 4):
            if offset in seen_offsets:
                continue
            seen_offsets.add(offset)
            if offset + 4 > len(patched_data):
                continue
            if offset < section.offset or offset + 4 > section.end_offset:
                continue
            if original_data[offset : offset + 4] == patched_data[offset : offset + 4]:
                continue
            instruction_word = int.from_bytes(patched_data[offset : offset + 4], "big")
            instruction_address = section.address + (offset - section.offset)
            decoded = decode_unconditional_branch(instruction_word, instruction_address)
            if decoded is None:
                continue
            (
                target_classification,
                target_section_name,
                target_in_changed_region,
                target_changed_range_classification,
                target_changed_range_section_name,
                target_annotations,
            ) = _classify_branch_target(
                decoded.target_address,
                original_header,
                patched_header,
                changed_ranges,
                metadata_spans,
            )
            branches.append(
                dataclasses.replace(
                    decoded,
                    instruction_offset=offset,
                    target_classification=target_classification,
                    target_section_name=target_section_name,
                    target_in_changed_region=target_in_changed_region,
                    target_changed_range_classification=target_changed_range_classification,
                    target_changed_range_section_name=target_changed_range_section_name,
                    target_annotations=target_annotations,
                )
            )
    return tuple(branches)


def detect_zero_candidates(data: bytes, header: DolHeader) -> tuple[ZeroCandidateRegion, ...]:
    regions: list[ZeroCandidateRegion] = []
    for section in header.sections:
        start: int | None = None
        section_bytes = data[section.offset : section.end_offset]
        for index, value in enumerate(section_bytes):
            if value == 0:
                if start is None:
                    start = index
            elif start is not None:
                run_length = index - start
                if run_length >= _ZERO_RUN_THRESHOLD:
                    regions.append(
                        ZeroCandidateRegion(
                            section_name=section.name,
                            file_offset=section.offset + start,
                            virtual_address=section.address + start,
                            length=run_length,
                        )
                    )
                start = None
        if start is not None:
            run_length = len(section_bytes) - start
            if run_length >= _ZERO_RUN_THRESHOLD:
                regions.append(
                    ZeroCandidateRegion(
                        section_name=section.name,
                        file_offset=section.offset + start,
                        virtual_address=section.address + start,
                        length=run_length,
                    )
                )
    return tuple(regions)


def analyze_dol_patch(
    original_path: Path,
    patched_path: Path,
    metadata_spans: Sequence[MetadataSpan] = (),
) -> DolDiffReport:
    original_header, original_data = parse_dol_file(original_path)
    patched_header, patched_data = parse_dol_file(patched_path)
    changed_ranges = group_changed_ranges(original_data, patched_data, original_header, metadata_spans)
    decoded_branches = detect_changed_branches(
        original_header,
        patched_header,
        original_data,
        patched_data,
        changed_ranges,
        metadata_spans,
    )
    zero_candidates = detect_zero_candidates(patched_data, patched_header)
    return DolDiffReport(
        original_path=str(original_path),
        patched_path=str(patched_path),
        original_size=len(original_data),
        patched_size=len(patched_data),
        original_sha256=_sha256_bytes(original_data),
        patched_sha256=_sha256_bytes(patched_data),
        original_header=original_header,
        patched_header=patched_header,
        section_mappings_changed=_section_signature(original_header) != _section_signature(patched_header),
        changed_ranges=changed_ranges,
        decoded_branches=decoded_branches,
        zero_candidates=zero_candidates,
    )


def build_file_identity(path: Path, label: str) -> DolFileIdentity:
    header, data = parse_dol_file(path)
    return DolFileIdentity(label=label, path=str(path), size=len(data), sha256=_sha256_bytes(data), header=header)


def summarize_comparison(label: str, left_label: str, right_label: str, report: DolDiffReport) -> ComparisonSummary:
    bytes_by_classification: defaultdict[str, int] = defaultdict(int)
    bytes_by_section: defaultdict[str, int] = defaultdict(int)
    for changed_range in report.changed_ranges:
        bytes_by_classification[changed_range.classification] += changed_range.length
        section_key = changed_range.section_name or changed_range.classification
        bytes_by_section[section_key] += changed_range.length

    has_text_changes = bytes_by_classification.get("text", 0) > 0
    has_data_changes = bytes_by_classification.get("data", 0) > 0
    has_header_changes = bytes_by_classification.get("header", 0) > 0
    has_appended_changes = bytes_by_classification.get("newly appended region", 0) > 0
    has_unmapped_changes = bytes_by_classification.get("unmapped file region", 0) > 0
    total_changed_bytes = sum(changed_range.length for changed_range in report.changed_ranges)
    return ComparisonSummary(
        label=label,
        left_label=left_label,
        right_label=right_label,
        report=report,
        total_changed_bytes=total_changed_bytes,
        changed_range_count=len(report.changed_ranges),
        changed_bytes_by_classification=tuple(sorted(bytes_by_classification.items())),
        changed_bytes_by_section=tuple(sorted(bytes_by_section.items())),
        has_text_changes=has_text_changes,
        has_data_changes=has_data_changes,
        has_header_changes=has_header_changes,
        has_appended_changes=has_appended_changes,
        has_unmapped_changes=has_unmapped_changes,
        is_data_only=(
            total_changed_bytes > 0
            and has_data_changes
            and not has_text_changes
            and not has_header_changes
            and not has_appended_changes
            and not has_unmapped_changes
        ),
    )


def analyze_three_way_dol_patch(
    first_path: Path,
    second_path: Path,
    third_path: Path,
    *,
    first_label: str = "A",
    second_label: str = "B",
    third_label: str = "C",
    metadata_spans: Sequence[MetadataSpan] = (),
) -> ThreeWayDolDiffReport:
    first_file = build_file_identity(first_path, first_label)
    second_file = build_file_identity(second_path, second_label)
    third_file = build_file_identity(third_path, third_label)

    first_to_second = analyze_dol_patch(first_path, second_path, metadata_spans)
    second_to_third = analyze_dol_patch(second_path, third_path, metadata_spans)
    first_to_third = analyze_dol_patch(first_path, third_path, metadata_spans)

    return ThreeWayDolDiffReport(
        files=(first_file, second_file, third_file),
        comparisons=(
            summarize_comparison(f"{first_label}->{second_label}", first_label, second_label, first_to_second),
            summarize_comparison(f"{second_label}->{third_label}", second_label, third_label, second_to_third),
            summarize_comparison(f"{first_label}->{third_label}", first_label, third_label, first_to_third),
        ),
    )


def load_metadata_spans(path: Path) -> tuple[MetadataSpan, ...]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list):
        raise DolAnalysisError("Metadata JSON must be a list of span objects.")

    spans: list[MetadataSpan] = []
    for item in payload:
        if not isinstance(item, dict):
            raise DolAnalysisError("Each metadata span must be a JSON object.")
        spans.append(
            MetadataSpan(
                name=str(item["name"]),
                start_address=int(item["start_address"]),
                length=int(item["length"]),
                category=str(item.get("category", "metadata")),
                description=str(item["description"]) if item.get("description") is not None else None,
            )
        )
    return tuple(spans)


def _header_to_dict(header: DolHeader) -> dict[str, Any]:
    return {
        "text_sections": [
            {
                "name": section.name,
                "file_offset": section.offset,
                "virtual_address": section.address,
                "size": section.size,
            }
            for section in header.sections
            if section.kind == "text"
        ],
        "data_sections": [
            {
                "name": section.name,
                "file_offset": section.offset,
                "virtual_address": section.address,
                "size": section.size,
            }
            for section in header.sections
            if section.kind == "data"
        ],
        "bss_address": header.bss_address,
        "bss_size": header.bss_size,
        "entry_point": header.entry_point,
    }


def _annotations_to_dict(annotations: Iterable[RangeAnnotation]) -> list[dict[str, Any]]:
    return [
        {
            "name": annotation.name,
            "category": annotation.category,
            "start_address": annotation.start_address,
            "length": annotation.length,
            "description": annotation.description,
        }
        for annotation in annotations
    ]


def report_to_dict(report: DolDiffReport) -> dict[str, Any]:
    return {
        "original_path": report.original_path,
        "patched_path": report.patched_path,
        "original_size": report.original_size,
        "patched_size": report.patched_size,
        "original_sha256": report.original_sha256,
        "patched_sha256": report.patched_sha256,
        "size_delta": report.patched_size - report.original_size,
        "section_mappings_changed": report.section_mappings_changed,
        "original_header": _header_to_dict(report.original_header),
        "patched_header": _header_to_dict(report.patched_header),
        "changed_ranges": [
            {
                "file_offset": changed_range.start,
                "virtual_address": changed_range.virtual_address,
                "length": changed_range.length,
                "classification": changed_range.classification,
                "section_name": changed_range.section_name,
                "annotations": _annotations_to_dict(changed_range.annotations),
            }
            for changed_range in report.changed_ranges
        ],
        "decoded_branches": [
            {
                "instruction_offset": branch.instruction_offset,
                "instruction_address": branch.instruction_address,
                "instruction_word": branch.instruction_word,
                "mnemonic": branch.mnemonic,
                "absolute": branch.absolute,
                "link": branch.link,
                "target_address": branch.target_address,
                "target_classification": branch.target_classification,
                "target_section_name": branch.target_section_name,
                "target_in_changed_region": branch.target_in_changed_region,
                "target_changed_range_classification": branch.target_changed_range_classification,
                "target_changed_range_section_name": branch.target_changed_range_section_name,
                "target_annotations": _annotations_to_dict(branch.target_annotations),
            }
            for branch in report.decoded_branches
        ],
        "zero_candidates": [
            {
                "section_name": region.section_name,
                "file_offset": region.file_offset,
                "virtual_address": region.virtual_address,
                "length": region.length,
            }
            for region in report.zero_candidates
        ],
    }


def comparison_to_dict(comparison: ComparisonSummary) -> dict[str, Any]:
    return {
        "label": comparison.label,
        "left_label": comparison.left_label,
        "right_label": comparison.right_label,
        "byte_identical": comparison.report.original_sha256 == comparison.report.patched_sha256,
        "changed_range_count": comparison.changed_range_count,
        "total_changed_bytes": comparison.total_changed_bytes,
        "changed_bytes_by_classification": dict(comparison.changed_bytes_by_classification),
        "changed_bytes_by_section": dict(comparison.changed_bytes_by_section),
        "has_text_changes": comparison.has_text_changes,
        "has_data_changes": comparison.has_data_changes,
        "has_header_changes": comparison.has_header_changes,
        "has_appended_changes": comparison.has_appended_changes,
        "has_unmapped_changes": comparison.has_unmapped_changes,
        "is_data_only": comparison.is_data_only,
        "report": report_to_dict(comparison.report),
    }


def three_way_report_to_dict(report: ThreeWayDolDiffReport) -> dict[str, Any]:
    file_map = {
        file_identity.label: {
            "path": file_identity.path,
            "size": file_identity.size,
            "sha256": file_identity.sha256,
            "header": _header_to_dict(file_identity.header),
        }
        for file_identity in report.files
    }
    identical_pairs = {}
    for first_index, first_file in enumerate(report.files):
        for second_file in report.files[first_index + 1 :]:
            identical_pairs[f"{first_file.label}=={second_file.label}"] = first_file.sha256 == second_file.sha256

    return {
        "files": file_map,
        "identical_pairs": identical_pairs,
        "comparisons": [comparison_to_dict(comparison) for comparison in report.comparisons],
    }


def _format_annotations(annotations: Sequence[RangeAnnotation]) -> str:
    if not annotations:
        return "-"
    return ", ".join(annotation.name for annotation in annotations)


def render_markdown_report(report: DolDiffReport) -> str:
    lines = [
        "# Prime 3 main.dol Patch Analysis",
        "",
        f"- Original: `{report.original_path}`",
        f"- Patched: `{report.patched_path}`",
        f"- Original SHA-256: `{report.original_sha256}`",
        f"- Patched SHA-256: `{report.patched_sha256}`",
        f"- Original size: `{report.original_size}` bytes",
        f"- Patched size: `{report.patched_size}` bytes",
        f"- Size delta: `{report.patched_size - report.original_size}` bytes",
        f"- Section mappings changed: `{report.section_mappings_changed}`",
        "",
        "## Changed Ranges",
    ]
    if not report.changed_ranges:
        lines.extend(["", "No changed ranges detected."])
    else:
        lines.extend(
            [
                "",
                "| File Offset | Virtual Address | Length | Classification | Section | Annotations |",
                "| --- | --- | ---: | --- | --- | --- |",
            ]
        )
        for changed_range in report.changed_ranges:
            address = "-" if changed_range.virtual_address is None else f"`0x{changed_range.virtual_address:08X}`"
            section = changed_range.section_name or "-"
            lines.append(
                f"| `0x{changed_range.start:X}` | {address} | `{changed_range.length}` | "
                f"{changed_range.classification} | {section} | {_format_annotations(changed_range.annotations)} |"
            )

    lines.extend(["", "## Decoded Branches"])
    if not report.decoded_branches:
        lines.extend(["", "No changed unconditional branch instructions were detected."])
    else:
        lines.extend(
            [
                "",
                "| Address | Word | Mnemonic | Target | Target Classification | Target Range | Target Annotations |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for branch in report.decoded_branches:
            target_range = branch.target_changed_range_classification or "-"
            if branch.target_changed_range_section_name is not None:
                target_range = f"{target_range} ({branch.target_changed_range_section_name})"
            lines.append(
                f"| `0x{branch.instruction_address:08X}` | `0x{branch.instruction_word:08X}` | {branch.mnemonic} | "
                f"`0x{branch.target_address:08X}` | {branch.target_classification} | {target_range} | "
                f"{_format_annotations(branch.target_annotations)} |"
            )

    lines.extend(["", "## Zero Candidates"])
    if not report.zero_candidates:
        lines.extend(["", f"No zero-filled runs of at least {_ZERO_RUN_THRESHOLD} bytes were detected."])
    else:
        lines.extend(
            [
                "",
                "| Section | File Offset | Virtual Address | Length |",
                "| --- | --- | --- | ---: |",
            ]
        )
        for region in report.zero_candidates:
            lines.append(
                f"| {region.section_name} | `0x{region.file_offset:X}` | "
                f"`0x{region.virtual_address:08X}` | `{region.length}` |"
            )

    return "\n".join(lines) + "\n"


def render_three_way_markdown_report(report: ThreeWayDolDiffReport) -> str:
    lines = ["# Prime 3 main.dol Three-Way Analysis", "", "## Files", ""]
    lines.extend(
        [
            "| Label | Path | SHA-256 | Size |",
            "| --- | --- | --- | ---: |",
        ]
    )
    for file_identity in report.files:
        lines.append(
            f"| {file_identity.label} | `{file_identity.path}` | `{file_identity.sha256}` | `{file_identity.size}` |"
        )

    lines.extend(["", "## Equality", ""])
    for first_index, first_file in enumerate(report.files):
        for second_file in report.files[first_index + 1 :]:
            identical = first_file.sha256 == second_file.sha256
            lines.append(f"- `{first_file.label} == {second_file.label}`: `{identical}`")

    for comparison in report.comparisons:
        diff_report = comparison.report
        lines.extend(
            [
                "",
                f"## {comparison.label}",
                "",
                f"- Byte-identical: `{diff_report.original_sha256 == diff_report.patched_sha256}`",
                f"- Changed ranges: `{comparison.changed_range_count}`",
                f"- Total changed bytes: `{comparison.total_changed_bytes}`",
                f"- Data only: `{comparison.is_data_only}`",
                f"- Has text changes: `{comparison.has_text_changes}`",
                f"- Has header changes: `{comparison.has_header_changes}`",
                f"- Has appended changes: `{comparison.has_appended_changes}`",
                f"- Has unmapped changes: `{comparison.has_unmapped_changes}`",
                "",
                "### Changed Bytes By Classification",
                "",
            ]
        )
        if comparison.changed_bytes_by_classification:
            for name, byte_count in comparison.changed_bytes_by_classification:
                lines.append(f"- `{name}`: `{byte_count}`")
        else:
            lines.append("- none")

        lines.extend(["", "### Changed Bytes By Section", ""])
        if comparison.changed_bytes_by_section:
            for name, byte_count in comparison.changed_bytes_by_section:
                lines.append(f"- `{name}`: `{byte_count}`")
        else:
            lines.append("- none")

        lines.extend(["", "### Changed Ranges", ""])
        if not diff_report.changed_ranges:
            lines.append("No changed ranges detected.")
        else:
            lines.extend(
                [
                    "| File Offset | Virtual Address | Length | Classification | Section | Annotations |",
                    "| --- | --- | ---: | --- | --- | --- |",
                ]
            )
            for changed_range in diff_report.changed_ranges:
                address = "-" if changed_range.virtual_address is None else f"`0x{changed_range.virtual_address:08X}`"
                section = changed_range.section_name or "-"
                lines.append(
                    f"| `0x{changed_range.start:X}` | {address} | `{changed_range.length}` | "
                    f"{changed_range.classification} | {section} | {_format_annotations(changed_range.annotations)} |"
                )

        lines.extend(["", "### Decoded Branches", ""])
        if not diff_report.decoded_branches:
            lines.append("No changed unconditional branch instructions were detected.")
        else:
            lines.extend(
                [
                    (
                        "| Address | Word | Mnemonic | Target | Target Classification | "
                        "Target Range | Target Annotations |"
                    ),
                    "| --- | --- | --- | --- | --- | --- | --- |",
                ]
            )
            for branch in diff_report.decoded_branches:
                target_range = branch.target_changed_range_classification or "-"
                if branch.target_changed_range_section_name is not None:
                    target_range = f"{target_range} ({branch.target_changed_range_section_name})"
                lines.append(
                    f"| `0x{branch.instruction_address:08X}` | `0x{branch.instruction_word:08X}` | {branch.mnemonic} | "
                    f"`0x{branch.target_address:08X}` | {branch.target_classification} | {target_range} | "
                    f"{_format_annotations(branch.target_annotations)} |"
                )

    return "\n".join(lines) + "\n"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze differences between Prime 3 main.dol files."
    )
    parser.add_argument("--original-dol", type=Path, required=True)
    parser.add_argument("--patched-dol", type=Path, required=True)
    parser.add_argument("--third-dol", type=Path)
    parser.add_argument("--original-label", default="original")
    parser.add_argument("--patched-label", default="patched")
    parser.add_argument("--third-label", default="third")
    parser.add_argument("--metadata-json", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)

    metadata_spans = load_metadata_spans(args.metadata_json) if args.metadata_json is not None else ()

    if args.third_dol is None:
        two_way_report = analyze_dol_patch(args.original_dol, args.patched_dol, metadata_spans)
        report_json = json.dumps(report_to_dict(two_way_report), indent=2, sort_keys=True) + "\n"
        report_markdown = render_markdown_report(two_way_report)
    else:
        three_way_report = analyze_three_way_dol_patch(
            args.original_dol,
            args.patched_dol,
            args.third_dol,
            first_label=args.original_label,
            second_label=args.patched_label,
            third_label=args.third_label,
            metadata_spans=metadata_spans,
        )
        report_json = json.dumps(three_way_report_to_dict(three_way_report), indent=2, sort_keys=True) + "\n"
        report_markdown = render_three_way_markdown_report(three_way_report)

    if args.json_output is not None:
        _write_text(args.json_output, report_json)
    else:
        print(report_json, end="")

    if args.markdown_output is not None:
        _write_text(args.markdown_output, report_markdown)
    elif args.json_output is not None:
        print(report_markdown, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
