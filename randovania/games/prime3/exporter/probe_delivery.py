from __future__ import annotations

import dataclasses
import hashlib
import json
from typing import TYPE_CHECKING, Any

from randovania.games.prime3.exporter.dol_patcher import (
    CorruptionDolVersionLike,
    DecodedBranchInstruction,
    DolHeader,
    GuardedInstructionPatchResult,
    Prime3DolPatchError,
    align_up,
    append_executable_text_section,
    decode_ppc_unconditional_branch,
    encode_ppc_unconditional_branch,
    identify_supported_corruption_version,
    parse_dol_header,
    patch_guarded_instruction_word,
)
from randovania.games.prime3.exporter.runtime_payload import Prime3RuntimePayloadManifest

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

ENTRY_GATE_ADDRESS = 0x80006320
EXPECTED_ENTRYPOINT = 0x80006320
EXPECTED_ENTRY_WORD = 0x4800016D
ENTRY_GATE_WORD = 0x48000000
ENTRY_CHECKPOINT_NAME = "entry"
MEM1_START = 0x80000000
MEM1_END = 0x81800000
OBSERVED_ENTRY_ARENA_HIGH = 0x817FE3A0


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
    checkpoint_gate: CheckpointGateResult | None = None
    entry_bootstrap: EntryBootstrapInstallResult | None = None
    relocated_runtime: RelocatedRuntimeInstallResult | None = None


@dataclasses.dataclass(frozen=True)
class CheckpointGateResult:
    checkpoint_name: str
    gate_address: int
    original_instruction: int
    replacement_instruction: int
    entrypoint: int
    file_offset: int
    text_section_name: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_name": self.checkpoint_name,
            "gate_address": self.gate_address,
            "original_instruction": self.original_instruction,
            "replacement_instruction": self.replacement_instruction,
            "entrypoint": self.entrypoint,
            "file_offset": self.file_offset,
            "text_section_name": self.text_section_name,
        }


@dataclasses.dataclass(frozen=True)
class EntryBootstrapInstallResult:
    bootstrap_mode: str
    entrypoint: int
    original_entry_instruction: int
    original_branch_target: int
    original_continuation_address: int
    bootstrap_address: int
    halt_loop_address: int | None
    bootstrap_size: int
    bootstrap_sha256: str
    replacement_instruction: int
    reserved_high: int
    original_observed_arena_high: int
    reserved_range_start: int
    reserved_range_end: int
    diagnostic_address: int
    diagnostic_block_size: int
    hook_installed: bool
    normal_exporter_integration: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "bootstrap_mode": self.bootstrap_mode,
            "entrypoint": self.entrypoint,
            "original_entry_instruction": self.original_entry_instruction,
            "original_branch_target": self.original_branch_target,
            "original_continuation_address": self.original_continuation_address,
            "bootstrap_address": self.bootstrap_address,
            "halt_loop_address": self.halt_loop_address,
            "bootstrap_size": self.bootstrap_size,
            "bootstrap_sha256": self.bootstrap_sha256,
            "replacement_instruction": self.replacement_instruction,
            "reserved_high": self.reserved_high,
            "original_observed_arena_high": self.original_observed_arena_high,
            "reserved_range_start": self.reserved_range_start,
            "reserved_range_end": self.reserved_range_end,
            "diagnostic_address": self.diagnostic_address,
            "diagnostic_block_size": self.diagnostic_block_size,
            "hook_installed": self.hook_installed,
            "normal_exporter_integration": self.normal_exporter_integration,
        }


@dataclasses.dataclass(frozen=True)
class RelocatedRuntimeInstallResult:
    bootstrap_mode: str
    entrypoint: int
    original_entry_instruction: int
    original_branch_target: int
    original_continuation_address: int
    bootstrap_address: int
    halt_loop_address: int | None
    bootstrap_size: int
    compound_payload_sha256: str
    replacement_instruction: int
    reserved_high: int
    original_observed_arena_high: int
    reserved_range_start: int
    reserved_range_end: int
    diagnostic_address: int
    diagnostic_block_size: int
    runtime_blob_offset: int
    runtime_blob_size: int
    runtime_destination: int
    runtime_entry: int
    runtime_code_start: int
    runtime_code_end: int
    runtime_state_start: int
    runtime_state_end: int
    cache_range_start: int
    cache_range_size: int
    hook_installed: bool
    normal_exporter_integration: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "bootstrap_mode": self.bootstrap_mode,
            "entrypoint": self.entrypoint,
            "original_entry_instruction": self.original_entry_instruction,
            "original_branch_target": self.original_branch_target,
            "original_continuation_address": self.original_continuation_address,
            "bootstrap_address": self.bootstrap_address,
            "halt_loop_address": self.halt_loop_address,
            "bootstrap_size": self.bootstrap_size,
            "compound_payload_sha256": self.compound_payload_sha256,
            "replacement_instruction": self.replacement_instruction,
            "reserved_high": self.reserved_high,
            "original_observed_arena_high": self.original_observed_arena_high,
            "reserved_range_start": self.reserved_range_start,
            "reserved_range_end": self.reserved_range_end,
            "diagnostic_address": self.diagnostic_address,
            "diagnostic_block_size": self.diagnostic_block_size,
            "runtime_blob_offset": self.runtime_blob_offset,
            "runtime_blob_size": self.runtime_blob_size,
            "runtime_destination": self.runtime_destination,
            "runtime_entry": self.runtime_entry,
            "runtime_code_start": self.runtime_code_start,
            "runtime_code_end": self.runtime_code_end,
            "runtime_state_start": self.runtime_state_start,
            "runtime_state_end": self.runtime_state_end,
            "cache_range_start": self.cache_range_start,
            "cache_range_size": self.cache_range_size,
            "hook_installed": self.hook_installed,
            "normal_exporter_integration": self.normal_exporter_integration,
        }


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
    checkpoint_gate: CheckpointGateResult | None
    entry_bootstrap: EntryBootstrapInstallResult | None
    relocated_runtime: RelocatedRuntimeInstallResult | None
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
            "checkpoint_gate": None if self.checkpoint_gate is None else self.checkpoint_gate.to_json_dict(),
            "entry_bootstrap": None if self.entry_bootstrap is None else self.entry_bootstrap.to_json_dict(),
            "relocated_runtime": None if self.relocated_runtime is None else self.relocated_runtime.to_json_dict(),
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


def validate_probe_virtual_address(payload_virtual_address: int, payload_size: int) -> None:
    if payload_virtual_address < MEM1_START:
        raise Prime3DolPatchError(f"Probe payload address 0x{payload_virtual_address:08x} is below MEM1.")
    payload_end = payload_virtual_address + payload_size
    if payload_end > MEM1_END:
        raise Prime3DolPatchError(
            f"Probe payload range 0x{payload_virtual_address:08x}..0x{payload_end:08x} exceeds MEM1."
        )


def install_checkpoint_gate(
    dol_bytes: bytes,
    *,
    gate_address: int,
    expected_original_word: int,
    checkpoint_name: str,
    versions: Iterable[CorruptionDolVersionLike] | None = None,
) -> tuple[bytes, CheckpointGateResult]:
    header = parse_dol_header(dol_bytes)
    if gate_address % 4 != 0:
        raise Prime3DolPatchError(f"Checkpoint gate address 0x{gate_address:08x} is not 4-byte aligned.")
    patched_bytes, patch_result = patch_guarded_instruction_word(
        dol_bytes,
        address=gate_address,
        expected_original_word=expected_original_word,
        replacement_word=ENTRY_GATE_WORD,
    )
    identify_supported_corruption_version(dol_bytes, versions=versions)
    return patched_bytes, _checkpoint_gate_result_from_patch(
        header,
        patch_result,
        checkpoint_name=checkpoint_name,
    )


def install_entry_gate(
    dol_bytes: bytes,
    *,
    versions: Iterable[CorruptionDolVersionLike] | None = None,
) -> tuple[bytes, CheckpointGateResult]:
    header = parse_dol_header(dol_bytes)
    if header.entry_point != EXPECTED_ENTRYPOINT:
        raise Prime3DolPatchError(
            f"Unexpected Corruption DOL entrypoint 0x{header.entry_point:08x}; expected 0x{EXPECTED_ENTRYPOINT:08x}."
        )
    return install_checkpoint_gate(
        dol_bytes,
        gate_address=ENTRY_GATE_ADDRESS,
        expected_original_word=EXPECTED_ENTRY_WORD,
        checkpoint_name=ENTRY_CHECKPOINT_NAME,
        versions=versions,
    )


def decode_entry_branch_plan(dol_bytes: bytes) -> DecodedBranchInstruction:
    header = parse_dol_header(dol_bytes)
    if header.entry_point != EXPECTED_ENTRYPOINT:
        raise Prime3DolPatchError(
            f"Unexpected Corruption DOL entrypoint 0x{header.entry_point:08x}; expected 0x{EXPECTED_ENTRYPOINT:08x}."
        )
    file_offset = header.offset_for_address(header.entry_point)
    if file_offset is None:
        raise Prime3DolPatchError(f"Entry point 0x{header.entry_point:08x} is not mapped in the DOL.")
    instruction_word = int.from_bytes(dol_bytes[file_offset : file_offset + 4], "big")
    decoded = decode_ppc_unconditional_branch(instruction_word, header.entry_point)
    if decoded is None:
        raise Prime3DolPatchError(
            f"Entry instruction 0x{instruction_word:08x} at 0x{header.entry_point:08x} is not an unconditional branch."
        )
    if decoded.absolute:
        raise Prime3DolPatchError("Entry bootstrap only supports a relative entry branch.")
    if not decoded.link:
        raise Prime3DolPatchError("Entry bootstrap requires a branch-and-link retail entry instruction.")
    return decoded


def install_entry_bootstrap_patch(
    dol_bytes: bytes,
    *,
    probe_section: Prime3ProbeSection,
    manifest: Prime3RuntimePayloadManifest,
    versions: Iterable[CorruptionDolVersionLike] | None = None,
) -> tuple[bytes, EntryBootstrapInstallResult]:
    identify_supported_corruption_version(dol_bytes, versions=versions)
    entry_bootstrap = manifest.entry_bootstrap
    if entry_bootstrap is None:
        raise Prime3DolPatchError("Entry bootstrap installation requires bootstrap metadata in the payload manifest.")
    decoded = decode_entry_branch_plan(dol_bytes)
    if decoded.instruction_word != entry_bootstrap.original_entry_instruction:
        raise Prime3DolPatchError(
            f"Unexpected retail entry instruction 0x{decoded.instruction_word:08x}; "
            f"expected 0x{entry_bootstrap.original_entry_instruction:08x}."
        )
    if decoded.target_address != entry_bootstrap.original_branch_target:
        raise Prime3DolPatchError(
            f"Unexpected retail entry branch target 0x{decoded.target_address:08x}; "
            f"expected 0x{entry_bootstrap.original_branch_target:08x}."
        )
    if decoded.continuation_address != entry_bootstrap.original_continuation_address:
        raise Prime3DolPatchError(
            f"Unexpected retail entry continuation 0x{decoded.continuation_address:08x}; "
            f"expected 0x{entry_bootstrap.original_continuation_address:08x}."
        )
    if probe_section.virtual_address != entry_bootstrap.staging_address:
        raise Prime3DolPatchError(
            f"Entry bootstrap staging address 0x{probe_section.virtual_address:08x} does not match manifest "
            f"staging address 0x{entry_bootstrap.staging_address:08x}."
        )

    replacement_instruction = encode_ppc_unconditional_branch(
        decoded.instruction_address,
        probe_section.entry_address,
        link=True,
    )
    patched_bytes, patch_result = patch_guarded_instruction_word(
        dol_bytes,
        address=decoded.instruction_address,
        expected_original_word=decoded.instruction_word,
        replacement_word=replacement_instruction,
    )
    return patched_bytes, EntryBootstrapInstallResult(
        bootstrap_mode=entry_bootstrap.mode,
        entrypoint=decoded.instruction_address,
        original_entry_instruction=decoded.instruction_word,
        original_branch_target=decoded.target_address,
        original_continuation_address=decoded.continuation_address,
        bootstrap_address=probe_section.entry_address,
        halt_loop_address=entry_bootstrap.halt_loop_address,
        bootstrap_size=probe_section.payload_size,
        bootstrap_sha256=probe_section.payload_sha256,
        replacement_instruction=patch_result.replacement_word,
        reserved_high=entry_bootstrap.reserved_boundary,
        original_observed_arena_high=OBSERVED_ENTRY_ARENA_HIGH,
        reserved_range_start=entry_bootstrap.reserved_range_start,
        reserved_range_end=entry_bootstrap.reserved_range_end,
        diagnostic_address=entry_bootstrap.diagnostic_address,
        diagnostic_block_size=entry_bootstrap.diagnostic_block_size,
        hook_installed=True,
        normal_exporter_integration=False,
    )


def install_relocated_runtime_patch(
    dol_bytes: bytes,
    *,
    probe_section: Prime3ProbeSection,
    manifest: Prime3RuntimePayloadManifest,
    versions: Iterable[CorruptionDolVersionLike] | None = None,
) -> tuple[bytes, RelocatedRuntimeInstallResult]:
    identify_supported_corruption_version(dol_bytes, versions=versions)
    entry_bootstrap = manifest.entry_bootstrap
    relocated_runtime = manifest.relocated_runtime
    if entry_bootstrap is None or relocated_runtime is None:
        raise Prime3DolPatchError("Relocated runtime installation requires both bootstrap and relocated metadata.")
    decoded = decode_entry_branch_plan(dol_bytes)
    if decoded.instruction_word != entry_bootstrap.original_entry_instruction:
        raise Prime3DolPatchError(
            f"Unexpected retail entry instruction 0x{decoded.instruction_word:08x}; "
            f"expected 0x{entry_bootstrap.original_entry_instruction:08x}."
        )
    if decoded.target_address != entry_bootstrap.original_branch_target:
        raise Prime3DolPatchError(
            f"Unexpected retail entry branch target 0x{decoded.target_address:08x}; "
            f"expected 0x{entry_bootstrap.original_branch_target:08x}."
        )
    if decoded.continuation_address != entry_bootstrap.original_continuation_address:
        raise Prime3DolPatchError(
            f"Unexpected retail entry continuation 0x{decoded.continuation_address:08x}; "
            f"expected 0x{entry_bootstrap.original_continuation_address:08x}."
        )
    if probe_section.virtual_address != entry_bootstrap.staging_address:
        raise Prime3DolPatchError(
            f"Relocated runtime staging address 0x{probe_section.virtual_address:08x} does not match manifest "
            f"staging address 0x{entry_bootstrap.staging_address:08x}."
        )

    replacement_instruction = encode_ppc_unconditional_branch(
        decoded.instruction_address,
        probe_section.entry_address,
        link=True,
    )
    patched_bytes, patch_result = patch_guarded_instruction_word(
        dol_bytes,
        address=decoded.instruction_address,
        expected_original_word=decoded.instruction_word,
        replacement_word=replacement_instruction,
    )
    return patched_bytes, RelocatedRuntimeInstallResult(
        bootstrap_mode=entry_bootstrap.mode,
        entrypoint=decoded.instruction_address,
        original_entry_instruction=decoded.instruction_word,
        original_branch_target=decoded.target_address,
        original_continuation_address=decoded.continuation_address,
        bootstrap_address=probe_section.entry_address,
        halt_loop_address=entry_bootstrap.halt_loop_address,
        bootstrap_size=probe_section.payload_size,
        compound_payload_sha256=manifest.payload_sha256,
        replacement_instruction=patch_result.replacement_word,
        reserved_high=entry_bootstrap.reserved_boundary,
        original_observed_arena_high=OBSERVED_ENTRY_ARENA_HIGH,
        reserved_range_start=entry_bootstrap.reserved_range_start,
        reserved_range_end=entry_bootstrap.reserved_range_end,
        diagnostic_address=entry_bootstrap.diagnostic_address,
        diagnostic_block_size=entry_bootstrap.diagnostic_block_size,
        runtime_blob_offset=relocated_runtime.embedded_runtime_blob_offset,
        runtime_blob_size=relocated_runtime.embedded_runtime_blob_size,
        runtime_destination=relocated_runtime.runtime_destination_address,
        runtime_entry=relocated_runtime.runtime_entry_address,
        runtime_code_start=relocated_runtime.runtime_code_start,
        runtime_code_end=relocated_runtime.runtime_code_end,
        runtime_state_start=relocated_runtime.runtime_state_start,
        runtime_state_end=relocated_runtime.runtime_state_end,
        cache_range_start=relocated_runtime.cache_range_start,
        cache_range_size=relocated_runtime.cache_range_size,
        hook_installed=True,
        normal_exporter_integration=False,
    )


def _checkpoint_gate_result_from_patch(
    header: DolHeader,
    patch_result: GuardedInstructionPatchResult,
    *,
    checkpoint_name: str,
) -> CheckpointGateResult:
    section = header.section_for_address(patch_result.address)
    if section is None:
        raise Prime3DolPatchError(f"Checkpoint gate address 0x{patch_result.address:08x} is not mapped in the DOL.")
    return CheckpointGateResult(
        checkpoint_name=checkpoint_name,
        gate_address=patch_result.address,
        original_instruction=patch_result.original_word,
        replacement_instruction=patch_result.replacement_word,
        entrypoint=header.entry_point,
        file_offset=patch_result.file_offset,
        text_section_name=section.name,
    )


def build_unhooked_probe_dol(
    original_dol_bytes: bytes,
    payload_bytes: bytes,
    manifest: Prime3RuntimePayloadManifest,
    *,
    payload_virtual_address: int | None = None,
    halt_at_address: int | None = None,
    expected_halt_word: int | None = None,
    checkpoint_name: str | None = None,
    halt_at_entry: bool = False,
    install_entry_bootstrap: bool = False,
    install_relocated_runtime: bool = False,
    versions: Iterable[CorruptionDolVersionLike] | None = None,
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
    if payload_virtual_address is None:
        payload_virtual_address = identify_probe_virtual_address(header, manifest.required_alignment)
    validate_probe_virtual_address(payload_virtual_address, len(payload_bytes))
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
    checkpoint_gate = None
    entry_bootstrap = None
    relocated_runtime = None
    checkpoint_spec = _resolve_checkpoint_gate(
        halt_at_address=halt_at_address,
        expected_halt_word=expected_halt_word,
        checkpoint_name=checkpoint_name,
        halt_at_entry=halt_at_entry,
    )
    if (install_entry_bootstrap or install_relocated_runtime) and checkpoint_spec is not None:
        raise Prime3DolPatchError("Bootstrap installation modes cannot be combined with a checkpoint gate.")
    if install_entry_bootstrap and install_relocated_runtime:
        raise Prime3DolPatchError("Use only one bootstrap installation mode at a time.")
    if install_entry_bootstrap:
        probe_dol_bytes, entry_bootstrap = install_entry_bootstrap_patch(
            probe_dol_bytes,
            probe_section=probe_section,
            manifest=manifest,
            versions=versions,
        )
    if install_relocated_runtime:
        probe_dol_bytes, relocated_runtime = install_relocated_runtime_patch(
            probe_dol_bytes,
            probe_section=probe_section,
            manifest=manifest,
            versions=versions,
        )
    if checkpoint_spec is not None:
        probe_dol_bytes, checkpoint_gate = install_checkpoint_gate(
            probe_dol_bytes,
            gate_address=checkpoint_spec.gate_address,
            expected_original_word=checkpoint_spec.expected_original_word,
            checkpoint_name=checkpoint_spec.checkpoint_name,
            versions=versions,
        )
    return ProbeDolBuildResult(
        probe_dol_bytes=probe_dol_bytes,
        probe_section=probe_section,
        checkpoint_gate=checkpoint_gate,
        entry_bootstrap=entry_bootstrap,
        relocated_runtime=relocated_runtime,
    )


def verify_probe_delivery(
    *,
    original_dol_path: Path,
    probe_dol_path: Path,
    extracted_final_dol_path: Path,
    payload_bin_path: Path,
    payload_manifest_path: Path,
    payload_virtual_address: int | None = None,
    halt_at_address: int | None = None,
    expected_halt_word: int | None = None,
    checkpoint_name: str | None = None,
    halt_at_entry: bool = False,
    install_entry_bootstrap: bool = False,
    install_relocated_runtime: bool = False,
    versions: Iterable[CorruptionDolVersionLike] | None = None,
) -> ProbeDeliveryVerification:
    original_dol_bytes = original_dol_path.read_bytes()
    probe_dol_bytes = probe_dol_path.read_bytes()
    extracted_dol_bytes = extracted_final_dol_path.read_bytes()
    payload_bytes = payload_bin_path.read_bytes()
    manifest_text = payload_manifest_path.read_text(encoding="utf-8")
    manifest = Prime3RuntimePayloadManifest.from_json_text(manifest_text)

    build_result = build_unhooked_probe_dol(
        original_dol_bytes,
        payload_bytes,
        manifest,
        payload_virtual_address=payload_virtual_address,
        halt_at_address=halt_at_address,
        expected_halt_word=expected_halt_word,
        checkpoint_name=checkpoint_name,
        halt_at_entry=halt_at_entry,
        install_entry_bootstrap=install_entry_bootstrap,
        install_relocated_runtime=install_relocated_runtime,
        versions=versions,
    )
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
    if build_result.checkpoint_gate is not None:
        _verify_checkpoint_gate_word(probe_dol_bytes, probe_header, build_result.checkpoint_gate)
        _verify_checkpoint_gate_word(extracted_dol_bytes, extracted_header, build_result.checkpoint_gate)
    if build_result.entry_bootstrap is not None:
        _verify_entry_bootstrap_word(probe_dol_bytes, probe_header, build_result.entry_bootstrap)
        _verify_entry_bootstrap_word(extracted_dol_bytes, extracted_header, build_result.entry_bootstrap)
    if build_result.relocated_runtime is not None:
        _verify_relocated_runtime_word(probe_dol_bytes, probe_header, build_result.relocated_runtime)
        _verify_relocated_runtime_word(extracted_dol_bytes, extracted_header, build_result.relocated_runtime)

    return ProbeDeliveryVerification(
        original_dol=_file_identity("original", original_dol_path, original_dol_bytes),
        probe_dol=_file_identity("probe", probe_dol_path, probe_dol_bytes),
        extracted_final_dol=_file_identity("extracted_final", extracted_final_dol_path, extracted_dol_bytes),
        payload_bin=_file_identity("payload_bin", payload_bin_path, payload_bytes),
        payload_manifest=_file_identity("payload_manifest", payload_manifest_path, manifest_text.encode("utf-8")),
        probe_section=probe_section,
        checkpoint_gate=build_result.checkpoint_gate,
        entry_bootstrap=build_result.entry_bootstrap,
        relocated_runtime=build_result.relocated_runtime,
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


@dataclasses.dataclass(frozen=True)
class CheckpointGateSpec:
    gate_address: int
    expected_original_word: int
    checkpoint_name: str


def _resolve_checkpoint_gate(
    *,
    halt_at_address: int | None,
    expected_halt_word: int | None,
    checkpoint_name: str | None,
    halt_at_entry: bool,
) -> CheckpointGateSpec | None:
    if halt_at_entry:
        if halt_at_address is not None or expected_halt_word is not None or checkpoint_name is not None:
            raise Prime3DolPatchError("Use either --halt-at-entry or the explicit checkpoint gate arguments, not both.")
        return CheckpointGateSpec(
            gate_address=ENTRY_GATE_ADDRESS,
            expected_original_word=EXPECTED_ENTRY_WORD,
            checkpoint_name=ENTRY_CHECKPOINT_NAME,
        )

    if halt_at_address is None and expected_halt_word is None and checkpoint_name is None:
        return None
    if halt_at_address is None:
        raise Prime3DolPatchError("Checkpoint gate requires an explicit halt address.")
    if expected_halt_word is None:
        raise Prime3DolPatchError("Checkpoint gate requires an explicit expected halt word.")
    if checkpoint_name is None or not checkpoint_name.strip():
        raise Prime3DolPatchError("Checkpoint gate requires a non-empty checkpoint name.")
    return CheckpointGateSpec(
        gate_address=halt_at_address,
        expected_original_word=expected_halt_word,
        checkpoint_name=checkpoint_name,
    )


def _verify_checkpoint_gate_word(dol_bytes: bytes, header: DolHeader, checkpoint_gate: CheckpointGateResult) -> None:
    file_offset = header.offset_for_address(checkpoint_gate.gate_address)
    if file_offset is None:
        raise Prime3DolPatchError(
            f"Checkpoint gate address 0x{checkpoint_gate.gate_address:08x} is not mapped in the DOL."
        )
    observed = int.from_bytes(dol_bytes[file_offset : file_offset + 4], "big")
    if observed != checkpoint_gate.replacement_instruction:
        raise Prime3DolPatchError(
            f"DOL checkpoint gate word at 0x{checkpoint_gate.gate_address:08x} was 0x{observed:08x}, "
            f"expected 0x{checkpoint_gate.replacement_instruction:08x}."
        )


def _verify_entry_bootstrap_word(
    dol_bytes: bytes,
    header: DolHeader,
    entry_bootstrap: EntryBootstrapInstallResult,
) -> None:
    file_offset = header.offset_for_address(entry_bootstrap.entrypoint)
    if file_offset is None:
        raise Prime3DolPatchError(f"Entry bootstrap address 0x{entry_bootstrap.entrypoint:08x} is not mapped.")
    observed = int.from_bytes(dol_bytes[file_offset : file_offset + 4], "big")
    if observed != entry_bootstrap.replacement_instruction:
        raise Prime3DolPatchError(
            f"DOL entry bootstrap word at 0x{entry_bootstrap.entrypoint:08x} was 0x{observed:08x}, "
            f"expected 0x{entry_bootstrap.replacement_instruction:08x}."
        )


def _verify_relocated_runtime_word(
    dol_bytes: bytes,
    header: DolHeader,
    relocated_runtime: RelocatedRuntimeInstallResult,
) -> None:
    file_offset = header.offset_for_address(relocated_runtime.entrypoint)
    if file_offset is None:
        raise Prime3DolPatchError(
            f"Relocated runtime bootstrap address 0x{relocated_runtime.entrypoint:08x} is not mapped."
        )
    observed = int.from_bytes(dol_bytes[file_offset : file_offset + 4], "big")
    if observed != relocated_runtime.replacement_instruction:
        raise Prime3DolPatchError(
            f"DOL relocated runtime bootstrap word at 0x{relocated_runtime.entrypoint:08x} was 0x{observed:08x}, "
            f"expected 0x{relocated_runtime.replacement_instruction:08x}."
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
