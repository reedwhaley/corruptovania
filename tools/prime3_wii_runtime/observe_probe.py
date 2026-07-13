from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Protocol

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
    expected_game_id: bytes
    payload_address: int
    payload_bytes: bytes
    manifest: Prime3RuntimePayloadManifest
    startup_words: tuple[StartupWordExpectation, ...]


class ProbeObservationError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-address", type=_parse_int, required=True)
    parser.add_argument("--payload-bin", type=Path, required=True)
    parser.add_argument("--payload-manifest", type=Path, required=True)
    parser.add_argument("--expected-game-id", default="RM3E01")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--startup-word", action="append", default=[])
    return parser.parse_args()


def observe_probe_memory(
    backend: DolphinReadOnlyBackend,
    config: ProbeObservationConfig,
) -> dict[str, object]:
    _ensure_connected(backend)
    game_id = _read_exact(backend, GAME_ID_ADDRESS, len(config.expected_game_id), "game ID")
    if game_id != config.expected_game_id:
        raise ProbeObservationError(
            f"Unexpected game ID {game_id!r}; expected {config.expected_game_id!r}."
        )

    startup_words = {}
    for item in config.startup_words:
        observed = int.from_bytes(_read_exact(backend, item.address, 4, f"startup word 0x{item.address:08x}"), "big")
        startup_words[f"0x{item.address:08X}"] = {
            "expected": item.expected_word,
            "observed": observed,
            "matches": observed == item.expected_word,
        }

    payload_bytes = _read_exact(backend, config.payload_address, config.manifest.payload_size, "payload bytes")
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()

    result: dict[str, object] = {
        "game_id": game_id.decode("ascii", errors="replace"),
        "startup_words": startup_words,
        "payload_address": config.payload_address,
        "payload_size": config.manifest.payload_size,
        "payload_sha256": payload_sha256,
        "payload_matches_expected": payload_bytes == config.payload_bytes,
        "low_memory_words": {},
    }

    if config.manifest.canary_start_offset is not None and config.manifest.canary_size is not None:
        start = config.manifest.canary_start_offset
        end = start + config.manifest.canary_size
        canary_bytes = payload_bytes[start:end]
        result["canary"] = {
            "address": config.payload_address + start,
            "size": config.manifest.canary_size,
            "sha256": hashlib.sha256(canary_bytes).hexdigest(),
            "matches_expected": canary_bytes == config.payload_bytes[start:end],
        }

    if config.manifest.counter_offset is not None and config.manifest.counter_size is not None:
        start = config.manifest.counter_offset
        end = start + config.manifest.counter_size
        result["counter"] = {
            "address": config.payload_address + start,
            "size": config.manifest.counter_size,
            "value": int.from_bytes(payload_bytes[start:end], "big"),
        }

    low_memory_words = {}
    for address in LOW_MEMORY_WORDS:
        low_memory_words[f"0x{address:08X}"] = int.from_bytes(
            _read_exact(backend, address, 4, f"word 0x{address:08x}"),
            "big",
        )
    result["low_memory_words"] = low_memory_words

    boot_info_pointer = low_memory_words["0x800000F4"]
    if boot_info_pointer != 0:
        result["boot_info_plus_8"] = int.from_bytes(
            _read_exact(backend, boot_info_pointer + 0x08, 4, f"word 0x{boot_info_pointer + 0x08:08x}"),
            "big",
        )
    return result


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
    manifest = Prime3RuntimePayloadManifest.from_json_text(args.payload_manifest.read_text(encoding="utf-8"))
    payload_bytes = args.payload_bin.read_bytes()
    config = ProbeObservationConfig(
        expected_game_id=args.expected_game_id.encode("ascii"),
        payload_address=args.payload_address,
        payload_bytes=payload_bytes,
        manifest=manifest,
        startup_words=tuple(_parse_startup_word(item) for item in args.startup_word),
    )
    report = observe_probe_memory(dolphin_memory_engine, config)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
