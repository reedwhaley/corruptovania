from __future__ import annotations

import dataclasses
import importlib.util
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions
from retro_data_structures.game_check import Game as RDSGame

from randovania.games.prime3.exporter import dol_patcher


@dataclasses.dataclass(frozen=True)
class FakeVersion:
    game: RDSGame
    description: str
    build_string_address: int
    build_string: bytes


def _load_analyzer_module():
    module_path = Path(__file__).resolve().parents[4].joinpath("tools", "prime3_patcher", "analyze_main_dol_patch.py")
    spec = importlib.util.spec_from_file_location("analyze_main_dol_patch_for_prime3_tests", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


analyzer = _load_analyzer_module()


def _make_fake_version(
    *,
    address: int = 0x80500020,
    build_string: bytes = b"!#$MetroidBuildInfo!#$FAKE",
) -> FakeVersion:
    return FakeVersion(
        game=RDSGame.CORRUPTION,
        description="Synthetic Corruption",
        build_string_address=address,
        build_string=build_string,
    )


def _build_synthetic_dol(
    version: FakeVersion | Any,
    *,
    section_address: int | None = None,
    text_sections: list[tuple[int, int, bytes]] | None = None,
    data_sections: list[tuple[int, int, bytes]] | None = None,
    build_string_bytes: bytes | None = None,
    include_build_string: bool = True,
    bss_address: int = 0x80600000,
    bss_size: int = 0x100,
    entry_point: int = 0x80004000,
) -> bytes:
    text_sections = list(text_sections or [])
    data_sections = list(data_sections or [])

    if include_build_string:
        section_address = version.build_string_address - 0x20 if section_address is None else section_address
        build_bytes = version.build_string if build_string_bytes is None else build_string_bytes
        text_sections.insert(0, (0x100, section_address, b"\x60\x00\x00\x00" * 8 + build_bytes + b"\x00" * 0x20))

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

    result = bytearray(payload_end)
    for index, value in enumerate(offsets):
        result[index * 4 : (index + 1) * 4] = value.to_bytes(4, "big")
    for index, value in enumerate(addresses):
        base = 0x48 + (index * 4)
        result[base : base + 4] = value.to_bytes(4, "big")
    for index, value in enumerate(sizes):
        base = 0x90 + (index * 4)
        result[base : base + 4] = value.to_bytes(4, "big")
    result[0xD8:0xDC] = bss_address.to_bytes(4, "big")
    result[0xDC:0xE0] = bss_size.to_bytes(4, "big")
    result[0xE0:0xE4] = entry_point.to_bytes(4, "big")

    for offset, _address, contents in text_sections + data_sections:
        result[offset : offset + len(contents)] = contents
    return bytes(result)


def _build_dol_without_text_slots(version: FakeVersion | Any) -> bytes:
    text_sections = []
    for index in range(7):
        text_sections.append((0x100 + (index * 0x40), 0x80004000 + (index * 0x100), b"\x60\x00\x00\x00" * 8))
    return _build_synthetic_dol(version, text_sections=text_sections, include_build_string=False)


def test_parse_dol_header_reports_text_and_data_slots() -> None:
    version = _make_fake_version()
    data = _build_synthetic_dol(version, data_sections=[(0x220, 0x80590000, b"A" * 16)])

    header = dol_patcher.parse_dol_header(data)

    assert [section.name for section in header.text_sections()] == ["text0"]
    assert [section.name for section in header.data_sections()] == ["data0"]
    assert header.unused_text_slots()[0].name == "text1"
    assert header.unused_data_slots()[0].name == "data1"


def test_parse_dol_sections_success() -> None:
    version = _make_fake_version()
    sections = dol_patcher.parse_dol_sections(_build_synthetic_dol(version))

    assert sections[0].name == "text0"
    assert sections[0].address == 0x80500000


def test_virtual_address_to_file_offset_maps_build_string() -> None:
    version = _make_fake_version()
    header = dol_patcher.parse_dol_header(_build_synthetic_dol(version))

    file_offset = dol_patcher.virtual_address_to_file_offset(
        header.text_sections(),
        version.build_string_address,
        len(version.build_string),
    )

    assert file_offset == 0x120


def test_patch_prime3_corruption_dol_success() -> None:
    version = _make_fake_version()
    original = _build_synthetic_dol(version)
    layout_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")

    patched, result = dol_patcher.patch_prime3_corruption_dol(original, layout_uuid, version=version)

    assert patched != original
    assert len(patched) == len(original)
    assert patched[:0x100] == original[:0x100]
    assert patched[0x126:0x136] == layout_uuid.bytes
    assert result.changed is True
    assert result.bytes_changed == 16


def test_patch_prime3_corruption_dol_is_idempotent() -> None:
    version = _make_fake_version()
    layout_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    first, _ = dol_patcher.patch_prime3_corruption_dol(_build_synthetic_dol(version), layout_uuid, version=version)

    second, result = dol_patcher.patch_prime3_corruption_dol(first, layout_uuid, version=version)

    assert second == first
    assert result.changed is False
    assert result.previous_layout_uuid == layout_uuid


def test_patch_prime3_corruption_dol_rejects_conflicting_uuid() -> None:
    version = _make_fake_version()
    existing_uuid = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    desired_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    build_string = bytearray(version.build_string)
    build_string[6:22] = existing_uuid.bytes

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="conflicting layout UUID"):
        dol_patcher.patch_prime3_corruption_dol(
            _build_synthetic_dol(version, build_string_bytes=bytes(build_string)),
            desired_uuid,
            version=version,
        )


def test_identify_supported_corruption_version_accepts_real_metadata() -> None:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    identified = dol_patcher.identify_supported_corruption_version(_build_synthetic_dol(version))

    assert identified is version


def test_identify_supported_corruption_version_rejects_non_corruption_candidates() -> None:
    version = _make_fake_version()
    wrong_game_version = dataclasses.replace(version, game=RDSGame.PRIME)

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="Unsupported non-Corruption"):
        dol_patcher.identify_supported_corruption_version(_build_synthetic_dol(version), versions=(wrong_game_version,))


def test_identify_supported_corruption_version_rejects_unknown_build() -> None:
    version = _make_fake_version()
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="Unsupported or unknown"):
        dol_patcher.identify_supported_corruption_version(
            _build_synthetic_dol(version, build_string_bytes=b"X" * len(version.build_string)),
            versions=(version,),
        )


def test_patch_prime3_corruption_dol_rejects_unexpected_build_string() -> None:
    version = _make_fake_version()
    data = bytearray(_build_synthetic_dol(version))
    data[0x125] ^= 0x01

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="Unexpected build string bytes"):
        dol_patcher.patch_prime3_corruption_dol(bytes(data), uuid.uuid4(), version=version)


def test_virtual_address_to_file_offset_rejects_unmapped_address() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="is not mapped"):
        dol_patcher.virtual_address_to_file_offset(
            dol_patcher.parse_dol_sections(_build_synthetic_dol(_make_fake_version())),
            0x90000000,
            4,
        )


def test_parse_dol_header_rejects_truncated_dol() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="truncated before the header"):
        dol_patcher.parse_dol_header(b"\x00" * 0xFF)


def test_parse_dol_header_rejects_malformed_section() -> None:
    data = bytearray(b"\x00" * 0x100)
    data[0x90:0x94] = (4).to_bytes(4, "big")

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="mapped sections need an address"):
        dol_patcher.parse_dol_header(bytes(data))


def test_parse_dol_header_rejects_file_overlap() -> None:
    version = _make_fake_version()
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="overlap in file space"):
        dol_patcher.parse_dol_header(
            _build_synthetic_dol(
                version,
                text_sections=[
                    (0x100, 0x80004000, b"A" * 0x20),
                    (0x110, 0x80005000, b"B" * 0x20),
                ],
                include_build_string=False,
            )
        )


def test_parse_dol_header_rejects_virtual_overlap() -> None:
    version = _make_fake_version()
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="overlap in virtual address space"):
        dol_patcher.parse_dol_header(
            _build_synthetic_dol(
                version,
                text_sections=[
                    (0x100, 0x80004000, b"A" * 0x20),
                    (0x140, 0x80004010, b"B" * 0x20),
                ],
                include_build_string=False,
            )
        )


def test_append_executable_text_section_selects_first_free_slot() -> None:
    version = _make_fake_version()
    original = _build_synthetic_dol(version)

    patched, result = dol_patcher.append_executable_text_section(
        original,
        payload_bytes=b"\x60\x00\x00\x00" * 2,
        payload_virtual_address=0x80510000,
        required_alignment=0x20,
        entry_symbol_offset=4,
    )

    header = dol_patcher.parse_dol_header(patched)
    inserted = header.text_sections()[1]
    assert result.text_kind_index == 1
    assert inserted.name == "text1"
    assert inserted.address == 0x80510000
    assert inserted.size == 8
    assert patched[result.file_offset : result.file_offset + 8] == b"\x60\x00\x00\x00" * 2
    assert result.entry_symbol_address == 0x80510004


def test_append_executable_text_section_aligns_payload_and_reports_padding() -> None:
    version = _make_fake_version()
    original = _build_synthetic_dol(version)

    patched, result = dol_patcher.append_executable_text_section(
        original,
        payload_bytes=b"\xAA" * 5,
        payload_virtual_address=0x80510000,
        required_alignment=0x40,
    )

    assert result.file_offset % 0x40 == 0
    assert result.alignment_padding == result.file_offset - len(original)
    assert patched[len(original) : result.file_offset] == b"\x00" * result.alignment_padding


def test_append_executable_text_section_rejects_no_available_slot() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="no unused text section slots"):
        dol_patcher.append_executable_text_section(
            _build_dol_without_text_slots(_make_fake_version()),
            payload_bytes=b"\xAA" * 4,
            payload_virtual_address=0x80520000,
            required_alignment=0x20,
        )


def test_append_executable_text_section_preserves_existing_sections() -> None:
    version = _make_fake_version()
    original = _build_synthetic_dol(version, data_sections=[(0x260, 0x80590000, b"D" * 16)])

    patched, _result = dol_patcher.append_executable_text_section(
        original,
        payload_bytes=b"\xAA" * 4,
        payload_virtual_address=0x80520000,
        required_alignment=0x20,
    )

    patched_header = dol_patcher.parse_dol_header(patched)
    assert patched_header.text_sections()[0].address == (
        dol_patcher.parse_dol_header(original).text_sections()[0].address
    )
    assert patched_header.data_sections()[0].address == 0x80590000


def test_append_executable_text_section_rejects_text_overlap() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="overlaps existing text0 section"):
        dol_patcher.append_executable_text_section(
            _build_synthetic_dol(_make_fake_version()),
            payload_bytes=b"\xAA" * 4,
            payload_virtual_address=0x80500010,
            required_alignment=0x20,
        )


def test_append_executable_text_section_rejects_data_overlap() -> None:
    version = _make_fake_version()
    original = _build_synthetic_dol(version, data_sections=[(0x260, 0x80590000, b"D" * 16)])

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="overlaps existing data0 section"):
        dol_patcher.append_executable_text_section(
            original,
            payload_bytes=b"\xAA" * 4,
            payload_virtual_address=0x80590008,
            required_alignment=0x20,
        )


def test_append_executable_text_section_rejects_bss_overlap() -> None:
    version = _make_fake_version()
    original = _build_synthetic_dol(version, bss_address=0x805A0000, bss_size=0x100)

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="overlaps the DOL BSS range"):
        dol_patcher.append_executable_text_section(
            original,
            payload_bytes=b"\xAA" * 4,
            payload_virtual_address=0x805A0040,
            required_alignment=0x20,
        )


def test_append_executable_text_section_rejects_virtual_overflow() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="payload virtual range overflows"):
        dol_patcher.append_executable_text_section(
            _build_synthetic_dol(_make_fake_version()),
            payload_bytes=b"\xAA" * 8,
            payload_virtual_address=0xFFFF_FFFC,
            required_alignment=0x20,
        )


def test_append_executable_text_section_rejects_duplicate_insertion() -> None:
    first, _ = dol_patcher.append_executable_text_section(
        _build_synthetic_dol(_make_fake_version()),
        payload_bytes=b"\xAA" * 4,
        payload_virtual_address=0x80510000,
        required_alignment=0x20,
    )

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="overlaps existing text1 section"):
        dol_patcher.append_executable_text_section(
            first,
            payload_bytes=b"\xBB" * 4,
            payload_virtual_address=0x80510000,
            required_alignment=0x20,
        )


@pytest.mark.parametrize(
    ("source", "target", "link", "absolute", "expected_word"),
    [
        (0x80004000, 0x80004008, False, False, 0x48000008),
        (0x80004008, 0x80004004, False, False, 0x4BFFFFFC),
        (0x80004000, 0x80004008, True, False, 0x48000009),
        (0x80004000, 0x00000000, False, True, 0x48000002),
    ],
)
def test_encode_ppc_unconditional_branch_round_trips_through_analyzer(
    source: int,
    target: int,
    link: bool,
    absolute: bool,
    expected_word: int,
) -> None:
    encoded = dol_patcher.encode_ppc_unconditional_branch(source, target, link=link, absolute=absolute)
    decoded = analyzer.decode_unconditional_branch(encoded, source)

    assert encoded == expected_word
    assert decoded is not None
    assert decoded.target_address == target
    assert decoded.link is link
    assert decoded.absolute is absolute


def test_encode_ppc_unconditional_branch_supports_range_limits() -> None:
    max_positive = dol_patcher.encode_ppc_unconditional_branch(0x80004000, 0x82003FFC)
    max_negative = dol_patcher.encode_ppc_unconditional_branch(0x82004000, 0x80004000)

    assert analyzer.decode_unconditional_branch(max_positive, 0x80004000) is not None
    assert analyzer.decode_unconditional_branch(max_negative, 0x82004000) is not None


def test_encode_ppc_unconditional_branch_rejects_out_of_range_displacement() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="outside the signed 26-bit branch range"):
        dol_patcher.encode_ppc_unconditional_branch(0x80004000, 0x82004000)


def test_encode_ppc_unconditional_branch_rejects_unaligned_source() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="source address"):
        dol_patcher.encode_ppc_unconditional_branch(0x80004002, 0x80004008)


def test_encode_ppc_unconditional_branch_rejects_unaligned_target() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="target address"):
        dol_patcher.encode_ppc_unconditional_branch(0x80004000, 0x80004006)


def test_encode_ppc_unconditional_branch_rejects_absolute_out_of_range() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="absolute range"):
        dol_patcher.encode_ppc_unconditional_branch(0x80004000, 0x80000000, absolute=True)


def test_patch_guarded_instruction_word_success() -> None:
    original = _build_synthetic_dol(
        _make_fake_version(),
        include_build_string=False,
        text_sections=[(0x100, 0x80004000, b"\x60\x00\x00\x00")],
    )

    patched, result = dol_patcher.patch_guarded_instruction_word(
        original,
        address=0x80004000,
        expected_original_word=0x60000000,
        replacement_word=0x48000008,
    )

    assert patched[0x100:0x104] == (0x48000008).to_bytes(4, "big")
    assert result.file_offset == 0x100
    assert result.changed is True


def test_patch_guarded_instruction_word_rejects_unexpected_original_instruction() -> None:
    original = _build_synthetic_dol(
        _make_fake_version(),
        include_build_string=False,
        text_sections=[(0x100, 0x80004000, b"\x60\x00\x00\x00")],
    )

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="expected 0x60000001"):
        dol_patcher.patch_guarded_instruction_word(
            original,
            address=0x80004000,
            expected_original_word=0x60000001,
            replacement_word=0x48000008,
        )


def test_patch_guarded_instruction_word_rejects_data_target() -> None:
    original = _build_synthetic_dol(
        _make_fake_version(),
        include_build_string=False,
        data_sections=[(0x100, 0x80590000, b"\x60\x00\x00\x00")],
    )

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="not text"):
        dol_patcher.patch_guarded_instruction_word(
            original,
            address=0x80590000,
            expected_original_word=0x60000000,
            replacement_word=0x48000008,
        )


def test_patch_guarded_instruction_word_rejects_unmapped_target() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="not mapped"):
        dol_patcher.patch_guarded_instruction_word(
            _build_synthetic_dol(_make_fake_version(), include_build_string=False),
            address=0x81234567,
            expected_original_word=0,
            replacement_word=0,
        )


def test_patch_guarded_instruction_word_rejects_already_patched_instruction() -> None:
    original = _build_synthetic_dol(
        _make_fake_version(),
        include_build_string=False,
        text_sections=[(0x100, 0x80004000, (0x48000008).to_bytes(4, "big"))],
    )

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="already contains the replacement"):
        dol_patcher.patch_guarded_instruction_word(
            original,
            address=0x80004000,
            expected_original_word=0x60000000,
            replacement_word=0x48000008,
        )


def test_build_single_instruction_trampoline_success() -> None:
    plan = dol_patcher.build_single_instruction_trampoline(
        hook_address=0x80004000,
        expected_original_instruction=0x60000000,
        payload_entry_address=0x80510000,
        trampoline_address=0x80510010,
    )

    assert plan.hook_patch.instruction_word == dol_patcher.encode_ppc_unconditional_branch(0x80004000, 0x80510000)
    assert plan.displaced_instruction_word == 0x60000000
    assert plan.return_branch.instruction_word == dol_patcher.encode_ppc_unconditional_branch(0x80510014, 0x80004004)


def test_build_single_instruction_trampoline_supports_payload_relative_offset() -> None:
    plan = dol_patcher.build_single_instruction_trampoline(
        hook_address=0x80004000,
        expected_original_instruction=0x60000000,
        payload_entry_address=0x80510000,
        trampoline_offset_from_payload=0x20,
    )

    assert plan.trampoline_address == 0x80510020


def test_build_single_instruction_trampoline_rejects_relative_branch_displacement() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="not safe to displace"):
        dol_patcher.build_single_instruction_trampoline(
            hook_address=0x80004000,
            expected_original_instruction=0x48000008,
            payload_entry_address=0x80510000,
            trampoline_address=0x80510010,
        )


def test_build_single_instruction_trampoline_rejects_control_flow_instruction() -> None:
    bc_word = 0x40820008
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="not safe to displace"):
        dol_patcher.build_single_instruction_trampoline(
            hook_address=0x80004000,
            expected_original_instruction=bc_word,
            payload_entry_address=0x80510000,
            trampoline_address=0x80510010,
        )


def test_build_single_instruction_trampoline_rejects_missing_trampoline_location() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="required"):
        dol_patcher.build_single_instruction_trampoline(
            hook_address=0x80004000,
            expected_original_instruction=0x60000000,
            payload_entry_address=0x80510000,
        )


def test_payload_artifact_json_round_trip() -> None:
    artifact = dol_patcher.Prime3PayloadArtifact.create(
        payload_bytes=b"\x60\x00\x00\x00",
        load_address=0x80510000,
        entry_symbol_offset=0,
        required_alignment=0x20,
        protocol_manifest_version="prime3-wii-v1",
        build_tool_identity="synthetic-test",
        build_tool_version="1.0",
        source_digest="deadbeef",
    )

    round_trip = dol_patcher.Prime3PayloadArtifact.from_json(artifact.as_json)

    assert round_trip == artifact
    assert round_trip.entry_symbol_address == 0x80510000


def test_payload_artifact_rejects_invalid_hash() -> None:
    artifact = dol_patcher.Prime3PayloadArtifact.create(
        payload_bytes=b"\x60\x00\x00\x00",
        load_address=0x80510000,
        entry_symbol_offset=0,
        required_alignment=0x20,
        protocol_manifest_version="prime3-wii-v1",
        build_tool_identity="synthetic-test",
        build_tool_version="1.0",
        source_digest="deadbeef",
    )
    payload = dict(artifact.as_json)
    payload["payload_sha256"] = "0" * 64

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="hash mismatch"):
        dol_patcher.Prime3PayloadArtifact.from_json(payload)


def test_payload_artifact_rejects_invalid_alignment() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="power of two"):
        dol_patcher.Prime3PayloadArtifact.create(
            payload_bytes=b"\x60\x00\x00\x00",
            load_address=0x80510000,
            entry_symbol_offset=0,
            required_alignment=24,
            protocol_manifest_version="prime3-wii-v1",
            build_tool_identity="synthetic-test",
            build_tool_version="1.0",
            source_digest="deadbeef",
        )


def test_payload_artifact_rejects_invalid_entry_offset() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="outside payload size"):
        dol_patcher.Prime3PayloadArtifact.create(
            payload_bytes=b"\x60\x00\x00\x00",
            load_address=0x80510000,
            entry_symbol_offset=8,
            required_alignment=0x20,
            protocol_manifest_version="prime3-wii-v1",
            build_tool_identity="synthetic-test",
            build_tool_version="1.0",
            source_digest="deadbeef",
        )


def test_atomic_replace_file(tmp_path: Path) -> None:
    path = tmp_path.joinpath("main.dol")
    path.write_bytes(b"old")

    dol_patcher.atomic_replace_file(path, b"new")

    assert path.read_bytes() == b"new"


def test_atomic_replace_file_surfaces_write_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path.joinpath("main.dol")
    path.write_bytes(b"old")

    def fake_replace(self: Path, target: Path) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fake_replace)

    with pytest.raises(OSError, match="replace failed"):
        dol_patcher.atomic_replace_file(path, b"new")


def test_patch_prime3_corruption_dol_file_atomic(tmp_path: Path) -> None:
    version = _make_fake_version()
    path = tmp_path.joinpath("main.dol")
    path.write_bytes(_build_synthetic_dol(version))

    result = dol_patcher.patch_prime3_corruption_dol_file_atomic(
        path,
        uuid.UUID("12345678-1234-5678-1234-567812345678"),
        versions=(version,),
    )

    assert path.read_bytes()[0x126:0x136] == uuid.UUID("12345678-1234-5678-1234-567812345678").bytes
    assert result.layout_uuid == uuid.UUID("12345678-1234-5678-1234-567812345678")
