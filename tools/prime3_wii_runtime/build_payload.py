from __future__ import annotations

import argparse
import dataclasses
import hashlib
import os
import subprocess
import sys
from pathlib import Path

if __package__ in {None, ""}:
    _repository_root = Path(__file__).resolve().parents[2]
    _repository_root_str = os.fspath(_repository_root)
    if _repository_root_str not in sys.path:
        sys.path.insert(0, _repository_root_str)

from randovania.game_connection.executor.prime3_wii_protocol import PROTOCOL_VERSION
from randovania.games.prime3.exporter.runtime_payload import (
    PRIME3_RUNTIME_CONTINUE_MODES,
    PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES,
    PRIME3_RUNTIME_ENTRY_SYMBOL,
    PRIME3_RUNTIME_HALT_MODES,
    PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_CONTINUE,
    PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT,
    PRIME3_RUNTIME_PAYLOAD_MODE_NORMAL,
    PRIME3_RUNTIME_PAYLOAD_MODE_PROBE,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT,
    PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT,
    PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION,
    PRIME3_RUNTIME_RELOCATED_MODES,
    PRIME3_RUNTIME_REQUIRED_ALIGNMENT,
    PRIME3_RUNTIME_TARGET_ABI,
    PRIME3_RUNTIME_TARGET_ARCHITECTURE,
    PRIME3_RUNTIME_TARGET_ENDIANNESS,
    Prime3EntryBootstrapMetadata,
    Prime3RelocatedRuntimeMetadata,
    Prime3RuntimePayloadManifest,
    compute_cache_range,
    compute_source_digest,
)
from randovania.games.prime3.exporter.runtime_toolchain import resolve_prime3_runtime_toolchain

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = ROOT.joinpath("build", "prime3_wii_runtime")
SOURCE_FILES = (
    Path("payload.S"),
    Path("payload.ld"),
    Path("relocated_runtime.S"),
    Path("relocated_runtime.ld"),
    Path("build_payload.py"),
)
PROBE_CANARY_START_SYMBOL = "payload_canary_start"
PROBE_CANARY_END_SYMBOL = "payload_canary_end"
PROBE_COUNTER_SYMBOL = "payload_execution_counter"
BOOTSTRAP_SAVE_AREA_START_SYMBOL = "payload_save_area_start"
BOOTSTRAP_SAVE_AREA_END_SYMBOL = "payload_save_area_end"
BOOTSTRAP_HALT_LOOP_SYMBOL = "payload_halt_loop"
EMBEDDED_RUNTIME_START_SYMBOL = "payload_embedded_runtime_start"
EMBEDDED_RUNTIME_END_SYMBOL = "payload_embedded_runtime_end"
BOOTSTRAP_STAGING_ADDRESS = 0x806843C0
BOOTSTRAP_ORIGINAL_ENTRY_INSTRUCTION = 0x4800016D
BOOTSTRAP_ORIGINAL_BRANCH_TARGET = 0x8000648C
BOOTSTRAP_ORIGINAL_CONTINUATION_ADDRESS = 0x80006324
BOOTSTRAP_DIAGNOSTIC_BLOCK_SIZE = 0x40
BOOTSTRAP_CANARY_BYTES = b"P3BOOTSTRAPCANRY"
BOOTSTRAP_CANARY_OFFSET = 0x00
BOOTSTRAP_MARKER_OFFSET = 0x14
BOOTSTRAP_COUNTER_OFFSET = 0x18
BOOTSTRAP_ORIGINAL_80000034_OFFSET = 0x1C
BOOTSTRAP_ORIGINAL_80003110_OFFSET = 0x20
BOOTSTRAP_REPLACEMENT_VALUE_OFFSET = 0x24
BOOTSTRAP_STATUS_OFFSET = 0x28
BOOTSTRAP_MARKER_VALUE = 0x50334254
BOOTSTRAP_HALT_STATUS_VALUE = 0xB0070001
BOOTSTRAP_CONTINUE_STATUS_VALUE = 0xB0070002
RELOCATED_COPY_HALT_STATUS_VALUE = 0xB0071001
RELOCATED_RETURN_HALT_STATUS_VALUE = 0xB0071002
RELOCATED_CONTINUE_STATUS_VALUE = 0xB0071003
RELOCATED_RUNTIME_DESTINATION = 0x817E1000
RELOCATED_RUNTIME_CACHE_LINE_SIZE = 0x20
RELOCATED_RUNTIME_CANARY_BYTES = b"P3HIRUNTIMECANAR"
RELOCATED_COPY_COMPLETE_MARKER_VALUE = 0x434F5059
RELOCATED_EXECUTED_MARKER_VALUE = 0x52554E21
RELOCATED_SUCCESS_STATUS_VALUE = 0x52544F4B
RELOCATED_BOOTSTRAP_RETURN_MARKER_VALUE = 0x4252544E
RUNTIME_ENTRY_SYMBOL = "runtime_entry"
RUNTIME_CODE_START_SYMBOL = "runtime_code_start"
RUNTIME_CODE_END_SYMBOL = "runtime_code_end"
RUNTIME_STATE_START_SYMBOL = "runtime_state_start"
RUNTIME_STATE_END_SYMBOL = "runtime_state_end"
RUNTIME_CANARY_START_SYMBOL = "runtime_canary_start"
RUNTIME_CANARY_END_SYMBOL = "runtime_canary_end"
RUNTIME_COPY_COMPLETE_MARKER_SYMBOL = "runtime_copy_complete_marker"
RUNTIME_EXECUTED_MARKER_SYMBOL = "runtime_executed_marker"
RUNTIME_EXECUTION_COUNTER_SYMBOL = "runtime_execution_counter"
RUNTIME_STATUS_SYMBOL = "runtime_status"
RUNTIME_BOOTSTRAP_RETURN_MARKER_SYMBOL = "runtime_bootstrap_return_marker"


@dataclasses.dataclass(frozen=True)
class RelocatedRuntimeBuildResult:
    payload_bytes: bytes
    payload_sha256: str
    payload_size: int
    entry_address: int
    code_start: int
    code_end: int
    state_start: int
    state_end: int
    canary_address: int
    canary_size: int
    canary_sha256: str
    copy_complete_marker_address: int
    runtime_executed_marker_address: int
    runtime_execution_counter_address: int
    runtime_status_address: int
    bootstrap_return_marker_address: int
    cache_range_start: int
    cache_range_size: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--bootstrap-halt", action="store_true")
    parser.add_argument("--bootstrap-continue", action="store_true")
    parser.add_argument("--relocated-copy-halt", action="store_true")
    parser.add_argument("--relocated-return-halt", action="store_true")
    parser.add_argument("--relocated-continue", action="store_true")
    parser.add_argument("--reserved-high")
    parser.add_argument("--diagnostic-address")
    parser.add_argument("--runtime-destination")
    return parser.parse_args()


def build_prime3_runtime_payload(
    output_dir: Path,
    *,
    probe: bool = False,
    payload_mode: str = PRIME3_RUNTIME_PAYLOAD_MODE_NORMAL,
    reserved_high: int | None = None,
    diagnostic_address: int | None = None,
    runtime_destination: int | None = None,
) -> Prime3RuntimePayloadManifest:
    if probe:
        if payload_mode != PRIME3_RUNTIME_PAYLOAD_MODE_NORMAL:
            raise RuntimeError("Use either probe=True or an explicit payload_mode, not both.")
        payload_mode = PRIME3_RUNTIME_PAYLOAD_MODE_PROBE
    toolchain = resolve_prime3_runtime_toolchain()

    output_dir.mkdir(parents=True, exist_ok=True)
    object_path = output_dir.joinpath("payload.o")
    elf_path = output_dir.joinpath("payload.elf")
    binary_path = output_dir.joinpath("payload.bin")
    map_path = output_dir.joinpath("payload.map")
    manifest_path = output_dir.joinpath("payload.json")

    relocated_runtime = None
    extra_link_objects: list[str] = []
    compiler_defines: list[str] = []
    linker_defines: list[str] = []

    if payload_mode == PRIME3_RUNTIME_PAYLOAD_MODE_PROBE:
        compiler_defines.append("-DPRIME3_RUNTIME_PROBE_MODE=1")
    elif payload_mode in PRIME3_RUNTIME_RELOCATED_MODES:
        if reserved_high is None or diagnostic_address is None:
            raise RuntimeError("Relocated runtime modes require reserved_high and diagnostic_address.")
        runtime_destination = RELOCATED_RUNTIME_DESTINATION if runtime_destination is None else runtime_destination
        relocated_runtime = _build_relocated_runtime(
            toolchain=toolchain,
            output_dir=output_dir.joinpath("relocated_runtime"),
            runtime_destination=runtime_destination,
        )
        _write_runtime_blob_object(
            toolchain=toolchain,
            output_dir=output_dir.joinpath("relocated_runtime"),
        )
        extra_link_objects.append(os.fspath(output_dir.joinpath("relocated_runtime", "runtime_blob.o")))
        compiler_defines.extend(
            [
                "-DPRIME3_RUNTIME_RELOCATED_MODE=1",
                f"-DPRIME3_BOOTSTRAP_STAGING_ADDRESS=0x{BOOTSTRAP_STAGING_ADDRESS:08X}",
                f"-DPRIME3_BOOTSTRAP_RESERVED_HIGH=0x{reserved_high:08X}",
                f"-DPRIME3_BOOTSTRAP_DIAGNOSTIC_ADDRESS=0x{diagnostic_address:08X}",
                f"-DPRIME3_RELOCATED_RUNTIME_DESTINATION_ADDRESS=0x{runtime_destination:08X}",
                f"-DPRIME3_RELOCATED_RUNTIME_ENTRY_ADDRESS=0x{relocated_runtime.entry_address:08X}",
                f"-DPRIME3_RELOCATED_CACHE_RANGE_START=0x{relocated_runtime.cache_range_start:08X}",
                (
                    f"-DPRIME3_RELOCATED_CACHE_RANGE_END="
                    f"0x{relocated_runtime.cache_range_start + relocated_runtime.cache_range_size:08X}"
                ),
                f"-DPRIME3_RUNTIME_CACHE_LINE_SIZE={RELOCATED_RUNTIME_CACHE_LINE_SIZE}",
                f"-DPRIME3_RUNTIME_COPY_COMPLETE_MARKER_ADDRESS=0x{relocated_runtime.copy_complete_marker_address:08X}",
                f"-DPRIME3_RUNTIME_COPY_COMPLETE_MARKER_VALUE=0x{RELOCATED_COPY_COMPLETE_MARKER_VALUE:08X}",
                f"-DPRIME3_RUNTIME_BOOTSTRAP_RETURN_MARKER_ADDRESS=0x{relocated_runtime.bootstrap_return_marker_address:08X}",
                f"-DPRIME3_RUNTIME_BOOTSTRAP_RETURN_MARKER_VALUE=0x{RELOCATED_BOOTSTRAP_RETURN_MARKER_VALUE:08X}",
            ]
        )
        compiler_defines.append(f"-DPRIME3_BOOTSTRAP_STATUS_VALUE=0x{_bootstrap_status_value(payload_mode):08X}")
        linker_defines.append(f"--defsym=__payload_link_address=0x{BOOTSTRAP_STAGING_ADDRESS:08X}")
        if payload_mode == PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT:
            compiler_defines.append("-DPRIME3_RUNTIME_RELOCATED_COPY_HALT=1")
        elif payload_mode == PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT:
            compiler_defines.append("-DPRIME3_RUNTIME_RELOCATED_RETURN_HALT=1")
        else:
            compiler_defines.append("-DPRIME3_RUNTIME_RELOCATED_CONTINUE=1")
    elif payload_mode in PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES:
        if reserved_high is None or diagnostic_address is None:
            raise RuntimeError("Entry bootstrap payload mode requires reserved_high and diagnostic_address.")
        compiler_defines.extend(
            [
                "-DPRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODE=1",
                f"-DPRIME3_BOOTSTRAP_STAGING_ADDRESS=0x{BOOTSTRAP_STAGING_ADDRESS:08X}",
                f"-DPRIME3_BOOTSTRAP_RESERVED_HIGH=0x{reserved_high:08X}",
                f"-DPRIME3_BOOTSTRAP_DIAGNOSTIC_ADDRESS=0x{diagnostic_address:08X}",
                f"-DPRIME3_BOOTSTRAP_STATUS_VALUE=0x{_bootstrap_status_value(payload_mode):08X}",
            ]
        )
        linker_defines.append(f"--defsym=__payload_link_address=0x{BOOTSTRAP_STAGING_ADDRESS:08X}")
        if payload_mode == PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT:
            compiler_defines.append("-DPRIME3_RUNTIME_ENTRY_BOOTSTRAP_HALT=1")
        else:
            compiler_defines.append("-DPRIME3_RUNTIME_ENTRY_BOOTSTRAP_CONTINUE=1")

    _run(
        [
            os.fspath(toolchain.compiler_path),
            *toolchain.required_machine_flags,
            *compiler_defines,
            "-x",
            "assembler-with-cpp",
            "-c",
            os.fspath(SCRIPT_ROOT.joinpath("payload.S")),
            "-o",
            os.fspath(object_path),
        ]
    )
    _run(
        [
            os.fspath(toolchain.linker_path),
            "-EB",
            "--build-id=none",
            "--gc-sections",
            *linker_defines,
            "-T",
            os.fspath(SCRIPT_ROOT.joinpath("payload.ld")),
            "-Map",
            os.fspath(map_path),
            "-o",
            os.fspath(elf_path),
            os.fspath(object_path),
            *extra_link_objects,
        ]
    )
    _run(
        [
            os.fspath(toolchain.objcopy_path),
            "-O",
            "binary",
            os.fspath(elf_path),
            os.fspath(binary_path),
        ]
    )

    payload_bytes = binary_path.read_bytes()
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    readelf_header = _run([os.fspath(toolchain.readelf_path), "-h", os.fspath(elf_path)])
    readelf_symbols = _run([os.fspath(toolchain.readelf_path), "-s", "--wide", os.fspath(elf_path)])
    readelf_relocations = _run([os.fspath(toolchain.readelf_path), "-r", os.fspath(elf_path)])
    readelf_dynamic = _run([os.fspath(toolchain.readelf_path), "-d", os.fspath(elf_path)], allow_failure=True)
    _validate_readelf_header(readelf_header)

    symbol_base = BOOTSTRAP_STAGING_ADDRESS if payload_mode in PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES else 0
    entry_offset = _extract_entry_offset(readelf_symbols, PRIME3_RUNTIME_ENTRY_SYMBOL, symbol_base=symbol_base)
    canary_start_offset = _extract_optional_symbol_offset(
        readelf_symbols,
        PROBE_CANARY_START_SYMBOL,
        symbol_base=symbol_base,
    )
    canary_end_offset = _extract_optional_symbol_offset(
        readelf_symbols,
        PROBE_CANARY_END_SYMBOL,
        symbol_base=symbol_base,
    )
    counter_offset = _extract_optional_symbol_offset(readelf_symbols, PROBE_COUNTER_SYMBOL, symbol_base=symbol_base)
    save_area_start_offset = _extract_optional_symbol_offset(
        readelf_symbols,
        BOOTSTRAP_SAVE_AREA_START_SYMBOL,
        symbol_base=symbol_base,
    )
    save_area_end_offset = _extract_optional_symbol_offset(
        readelf_symbols,
        BOOTSTRAP_SAVE_AREA_END_SYMBOL,
        symbol_base=symbol_base,
    )
    halt_loop_offset = _extract_optional_symbol_offset(
        readelf_symbols,
        BOOTSTRAP_HALT_LOOP_SYMBOL,
        symbol_base=symbol_base,
    )
    embedded_runtime_start_offset = _extract_optional_symbol_offset(
        readelf_symbols,
        EMBEDDED_RUNTIME_START_SYMBOL,
        symbol_base=symbol_base,
    )
    embedded_runtime_end_offset = _extract_optional_symbol_offset(
        readelf_symbols,
        EMBEDDED_RUNTIME_END_SYMBOL,
        symbol_base=symbol_base,
    )
    unresolved_relocation_count = _count_relocations(readelf_relocations)
    dynamic_section_count = _count_dynamic_sections(readelf_dynamic)

    canary_size = None
    if canary_start_offset is not None or canary_end_offset is not None:
        if canary_start_offset is None or canary_end_offset is None or canary_end_offset <= canary_start_offset:
            raise RuntimeError("Probe payload canary symbols are malformed.")
        canary_size = canary_end_offset - canary_start_offset

    entry_bootstrap = None
    relocated_runtime_metadata = None
    if payload_mode in PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES:
        if (
            save_area_start_offset is None
            or save_area_end_offset is None
            or save_area_end_offset <= save_area_start_offset
        ):
            raise RuntimeError("Entry bootstrap payload save-area symbols are malformed.")
        if payload_mode in PRIME3_RUNTIME_HALT_MODES and halt_loop_offset is None:
            raise RuntimeError("Halt bootstrap payload is missing the halt-loop symbol.")
        if payload_mode in PRIME3_RUNTIME_CONTINUE_MODES and halt_loop_offset is not None:
            raise RuntimeError("Continue bootstrap payload should not export a halt-loop symbol.")
        assert reserved_high is not None
        assert diagnostic_address is not None
        entry_bootstrap = Prime3EntryBootstrapMetadata(
            mode=payload_mode,
            staging_address=BOOTSTRAP_STAGING_ADDRESS,
            staging_save_area_offset=save_area_start_offset,
            staging_save_area_size=save_area_end_offset - save_area_start_offset,
            halt_loop_address=None if halt_loop_offset is None else BOOTSTRAP_STAGING_ADDRESS + halt_loop_offset,
            reserved_boundary=reserved_high,
            reserved_range_start=reserved_high,
            reserved_range_end=0x817FE3A0,
            diagnostic_address=diagnostic_address,
            diagnostic_block_size=BOOTSTRAP_DIAGNOSTIC_BLOCK_SIZE,
            canary_address=diagnostic_address + BOOTSTRAP_CANARY_OFFSET,
            canary_size=len(BOOTSTRAP_CANARY_BYTES),
            canary_sha256=hashlib.sha256(BOOTSTRAP_CANARY_BYTES).hexdigest(),
            marker_address=diagnostic_address + BOOTSTRAP_MARKER_OFFSET,
            marker_value=BOOTSTRAP_MARKER_VALUE,
            counter_address=diagnostic_address + BOOTSTRAP_COUNTER_OFFSET,
            counter_size=4,
            original_80000034_address=diagnostic_address + BOOTSTRAP_ORIGINAL_80000034_OFFSET,
            original_80003110_address=diagnostic_address + BOOTSTRAP_ORIGINAL_80003110_OFFSET,
            replacement_value_address=diagnostic_address + BOOTSTRAP_REPLACEMENT_VALUE_OFFSET,
            replacement_value=reserved_high,
            status_address=diagnostic_address + BOOTSTRAP_STATUS_OFFSET,
            status_value=_bootstrap_status_value(payload_mode),
            original_entry_instruction=BOOTSTRAP_ORIGINAL_ENTRY_INSTRUCTION,
            original_branch_target=BOOTSTRAP_ORIGINAL_BRANCH_TARGET,
            original_continuation_address=BOOTSTRAP_ORIGINAL_CONTINUATION_ADDRESS,
        )

    if payload_mode in PRIME3_RUNTIME_RELOCATED_MODES:
        if embedded_runtime_start_offset is None or embedded_runtime_end_offset is None:
            raise RuntimeError("Relocated compound payload is missing the embedded runtime blob symbols.")
        if embedded_runtime_end_offset <= embedded_runtime_start_offset:
            raise RuntimeError("Relocated embedded runtime blob symbols are malformed.")
        assert relocated_runtime is not None
        low_bootstrap_bytes = payload_bytes[:embedded_runtime_start_offset]
        embedded_runtime_bytes = payload_bytes[embedded_runtime_start_offset:embedded_runtime_end_offset]
        if hashlib.sha256(embedded_runtime_bytes).hexdigest() != relocated_runtime.payload_sha256:
            raise RuntimeError("Embedded runtime blob hash does not match the separately linked runtime payload.")
        runtime_destination = RELOCATED_RUNTIME_DESTINATION if runtime_destination is None else runtime_destination
        relocated_runtime_metadata = Prime3RelocatedRuntimeMetadata(
            mode=payload_mode,
            low_bootstrap_address=BOOTSTRAP_STAGING_ADDRESS,
            low_bootstrap_size=len(low_bootstrap_bytes),
            low_bootstrap_sha256=hashlib.sha256(low_bootstrap_bytes).hexdigest(),
            embedded_runtime_blob_offset=embedded_runtime_start_offset,
            embedded_runtime_blob_size=len(embedded_runtime_bytes),
            embedded_runtime_blob_sha256=relocated_runtime.payload_sha256,
            runtime_destination_address=runtime_destination,
            runtime_entry_address=relocated_runtime.entry_address,
            runtime_code_start=relocated_runtime.code_start,
            runtime_code_end=relocated_runtime.code_end,
            runtime_state_start=relocated_runtime.state_start,
            runtime_state_end=relocated_runtime.state_end,
            required_source_alignment=PRIME3_RUNTIME_REQUIRED_ALIGNMENT,
            required_destination_alignment=PRIME3_RUNTIME_REQUIRED_ALIGNMENT,
            cache_line_size=RELOCATED_RUNTIME_CACHE_LINE_SIZE,
            cache_range_start=relocated_runtime.cache_range_start,
            cache_range_size=relocated_runtime.cache_range_size,
            runtime_canary_address=relocated_runtime.canary_address,
            runtime_canary_size=relocated_runtime.canary_size,
            runtime_canary_sha256=relocated_runtime.canary_sha256,
            copy_complete_marker_address=relocated_runtime.copy_complete_marker_address,
            copy_complete_marker_value=RELOCATED_COPY_COMPLETE_MARKER_VALUE,
            runtime_executed_marker_address=relocated_runtime.runtime_executed_marker_address,
            runtime_executed_marker_value=RELOCATED_EXECUTED_MARKER_VALUE,
            runtime_execution_counter_address=relocated_runtime.runtime_execution_counter_address,
            runtime_execution_counter_size=4,
            runtime_status_address=relocated_runtime.runtime_status_address,
            runtime_success_status_value=RELOCATED_SUCCESS_STATUS_VALUE,
            bootstrap_return_marker_address=relocated_runtime.bootstrap_return_marker_address,
            bootstrap_return_marker_value=RELOCATED_BOOTSTRAP_RETURN_MARKER_VALUE,
        )

    manifest = Prime3RuntimePayloadManifest(
        schema_version=PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION,
        target_architecture=PRIME3_RUNTIME_TARGET_ARCHITECTURE,
        target_endianness=PRIME3_RUNTIME_TARGET_ENDIANNESS,
        target_abi=PRIME3_RUNTIME_TARGET_ABI,
        compiler_identity=f"powerpc-eabi-gcc (devkitPPC release {toolchain.devkitppc_release})",
        compiler_version=toolchain.compiler_version,
        linker_identity="GNU ld",
        linker_version=toolchain.binutils_version,
        payload_sha256=payload_sha256,
        payload_size=len(payload_bytes),
        required_alignment=PRIME3_RUNTIME_REQUIRED_ALIGNMENT,
        entry_symbol_name=PRIME3_RUNTIME_ENTRY_SYMBOL,
        entry_symbol_offset=entry_offset,
        source_digest=compute_source_digest(SCRIPT_ROOT, SOURCE_FILES),
        protocol_artifact_version=PROTOCOL_VERSION,
        unresolved_relocation_count=unresolved_relocation_count,
        dynamic_section_count=dynamic_section_count,
        payload_mode=payload_mode,
        canary_start_offset=canary_start_offset,
        canary_size=canary_size,
        counter_offset=counter_offset,
        counter_size=4 if counter_offset is not None else None,
        entry_bootstrap=entry_bootstrap,
        relocated_runtime=relocated_runtime_metadata,
    )
    manifest.validate()
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")
    return manifest


def _build_relocated_runtime(
    *,
    toolchain,
    output_dir: Path,
    runtime_destination: int,
) -> RelocatedRuntimeBuildResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    object_path = output_dir.joinpath("relocated_runtime.o")
    elf_path = output_dir.joinpath("relocated_runtime.elf")
    binary_path = output_dir.joinpath("runtime_blob.bin")
    map_path = output_dir.joinpath("relocated_runtime.map")
    compiler_defines = [
        f"-DPRIME3_RUNTIME_EXECUTED_MARKER_VALUE=0x{RELOCATED_EXECUTED_MARKER_VALUE:08X}",
        f"-DPRIME3_RUNTIME_SUCCESS_STATUS_VALUE=0x{RELOCATED_SUCCESS_STATUS_VALUE:08X}",
    ]
    _run(
        [
            os.fspath(toolchain.compiler_path),
            *toolchain.required_machine_flags,
            *compiler_defines,
            "-x",
            "assembler-with-cpp",
            "-c",
            os.fspath(SCRIPT_ROOT.joinpath("relocated_runtime.S")),
            "-o",
            os.fspath(object_path),
        ]
    )
    _run(
        [
            os.fspath(toolchain.linker_path),
            "-EB",
            "--build-id=none",
            "--gc-sections",
            f"--defsym=__runtime_link_address=0x{runtime_destination:08X}",
            "-T",
            os.fspath(SCRIPT_ROOT.joinpath("relocated_runtime.ld")),
            "-Map",
            os.fspath(map_path),
            "-o",
            os.fspath(elf_path),
            os.fspath(object_path),
        ]
    )
    _run(
        [
            os.fspath(toolchain.objcopy_path),
            "-O",
            "binary",
            os.fspath(elf_path),
            os.fspath(binary_path),
        ]
    )
    payload_bytes = binary_path.read_bytes()
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    readelf_header = _run([os.fspath(toolchain.readelf_path), "-h", os.fspath(elf_path)])
    readelf_symbols = _run([os.fspath(toolchain.readelf_path), "-s", "--wide", os.fspath(elf_path)])
    readelf_relocations = _run([os.fspath(toolchain.readelf_path), "-r", os.fspath(elf_path)])
    readelf_dynamic = _run([os.fspath(toolchain.readelf_path), "-d", os.fspath(elf_path)], allow_failure=True)
    _validate_readelf_header(readelf_header)
    if _count_relocations(readelf_relocations) != 0:
        raise RuntimeError("Relocated runtime ELF has unresolved relocations.")
    if _count_dynamic_sections(readelf_dynamic) != 0:
        raise RuntimeError("Relocated runtime ELF has dynamic sections.")

    entry_address = _extract_symbol_address(readelf_symbols, RUNTIME_ENTRY_SYMBOL)
    code_start = _extract_symbol_address(readelf_symbols, RUNTIME_CODE_START_SYMBOL)
    code_end = _extract_symbol_address(readelf_symbols, RUNTIME_CODE_END_SYMBOL)
    state_start = _extract_symbol_address(readelf_symbols, RUNTIME_STATE_START_SYMBOL)
    state_end = _extract_symbol_address(readelf_symbols, RUNTIME_STATE_END_SYMBOL)
    canary_start = _extract_symbol_address(readelf_symbols, RUNTIME_CANARY_START_SYMBOL)
    canary_end = _extract_symbol_address(readelf_symbols, RUNTIME_CANARY_END_SYMBOL)
    copy_complete_marker_address = _extract_symbol_address(readelf_symbols, RUNTIME_COPY_COMPLETE_MARKER_SYMBOL)
    runtime_executed_marker_address = _extract_symbol_address(readelf_symbols, RUNTIME_EXECUTED_MARKER_SYMBOL)
    runtime_execution_counter_address = _extract_symbol_address(readelf_symbols, RUNTIME_EXECUTION_COUNTER_SYMBOL)
    runtime_status_address = _extract_symbol_address(readelf_symbols, RUNTIME_STATUS_SYMBOL)
    bootstrap_return_marker_address = _extract_symbol_address(readelf_symbols, RUNTIME_BOOTSTRAP_RETURN_MARKER_SYMBOL)
    cache_range_start, cache_range_size = compute_cache_range(
        address=runtime_destination,
        size=len(payload_bytes),
        cache_line_size=RELOCATED_RUNTIME_CACHE_LINE_SIZE,
    )
    return RelocatedRuntimeBuildResult(
        payload_bytes=payload_bytes,
        payload_sha256=payload_sha256,
        payload_size=len(payload_bytes),
        entry_address=entry_address,
        code_start=code_start,
        code_end=code_end,
        state_start=state_start,
        state_end=state_end,
        canary_address=canary_start,
        canary_size=canary_end - canary_start,
        canary_sha256=hashlib.sha256(RELOCATED_RUNTIME_CANARY_BYTES).hexdigest(),
        copy_complete_marker_address=copy_complete_marker_address,
        runtime_executed_marker_address=runtime_executed_marker_address,
        runtime_execution_counter_address=runtime_execution_counter_address,
        runtime_status_address=runtime_status_address,
        bootstrap_return_marker_address=bootstrap_return_marker_address,
        cache_range_start=cache_range_start,
        cache_range_size=cache_range_size,
    )


def _write_runtime_blob_object(*, toolchain, output_dir: Path) -> None:
    _run(
        [
            os.fspath(toolchain.objcopy_path),
            "-I",
            "binary",
            "-O",
            "elf32-powerpc",
            "-B",
            "powerpc",
            "runtime_blob.bin",
            "runtime_blob.o",
        ],
        cwd=output_dir,
    )


def _bootstrap_status_value(payload_mode: str) -> int:
    if payload_mode == PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT:
        return BOOTSTRAP_HALT_STATUS_VALUE
    if payload_mode == PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_CONTINUE:
        return BOOTSTRAP_CONTINUE_STATUS_VALUE
    if payload_mode == PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT:
        return RELOCATED_COPY_HALT_STATUS_VALUE
    if payload_mode == PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT:
        return RELOCATED_RETURN_HALT_STATUS_VALUE
    if payload_mode == PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE:
        return RELOCATED_CONTINUE_STATUS_VALUE
    raise RuntimeError(f"Unsupported bootstrap payload mode {payload_mode!r}.")


def _run(command: list[str], *, allow_failure: bool = False, cwd: Path | None = None) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=cwd)
    if result.returncode != 0 and not allow_failure:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return (result.stdout or result.stderr).strip()


def _validate_readelf_header(output: str) -> None:
    required_lines = (
        "Class:                             ELF32",
        "Data:                              2's complement, big endian",
        "Type:                              EXEC (Executable file)",
        "Machine:                           PowerPC",
    )
    for line in required_lines:
        if line not in output:
            raise RuntimeError(f"Built payload ELF is missing expected header line: {line!r}")


def _extract_entry_offset(symbol_output: str, entry_symbol: str, *, symbol_base: int = 0) -> int:
    return _normalize_symbol_value(_extract_symbol_address(symbol_output, entry_symbol), symbol_base=symbol_base)


def _extract_symbol_address(symbol_output: str, symbol_name: str) -> int:
    for line in symbol_output.splitlines():
        if line.strip().endswith(f" {symbol_name}"):
            return int(line.split()[1], 16)
    raise RuntimeError(f"Unable to locate symbol {symbol_name!r} in readelf symbol output.")


def _extract_optional_symbol_offset(symbol_output: str, symbol_name: str, *, symbol_base: int = 0) -> int | None:
    for line in symbol_output.splitlines():
        if line.strip().endswith(f" {symbol_name}"):
            return _normalize_symbol_value(int(line.split()[1], 16), symbol_base=symbol_base)
    return None


def _normalize_symbol_value(value: int, *, symbol_base: int) -> int:
    if value < symbol_base:
        raise RuntimeError(f"Symbol value 0x{value:08x} is below the expected base 0x{symbol_base:08x}.")
    return value - symbol_base


def _count_relocations(relocation_output: str) -> int:
    count = 0
    for line in relocation_output.splitlines():
        stripped = line.strip()
        if stripped.startswith(("Offset", "There are no relocations")):
            continue
        if stripped and stripped[0] in "0123456789abcdefABCDEF":
            count += 1
    return count


def _count_dynamic_sections(dynamic_output: str) -> int:
    if not dynamic_output or "There is no dynamic section in this file." in dynamic_output:
        return 0
    count = 0
    for line in dynamic_output.splitlines():
        stripped = line.strip()
        if stripped.startswith(("Tag", "Dynamic section at offset")):
            continue
        if stripped.startswith("0x"):
            count += 1
    return count


def main() -> None:
    args = parse_args()
    selected_modes = [
        args.probe,
        args.bootstrap_halt,
        args.bootstrap_continue,
        args.relocated_copy_halt,
        args.relocated_return_halt,
        args.relocated_continue,
    ]
    if sum(1 for selected in selected_modes if selected) > 1:
        raise RuntimeError("Use only one payload mode flag at a time.")
    if args.probe:
        payload_mode = PRIME3_RUNTIME_PAYLOAD_MODE_PROBE
    elif args.bootstrap_halt:
        payload_mode = PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_HALT
    elif args.bootstrap_continue:
        payload_mode = PRIME3_RUNTIME_PAYLOAD_MODE_ENTRY_BOOTSTRAP_CONTINUE
    elif args.relocated_copy_halt:
        payload_mode = PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_COPY_HALT
    elif args.relocated_return_halt:
        payload_mode = PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_RETURN_HALT
    elif args.relocated_continue:
        payload_mode = PRIME3_RUNTIME_PAYLOAD_MODE_RELOCATED_CONTINUE
    else:
        payload_mode = PRIME3_RUNTIME_PAYLOAD_MODE_NORMAL

    reserved_high = None if args.reserved_high is None else int(args.reserved_high, 0)
    diagnostic_address = None if args.diagnostic_address is None else int(args.diagnostic_address, 0)
    runtime_destination = None if args.runtime_destination is None else int(args.runtime_destination, 0)
    if payload_mode in PRIME3_RUNTIME_ENTRY_BOOTSTRAP_MODES:
        if reserved_high is None or diagnostic_address is None:
            raise RuntimeError("Bootstrap payload modes require --reserved-high and --diagnostic-address.")
    build_prime3_runtime_payload(
        Path(args.output_dir),
        payload_mode=payload_mode,
        reserved_high=reserved_high,
        diagnostic_address=diagnostic_address,
        runtime_destination=runtime_destination,
    )


if __name__ == "__main__":
    main()
