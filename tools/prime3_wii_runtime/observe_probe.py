from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Protocol, TypedDict

if __package__ in {None, ""}:
    _repository_root = Path(__file__).resolve().parents[2]
    _repository_root_str = os.fspath(_repository_root)
    if _repository_root_str not in sys.path:
        sys.path.insert(0, _repository_root_str)

import dolphin_memory_engine  # type: ignore[import-untyped]

from randovania.games.prime3.exporter.runtime_payload import Prime3RuntimePayloadManifest

GAME_ID_ADDRESS = 0x80000000
BOOT_INFO_POINTER_ADDRESS = 0x800000F4
LOW_MEMORY_WORDS = (
    0x80000034,
    0x80003110,
    BOOT_INFO_POINTER_ADDRESS,
)
MEM1_START = 0x80000000
MEM1_END = 0x81800000


class DolphinReadOnlyBackend(Protocol):
    def is_hooked(self) -> bool: ...

    def hook(self) -> None: ...

    def un_hook(self) -> None: ...

    def read_bytes(self, address: int, size: int) -> bytes: ...


@dataclasses.dataclass(frozen=True)
class StartupWordExpectation:
    address: int
    expected_word: int


@dataclasses.dataclass(frozen=True)
class ProbeObservationConfig:
    checkpoint_name: str | None
    halt_address: int | None
    expected_halt_word: int | None
    expected_game_id: bytes
    payload_address: int
    payload_bytes: bytes
    manifest: Prime3RuntimePayloadManifest
    startup_words: tuple[StartupWordExpectation, ...]
    repeat_delay_seconds: float = 0.0
    iso_path: str | None = None
    iso_sha256: str | None = None
    dolphin_command_line: str | None = None


class ProbeObservationError(RuntimeError):
    pass


class StartupWordObservation(TypedDict):
    expected: int
    observed: int
    matches: bool


class ProbeCanaryObservation(TypedDict):
    address: int
    size: int
    sha256: str
    matches_expected: bool


class ProbeCounterObservation(TypedDict):
    address: int
    size: int
    value: int


class BootstrapDiagnosticObservation(TypedDict):
    address: int
    size: int
    sha256: str
    canary_matches_expected: bool
    marker_value: int
    marker_matches_expected: bool
    counter_value: int
    original_80000034: int
    original_80003110: int
    replacement_value: int
    replacement_matches_expected: bool
    status_value: int
    status_matches_expected: bool


class ProbeState(TypedDict):
    game_id: bytes
    startup_words: dict[str, StartupWordObservation]
    live_halt_word: int | None
    payload_sha256: str
    payload_matches_expected: bool
    payload_all_zero: bool
    payload_classification: str
    low_memory_words: dict[str, int]
    canary: ProbeCanaryObservation | None
    counter: ProbeCounterObservation | None
    bootstrap_diagnostic: BootstrapDiagnosticObservation | None
    boot_info_plus_8: int | None
    invalid_boot_info_pointer: int | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-address", type=_parse_int, required=True)
    parser.add_argument("--payload-bin", type=Path, required=True)
    parser.add_argument("--payload-manifest", type=Path, required=True)
    parser.add_argument("--checkpoint-name")
    parser.add_argument("--halt-address", type=_parse_int)
    parser.add_argument("--expected-halt-word", type=_parse_int)
    parser.add_argument("--expected-game-id", default="RM3E01")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--startup-word", action="append", default=[])
    parser.add_argument("--repeat-delay-ms", type=int, default=0)
    parser.add_argument("--iso-path")
    parser.add_argument("--iso-sha256")
    parser.add_argument("--dolphin-command-line")
    return parser.parse_args()


def observe_probe_memory(
    backend: DolphinReadOnlyBackend,
    config: ProbeObservationConfig,
) -> dict[str, object]:
    _ensure_connected(backend)
    first_read = _read_probe_state(backend, config)
    advance_cycle = getattr(backend, "advance_cycle", None)
    if callable(advance_cycle):
        advance_cycle()
    if config.repeat_delay_seconds > 0:
        time.sleep(config.repeat_delay_seconds)
    second_read = _read_probe_state(backend, config)

    game_id = first_read["game_id"]
    if game_id != config.expected_game_id:
        raise ProbeObservationError(
            f"Unexpected game ID {game_id!r}; expected {config.expected_game_id!r}."
        )

    result: dict[str, object] = {
        "checkpoint_name": config.checkpoint_name,
        "expected_halt_address": config.halt_address,
        "expected_halt_word": config.expected_halt_word,
        "live_halt_word": first_read["live_halt_word"],
        "halt_active": _halt_active(first_read, config),
        "game_id": game_id.decode("ascii", errors="replace"),
        "entrypoint_address": config.startup_words[0].address if config.startup_words else None,
        "startup_words": first_read["startup_words"],
        "payload_address": config.payload_address,
        "payload_size": config.manifest.payload_size,
        "expected_payload_sha256": hashlib.sha256(config.payload_bytes).hexdigest(),
        "live_payload_sha256": first_read["payload_sha256"],
        "payload_matches_expected": first_read["payload_matches_expected"],
        "payload_classification": first_read["payload_classification"],
        "payload_all_zero": first_read["payload_all_zero"],
        "repeated_read_stable": first_read["payload_sha256"] == second_read["payload_sha256"],
        "second_live_payload_sha256": second_read["payload_sha256"],
        "entry_gate_active": all(item["matches"] for item in first_read["startup_words"].values())
        if first_read["startup_words"]
        else False,
        "low_memory_words": first_read["low_memory_words"],
    }
    if config.manifest.entry_bootstrap is not None:
        result["bootstrap_staging_address"] = config.manifest.entry_bootstrap.staging_address
        result["bootstrap_halt_loop_address"] = config.manifest.entry_bootstrap.halt_loop_address
        result["reserved_boundary"] = config.manifest.entry_bootstrap.reserved_boundary
        result["reserved_range_start"] = config.manifest.entry_bootstrap.reserved_range_start
        result["reserved_range_end"] = config.manifest.entry_bootstrap.reserved_range_end
        result["diagnostic_address"] = config.manifest.entry_bootstrap.diagnostic_address

    if first_read["canary"] is not None:
        result["canary"] = first_read["canary"]
    if first_read["counter"] is not None:
        result["counter"] = first_read["counter"]
    if first_read["bootstrap_diagnostic"] is not None:
        result["bootstrap_diagnostic"] = first_read["bootstrap_diagnostic"]
    if first_read["boot_info_plus_8"] is not None:
        result["boot_info_plus_8"] = first_read["boot_info_plus_8"]
    if first_read["invalid_boot_info_pointer"] is not None:
        result["invalid_boot_info_pointer"] = first_read["invalid_boot_info_pointer"]
    if config.iso_path is not None:
        result["iso_path"] = config.iso_path
    if config.iso_sha256 is not None:
        result["iso_sha256"] = config.iso_sha256
    if config.dolphin_command_line is not None:
        result["dolphin_command_line"] = config.dolphin_command_line
    return result


def _read_probe_state(
    backend: DolphinReadOnlyBackend,
    config: ProbeObservationConfig,
) -> ProbeState:
    game_id = _read_exact(backend, GAME_ID_ADDRESS, len(config.expected_game_id), "game ID")
    startup_words: dict[str, StartupWordObservation] = {}
    for item in config.startup_words:
        observed = int.from_bytes(_read_exact(backend, item.address, 4, f"startup word 0x{item.address:08x}"), "big")
        startup_words[f"0x{item.address:08X}"] = {
            "expected": item.expected_word,
            "observed": observed,
            "matches": observed == item.expected_word,
        }
    live_halt_word = None
    if config.halt_address is not None:
        live_halt_word = int.from_bytes(
            _read_exact(backend, config.halt_address, 4, f"halt word 0x{config.halt_address:08x}"),
            "big",
        )

    payload_bytes = _read_exact(backend, config.payload_address, config.manifest.payload_size, "payload bytes")
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    low_memory_words: dict[str, int] = {}
    for address in LOW_MEMORY_WORDS:
        low_memory_words[f"0x{address:08X}"] = int.from_bytes(
            _read_exact(backend, address, 4, f"word 0x{address:08x}"),
            "big",
        )

    canary: ProbeCanaryObservation | None = None
    if config.manifest.canary_start_offset is not None and config.manifest.canary_size is not None:
        start = config.manifest.canary_start_offset
        end = start + config.manifest.canary_size
        canary_bytes = payload_bytes[start:end]
        canary = {
            "address": config.payload_address + start,
            "size": config.manifest.canary_size,
            "sha256": hashlib.sha256(canary_bytes).hexdigest(),
            "matches_expected": canary_bytes == config.payload_bytes[start:end],
        }

    counter: ProbeCounterObservation | None = None
    if config.manifest.counter_offset is not None and config.manifest.counter_size is not None:
        start = config.manifest.counter_offset
        end = start + config.manifest.counter_size
        counter = {
            "address": config.payload_address + start,
            "size": config.manifest.counter_size,
            "value": int.from_bytes(payload_bytes[start:end], "big"),
        }

    bootstrap_diagnostic: BootstrapDiagnosticObservation | None = None
    if config.manifest.entry_bootstrap is not None:
        metadata = config.manifest.entry_bootstrap
        diagnostic_bytes = _read_exact(
            backend,
            metadata.diagnostic_address,
            metadata.diagnostic_block_size,
            f"bootstrap diagnostic block 0x{metadata.diagnostic_address:08x}",
        )
        canary_start = metadata.canary_address - metadata.diagnostic_address
        canary_end = canary_start + metadata.canary_size
        canary_bytes = diagnostic_bytes[canary_start:canary_end]
        marker_start = metadata.marker_address - metadata.diagnostic_address
        counter_start = metadata.counter_address - metadata.diagnostic_address
        original_34_start = metadata.original_80000034_address - metadata.diagnostic_address
        original_3110_start = metadata.original_80003110_address - metadata.diagnostic_address
        replacement_start = metadata.replacement_value_address - metadata.diagnostic_address
        status_start = metadata.status_address - metadata.diagnostic_address
        marker_value = int.from_bytes(diagnostic_bytes[marker_start : marker_start + 4], "big")
        counter_value = int.from_bytes(
            diagnostic_bytes[counter_start : counter_start + metadata.counter_size],
            "big",
        )
        replacement_value = int.from_bytes(diagnostic_bytes[replacement_start : replacement_start + 4], "big")
        status_value = int.from_bytes(diagnostic_bytes[status_start : status_start + 4], "big")
        bootstrap_diagnostic = {
            "address": metadata.diagnostic_address,
            "size": metadata.diagnostic_block_size,
            "sha256": hashlib.sha256(diagnostic_bytes).hexdigest(),
            "canary_matches_expected": hashlib.sha256(canary_bytes).hexdigest() == metadata.canary_sha256,
            "marker_value": marker_value,
            "marker_matches_expected": marker_value == metadata.marker_value,
            "counter_value": counter_value,
            "original_80000034": int.from_bytes(diagnostic_bytes[original_34_start : original_34_start + 4], "big"),
            "original_80003110": int.from_bytes(
                diagnostic_bytes[original_3110_start : original_3110_start + 4],
                "big",
            ),
            "replacement_value": replacement_value,
            "replacement_matches_expected": replacement_value == metadata.replacement_value,
            "status_value": status_value,
            "status_matches_expected": status_value == metadata.status_value,
        }

    boot_info_pointer = low_memory_words["0x800000F4"]
    boot_info_plus_8 = None
    invalid_boot_info_pointer = None
    if boot_info_pointer != 0:
        if not MEM1_START <= boot_info_pointer <= MEM1_END - 4:
            invalid_boot_info_pointer = boot_info_pointer
        else:
            boot_info_plus_8 = int.from_bytes(
                _read_exact(backend, boot_info_pointer + 0x08, 4, f"word 0x{boot_info_pointer + 0x08:08x}"),
                "big",
            )

    return {
        "game_id": game_id,
        "startup_words": startup_words,
        "live_halt_word": live_halt_word,
        "payload_sha256": payload_sha256,
        "payload_matches_expected": payload_bytes == config.payload_bytes,
        "payload_all_zero": all(item == 0 for item in payload_bytes),
        "payload_classification": _classify_payload(payload_bytes, config.payload_bytes),
        "low_memory_words": low_memory_words,
        "canary": canary,
        "counter": counter,
        "bootstrap_diagnostic": bootstrap_diagnostic,
        "boot_info_plus_8": boot_info_plus_8,
        "invalid_boot_info_pointer": invalid_boot_info_pointer,
    }


def _classify_payload(payload_bytes: bytes, expected_payload_bytes: bytes) -> str:
    if len(payload_bytes) != len(expected_payload_bytes):
        return "partial read"
    if payload_bytes == expected_payload_bytes:
        return "exact payload match"
    if all(item == 0 for item in payload_bytes):
        return "all zero"
    return "payload present but altered"


def _halt_active(first_read: ProbeState, config: ProbeObservationConfig) -> bool | None:
    if config.halt_address is None:
        return None
    startup_key = f"0x{config.halt_address:08X}"
    if startup_key in first_read["startup_words"]:
        return first_read["startup_words"][startup_key]["matches"]
    if config.expected_halt_word is None or first_read["live_halt_word"] is None:
        return None
    return first_read["live_halt_word"] == config.expected_halt_word


def _ensure_connected(backend: DolphinReadOnlyBackend) -> None:
    if not backend.is_hooked():
        backend.hook()
    if not backend.is_hooked():
        raise ProbeObservationError("Unable to connect to Dolphin.")


def _read_exact(backend: DolphinReadOnlyBackend, address: int, size: int, label: str) -> bytes:
    try:
        data = backend.read_bytes(address, size)
    except RuntimeError as exc:
        raise ProbeObservationError(f"Unable to read {label}: {exc}") from exc
    if len(data) != size:
        raise ProbeObservationError(f"Short read for {label}: expected {size} bytes, got {len(data)}.")
    return data


def _parse_int(value: str) -> int:
    return int(value, 0)


def _parse_startup_word(value: str) -> StartupWordExpectation:
    address_text, expected_text = value.split("=", 1)
    return StartupWordExpectation(address=_parse_int(address_text), expected_word=_parse_int(expected_text))


def main() -> None:
    args = parse_args()
    if args.checkpoint_name is None and args.halt_address is None and args.expected_halt_word is None:
        checkpoint_name = None
    else:
        if args.checkpoint_name is None or not args.checkpoint_name.strip():
            raise ProbeObservationError("Checkpoint observation requires a non-empty --checkpoint-name.")
        if args.halt_address is None:
            raise ProbeObservationError("Checkpoint observation requires --halt-address.")
        if args.expected_halt_word is None:
            raise ProbeObservationError("Checkpoint observation requires --expected-halt-word.")
        checkpoint_name = args.checkpoint_name
    manifest = Prime3RuntimePayloadManifest.from_json_text(args.payload_manifest.read_text(encoding="utf-8"))
    payload_bytes = args.payload_bin.read_bytes()
    config = ProbeObservationConfig(
        checkpoint_name=checkpoint_name,
        halt_address=args.halt_address,
        expected_halt_word=args.expected_halt_word,
        expected_game_id=args.expected_game_id.encode("ascii"),
        payload_address=args.payload_address,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=tuple(_parse_startup_word(item) for item in args.startup_word),
        repeat_delay_seconds=max(args.repeat_delay_ms, 0) / 1000.0,
        iso_path=args.iso_path,
        iso_sha256=args.iso_sha256,
        dolphin_command_line=args.dolphin_command_line,
    )
    report = observe_probe_memory(dolphin_memory_engine, config)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
