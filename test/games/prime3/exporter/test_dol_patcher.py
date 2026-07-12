from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING, Any

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions
from retro_data_structures.game_check import Game as RDSGame

from randovania.games.prime3.exporter import dol_patcher

if TYPE_CHECKING:
    import os
    from pathlib import Path


@dataclasses.dataclass(frozen=True)
class FakeVersion:
    game: RDSGame
    description: str
    build_string_address: int
    build_string: bytes


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
    section_file_offset: int = 0x100,
    section_size: int | None = None,
    build_string_bytes: bytes | None = None,
    extra_mutations: dict[int, int] | None = None,
) -> bytes:
    section_address = version.build_string_address - 0x20 if section_address is None else section_address
    in_section_offset = version.build_string_address - section_address
    section_size = max((section_size or 0), in_section_offset + len(version.build_string) + 0x20)
    build_string_bytes = version.build_string if build_string_bytes is None else build_string_bytes

    data = bytearray(max(section_file_offset + section_size, 0x100))
    data[0:4] = section_file_offset.to_bytes(4, "big")
    data[0x48:0x4C] = section_address.to_bytes(4, "big")
    data[0x90:0x94] = section_size.to_bytes(4, "big")
    start = section_file_offset + in_section_offset
    end = start + len(build_string_bytes)
    data[start:end] = build_string_bytes

    for offset, value in (extra_mutations or {}).items():
        data[offset] = value

    return bytes(data)


def test_parse_dol_sections_success() -> None:
    version = _make_fake_version()
    data = _build_synthetic_dol(version)

    sections = dol_patcher.parse_dol_sections(data)

    assert sections == (dol_patcher.DolSection(index=0, file_offset=0x100, address=0x80500000, size=0x5A),)


def test_virtual_address_to_file_offset_maps_build_string() -> None:
    version = _make_fake_version()
    data = _build_synthetic_dol(version)
    sections = dol_patcher.parse_dol_sections(data)

    file_offset = dol_patcher.virtual_address_to_file_offset(
        sections,
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
    assert patched[0x100:0x120] == original[0x100:0x120]
    assert patched[0x136:] == original[0x136:]
    assert patched[0x126:0x136] == layout_uuid.bytes
    assert result == dol_patcher.Prime3DolPatchResult(
        version_description="Synthetic Corruption",
        build_string_address=version.build_string_address,
        build_string_offset=0x126,
        layout_uuid=layout_uuid,
        previous_layout_uuid=None,
        changed=True,
        bytes_changed=16,
    )


def test_patch_prime3_corruption_dol_is_idempotent() -> None:
    version = _make_fake_version()
    layout_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    original = _build_synthetic_dol(version)

    first_patched, _ = dol_patcher.patch_prime3_corruption_dol(original, layout_uuid, version=version)
    second_patched, result = dol_patcher.patch_prime3_corruption_dol(first_patched, layout_uuid, version=version)

    assert second_patched == first_patched
    assert result.changed is False
    assert result.bytes_changed == 0
    assert result.previous_layout_uuid == layout_uuid


def test_patch_prime3_corruption_dol_rejects_conflicting_uuid() -> None:
    version = _make_fake_version()
    existing_uuid = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    desired_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    build_string = bytearray(version.build_string)
    build_string[6:22] = existing_uuid.bytes
    data = _build_synthetic_dol(version, build_string_bytes=bytes(build_string))

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="conflicting layout UUID"):
        dol_patcher.patch_prime3_corruption_dol(data, desired_uuid, version=version)


def test_identify_supported_corruption_version_accepts_real_metadata() -> None:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    data = _build_synthetic_dol(version, section_address=version.build_string_address - 0x20)

    identified = dol_patcher.identify_supported_corruption_version(data)

    assert identified is version


def test_identify_supported_corruption_version_rejects_non_corruption_candidates() -> None:
    version = _make_fake_version()
    data = _build_synthetic_dol(version)
    wrong_game_version = dataclasses.replace(version, game=RDSGame.PRIME)

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="Unsupported non-Corruption"):
        dol_patcher.identify_supported_corruption_version(data, versions=(wrong_game_version,))


def test_identify_supported_corruption_version_rejects_unknown_build() -> None:
    version = _make_fake_version()
    bad_build = version.build_string[:-1] + b"X"
    data = _build_synthetic_dol(version, build_string_bytes=bad_build)

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="Unsupported or unknown"):
        dol_patcher.identify_supported_corruption_version(data, versions=(version,))


def test_patch_prime3_corruption_dol_rejects_unexpected_build_string() -> None:
    version = _make_fake_version()
    data = bytearray(_build_synthetic_dol(version))
    data[0x125] ^= 0x01

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="Unexpected build string bytes"):
        dol_patcher.patch_prime3_corruption_dol(bytes(data), uuid.uuid4(), version=version)


def test_virtual_address_to_file_offset_rejects_unmapped_address() -> None:
    version = _make_fake_version()
    sections = dol_patcher.parse_dol_sections(_build_synthetic_dol(version))

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="is not mapped"):
        dol_patcher.virtual_address_to_file_offset(sections, 0x80600000, 4)


def test_parse_dol_sections_rejects_truncated_dol() -> None:
    with pytest.raises(dol_patcher.Prime3DolPatchError, match="truncated before the header"):
        dol_patcher.parse_dol_sections(b"\x00" * 0xFF)


def test_parse_dol_sections_rejects_malformed_section() -> None:
    data = bytearray(b"\x00" * 0x100)
    data[0x90:0x94] = (4).to_bytes(4, "big")

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="non-zero address"):
        dol_patcher.parse_dol_sections(bytes(data))


def test_parse_dol_sections_rejects_file_overlap() -> None:
    data = bytearray(b"\x00" * 0x200)
    data[0:4] = (0x100).to_bytes(4, "big")
    data[4:8] = (0x110).to_bytes(4, "big")
    data[0x48:0x4C] = (0x80500000).to_bytes(4, "big")
    data[0x4C:0x50] = (0x80500100).to_bytes(4, "big")
    data[0x90:0x94] = (0x20).to_bytes(4, "big")
    data[0x94:0x98] = (0x20).to_bytes(4, "big")

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="overlap in file space"):
        dol_patcher.parse_dol_sections(bytes(data))


def test_parse_dol_sections_rejects_address_overlap() -> None:
    data = bytearray(b"\x00" * 0x240)
    data[0:4] = (0x100).to_bytes(4, "big")
    data[4:8] = (0x120).to_bytes(4, "big")
    data[0x48:0x4C] = (0x80500000).to_bytes(4, "big")
    data[0x4C:0x50] = (0x80500010).to_bytes(4, "big")
    data[0x90:0x94] = (0x20).to_bytes(4, "big")
    data[0x94:0x98] = (0x20).to_bytes(4, "big")

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="overlap in virtual address space"):
        dol_patcher.parse_dol_sections(bytes(data))


def test_atomic_replace_file(tmp_path: Path) -> None:
    path = tmp_path.joinpath("main.dol")
    path.write_bytes(b"old")

    dol_patcher.atomic_replace_file(path, b"new")

    assert path.read_bytes() == b"new"
    assert not any(
        candidate.name.startswith("main.dol.") and candidate.suffix == ".tmp" for candidate in tmp_path.iterdir()
    )


def test_patch_prime3_corruption_dol_file_atomic(tmp_path: Path) -> None:
    version = _make_fake_version()
    path = tmp_path.joinpath("main.dol")
    path.write_bytes(_build_synthetic_dol(version))
    layout_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")

    result = dol_patcher.patch_prime3_corruption_dol_file_atomic(path, layout_uuid, versions=(version,))

    assert path.read_bytes()[0x126:0x136] == layout_uuid.bytes
    assert result.layout_uuid == layout_uuid


def test_atomic_replace_file_surfaces_write_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path.joinpath("main.dol")
    path.write_bytes(b"old")

    def fake_replace(src: str, dst: os.PathLike[str] | str) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(dol_patcher.os, "replace", fake_replace)

    with pytest.raises(OSError, match="replace failed"):
        dol_patcher.atomic_replace_file(path, b"new")
