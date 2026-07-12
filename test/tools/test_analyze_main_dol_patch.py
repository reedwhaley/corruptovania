from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[2].joinpath("tools", "prime3_patcher", "analyze_main_dol_patch.py")
    spec = importlib.util.spec_from_file_location("analyze_main_dol_patch", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


module = _load_module()


def _build_dol(
    *,
    text_sections: list[tuple[int, int, bytes]] | None = None,
    data_sections: list[tuple[int, int, bytes]] | None = None,
    bss_address: int = 0x80300000,
    bss_size: int = 0x100,
    entry_point: int = 0x80004000,
) -> bytes:
    text_sections = text_sections or []
    data_sections = data_sections or []
    offsets = [0] * 18
    addresses = [0] * 18
    sizes = [0] * 18

    payload_end = 0x100
    for index, (offset, address, contents) in enumerate(text_sections):
        offsets[index] = offset
        addresses[index] = address
        sizes[index] = len(contents)
        payload_end = max(payload_end, offset + len(contents))

    for index, (offset, address, contents) in enumerate(data_sections, start=7):
        offsets[index] = offset
        addresses[index] = address
        sizes[index] = len(contents)
        payload_end = max(payload_end, offset + len(contents))

    header = bytearray(0x100)
    for index, value in enumerate(offsets):
        header[index * 4 : (index + 1) * 4] = value.to_bytes(4, "big")
    for index, value in enumerate(addresses):
        header[0x48 + (index * 4) : 0x48 + ((index + 1) * 4)] = value.to_bytes(4, "big")
    for index, value in enumerate(sizes):
        header[0x90 + (index * 4) : 0x90 + ((index + 1) * 4)] = value.to_bytes(4, "big")
    header[0xD8:0xDC] = bss_address.to_bytes(4, "big")
    header[0xDC:0xE0] = bss_size.to_bytes(4, "big")
    header[0xE0:0xE4] = entry_point.to_bytes(4, "big")

    payload = bytearray(payload_end)
    payload[:0x100] = header
    for offset, _address, contents in text_sections + data_sections:
        payload[offset : offset + len(contents)] = contents
    return bytes(payload)


def test_parse_valid_dol_header():
    dol = _build_dol(
        text_sections=[(0x100, 0x80004000, b"A" * 16)],
        data_sections=[(0x200, 0x80300000, b"B" * 8)],
    )

    header = module.parse_dol_header(dol)

    assert header.entry_point == 0x80004000
    assert header.bss_address == 0x80300000
    assert header.section_for_offset(0x100).name == "text0"
    assert header.section_for_offset(0x200).name == "data0"


def test_malformed_dol_header_zero_size_nonzero_offset():
    dol = bytearray(_build_dol())
    dol[0:4] = (0x100).to_bytes(4, "big")

    with pytest.raises(module.DolAnalysisError, match="zero size but non-zero offset/address"):
        module.parse_dol_header(bytes(dol))


def test_truncated_dol_header():
    with pytest.raises(module.DolAnalysisError, match="requires 256 bytes"):
        module.parse_dol_header(b"\x00" * 32)


def test_text_section_mapping():
    dol = _build_dol(text_sections=[(0x120, 0x80004100, b"A" * 12)])
    header = module.parse_dol_header(dol)

    assert header.address_for_offset(0x124) == 0x80004104


def test_data_section_mapping():
    dol = _build_dol(data_sections=[(0x1C0, 0x80301000, b"B" * 12)])
    header = module.parse_dol_header(dol)

    assert header.address_for_offset(0x1C8) == 0x80301008


def test_unmapped_file_offsets():
    dol = _build_dol(text_sections=[(0x120, 0x80004100, b"A" * 8)])
    header = module.parse_dol_header(dol)

    assert header.section_for_offset(0x110) is None
    assert header.address_for_offset(0x110) is None


def test_virtual_address_mapping():
    dol = _build_dol(text_sections=[(0x120, 0x80004100, b"A" * 8)])
    header = module.parse_dol_header(dol)

    assert header.offset_for_address(0x80004104) == 0x124


def test_contiguous_diff_grouping():
    original = _build_dol(text_sections=[(0x100, 0x80004000, b"ABCDEFGH")])
    patched = bytearray(original)
    patched[0x102:0x106] = b"WXYZ"
    header = module.parse_dol_header(original)

    ranges = module.group_changed_ranges(original, bytes(patched), header)

    assert len(ranges) == 1
    assert ranges[0].start == 0x102
    assert ranges[0].length == 4


def test_separated_diff_grouping():
    original = _build_dol(text_sections=[(0x100, 0x80004000, b"ABCDEFGHJKLM")])
    patched = bytearray(original)
    patched[0x101] = ord("x")
    patched[0x108] = ord("y")
    header = module.parse_dol_header(original)

    ranges = module.group_changed_ranges(original, bytes(patched), header)

    assert [(item.start, item.length) for item in ranges] == [(0x101, 1), (0x108, 1)]


def test_dol_size_growth():
    original = _build_dol(text_sections=[(0x100, 0x80004000, b"A" * 8)])
    patched = original + (b"\x11" * 12)
    report = module.analyze_dol_patch(_write_tmp(original), _write_tmp(patched))

    assert report.patched_size > report.original_size
    assert any(item.classification == "newly appended region" for item in report.changed_ranges)


def test_section_table_changes():
    original = _build_dol(text_sections=[(0x100, 0x80004000, b"A" * 8)])
    patched = _build_dol(text_sections=[(0x100, 0x80004000, b"A" * 8)], data_sections=[(0x180, 0x80300000, b"B" * 4)])

    report = module.analyze_dol_patch(_write_tmp(original), _write_tmp(patched))

    assert report.section_mappings_changed is True


def test_relative_forward_branch_decoding():
    decoded = module.decode_unconditional_branch(0x48000008, 0x80004000)

    assert decoded is not None
    assert decoded.mnemonic == "b"
    assert decoded.target_address == 0x80004008


def test_relative_backward_branch_decoding():
    decoded = module.decode_unconditional_branch(0x4BFFFFFC, 0x80004008)

    assert decoded is not None
    assert decoded.target_address == 0x80004004


def test_branch_and_link_decoding():
    decoded = module.decode_unconditional_branch(0x48000009, 0x80004000)

    assert decoded is not None
    assert decoded.mnemonic == "bl"
    assert decoded.link is True


def test_absolute_branch_handling():
    decoded = module.decode_unconditional_branch(0x48000002, 0x80004000)

    assert decoded is not None
    assert decoded.absolute is True
    assert decoded.mnemonic == "ba"


def test_branch_target_classification():
    original = _build_dol(text_sections=[(0x100, 0x80004000, b"\x60\x00\x00\x00" * 4)])
    patched = bytearray(original)
    patched[0x100:0x104] = (0x48000008).to_bytes(4, "big")
    report = module.analyze_dol_patch(_write_tmp(original), _write_tmp(bytes(patched)))

    assert report.decoded_branches[0].target_classification == "inside original mapped section"
    assert report.decoded_branches[0].target_in_changed_region is False


def test_branch_target_can_land_in_changed_range():
    original = _build_dol(text_sections=[(0x100, 0x80004000, b"\x60\x00\x00\x00" * 6)])
    patched = bytearray(original)
    patched[0x100:0x104] = (0x48000008).to_bytes(4, "big")
    patched[0x108:0x10C] = (0x48000008).to_bytes(4, "big")

    report = module.analyze_dol_patch(_write_tmp(original), _write_tmp(bytes(patched)))

    assert report.decoded_branches[0].target_classification == "inside changed executable region"
    assert report.decoded_branches[0].target_changed_range_classification == "text"
    assert report.decoded_branches[0].target_changed_range_section_name == "text0"


def test_zero_filled_candidate_region_reporting():
    original = _build_dol(text_sections=[(0x100, 0x80004000, b"A" * 64)])
    patched = _build_dol(text_sections=[(0x100, 0x80004000, b"\x00" * 64)])
    report = module.analyze_dol_patch(_write_tmp(original), _write_tmp(patched))

    assert report.zero_candidates
    assert report.zero_candidates[0].length >= 32


def test_metadata_annotations_are_supplied_externally():
    original = _build_dol(text_sections=[(0x100, 0x80004000, b"A" * 8)])
    patched = _build_dol(text_sections=[(0x100, 0x80004000, b"B" * 8)])
    spans = (module.MetadataSpan(name="build_string", start_address=0x80004000, length=8),)

    report = module.analyze_dol_patch(_write_tmp(original), _write_tmp(patched), spans)

    assert report.changed_ranges[0].annotations[0].name == "build_string"


def test_three_identical_files():
    data = _build_dol(text_sections=[(0x100, 0x80004000, b"A" * 8)])
    a_path = _write_tmp(data)
    b_path = _write_tmp(data)
    c_path = _write_tmp(data)

    report = module.analyze_three_way_dol_patch(a_path, b_path, c_path)

    assert all(comparison.changed_range_count == 0 for comparison in report.comparisons)
    assert report.comparisons[0].report.original_sha256 == report.comparisons[0].report.patched_sha256


def test_three_way_separates_data_text_and_combined_changes():
    a = _build_dol(
        text_sections=[(0x100, 0x80004000, b"\x60\x00\x00\x00" * 4)],
        data_sections=[(0x200, 0x80300000, b"A" * 8)],
    )
    b = bytearray(a)
    b[0x200:0x204] = b"DATA"
    c = bytearray(b)
    c[0x100:0x104] = (0x48000008).to_bytes(4, "big")

    report = module.analyze_three_way_dol_patch(_write_tmp(a), _write_tmp(bytes(b)), _write_tmp(bytes(c)))
    comparisons = {comparison.label: comparison for comparison in report.comparisons}

    assert comparisons["A->B"].is_data_only is True
    assert comparisons["A->B"].has_text_changes is False
    assert comparisons["B->C"].has_text_changes is True
    assert comparisons["B->C"].has_data_changes is False
    assert comparisons["A->C"].has_text_changes is True
    assert comparisons["A->C"].has_data_changes is True


def test_three_way_json_output(tmp_path: Path):
    a = _build_dol(text_sections=[(0x100, 0x80004000, b"A" * 8)])
    b = _build_dol(text_sections=[(0x100, 0x80004000, b"B" * 8)])
    c = _build_dol(text_sections=[(0x100, 0x80004000, b"C" * 8)])
    a_path = tmp_path / "a.dol"
    b_path = tmp_path / "b.dol"
    c_path = tmp_path / "c.dol"
    output_path = tmp_path / "three_way.json"
    a_path.write_bytes(a)
    b_path.write_bytes(b)
    c_path.write_bytes(c)

    assert module.main(
        [
            "--original-dol",
            str(a_path),
            "--patched-dol",
            str(b_path),
            "--third-dol",
            str(c_path),
            "--original-label",
            "A",
            "--patched-label",
            "B",
            "--third-label",
            "C",
            "--json-output",
            str(output_path),
        ]
    ) == 0

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["files"]["A"]["sha256"]
    assert [item["label"] for item in payload["comparisons"]] == ["A->B", "B->C", "A->C"]


def test_three_way_markdown_output(tmp_path: Path):
    a = _build_dol(text_sections=[(0x100, 0x80004000, b"A" * 8)])
    b = _build_dol(text_sections=[(0x100, 0x80004000, b"B" * 8)])
    c = _build_dol(text_sections=[(0x100, 0x80004000, b"C" * 8)])
    a_path = tmp_path / "a.dol"
    b_path = tmp_path / "b.dol"
    c_path = tmp_path / "c.dol"
    output_path = tmp_path / "three_way.md"
    a_path.write_bytes(a)
    b_path.write_bytes(b)
    c_path.write_bytes(c)

    assert module.main(
        [
            "--original-dol",
            str(a_path),
            "--patched-dol",
            str(b_path),
            "--third-dol",
            str(c_path),
            "--original-label",
            "A",
            "--patched-label",
            "B",
            "--third-label",
            "C",
            "--markdown-output",
            str(output_path),
        ]
    ) == 0

    text = output_path.read_text(encoding="utf-8")
    assert "A->B" in text
    assert "B->C" in text
    assert "A->C" in text


def test_two_way_json_report_generation(tmp_path: Path):
    original = _build_dol(text_sections=[(0x100, 0x80004000, b"A" * 8)])
    patched = _build_dol(text_sections=[(0x100, 0x80004000, b"B" * 8)])
    original_path = tmp_path / "original.dol"
    patched_path = tmp_path / "patched.dol"
    json_path = tmp_path / "report.json"
    original_path.write_bytes(original)
    patched_path.write_bytes(patched)

    assert module.main(
        [
            "--original-dol",
            str(original_path),
            "--patched-dol",
            str(patched_path),
            "--json-output",
            str(json_path),
        ]
    ) == 0

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["changed_ranges"]


def test_two_way_markdown_report_generation(tmp_path: Path):
    original = _build_dol(text_sections=[(0x100, 0x80004000, b"A" * 8)])
    patched = _build_dol(text_sections=[(0x100, 0x80004000, b"B" * 8)])
    original_path = tmp_path / "original.dol"
    patched_path = tmp_path / "patched.dol"
    markdown_path = tmp_path / "report.md"
    original_path.write_bytes(original)
    patched_path.write_bytes(patched)

    assert module.main(
        [
            "--original-dol",
            str(original_path),
            "--patched-dol",
            str(patched_path),
            "--markdown-output",
            str(markdown_path),
        ]
    ) == 0

    text = markdown_path.read_text(encoding="utf-8")
    assert "Changed Ranges" in text


def test_reject_overlapping_section_definitions():
    dol = _build_dol(
        text_sections=[(0x100, 0x80004000, b"A" * 16), (0x108, 0x80005000, b"B" * 16)]
    )

    with pytest.raises(module.DolAnalysisError, match="Overlapping section file ranges"):
        module.parse_dol_header(dol)


def test_reject_invalid_section_definitions():
    dol = bytearray(_build_dol())
    dol[0:4] = (0x80).to_bytes(4, "big")
    dol[0x48:0x4C] = (0x80004000).to_bytes(4, "big")
    dol[0x90:0x94] = (0x20).to_bytes(4, "big")

    with pytest.raises(module.DolAnalysisError, match="starts inside the DOL header"):
        module.parse_dol_header(bytes(dol))


def _write_tmp(data: bytes) -> Path:
    tmp_dir = Path(tempfile.mkdtemp(prefix="doltmp-"))
    path = tmp_dir.joinpath(f"{hash(data)}.dol")
    path.write_bytes(data)
    return path
