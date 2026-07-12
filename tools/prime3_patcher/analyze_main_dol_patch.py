from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
from typing import Any

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
class ChangedRange:
    start: int
    end: int
    classification: str
    section_name: str | None
    virtual_address: int | None
    length: int


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
    original_header: DolHeader
    patched_header: DolHeader
    section_mappings_changed: bool
    changed_ranges: tuple[ChangedRange, ...]
    decoded_branches: tuple[DecodedBranch, ...]
    zero_candidates: tuple[ZeroCandidateRegion, ...]


def _read_u32_be(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "big")


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
            ranges.append(
                ChangedRange(
                    start=start,
                    end=offset,
                    classification=classification,
                    section_name=section_name,
                    virtual_address=virtual_address,
                    length=offset - start,
                )
            )
            start = None
    if start is not None:
        classification, section_name, virtual_address = _classify_offset(start, original_header, len(original_data))
        ranges.append(
            ChangedRange(
                start=start,
                end=max_size,
                classification=classification,
                section_name=section_name,
                virtual_address=virtual_address,
                length=max_size - start,
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


def _classify_branch_target(
    target_address: int,
    original_header: DolHeader,
    patched_header: DolHeader,
    changed_ranges: tuple[ChangedRange, ...],
) -> tuple[str, str | None, bool]:
    original_section = original_header.section_for_address(target_address)
    patched_section = patched_header.section_for_address(target_address)
    target_in_changed_region = any(
        changed_range.virtual_address is not None
        and changed_range.virtual_address <= target_address < changed_range.virtual_address + changed_range.length
        for changed_range in changed_ranges
    )
    if original_section is not None:
        return "inside original mapped section", original_section.name, target_in_changed_region
    if patched_section is not None:
        if original_header.offset_for_address(target_address) is None:
            return "inside patched or expanded section", patched_section.name, target_in_changed_region
        return "inside original mapped section", patched_section.name, target_in_changed_region
    return "outside mapped DOL memory", None, target_in_changed_region


def detect_changed_branches(
    original_header: DolHeader,
    patched_header: DolHeader,
    original_data: bytes,
    patched_data: bytes,
    changed_ranges: tuple[ChangedRange, ...],
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
            target_classification, target_section_name, target_in_changed_region = _classify_branch_target(
                decoded.target_address,
                original_header,
                patched_header,
                changed_ranges,
            )
            branches.append(
                dataclasses.replace(
                    decoded,
                    instruction_offset=offset,
                    target_classification=target_classification,
                    target_section_name=target_section_name,
                    target_in_changed_region=target_in_changed_region,
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


def analyze_dol_patch(original_path: Path, patched_path: Path) -> DolDiffReport:
    original_header, original_data = parse_dol_file(original_path)
    patched_header, patched_data = parse_dol_file(patched_path)
    changed_ranges = group_changed_ranges(original_data, patched_data, original_header)
    decoded_branches = detect_changed_branches(
        original_header,
        patched_header,
        original_data,
        patched_data,
        changed_ranges,
    )
    zero_candidates = detect_zero_candidates(patched_data, patched_header)
    return DolDiffReport(
        original_path=str(original_path),
        patched_path=str(patched_path),
        original_size=len(original_data),
        patched_size=len(patched_data),
        original_header=original_header,
        patched_header=patched_header,
        section_mappings_changed=_section_signature(original_header) != _section_signature(patched_header),
        changed_ranges=changed_ranges,
        decoded_branches=decoded_branches,
        zero_candidates=zero_candidates,
    )


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


def report_to_dict(report: DolDiffReport) -> dict[str, Any]:
    return {
        "original_path": report.original_path,
        "patched_path": report.patched_path,
        "original_size": report.original_size,
        "patched_size": report.patched_size,
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


def render_markdown_report(report: DolDiffReport) -> str:
    lines = [
        "# Prime 3 main.dol Patch Analysis",
        "",
        f"- Original: `{report.original_path}`",
        f"- Patched: `{report.patched_path}`",
        f"- Original size: `{report.original_size}` bytes",
        f"- Patched size: `{report.patched_size}` bytes",
        f"- Size delta: `{report.patched_size - report.original_size}` bytes",
        f"- Section mappings changed: `{report.section_mappings_changed}`",
        "",
        "## Changed Ranges",
    ]
    if not report.changed_ranges:
        lines.append("")
        lines.append("No changed ranges detected.")
    else:
        lines.extend(
            [
                "",
                "| File Offset | Virtual Address | Length | Classification | Section |",
                "| --- | --- | ---: | --- | --- |",
            ]
        )
        for changed_range in report.changed_ranges:
            address = "-" if changed_range.virtual_address is None else f"`0x{changed_range.virtual_address:08X}`"
            section = changed_range.section_name or "-"
            lines.append(
                f"| `0x{changed_range.start:X}` | {address} | `{changed_range.length}` | "
                f"{changed_range.classification} | {section} |"
            )

    lines.append("")
    lines.append("## Decoded Branches")
    if not report.decoded_branches:
        lines.append("")
        lines.append("No changed unconditional branch instructions were detected.")
    else:
        lines.extend(
            [
                "",
                "| Address | Word | Mnemonic | Target | Target Classification | In Changed Region |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for branch in report.decoded_branches:
            lines.append(
                f"| `0x{branch.instruction_address:08X}` | `0x{branch.instruction_word:08X}` | {branch.mnemonic} | "
                f"`0x{branch.target_address:08X}` | {branch.target_classification} | "
                f"{branch.target_in_changed_region} |"
            )

    lines.append("")
    lines.append("## Zero Candidates")
    if not report.zero_candidates:
        lines.append("")
        lines.append(f"No zero-filled runs of at least {_ZERO_RUN_THRESHOLD} bytes were detected.")
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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze differences between an original and patched Prime 3 main.dol."
    )
    parser.add_argument("--original-dol", type=Path, required=True)
    parser.add_argument("--patched-dol", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    args = parser.parse_args(argv)

    report = analyze_dol_patch(args.original_dol, args.patched_dol)
    report_json = json.dumps(report_to_dict(report), indent=2, sort_keys=True) + "\n"
    report_markdown = render_markdown_report(report)

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
