from __future__ import annotations

import argparse
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
    PRIME3_RUNTIME_ENTRY_SYMBOL,
    PRIME3_RUNTIME_PAYLOAD_SCHEMA_VERSION,
    PRIME3_RUNTIME_REQUIRED_ALIGNMENT,
    PRIME3_RUNTIME_TARGET_ABI,
    PRIME3_RUNTIME_TARGET_ARCHITECTURE,
    PRIME3_RUNTIME_TARGET_ENDIANNESS,
    Prime3RuntimePayloadManifest,
    compute_source_digest,
)
from randovania.games.prime3.exporter.runtime_toolchain import resolve_prime3_runtime_toolchain

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = ROOT.joinpath("build", "prime3_wii_runtime")
SOURCE_FILES = (
    Path("payload.S"),
    Path("payload.ld"),
    Path("build_payload.py"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def build_prime3_runtime_payload(output_dir: Path) -> Prime3RuntimePayloadManifest:
    toolchain = resolve_prime3_runtime_toolchain()

    output_dir.mkdir(parents=True, exist_ok=True)
    object_path = output_dir.joinpath("payload.o")
    elf_path = output_dir.joinpath("payload.elf")
    binary_path = output_dir.joinpath("payload.bin")
    map_path = output_dir.joinpath("payload.map")
    manifest_path = output_dir.joinpath("payload.json")

    _run(
        [
            os.fspath(toolchain.compiler_path),
            *toolchain.required_machine_flags,
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
            "-T",
            os.fspath(SCRIPT_ROOT.joinpath("payload.ld")),
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
    readelf_symbols = _run([os.fspath(toolchain.readelf_path), "-s", os.fspath(elf_path)])
    readelf_relocations = _run([os.fspath(toolchain.readelf_path), "-r", os.fspath(elf_path)])
    readelf_dynamic = _run([os.fspath(toolchain.readelf_path), "-d", os.fspath(elf_path)], allow_failure=True)

    entry_offset = _extract_entry_offset(readelf_symbols, PRIME3_RUNTIME_ENTRY_SYMBOL)
    unresolved_relocation_count = _count_relocations(readelf_relocations)
    dynamic_section_count = _count_dynamic_sections(readelf_dynamic)
    _validate_readelf_header(readelf_header)

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
    )
    manifest.validate()
    if manifest.protocol_artifact_version != PROTOCOL_VERSION:
        raise AssertionError("Unexpected protocol version serialization.")
    manifest_path.write_text(manifest.to_json_text(), encoding="utf-8")
    return manifest


def _run(command: list[str], *, allow_failure: bool = False) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
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


def _extract_entry_offset(symbol_output: str, entry_symbol: str) -> int:
    for line in symbol_output.splitlines():
        if line.strip().endswith(f" {entry_symbol}"):
            value = line.split()[1]
            return int(value, 16)
    raise RuntimeError(f"Unable to locate entry symbol {entry_symbol!r} in readelf symbol output.")


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
    build_prime3_runtime_payload(Path(args.output_dir))


if __name__ == "__main__":
    main()
