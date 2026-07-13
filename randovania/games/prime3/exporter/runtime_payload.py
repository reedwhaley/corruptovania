from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game_connection.executor.prime3_wii_protocol import PROTOCOL_VERSION
from randovania.games.prime3.exporter.dol_patcher import Prime3DolPatchError, Prime3PayloadArtifact

if TYPE_CHECKING:
    from collections.abc import Iterable

PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION = 1
PRIME3_RUNTIME_TARGET_ARCHITECTURE = "powerpc"
PRIME3_RUNTIME_TARGET_ENDIANNESS = "big"
PRIME3_RUNTIME_TARGET_ABI = "eabi"
PRIME3_RUNTIME_REQUIRED_ALIGNMENT = 0x20
PRIME3_RUNTIME_ENTRY_SYMBOL = "payload_entry"
PRIME3_RUNTIME_PAYLOAD_MODE_NORMAL = "normal"
PRIME3_RUNTIME_PAYLOAD_MODE_PROBE = "probe"
PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT = "entry_bootstrap_halt"
PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_CONTINUE = "entry_bootstrap_continue"
PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES = (
    PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT,
    PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_CONTINUE,
)


@dataclasses.dataclass(frozen=True)
class Prime3EntryBootstrapMetadata:
    mode: str
    staging_address: int
    staging_save_area_offset: int
    staging_save_area_size: int
    halt_loop_address: int | None
    reserved_boundary: int
    reserved_range_start: int
    reserved_range_end: int
    diagnostic_address: int
    diagnostic_block_size: int
    canary_address: int
    canary_size: int
    canary_sha256: str
    marker_address: int
    marker_value: int
    counter_address: int
    counter_size: int
    original_80000034_address: int
    original_80003110_address: int
    replacement_value_address: int
    replacement_value: int
    status_address: int
    status_value: int
    original_entry_instruction: int
    original_branch_target: int
    original_continuation_address: int

    def validate(self, *, payload_size: int) -> None:
        if self.mode not in PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES:
            raise Prime3DolPatchError(f"Unsupported Prime 3 entry bootstrap mode {self.mode!r}.")
        _validate_optional_range(
            payload_size=payload_size,
            field_name="staging_save_area_offset",
            start=self.staging_save_area_offset,
            size=self.staging_save_area_size,
        )
        if self.halt_loop_address is not None and not (
            self.staging_address <= self.halt_loop_address < self.staging_address + payload_size
        ):
            raise Prime3DolPatchError("Entry bootstrap halt loop address is outside the staged payload range.")
        if self.mode == PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT and self.halt_loop_address is None:
            raise Prime3DolPatchError("Entry bootstrap halt mode requires a halt loop address.")
        if self.mode == PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_CONTINUE and self.halt_loop_address is not None:
            raise Prime3DolPatchError("Entry bootstrap continue mode must not define a halt loop address.")
        if self.reserved_range_start != self.reserved_boundary:
            raise Prime3DolPatchError("Entry bootstrap reserved range must start at the reserved boundary.")
        if self.reserved_range_end <= self.reserved_range_start:
            raise Prime3DolPatchError("Entry bootstrap reserved range end must be above the reserved range start.")
        if not (self.reserved_range_start <= self.diagnostic_address < self.reserved_range_end):
            raise Prime3DolPatchError("Entry bootstrap diagnostic block address is outside the reserved range.")
        if self.diagnostic_address + self.diagnostic_block_size > self.reserved_range_end:
            raise Prime3DolPatchError("Entry bootstrap diagnostic block exceeds the reserved range.")

        occupied_ranges = (
            ("canary", self.canary_address, self.canary_size),
            ("marker", self.marker_address, 4),
            ("counter", self.counter_address, self.counter_size),
            ("original_80000034", self.original_80000034_address, 4),
            ("original_80003110", self.original_80003110_address, 4),
            ("replacement_value", self.replacement_value_address, 4),
            ("status", self.status_address, 4),
        )
        for name, start, size in occupied_ranges:
            if not (self.reserved_range_start <= start < self.reserved_range_end):
                raise Prime3DolPatchError(f"Entry bootstrap field {name} is outside the reserved range.")
            if start + size > self.reserved_range_end:
                raise Prime3DolPatchError(f"Entry bootstrap field {name} exceeds the reserved range.")
        for index, (first_name, first_start, first_size) in enumerate(occupied_ranges):
            first_end = first_start + first_size
            for second_name, second_start, second_size in occupied_ranges[index + 1 :]:
                second_end = second_start + second_size
                if first_start < second_end and second_start < first_end:
                    raise Prime3DolPatchError(
                        f"Entry bootstrap fields {first_name} and {second_name} overlap in the reserved range."
                    )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "staging_address": self.staging_address,
            "staging_save_area_offset": self.staging_save_area_offset,
            "staging_save_area_size": self.staging_save_area_size,
            "halt_loop_address": self.halt_loop_address,
            "reserved_boundary": self.reserved_boundary,
            "reserved_range_start": self.reserved_range_start,
            "reserved_range_end": self.reserved_range_end,
            "diagnostic_address": self.diagnostic_address,
            "diagnostic_block_size": self.diagnostic_block_size,
            "canary_address": self.canary_address,
            "canary_size": self.canary_size,
            "canary_sha256": self.canary_sha256,
            "marker_address": self.marker_address,
            "marker_value": self.marker_value,
            "counter_address": self.counter_address,
            "counter_size": self.counter_size,
            "original_80000034_address": self.original_80000034_address,
            "original_80003110_address": self.original_80003110_address,
            "replacement_value_address": self.replacement_value_address,
            "replacement_value": self.replacement_value,
            "status_address": self.status_address,
            "status_value": self.status_value,
            "original_entry_instruction": self.original_entry_instruction,
            "original_branch_target": self.original_branch_target,
            "original_continuation_address": self.original_continuation_address,
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, object], *, payload_size: int) -> Prime3EntryBootstrapMetadata:
        metadata = cls(
            mode=_json_string(data, "mode"),
            staging_address=_json_int(data, "staging_address"),
            staging_save_area_offset=_json_int(data, "staging_save_area_offset"),
            staging_save_area_size=_json_int(data, "staging_save_area_size"),
            halt_loop_address=_json_optional_int(data, "halt_loop_address"),
            reserved_boundary=_json_int(data, "reserved_boundary"),
            reserved_range_start=_json_int(data, "reserved_range_start"),
            reserved_range_end=_json_int(data, "reserved_range_end"),
            diagnostic_address=_json_int(data, "diagnostic_address"),
            diagnostic_block_size=_json_int(data, "diagnostic_block_size"),
            canary_address=_json_int(data, "canary_address"),
            canary_size=_json_int(data, "canary_size"),
            canary_sha256=_json_string(data, "canary_sha256"),
            marker_address=_json_int(data, "marker_address"),
            marker_value=_json_int(data, "marker_value"),
            counter_address=_json_int(data, "counter_address"),
            counter_size=_json_int(data, "counter_size"),
            original_80000034_address=_json_int(data, "original_80000034_address"),
            original_80003110_address=_json_int(data, "original_80003110_address"),
            replacement_value_address=_json_int(data, "replacement_value_address"),
            replacement_value=_json_int(data, "replacement_value"),
            status_address=_json_int(data, "status_address"),
            status_value=_json_int(data, "status_value"),
            original_entry_instruction=_json_int(data, "original_entry_instruction"),
            original_branch_target=_json_int(data, "original_branch_target"),
            original_continuation_address=_json_int(data, "original_continuation_address"),
        )
        metadata.validate(payload_size=payload_size)
        return metadata


@dataclasses.dataclass(frozen=True)
class Prime3RuntimePayloadManifest:
    schema_version: int
    target_architecture: str
    target_endianness: str
    target_abi: str
    compiler_identity: str
    compiler_version: str
    linker_identity: str
    linker_version: str
    payload_sha256: str
    payload_size: int
    required_alignment: int
    entry_symbol_name: str
    entry_symbol_offset: int
    source_digest: str
    protocol_artifact_version: int
    unresolved_relocation_count: int
    dynamic_section_count: int
    payload_mode: str = PRIME3_RUNTIME_PAYLOAD_MODE_NORMAL
    canary_start_offset: int | None = None
    canary_size: int | None = None
    counter_offset: int | None = None
    counter_size: int | None = None
    entry_bootstrap: Prime3EntryBootstrapMetadata | None = None

    def validate(self) -> None:
        if self.schema_version != PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION:
            raise Prime3DolPatchError(
                f"Unsupported Prime 3 runtime payload schema version {self.schema_version}; "
                f"expected {PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION}."
            )
        if self.target_architecture != PRIME3_RUNTIME_TARGET_ARCHITECTURE:
            raise Prime3DolPatchError(
                f"Unsupported payload architecture {self.target_architecture!r}; "
                f"expected {PRIME3_RUNTIME_TARGET_ARCHITECTURE!r}."
            )
        if self.target_endianness != PRIME3_RUNTIME_TARGET_ENDIANNESS:
            raise Prime3DolPatchError(
                f"Unsupported payload endianness {self.target_endianness!r}; "
                f"expected {PRIME3_RUNTIME_TARGET_ENDIANNESS!r}."
            )
        if self.target_abi != PRIME3_RUNTIME_TARGET_ABI:
            raise Prime3DolPatchError(
                f"Unsupported payload ABI {self.target_abi!r}; expected {PRIME3_RUNTIME_TARGET_ABI!r}."
            )
        if self.payload_size < 0:
            raise Prime3DolPatchError(f"Payload size must be non-negative, got {self.payload_size}.")
        if self.entry_symbol_offset < 0 or self.entry_symbol_offset > self.payload_size:
            raise Prime3DolPatchError(
                f"Payload entry offset {self.entry_symbol_offset} is outside payload size {self.payload_size}."
            )
        if self.unresolved_relocation_count != 0:
            raise Prime3DolPatchError(
                f"Payload manifest reports {self.unresolved_relocation_count} unresolved relocations."
            )
        if self.dynamic_section_count != 0:
            raise Prime3DolPatchError(f"Payload manifest reports {self.dynamic_section_count} dynamic sections.")
        if self.protocol_artifact_version != PROTOCOL_VERSION:
            raise Prime3DolPatchError(
                f"Payload protocol version {self.protocol_artifact_version!r} does not match {PROTOCOL_VERSION!r}."
            )
        if self.payload_mode not in (
            PRIME3_RUNTIME_PAYLOAD_MODE_NORMAL,
            PRIME3_RUNTIME_PAYLOAD_MODE_PROBE,
            *PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES,
        ):
            raise Prime3DolPatchError(f"Unsupported payload mode {self.payload_mode!r}.")
        _validate_optional_range(
            payload_size=self.payload_size,
            field_name="canary_start_offset",
            start=self.canary_start_offset,
            size=self.canary_size,
        )
        _validate_optional_range(
            payload_size=self.payload_size,
            field_name="counter_offset",
            start=self.counter_offset,
            size=self.counter_size,
        )
        if self.entry_bootstrap is None and self.payload_mode in PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES:
            raise Prime3DolPatchError("Entry bootstrap payload mode requires entry bootstrap metadata.")
        if self.entry_bootstrap is not None:
            self.entry_bootstrap.validate(payload_size=self.payload_size)
            if self.payload_mode != self.entry_bootstrap.mode:
                raise Prime3DolPatchError("Payload mode does not match entry bootstrap metadata mode.")
        Prime3PayloadArtifact.create(
            payload_bytes=b"\x00" * self.payload_size,
            load_address=0,
            entry_symbol_offset=self.entry_symbol_offset,
            required_alignment=self.required_alignment,
            protocol_manifest_version=str(self.protocol_artifact_version),
            build_tool_identity=self.compiler_identity,
            build_tool_version=self.compiler_version,
            source_digest=self.source_digest,
        )

    def to_json_dict(self) -> dict[str, object]:
        result = {
            "compiler_identity": self.compiler_identity,
            "compiler_version": self.compiler_version,
            "dynamic_section_count": self.dynamic_section_count,
            "entry_symbol_name": self.entry_symbol_name,
            "entry_symbol_offset": self.entry_symbol_offset,
            "linker_identity": self.linker_identity,
            "linker_version": self.linker_version,
            "payload_sha256": self.payload_sha256,
            "payload_size": self.payload_size,
            "payload_mode": self.payload_mode,
            "protocol_artifact_version": self.protocol_artifact_version,
            "required_alignment": self.required_alignment,
            "schema_version": self.schema_version,
            "source_digest": self.source_digest,
            "target_abi": self.target_abi,
            "target_architecture": self.target_architecture,
            "target_endianness": self.target_endianness,
            "unresolved_relocation_count": self.unresolved_relocation_count,
        }
        if self.canary_start_offset is not None:
            result["canary_start_offset"] = self.canary_start_offset
            result["canary_size"] = self.canary_size
        if self.counter_offset is not None:
            result["counter_offset"] = self.counter_offset
            result["counter_size"] = self.counter_size
        if self.entry_bootstrap is not None:
            result["entry_bootstrap"] = self.entry_bootstrap.to_json_dict()
        return result

    def to_json_text(self) -> str:
        return json.dumps(self.to_json_dict(), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_json_dict(cls, data: dict[str, object]) -> Prime3RuntimePayloadManifest:
        required_keys = {
            "compiler_identity",
            "compiler_version",
            "dynamic_section_count",
            "entry_symbol_name",
            "entry_symbol_offset",
            "linker_identity",
            "linker_version",
            "payload_sha256",
            "payload_size",
            "payload_mode",
            "protocol_artifact_version",
            "required_alignment",
            "schema_version",
            "source_digest",
            "target_abi",
            "target_architecture",
            "target_endianness",
            "unresolved_relocation_count",
            "canary_start_offset",
            "canary_size",
            "counter_offset",
            "counter_size",
            "entry_bootstrap",
        }
        unknown_keys = set(data) - required_keys
        if unknown_keys:
            raise Prime3DolPatchError(f"Unknown Prime 3 runtime payload manifest keys: {sorted(unknown_keys)}")

        manifest = cls(
            schema_version=_json_int(data, "schema_version"),
            target_architecture=_json_string(data, "target_architecture"),
            target_endianness=_json_string(data, "target_endianness"),
            target_abi=_json_string(data, "target_abi"),
            compiler_identity=_json_string(data, "compiler_identity"),
            compiler_version=_json_string(data, "compiler_version"),
            linker_identity=_json_string(data, "linker_identity"),
            linker_version=_json_string(data, "linker_version"),
            payload_sha256=_json_string(data, "payload_sha256"),
            payload_size=_json_int(data, "payload_size"),
            payload_mode=_json_string(data, "payload_mode"),
            required_alignment=_json_int(data, "required_alignment"),
            entry_symbol_name=_json_string(data, "entry_symbol_name"),
            entry_symbol_offset=_json_int(data, "entry_symbol_offset"),
            source_digest=_json_string(data, "source_digest"),
            protocol_artifact_version=_json_int(data, "protocol_artifact_version"),
            unresolved_relocation_count=_json_int(data, "unresolved_relocation_count"),
            dynamic_section_count=_json_int(data, "dynamic_section_count"),
            canary_start_offset=_json_optional_int(data, "canary_start_offset"),
            canary_size=_json_optional_int(data, "canary_size"),
            counter_offset=_json_optional_int(data, "counter_offset"),
            counter_size=_json_optional_int(data, "counter_size"),
            entry_bootstrap=_json_optional_entry_bootstrap(
                data,
                "entry_bootstrap",
                payload_size=_json_int(data, "payload_size"),
            ),
        )
        manifest.validate()
        return manifest

    @classmethod
    def from_json_text(cls, text: str) -> Prime3RuntimePayloadManifest:
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise Prime3DolPatchError(f"Invalid Prime 3 runtime payload manifest JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise Prime3DolPatchError("Prime 3 runtime payload manifest must be a JSON object.")
        return cls.from_json_dict(raw)


def compute_source_digest(source_root: Path, relative_paths: Iterable[str | Path]) -> str:
    digest = hashlib.sha256()
    for relative_path in sorted((Path(path) for path in relative_paths), key=lambda path: path.as_posix()):
        digest.update(relative_path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(source_root.joinpath(relative_path).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_prime3_runtime_payload_artifact(
    *,
    manifest_path: Path,
    payload_path: Path,
    load_address: int,
) -> Prime3PayloadArtifact:
    manifest = Prime3RuntimePayloadManifest.from_json_text(manifest_path.read_text(encoding="utf-8"))
    payload_bytes = payload_path.read_bytes()
    actual_hash = hashlib.sha256(payload_bytes).hexdigest()
    if actual_hash != manifest.payload_sha256:
        raise Prime3DolPatchError(
            f"Payload hash mismatch for {payload_path}: expected {manifest.payload_sha256}, got {actual_hash}."
        )
    if len(payload_bytes) != manifest.payload_size:
        raise Prime3DolPatchError(
            f"Payload size mismatch for {payload_path}: expected {manifest.payload_size}, got {len(payload_bytes)}."
        )

    build_tool_identity = f"{manifest.compiler_identity} + {manifest.linker_identity}"
    build_tool_version = f"{manifest.compiler_version} / {manifest.linker_version}"
    return Prime3PayloadArtifact.create(
        payload_bytes=payload_bytes,
        load_address=load_address,
        entry_symbol_offset=manifest.entry_symbol_offset,
        required_alignment=manifest.required_alignment,
        protocol_manifest_version=str(manifest.protocol_artifact_version),
        build_tool_identity=build_tool_identity,
        build_tool_version=build_tool_version,
        source_digest=manifest.source_digest,
    )


def _json_int(data: dict[str, object], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be an integer.")
    return value


def _json_string(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be a string.")
    return value


def _json_optional_int(data: dict[str, object], key: str) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, int):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be an integer when present.")
    return value


def _json_optional_entry_bootstrap(
    data: dict[str, object],
    key: str,
    *,
    payload_size: int,
) -> Prime3EntryBootstrapMetadata | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise Prime3DolPatchError(f"Prime 3 runtime payload manifest field {key!r} must be an object when present.")
    return Prime3EntryBootstrapMetadata.from_json_dict(value, payload_size=payload_size)


def _json_optional_int(data: dict[str, object], key: str) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, int):
        raise Prime3DolPatchError(f"Expected integer for Prime 3 runtime payload manifest field {key!r}.")
    return value


def _validate_optional_range(*, payload_size: int, field_name: str, start: int | None, size: int | None) -> None:
    if start is None and size is None:
        return
    if start is None or size is None:
        raise Prime3DolPatchError(f"Payload manifest must provide both {field_name} and its size together.")
    if size <= 0:
        raise Prime3DolPatchError(f"Payload manifest field {field_name!r} size must be positive, got {size}.")
    if start < 0 or start + size > payload_size:
        raise Prime3DolPatchError(
            f"Payload manifest field {field_name!r} range {start}..{start + size} "
            f"is outside payload size {payload_size}."
        )
