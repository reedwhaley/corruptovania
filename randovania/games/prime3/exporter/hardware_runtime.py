from __future__ import annotations

import dataclasses
import hashlib
import os
from typing import TYPE_CHECKING

import randovania
from randovania.game_connection.executor.prime3_wii_protocol import (
    Prime3WiiCapability,
    Prime3WiiCommand,
)
from randovania.games.prime3.exporter.dol_patcher import (
    DecodedBranchInstruction,
    Prime3DolPatchError,
    Prime3DolPatchResult,
    atomic_replace_file,
    decode_ppc_unconditional_branch,
    identify_supported_corruption_version,
    parse_dol_header,
    patch_prime3_corruption_dol,
)
from randovania.games.prime3.exporter.probe_delivery import (
    RECURRING_POLL_HOOK_ADDRESS,
    RECURRING_POLL_HOOK_EXPECTED_WORD,
    ProbeDolBuildResult,
    build_unhooked_probe_dol,
)
from randovania.games.prime3.exporter.runtime_payload import (
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
    Prime3RuntimePayloadManifest,
)
from tools.prime3_wii_runtime.build_payload import build_prime3_runtime_payload

if TYPE_CHECKING:
    import uuid
    from pathlib import Path

CP3W_UDP_PORT = 43674
PRODUCTION_RUNTIME_MODE = "cp3w_inventory_service"
PRODUCTION_RESERVED_HIGH = 0x817E0000
PRODUCTION_DIAGNOSTIC_ADDRESS = 0x817E0100
PRODUCTION_RUNTIME_ASSET_DIR = os.fspath(
    randovania.get_data_path().parents[1].joinpath("build", "prime3_wii_runtime", "production")
)
PRODUCTION_RUNTIME_BUILD_COMMAND = "python -u tools/build_prime3_runtime_assets.py"


@dataclasses.dataclass(frozen=True)
class Prime3HardwareArtifactValidation:
    version_description: str
    payload_sha256: str
    runtime_blob_sha256: str
    runtime_section_address: int
    runtime_section_size: int
    entry_hook_target: int
    recurring_hook_target: int
    udp_port: int
    runtime_mode: str
    game_identity_supported: bool
    inventory_supported: bool
    runtime_occurrence_count: int


@dataclasses.dataclass(frozen=True)
class Prime3HardwarePatchResult:
    identity_patch: Prime3DolPatchResult
    delivery: ProbeDolBuildResult
    validation: Prime3HardwareArtifactValidation


@dataclasses.dataclass(frozen=True)
class Prime3ProductionRuntimeAssets:
    directory: Path
    elf_path: Path | None
    payload_path: Path
    manifest_path: Path
    payload: bytes
    manifest: Prime3RuntimePayloadManifest
    elf_sha256: str | None
    payload_sha256: str
    manifest_sha256: str


def build_production_runtime_payload(output_dir: Path) -> Prime3RuntimePayloadManifest:
    return build_prime3_runtime_payload(
        output_dir,
        payload_mode=PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
        enable_recurring_hook_diagnostics=False,
        enable_ios_udp_diagnostic=True,
        ios_udp_mode=PRODUCTION_RUNTIME_MODE,
        ios_udp_loop_count=0,
        reserved_high=PRODUCTION_RESERVED_HIGH,
        diagnostic_address=PRODUCTION_DIAGNOSTIC_ADDRESS,
    )


def load_validated_production_runtime_assets(
    asset_dir: Path,
    *,
    require_elf: bool,
) -> Prime3ProductionRuntimeAssets:
    payload_path = asset_dir.joinpath("payload.bin")
    manifest_path = asset_dir.joinpath("payload.json")
    elf_path = asset_dir.joinpath("payload.elf")
    required_paths = [payload_path, manifest_path]
    if require_elf:
        required_paths.append(elf_path)
    missing = [os.fspath(path) for path in required_paths if not path.is_file()]
    if missing:
        raise Prime3DolPatchError(
            "Validated Prime 3 CP3W runtime assets are missing: "
            f"{', '.join(missing)}. Run `{PRODUCTION_RUNTIME_BUILD_COMMAND}` before packaging."
        )

    payload = payload_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    manifest = Prime3RuntimePayloadManifest.from_json_text(manifest_bytes.decode("utf-8"))
    _validate_production_manifest(payload, manifest)

    elf_bytes = elf_path.read_bytes() if elf_path.is_file() else None
    if elf_bytes is not None and not elf_bytes.startswith(b"\x7fELF"):
        raise Prime3DolPatchError(f"Prime 3 CP3W runtime ELF is invalid: {elf_path}")

    return Prime3ProductionRuntimeAssets(
        directory=asset_dir,
        elf_path=elf_path if elf_bytes is not None else None,
        payload_path=payload_path,
        manifest_path=manifest_path,
        payload=payload,
        manifest=manifest,
        elf_sha256=hashlib.sha256(elf_bytes).hexdigest() if elf_bytes is not None else None,
        payload_sha256=hashlib.sha256(payload).hexdigest(),
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
    )


def load_or_build_production_runtime(
    output_dir: Path,
) -> tuple[bytes, Prime3RuntimePayloadManifest]:
    packaged_dir = randovania.get_data_path().joinpath("prime3_wii_runtime")
    packaged_payload = packaged_dir.joinpath("payload.bin")
    packaged_manifest = packaged_dir.joinpath("payload.json")
    if packaged_payload.is_file() and packaged_manifest.is_file():
        assets = load_validated_production_runtime_assets(packaged_dir, require_elf=False)
        manifest = assets.manifest
        payload = assets.payload
    else:
        manifest = build_production_runtime_payload(output_dir)
        assets = load_validated_production_runtime_assets(output_dir, require_elf=True)
        payload = assets.payload
    _validate_production_manifest(payload, manifest)
    return payload, manifest


def patch_prime3_hardware_dol(
    original_dol: bytes,
    layout_uuid: uuid.UUID,
    *,
    payload: bytes,
    manifest: Prime3RuntimePayloadManifest,
) -> tuple[bytes, Prime3HardwarePatchResult]:
    identify_supported_corruption_version(original_dol)
    _reject_existing_or_partial_installation(original_dol, manifest)
    _validate_production_manifest(payload, manifest)

    identity_dol, identity_patch = patch_prime3_corruption_dol(original_dol, layout_uuid)
    assert manifest.entry_bootstrap is not None
    delivery = build_unhooked_probe_dol(
        identity_dol,
        payload,
        manifest,
        payload_virtual_address=manifest.entry_bootstrap.staging_address,
        install_recurring_poll_hook=True,
        enable_ios_udp_diagnostic=True,
    )
    validation = validate_prime3_hardware_artifact(delivery.probe_dol_bytes, payload=payload, manifest=manifest)
    return delivery.probe_dol_bytes, Prime3HardwarePatchResult(identity_patch, delivery, validation)


def patch_prime3_hardware_dol_file_atomic(
    path: Path,
    layout_uuid: uuid.UUID,
    *,
    runtime_build_dir: Path,
) -> Prime3HardwarePatchResult:
    payload, manifest = load_or_build_production_runtime(runtime_build_dir)
    patched_dol, result = patch_prime3_hardware_dol(
        path.read_bytes(),
        layout_uuid,
        payload=payload,
        manifest=manifest,
    )
    atomic_replace_file(path, patched_dol)
    return result


def validate_prime3_hardware_artifact(
    dol: bytes,
    *,
    payload: bytes,
    manifest: Prime3RuntimePayloadManifest,
) -> Prime3HardwareArtifactValidation:
    version = identify_supported_corruption_version(dol)
    _validate_production_manifest(payload, manifest)
    occurrences = dol.count(payload)
    if occurrences != 1:
        raise Prime3DolPatchError(f"Expected exactly one CP3W runtime payload, found {occurrences}.")

    payload_offset = dol.index(payload)
    header = parse_dol_header(dol)
    section = header.section_for_offset(payload_offset)
    if section is None or section.kind != "text" or section.file_offset != payload_offset:
        raise Prime3DolPatchError("CP3W runtime payload is not the start of an executable DOL text section.")
    if section.size != len(payload):
        raise Prime3DolPatchError("CP3W runtime text section size does not match the canonical payload.")

    expected_entry_target = section.address + manifest.entry_symbol_offset
    entry_branch = _branch_at(dol, header.entry_point)
    if not entry_branch.link or entry_branch.target_address != expected_entry_target:
        raise Prime3DolPatchError("Prime 3 startup hook does not target the canonical CP3W bootstrap entry.")

    relocated = manifest.relocated_runtime
    assert relocated is not None
    recurring_branch = _branch_at(dol, RECURRING_POLL_HOOK_ADDRESS)
    if recurring_branch.link or recurring_branch.target_address != relocated.runtime_poll_hook_wrapper_address:
        raise Prime3DolPatchError("Prime 3 recurring hook does not target the canonical CP3W poll wrapper.")

    blob_start = relocated.embedded_runtime_blob_offset
    blob_end = blob_start + relocated.embedded_runtime_blob_size
    runtime_blob = payload[blob_start:blob_end]
    runtime_blob_hash = hashlib.sha256(runtime_blob).hexdigest()
    if runtime_blob_hash != relocated.embedded_runtime_blob_sha256:
        raise Prime3DolPatchError("Embedded CP3W runtime signature does not match its manifest.")

    transport = relocated.transport
    assert transport is not None
    identity = transport.cp3w_game_identity
    inventory = transport.cp3w_inventory
    return Prime3HardwareArtifactValidation(
        version_description=version.description,
        payload_sha256=manifest.payload_sha256,
        runtime_blob_sha256=runtime_blob_hash,
        runtime_section_address=section.address,
        runtime_section_size=section.size,
        entry_hook_target=entry_branch.target_address,
        recurring_hook_target=recurring_branch.target_address,
        udp_port=transport.udp_port,
        runtime_mode=transport.mode,
        game_identity_supported=(
            identity is not None
            and identity.command_value == int(Prime3WiiCommand.GET_GAME_IDENTITY)
            and identity.capability_value == int(Prime3WiiCapability.GAME_IDENTITY)
        ),
        inventory_supported=(
            inventory is not None
            and inventory.command_value == int(Prime3WiiCommand.GET_INVENTORY)
            and inventory.capability_value == int(Prime3WiiCapability.INVENTORY_STATE)
        ),
        runtime_occurrence_count=occurrences,
    )


def _validate_production_manifest(payload: bytes, manifest: Prime3RuntimePayloadManifest) -> None:
    manifest.validate()
    if len(payload) != manifest.payload_size or hashlib.sha256(payload).hexdigest() != manifest.payload_sha256:
        raise Prime3DolPatchError("Canonical CP3W payload does not match its manifest size and SHA-256.")
    if manifest.payload_mode != PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE:
        raise Prime3DolPatchError("Hardware CP3W payload must use relocated_continue bootstrap mode.")
    relocated = manifest.relocated_runtime
    if relocated is None or relocated.transport is None:
        raise Prime3DolPatchError("Hardware CP3W payload is missing relocated transport metadata.")
    transport = relocated.transport
    if transport.mode != PRODUCTION_RUNTIME_MODE or transport.udp_port != CP3W_UDP_PORT:
        raise Prime3DolPatchError("Hardware CP3W payload is not the unbounded UDP 43674 service.")
    if transport.cp3w_game_identity is None or transport.cp3w_inventory is None:
        raise Prime3DolPatchError("Hardware CP3W payload lacks identity or inventory protocol metadata.")


def _branch_at(dol: bytes, address: int) -> DecodedBranchInstruction:
    header = parse_dol_header(dol)
    offset = header.offset_for_address(address)
    if offset is None or offset + 4 > len(dol):
        raise Prime3DolPatchError(f"CP3W hook address 0x{address:08X} is not mapped in the DOL.")
    word = int.from_bytes(dol[offset : offset + 4], "big")
    branch = decode_ppc_unconditional_branch(word, address)
    if branch is None:
        raise Prime3DolPatchError(f"CP3W hook at 0x{address:08X} is not an unconditional branch.")
    return branch


def _reject_existing_or_partial_installation(dol: bytes, manifest: Prime3RuntimePayloadManifest) -> None:
    header = parse_dol_header(dol)
    entry = manifest.entry_bootstrap
    if entry is None:
        raise Prime3DolPatchError("Hardware CP3W manifest is missing startup metadata.")
    entry_offset = header.offset_for_address(header.entry_point)
    recurring_offset = header.offset_for_address(RECURRING_POLL_HOOK_ADDRESS)
    if entry_offset is None or recurring_offset is None:
        raise Prime3DolPatchError("Prime 3 startup or recurring hook address is not mapped.")
    entry_word = int.from_bytes(dol[entry_offset : entry_offset + 4], "big")
    recurring_word = int.from_bytes(dol[recurring_offset : recurring_offset + 4], "big")
    if entry_word != entry.original_entry_instruction or recurring_word != RECURRING_POLL_HOOK_EXPECTED_WORD:
        raise Prime3DolPatchError(
            "Prime 3 DOL already contains a CP3W runtime/startup hook or a partial incompatible installation; "
            "refusing to install a duplicate."
        )
