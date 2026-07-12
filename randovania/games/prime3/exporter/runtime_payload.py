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
        return {
            "compiler_identity": self.compiler_identity,
            "compiler_version": self.compiler_version,
            "dynamic_section_count": self.dynamic_section_count,
            "entry_symbol_name": self.entry_symbol_name,
            "entry_symbol_offset": self.entry_symbol_offset,
            "linker_identity": self.linker_identity,
            "linker_version": self.linker_version,
            "payload_sha256": self.payload_sha256,
            "payload_size": self.payload_size,
            "protocol_artifact_version": self.protocol_artifact_version,
            "required_alignment": self.required_alignment,
            "schema_version": self.schema_version,
            "source_digest": self.source_digest,
            "target_abi": self.target_abi,
            "target_architecture": self.target_architecture,
            "target_endianness": self.target_endianness,
            "unresolved_relocation_count": self.unresolved_relocation_count,
        }

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
            "protocol_artifact_version",
            "required_alignment",
            "schema_version",
            "source_digest",
            "target_abi",
            "target_architecture",
            "target_endianness",
            "unresolved_relocation_count",
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
            required_alignment=_json_int(data, "required_alignment"),
            entry_symbol_name=_json_string(data, "entry_symbol_name"),
            entry_symbol_offset=_json_int(data, "entry_symbol_offset"),
            source_digest=_json_string(data, "source_digest"),
            protocol_artifact_version=_json_int(data, "protocol_artifact_version"),
            unresolved_relocation_count=_json_int(data, "unresolved_relocation_count"),
            dynamic_section_count=_json_int(data, "dynamic_section_count"),
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
