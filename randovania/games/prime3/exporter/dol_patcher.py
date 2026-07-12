from __future__ import annotations

import dataclasses
import os
import tempfile
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions
from retro_data_structures.game_check import Game as RDSGame

if TYPE_CHECKING:
    from collections.abc import Iterable

_DOL_HEADER_SIZE = 0x100
_DOL_SECTION_COUNT = 18
_UUID_START = 6
_UUID_LENGTH = 16


class Prime3DolPatchError(RuntimeError):
    """Raised when a Prime 3 DOL cannot be validated or patched safely."""


class CorruptionDolVersionLike(Protocol):
    game: RDSGame
    description: str
    build_string_address: int
    build_string: bytes


@dataclasses.dataclass(frozen=True)
class DolSection:
    index: int
    file_offset: int
    address: int
    size: int

    @property
    def end_address(self) -> int:
        return self.address + self.size

    @property
    def end_offset(self) -> int:
        return self.file_offset + self.size


@dataclasses.dataclass(frozen=True)
class Prime3DolPatchResult:
    version_description: str
    build_string_address: int
    build_string_offset: int
    layout_uuid: uuid.UUID
    previous_layout_uuid: uuid.UUID | None
    changed: bool
    bytes_changed: int


def _read_u32_be(data: bytes | bytearray, offset: int) -> int:
    end = offset + 4
    if end > len(data):
        raise Prime3DolPatchError("DOL header is truncated.")
    return int.from_bytes(data[offset:end], "big")


def parse_dol_sections(data: bytes | bytearray) -> tuple[DolSection, ...]:
    if len(data) < _DOL_HEADER_SIZE:
        raise Prime3DolPatchError("DOL file is truncated before the header is complete.")

    sections: list[DolSection] = []
    for index in range(_DOL_SECTION_COUNT):
        file_offset = _read_u32_be(data, index * 4)
        address = _read_u32_be(data, 0x48 + (index * 4))
        size = _read_u32_be(data, 0x90 + (index * 4))

        if size == 0:
            if file_offset != 0 or address != 0:
                raise Prime3DolPatchError(f"DOL section {index} is malformed: empty sections must be zeroed.")
            continue

        if address == 0:
            raise Prime3DolPatchError(f"DOL section {index} is malformed: mapped sections require a non-zero address.")
        if file_offset < _DOL_HEADER_SIZE:
            raise Prime3DolPatchError(
                f"DOL section {index} is malformed: file offset 0x{file_offset:08x} overlaps the header."
            )
        if file_offset + size > len(data):
            raise Prime3DolPatchError(
                f"DOL section {index} is truncated: 0x{file_offset:08x}+0x{size:x} exceeds file length 0x{len(data):x}."
            )

        sections.append(DolSection(index=index, file_offset=file_offset, address=address, size=size))

    sorted_sections = sorted(sections, key=lambda section: section.file_offset)
    for previous, current in zip(sorted_sections, sorted_sections[1:], strict=False):
        if current.file_offset < previous.end_offset:
            raise Prime3DolPatchError(
                f"DOL sections {previous.index} and {current.index} overlap in file space."
            )

    address_sorted_sections = sorted(sections, key=lambda section: section.address)
    for previous, current in zip(address_sorted_sections, address_sorted_sections[1:], strict=False):
        if current.address < previous.end_address:
            raise Prime3DolPatchError(
                f"DOL sections {previous.index} and {current.index} overlap in virtual address space."
            )

    return tuple(sections)


def virtual_address_to_file_offset(
    sections: Iterable[DolSection],
    address: int,
    size: int = 1,
) -> int:
    if size <= 0:
        raise Prime3DolPatchError(f"Address mapping size must be positive, got {size}.")

    for section in sections:
        if section.address <= address and address + size <= section.end_address:
            return section.file_offset + (address - section.address)

    raise Prime3DolPatchError(
        f"Virtual address 0x{address:08x} (+0x{size:x}) is not mapped by any DOL section."
    )


def _iter_supported_corruption_versions(
    versions: Iterable[CorruptionDolVersionLike] | None = None,
) -> tuple[CorruptionDolVersionLike, ...]:
    raw_versions: tuple[CorruptionDolVersionLike, ...]
    if versions is None:
        raw_versions = cast("tuple[CorruptionDolVersionLike, ...]", tuple(corruption_dol_versions.ALL_VERSIONS))
    else:
        raw_versions = tuple(versions)
    result = []
    for version in raw_versions:
        if version.game is not RDSGame.CORRUPTION:
            raise Prime3DolPatchError(f"Unsupported non-Corruption DOL version candidate: {version.description}")
        result.append(version)
    return tuple(result)


def _read_build_string_at_version(
    data: bytes | bytearray,
    sections: tuple[DolSection, ...],
    version: CorruptionDolVersionLike,
) -> tuple[int, bytes]:
    file_offset = virtual_address_to_file_offset(sections, version.build_string_address, len(version.build_string))
    observed = bytes(data[file_offset : file_offset + len(version.build_string)])
    return file_offset, observed


def identify_supported_corruption_version(
    data: bytes | bytearray,
    versions: Iterable[CorruptionDolVersionLike] | None = None,
) -> CorruptionDolVersionLike:
    sections = parse_dol_sections(data)
    matches = []
    for version in _iter_supported_corruption_versions(versions):
        try:
            _file_offset, observed = _read_build_string_at_version(data, sections, version)
        except Prime3DolPatchError:
            continue

        expected = bytearray(version.build_string)
        expected[_UUID_START : _UUID_START + _UUID_LENGTH] = observed[_UUID_START : _UUID_START + _UUID_LENGTH]
        if observed == expected:
            matches.append(version)

    if not matches:
        raise Prime3DolPatchError("Unsupported or unknown Metroid Prime 3: Corruption DOL version.")
    if len(matches) > 1:
        descriptions = ", ".join(version.description for version in matches)
        raise Prime3DolPatchError(f"Ambiguous Corruption DOL version match: {descriptions}")

    return matches[0]


def patch_prime3_corruption_dol(
    data: bytes | bytearray,
    layout_uuid: uuid.UUID,
    *,
    version: CorruptionDolVersionLike | None = None,
    versions: Iterable[CorruptionDolVersionLike] | None = None,
) -> tuple[bytes, Prime3DolPatchResult]:
    mutable = bytearray(data)
    sections = parse_dol_sections(mutable)
    selected_version = identify_supported_corruption_version(mutable, versions) if version is None else version

    supported_versions = _iter_supported_corruption_versions((selected_version,))
    selected_version = supported_versions[0]

    build_string_offset, observed = _read_build_string_at_version(mutable, sections, selected_version)

    expected = bytearray(selected_version.build_string)
    current_uuid_bytes = observed[_UUID_START : _UUID_START + _UUID_LENGTH]
    expected[_UUID_START : _UUID_START + _UUID_LENGTH] = current_uuid_bytes
    if observed != expected:
        raise Prime3DolPatchError(
            "Unexpected build string bytes for "
            f"{selected_version.description} at 0x{selected_version.build_string_address:08x}."
        )

    retail_bytes = selected_version.build_string[_UUID_START : _UUID_START + _UUID_LENGTH]
    previous_layout_uuid = None if current_uuid_bytes == retail_bytes else uuid.UUID(bytes=bytes(current_uuid_bytes))
    if previous_layout_uuid is not None and previous_layout_uuid != layout_uuid:
        raise Prime3DolPatchError(
            f"DOL already embeds conflicting layout UUID {previous_layout_uuid} for {selected_version.description}."
        )

    changed = current_uuid_bytes != layout_uuid.bytes
    mutable[build_string_offset + _UUID_START : build_string_offset + _UUID_START + _UUID_LENGTH] = layout_uuid.bytes

    result = Prime3DolPatchResult(
        version_description=selected_version.description,
        build_string_address=selected_version.build_string_address,
        build_string_offset=build_string_offset + _UUID_START,
        layout_uuid=layout_uuid,
        previous_layout_uuid=previous_layout_uuid,
        changed=changed,
        bytes_changed=_UUID_LENGTH if changed else 0,
    )
    return bytes(mutable), result


def atomic_replace_file(path: Path, data: bytes) -> None:
    path = Path(path)
    temp_fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f"{path.name}.", suffix=".tmp")
    temp_path = Path(temp_name)
    try:
        with os.fdopen(temp_fd, "wb") as temp_file:
            temp_file.write(data)
        temp_path.replace(path)
    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass
        raise


def patch_prime3_corruption_dol_file_atomic(
    path: Path,
    layout_uuid: uuid.UUID,
    *,
    versions: Iterable[CorruptionDolVersionLike] | None = None,
) -> Prime3DolPatchResult:
    original_data = path.read_bytes()
    patched_data, result = patch_prime3_corruption_dol(original_data, layout_uuid, versions=versions)
    atomic_replace_file(path, patched_data)
    return result
