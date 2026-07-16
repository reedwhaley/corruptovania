from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Protocol, TypedDict, cast

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
DIAGNOSTIC_MARKER_NAMES = {
    0xC0DE0001: "hook_wrapper_entered",
    0xC0DE0002: "poll_entry",
    0xC0DE0003: "state_machine_entry",
    0xC0DE0004: "c_before_veneer_call",
    0xC0DE0005: "retail_veneer_entered",
    0xC0DE0006: "retail_before_target",
    0xC0DE0007: "retail_target_returned",
    0xC0DE0008: "retail_before_lr_restore",
    0xC0DE0009: "retail_before_veneer_blr",
    0xC0DE000A: "c_after_veneer_call",
    0xC0DE000B: "poll_returning",
    0xC0DE000C: "wrapper_restoring_state",
    0xC0DE000D: "wrapper_returning_to_game",
}
TRANSPORT_PHASE_NAMES = {
    0: "UNINITIALIZED",
    1: "OPEN_KD",
    2: "WAIT_OPEN_KD",
    3: "NWC24_STARTUP",
    4: "WAIT_NWC24_STARTUP",
    5: "CLOSE_KD",
    6: "WAIT_CLOSE_KD",
    7: "OPEN_IP",
    8: "WAIT_OPEN_IP",
    9: "SO_STARTUP",
    10: "WAIT_SO_STARTUP",
    19: "HOST_ID_READY",
    18: "SO_STARTED",
    11: "GET_HOST_ID",
    12: "WAIT_GETHOSTID",
    13: "CREATE_SOCKET",
    14: "WAIT_CREATE_SOCKET",
    15: "BIND_SOCKET",
    16: "WAIT_BIND_SOCKET",
    17: "BOUND_NO_RECV",
    21: "CLOSE_SOCKET_AFTER_BIND_FAILURE",
    22: "WAIT_CLOSE_SOCKET_AFTER_BIND_FAILURE",
    23: "BIND_FAILED_CLEANED",
    24: "FAILED_SOCKET_LEAK",
    0xFE: "DIAGNOSTIC_COMPLETE",
    0xFF: "FAILED",
    20: "SOCKET_READY",
}
TRANSPORT_OPERATION_NAMES = {
    0: "none",
    1: "open_kd",
    2: "nwc24_startup",
    3: "close_kd",
    4: "open_ip",
    5: "startup",
    6: "get_host_id",
    7: "create_socket",
    8: "bind_socket",
    9: "close_socket_after_bind_failure",
}


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
    hook_address: int | None = None
    expected_hook_word: int | None = None
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


class RelocatedRuntimeObservation(TypedDict):
    address: int
    size: int
    sha256: str
    code_sha256: str
    state_sha256: str
    matches_expected: bool
    all_zero: bool
    classification: str
    copy_complete_marker_value: int
    copy_complete_matches_expected: bool
    runtime_executed_marker_value: int
    runtime_executed_matches_expected: bool
    runtime_execution_counter_value: int
    runtime_status_value: int
    runtime_status_matches_expected: bool
    bootstrap_return_marker_value: int
    bootstrap_return_matches_expected: bool
    runtime_poll_counter_value: int
    runtime_poll_heartbeat_value: int
    runtime_poll_last_sequence_value: int
    diagnostics: dict[str, object] | None
    transport: dict[str, object] | None
    abi_probe: dict[str, object] | None
    retail_ios_wrapper: dict[str, object] | None


class ProbeState(TypedDict):
    game_id: bytes
    startup_words: dict[str, StartupWordObservation]
    live_halt_word: int | None
    live_hook_word: int | None
    payload_sha256: str
    payload_matches_expected: bool
    payload_all_zero: bool
    payload_classification: str
    low_memory_words: dict[str, int]
    canary: ProbeCanaryObservation | None
    counter: ProbeCounterObservation | None
    bootstrap_diagnostic: BootstrapDiagnosticObservation | None
    relocated_runtime: RelocatedRuntimeObservation | None
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
    parser.add_argument("--hook-address", type=_parse_int)
    parser.add_argument("--expected-hook-word", type=_parse_int)
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
        "hook_address": config.hook_address,
        "expected_hook_word": config.expected_hook_word,
        "live_hook_word": first_read["live_hook_word"],
        "hook_word_matches_expected": (
            None
            if config.hook_address is None or config.expected_hook_word is None or first_read["live_hook_word"] is None
            else first_read["live_hook_word"] == config.expected_hook_word
        ),
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
        "poll_rate_sample_interval_seconds": config.repeat_delay_seconds,
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
    if first_read["relocated_runtime"] is not None:
        first_runtime = first_read["relocated_runtime"]
        second_runtime = second_read["relocated_runtime"]
        assert first_runtime is not None
        assert second_runtime is not None
        result["relocated_runtime"] = first_runtime
        result["state_checksum"] = first_runtime["state_sha256"]
        result["second_state_checksum"] = second_runtime["state_sha256"]
        result["poll_counter_delta"] = (
            second_runtime["runtime_poll_counter_value"] - first_runtime["runtime_poll_counter_value"]
        )
        result["poll_counter_monotonic"] = (
            second_runtime["runtime_poll_counter_value"] >= first_runtime["runtime_poll_counter_value"]
        )
        result["heartbeat_updated"] = (
            second_runtime["runtime_poll_heartbeat_value"] != first_runtime["runtime_poll_heartbeat_value"]
        )
        result["approximate_calls_per_second"] = (
            None
            if config.repeat_delay_seconds <= 0
            else (second_runtime["runtime_poll_counter_value"] - first_runtime["runtime_poll_counter_value"])
            / config.repeat_delay_seconds
        )
        diagnostics = first_runtime["diagnostics"]
        if diagnostics is not None:
            recurring_execution_continuing = cast("int", result["poll_counter_delta"]) > 0
            result["recurring_execution_continuing"] = recurring_execution_continuing
            result["probable_stop_boundary"] = _diagnostic_stop_boundary(
                diagnostics=diagnostics,
                transport=first_runtime["transport"],
                abi_probe=cast("dict[str, object] | None", first_runtime.get("abi_probe")),
                recurring_execution_continuing=recurring_execution_continuing,
            )
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


def _read_probe_state(  # noqa: C901
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
    live_hook_word = None
    if config.hook_address is not None:
        live_hook_word = int.from_bytes(
            _read_exact(backend, config.hook_address, 4, f"hook word 0x{config.hook_address:08x}"),
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

    relocated_runtime: RelocatedRuntimeObservation | None = None
    if config.manifest.relocated_runtime is not None:
        runtime_metadata = config.manifest.relocated_runtime
        start = runtime_metadata.embedded_runtime_blob_offset
        end = start + runtime_metadata.embedded_runtime_blob_size
        expected_runtime_bytes = config.payload_bytes[start:end]
        runtime_bytes = _read_exact(
            backend,
            runtime_metadata.runtime_destination_address,
            runtime_metadata.embedded_runtime_blob_size,
            f"relocated runtime bytes 0x{runtime_metadata.runtime_destination_address:08x}",
        )
        runtime_code_offset = runtime_metadata.runtime_code_start - runtime_metadata.runtime_destination_address
        runtime_code_end_offset = runtime_metadata.runtime_code_end - runtime_metadata.runtime_destination_address
        runtime_state_offset = runtime_metadata.runtime_state_start - runtime_metadata.runtime_destination_address
        runtime_state_end_offset = runtime_metadata.runtime_state_end - runtime_metadata.runtime_destination_address
        runtime_executed_marker_offset = (
            runtime_metadata.runtime_executed_marker_address - runtime_metadata.runtime_destination_address
        )
        copy_complete_marker_offset = (
            runtime_metadata.copy_complete_marker_address - runtime_metadata.runtime_destination_address
        )
        counter_offset = (
            runtime_metadata.runtime_execution_counter_address - runtime_metadata.runtime_destination_address
        )
        status_offset = runtime_metadata.runtime_status_address - runtime_metadata.runtime_destination_address
        bootstrap_return_offset = (
            runtime_metadata.bootstrap_return_marker_address - runtime_metadata.runtime_destination_address
        )
        poll_counter_offset = (
            runtime_metadata.runtime_poll_counter_address - runtime_metadata.runtime_destination_address
        )
        poll_heartbeat_offset = (
            runtime_metadata.runtime_poll_heartbeat_address - runtime_metadata.runtime_destination_address
        )
        poll_last_sequence_offset = (
            runtime_metadata.runtime_poll_last_sequence_address - runtime_metadata.runtime_destination_address
        )
        relocated_runtime = cast(
            "RelocatedRuntimeObservation",
            {
            "address": runtime_metadata.runtime_destination_address,
            "size": runtime_metadata.embedded_runtime_blob_size,
            "sha256": hashlib.sha256(runtime_bytes).hexdigest(),
            "code_sha256": hashlib.sha256(runtime_bytes[runtime_code_offset:runtime_code_end_offset]).hexdigest(),
            "state_sha256": hashlib.sha256(runtime_bytes[runtime_state_offset:runtime_state_end_offset]).hexdigest(),
            "matches_expected": runtime_bytes == expected_runtime_bytes,
            "all_zero": all(item == 0 for item in runtime_bytes),
            "classification": _classify_payload(runtime_bytes, expected_runtime_bytes),
            "copy_complete_marker_value": int.from_bytes(
                runtime_bytes[copy_complete_marker_offset : copy_complete_marker_offset + 4],
                "big",
            ),
            "copy_complete_matches_expected": int.from_bytes(
                runtime_bytes[copy_complete_marker_offset : copy_complete_marker_offset + 4],
                "big",
            )
            == runtime_metadata.copy_complete_marker_value,
            "runtime_executed_marker_value": int.from_bytes(
                runtime_bytes[runtime_executed_marker_offset : runtime_executed_marker_offset + 4],
                "big",
            ),
            "runtime_executed_matches_expected": int.from_bytes(
                runtime_bytes[runtime_executed_marker_offset : runtime_executed_marker_offset + 4],
                "big",
            )
            == runtime_metadata.runtime_executed_marker_value,
            "runtime_execution_counter_value": int.from_bytes(
                runtime_bytes[counter_offset : counter_offset + 4],
                "big",
            ),
            "runtime_status_value": int.from_bytes(runtime_bytes[status_offset : status_offset + 4], "big"),
            "runtime_status_matches_expected": int.from_bytes(runtime_bytes[status_offset : status_offset + 4], "big")
            == runtime_metadata.runtime_success_status_value,
            "bootstrap_return_marker_value": int.from_bytes(
                runtime_bytes[bootstrap_return_offset : bootstrap_return_offset + 4],
                "big",
            ),
            "bootstrap_return_matches_expected": int.from_bytes(
                runtime_bytes[bootstrap_return_offset : bootstrap_return_offset + 4],
                "big",
            )
            == runtime_metadata.bootstrap_return_marker_value,
            "runtime_poll_counter_value": int.from_bytes(
                runtime_bytes[poll_counter_offset : poll_counter_offset + 4],
                "big",
            ),
            "runtime_poll_heartbeat_value": int.from_bytes(
                runtime_bytes[poll_heartbeat_offset : poll_heartbeat_offset + 4],
                "big",
            ),
            "runtime_poll_last_sequence_value": int.from_bytes(
                runtime_bytes[poll_last_sequence_offset : poll_last_sequence_offset + 4],
                "big",
            ),
            "diagnostics": None,
            "transport": None,
            "retail_ios_wrapper": None,
            },
        )

        def _runtime_u32(address: int) -> int:
            start = address - runtime_metadata.runtime_destination_address
            return int.from_bytes(runtime_bytes[start : start + 4], "big")

        def _runtime_s32(address: int) -> int:
            start = address - runtime_metadata.runtime_destination_address
            return int.from_bytes(runtime_bytes[start : start + 4], "big", signed=True)

        if runtime_metadata.diagnostics is not None:
            diagnostics = runtime_metadata.diagnostics
            marker_value = _runtime_u32(diagnostics.last_execution_marker_address)
            relocated_runtime["diagnostics"] = {
                "ios_call_mechanism": (
                    "disabled"
                    if diagnostics.mode == "transport_disabled"
                    else "dry_run"
                    if diagnostics.mode == "dry_run"
                    else "retail_wrapper"
                ),
                "mode": diagnostics.mode,
                "hook_wrapper_entry_count": _runtime_u32(diagnostics.hook_wrapper_entry_count_address),
                "hook_wrapper_before_poll_count": _runtime_u32(diagnostics.hook_wrapper_before_poll_count_address),
                "runtime_poll_entry_count": _runtime_u32(diagnostics.runtime_poll_entry_count_address),
                "runtime_poll_exit_count": _runtime_u32(diagnostics.runtime_poll_exit_count_address),
                "state_machine_entry_count": _runtime_u32(diagnostics.state_machine_entry_count_address),
                "state_machine_exit_count": _runtime_u32(diagnostics.state_machine_exit_count_address),
                "c_before_veneer_call_count": _runtime_u32(diagnostics.c_before_veneer_call_count_address),
                "retail_veneer_entry_count": _runtime_u32(diagnostics.retail_veneer_entry_count_address),
                "retail_target_return_count": _runtime_u32(diagnostics.retail_target_return_count_address),
                "retail_veneer_exit_count": _runtime_u32(diagnostics.retail_veneer_exit_count_address),
                "c_after_veneer_call_count": _runtime_u32(diagnostics.c_after_veneer_call_count_address),
                "ios_submit_attempt_count": _runtime_u32(diagnostics.ios_submit_attempt_count_address),
                "ios_submit_return_count": _runtime_u32(diagnostics.ios_submit_return_count_address),
                "ios_submit_return_value": _runtime_s32(diagnostics.ios_submit_return_value_address),
                "callback_entry_count": _runtime_u32(diagnostics.callback_entry_count_address),
                "callback_exit_count": _runtime_u32(diagnostics.callback_exit_count_address),
                "hook_wrapper_after_poll_count": _runtime_u32(diagnostics.hook_wrapper_after_poll_count_address),
                "hook_wrapper_exit_count": _runtime_u32(diagnostics.hook_wrapper_exit_count_address),
                "last_execution_marker": marker_value,
                "last_execution_marker_name": _marker_name(marker_value),
                "last_transport_phase_before_step": _runtime_u32(diagnostics.last_transport_phase_before_step_address),
                "last_transport_phase_after_step": _runtime_u32(diagnostics.last_transport_phase_after_step_address),
                "callback_result": _runtime_s32(diagnostics.callback_result_address),
                "wrapper_counts_balanced": (
                    _runtime_u32(diagnostics.hook_wrapper_entry_count_address)
                    == _runtime_u32(diagnostics.hook_wrapper_exit_count_address)
                )
                and (
                    _runtime_u32(diagnostics.hook_wrapper_before_poll_count_address)
                    == _runtime_u32(diagnostics.hook_wrapper_after_poll_count_address)
                ),
                "poll_counts_balanced": (
                    _runtime_u32(diagnostics.runtime_poll_entry_count_address)
                    == _runtime_u32(diagnostics.runtime_poll_exit_count_address)
                ),
                "state_machine_counts_balanced": (
                    _runtime_u32(diagnostics.state_machine_entry_count_address)
                    == _runtime_u32(diagnostics.state_machine_exit_count_address)
                ),
                "ios_submission_attempted": _runtime_u32(diagnostics.ios_submit_attempt_count_address) > 0,
                "ios_submission_returned": _runtime_u32(diagnostics.ios_submit_return_count_address) > 0,
                "callback_observed": _runtime_u32(diagnostics.callback_entry_count_address) > 0,
                "counter_consistency": _diagnostic_counter_consistency(
                    hook_wrapper_entry_count=_runtime_u32(diagnostics.hook_wrapper_entry_count_address),
                    hook_wrapper_before_poll_count=_runtime_u32(diagnostics.hook_wrapper_before_poll_count_address),
                    runtime_poll_entry_count=_runtime_u32(diagnostics.runtime_poll_entry_count_address),
                    runtime_poll_exit_count=_runtime_u32(diagnostics.runtime_poll_exit_count_address),
                    state_machine_entry_count=_runtime_u32(diagnostics.state_machine_entry_count_address),
                    state_machine_exit_count=_runtime_u32(diagnostics.state_machine_exit_count_address),
                    c_before_veneer_call_count=_runtime_u32(diagnostics.c_before_veneer_call_count_address),
                    retail_veneer_entry_count=_runtime_u32(diagnostics.retail_veneer_entry_count_address),
                    retail_target_return_count=_runtime_u32(diagnostics.retail_target_return_count_address),
                    retail_veneer_exit_count=_runtime_u32(diagnostics.retail_veneer_exit_count_address),
                    c_after_veneer_call_count=_runtime_u32(diagnostics.c_after_veneer_call_count_address),
                    ios_submit_attempt_count=_runtime_u32(diagnostics.ios_submit_attempt_count_address),
                    ios_submit_return_count=_runtime_u32(diagnostics.ios_submit_return_count_address),
                    callback_entry_count=_runtime_u32(diagnostics.callback_entry_count_address),
                    callback_exit_count=_runtime_u32(diagnostics.callback_exit_count_address),
                    hook_wrapper_after_poll_count=_runtime_u32(diagnostics.hook_wrapper_after_poll_count_address),
                    hook_wrapper_exit_count=_runtime_u32(diagnostics.hook_wrapper_exit_count_address),
                ),
            }
        if runtime_metadata.retail_ios_wrapper is not None:
            wrapper = runtime_metadata.retail_ios_wrapper
            relocated_runtime["retail_ios_wrapper"] = {
                "supported_dol_sha256": wrapper.supported_dol_sha256,
                "open_async_address": wrapper.open_async_address,
                "open_address": wrapper.open_address,
                "close_async_address": wrapper.close_async_address,
                "close_address": wrapper.close_address,
                "read_async_address": wrapper.read_async_address,
                "read_sync_address": wrapper.read_sync_address,
                "write_async_address": wrapper.write_async_address,
                "write_sync_address": wrapper.write_sync_address,
                "seek_async_address": wrapper.seek_async_address,
                "seek_sync_address": wrapper.seek_sync_address,
                "confirmed_ioctl_async_address": wrapper.confirmed_ioctl_async_address,
                "confirmed_ioctl_sync_address": wrapper.confirmed_ioctl_sync_address,
                "confirmed_ioctlv_async_address": wrapper.confirmed_ioctlv_async_address,
                "confirmed_ioctlv_sync_address": wrapper.confirmed_ioctlv_sync_address,
                "open_async_guard_words": list(wrapper.open_async_guard_words),
                "callback_signature": wrapper.callback_signature,
                "preserved_registers": list(wrapper.preserved_registers),
                "submit_helper_address": wrapper.submit_helper_address,
                "request_allocator_address": wrapper.request_allocator_address,
                "evidence_source": wrapper.evidence_source,
                "confidence": wrapper.confidence,
            }
        if runtime_metadata.abi_probe is not None:
            abi_probe = runtime_metadata.abi_probe

            def read_u32_vector(address: int, size: int) -> list[int]:
                count = size // 4
                return [_runtime_u32(address + index * 4) for index in range(count)]

            result_flags = _runtime_u32(abi_probe.result_flags_address)
            supplied_args = read_u32_vector(abi_probe.supplied_args_address, abi_probe.supplied_args_size)
            pre_call_args = read_u32_vector(abi_probe.pre_call_args_address, abi_probe.pre_call_args_size)
            target_args = read_u32_vector(abi_probe.target_args_address, abi_probe.target_args_size)
            relocated_runtime["abi_probe"] = {
                "mode": abi_probe.mode,
                "supplied_args": supplied_args,
                "pre_call_args": pre_call_args,
                "target_args": target_args,
                "return_value": _runtime_s32(abi_probe.return_value_address),
                "expected_return_value": abi_probe.expected_return_value,
                "result_flags": result_flags,
                "stack_pointer_before": _runtime_u32(abi_probe.stack_pointer_before_address),
                "stack_pointer_after": _runtime_u32(abi_probe.stack_pointer_after_address),
                "saved_lr": _runtime_u32(abi_probe.saved_lr_address),
                "restored_lr": _runtime_u32(abi_probe.restored_lr_address),
                "saved_r2": _runtime_u32(abi_probe.saved_r2_address),
                "restored_r2": _runtime_u32(abi_probe.restored_r2_address),
                "saved_r13": _runtime_u32(abi_probe.saved_r13_address),
                "restored_r13": _runtime_u32(abi_probe.restored_r13_address),
                "target_ctr": _runtime_u32(abi_probe.target_ctr_address),
                "after_call_flag": _runtime_u32(abi_probe.after_call_flag_address),
                "supplied_args_match_pre_call": supplied_args == pre_call_args,
                "pre_call_args_match_target": pre_call_args == target_args,
                "return_value_matches_expected": _runtime_u32(abi_probe.return_value_address)
                == abi_probe.expected_return_value,
                "stack_pointer_restored": _runtime_u32(abi_probe.stack_pointer_before_address)
                == _runtime_u32(abi_probe.stack_pointer_after_address),
                "lr_restored": _runtime_u32(abi_probe.saved_lr_address) == _runtime_u32(abi_probe.restored_lr_address),
                "r2_restored": _runtime_u32(abi_probe.saved_r2_address) == _runtime_u32(abi_probe.restored_r2_address),
                "r13_restored": _runtime_u32(abi_probe.saved_r13_address)
                == _runtime_u32(abi_probe.restored_r13_address),
                "target_called": _runtime_u32(abi_probe.after_call_flag_address) != 0,
                "pass": result_flags & 0x003FFFFF == 0x003FFFFF,
            }
        if runtime_metadata.transport is not None:
                transport = runtime_metadata.transport

                def read_transport_u32_vector(address: int, size: int) -> list[int]:
                    count = size // 4
                    return [_runtime_u32(address + index * 4) for index in range(count)]

                def optional_u32(address: int | None) -> int | None:
                    if address is None:
                        return None
                    return _runtime_u32(address)

                def optional_s32(address: int | None) -> int | None:
                    if address is None:
                        return None
                    return _runtime_s32(address)

                def optional_u32_bits_from_s32(address: int | None) -> int | None:
                    if address is None:
                        return None
                    return _runtime_s32(address) & 0xFFFFFFFF

                phase_value = _runtime_u32(transport.phase_address)
                previous_phase = None
                previous_phase_name = None
                if runtime_metadata.diagnostics is not None:
                    previous_phase = _runtime_u32(runtime_metadata.diagnostics.last_transport_phase_before_step_address)
                    previous_phase_name = _phase_name(previous_phase)
                receive_preview_offset = (
                    transport.last_receive_preview_address - runtime_metadata.runtime_destination_address
                )
                send_preview_offset = transport.last_send_preview_address - runtime_metadata.runtime_destination_address
                nwc24_output_offset = (
                    transport.nwc24_output_buffer_address - runtime_metadata.runtime_destination_address
                )
                open_ip_path_address = optional_u32(transport.open_ip_path_pointer_address)
                open_ip_path_length = optional_u32(transport.open_ip_path_length_address)
                host_id_value = _runtime_u32(transport.host_id_address)
                host_id_bytes = [
                    (host_id_value >> 24) & 0xFF,
                    (host_id_value >> 16) & 0xFF,
                    (host_id_value >> 8) & 0xFF,
                    host_id_value & 0xFF,
                ]
                socket_request_address = optional_u32(transport.socket_request_address_address)
                socket_request_logical_size = optional_u32(transport.socket_request_logical_size_address)
                socket_request_bytes_hex = None
                if socket_request_address is not None and socket_request_logical_size is not None:
                    socket_request_bytes_hex = _read_exact(
                        backend,
                        socket_request_address,
                        socket_request_logical_size,
                        f"socket request 0x{socket_request_address:08x}",
                    ).hex()
                bind_request_address = optional_u32(transport.bind_request_address_address)
                bind_request_logical_size = optional_u32(transport.bind_request_logical_size_address)
                bind_request_bytes_hex = None
                bind_request_bytes_be = None
                if bind_request_address is not None and bind_request_logical_size is not None:
                    bind_request_bytes = _read_exact(
                        backend,
                        bind_request_address,
                        bind_request_logical_size,
                        f"bind request 0x{bind_request_address:08x}",
                    )
                    bind_request_bytes_hex = bind_request_bytes.hex()
                    bind_request_bytes_be = list(bind_request_bytes)
                cleanup_close_request_address = optional_u32(transport.cleanup_close_request_address_address)
                cleanup_close_request_logical_size = optional_u32(transport.cleanup_close_request_logical_size_address)
                cleanup_close_request_bytes_hex = None
                if cleanup_close_request_address is not None and cleanup_close_request_logical_size is not None:
                    cleanup_close_request_bytes_hex = _read_exact(
                        backend,
                        cleanup_close_request_address,
                        cleanup_close_request_logical_size,
                        f"cleanup close request 0x{cleanup_close_request_address:08x}",
                    ).hex()
                open_ip_path_bounded_string = None
                open_ip_path_bytes_hex = None
                if open_ip_path_address is not None and open_ip_path_length is not None:
                    raw_path = _read_exact(
                        backend,
                        open_ip_path_address,
                        min(open_ip_path_length + 1, 0x80),
                        f"open-ip path 0x{open_ip_path_address:08x}",
                    )
                    open_ip_path_bytes_hex = raw_path.hex()
                    open_ip_path_bounded_string = raw_path.split(b"\0", 1)[0].decode("ascii", errors="replace")
                relocated_runtime["transport"] = {
                "mode": transport.mode,
                "initialization_enabled": transport.initialization_enabled,
                "receive_enabled": transport.receive_enabled,
                "send_enabled": transport.send_enabled,
                "nwc24_startup_enabled": transport.nwc24_startup_enabled,
                "kd_close_enabled": transport.kd_close_enabled,
                "ip_close_on_success": transport.ip_close_on_success,
                "socket_close_on_success": transport.socket_close_on_success,
                "terminal_phase_value": transport.terminal_phase_value,
                "terminal_phase_name": transport.terminal_phase_name,
                "phase": phase_value,
                "phase_name": _phase_name(phase_value),
                "previous_phase": previous_phase,
                "previous_phase_name": previous_phase_name,
                "last_error": _runtime_s32(transport.last_error_address),
                "last_socket_error": _runtime_s32(transport.last_socket_error_address),
                "last_ios_result": _runtime_s32(transport.last_ios_result_address),
                "pending_operation": _runtime_u32(transport.pending_operation_address),
                "pending_operation_name": _operation_name(_runtime_u32(transport.pending_operation_address)),
                "pending_generation": _runtime_u32(transport.pending_generation_address),
                "callback_generation": _runtime_u32(transport.callback_generation_address),
                "callback_count": _runtime_u32(transport.callback_count_address),
                "rejected_callback_count": _runtime_u32(transport.rejected_callback_count_address),
                "callback_pending": _runtime_u32(transport.callback_pending_address),
                "open_kd_submit_count": _runtime_u32(transport.open_kd_submit_count_address),
                "open_kd_callback_count": _runtime_u32(transport.open_kd_callback_count_address),
                "nwc24_output_buffer_address": transport.nwc24_output_buffer_address,
                "nwc24_output_buffer_size": transport.nwc24_output_buffer_size,
                "nwc24_output_buffer_alignment": transport.nwc24_output_buffer_alignment,
                "nwc24_output_buffer_hex": runtime_bytes[
                    nwc24_output_offset : nwc24_output_offset + transport.nwc24_output_buffer_size
                ].hex(),
                "nwc24_submit_count": _runtime_u32(transport.nwc24_submit_count_address),
                "nwc24_callback_count": _runtime_u32(transport.nwc24_callback_count_address),
                "nwc24_synchronous_result": _runtime_s32(transport.nwc24_synchronous_result_address),
                "nwc24_callback_result": _runtime_s32(transport.nwc24_callback_result_address),
                "nwc24_output_digest": _runtime_u32(transport.nwc24_output_digest_address),
                "open_ip_submit_count": _runtime_u32(transport.open_ip_submit_count_address),
                "open_ip_callback_count": _runtime_u32(transport.open_ip_callback_count_address),
                "kd_close_submit_count": _runtime_u32(transport.kd_close_submit_count_address),
                "kd_close_callback_count": _runtime_u32(transport.kd_close_callback_count_address),
                "startup_submit_count": _runtime_u32(transport.startup_submit_count_address),
                "startup_callback_count": _runtime_u32(transport.startup_callback_count_address),
                "get_host_id_submit_count": _runtime_u32(transport.get_host_id_submit_count_address),
                "get_host_id_callback_count": _runtime_u32(transport.get_host_id_callback_count_address),
                "socket_submit_count": _runtime_u32(transport.socket_submit_count_address),
                "socket_callback_count": _runtime_u32(transport.socket_callback_count_address),
                "bind_submit_count": _runtime_u32(transport.bind_submit_count_address),
                "bind_callback_count": _runtime_u32(transport.bind_callback_count_address),
                "cleanup_close_callback_count": optional_u32(transport.cleanup_close_callback_count_address),
                "kd_fd": _runtime_s32(transport.kd_fd_address),
                "kd_closed": _runtime_u32(transport.kd_closed_address),
                "ip_fd": _runtime_s32(transport.ip_fd_address),
                "socket_fd": _runtime_s32(transport.socket_fd_address),
                "host_id": host_id_value,
                "host_id_bytes_be": host_id_bytes,
                "host_id_dotted_ipv4": ".".join(str(part) for part in host_id_bytes),
                "host_id_available": optional_u32(transport.host_id_available_address),
                "host_id_ready": optional_u32(transport.host_id_ready_address),
                "service_started": optional_u32(transport.service_started_address),
                "bound_port": _runtime_u32(transport.bound_port_address),
                "receive_submit_count": _runtime_u32(transport.receive_submit_count_address),
                "send_submit_count": _runtime_u32(transport.send_submit_count_address),
                "ip_close_submit_count": _runtime_u32(transport.ip_close_submit_count_address),
                "socket_close_submit_count": _runtime_u32(transport.socket_close_submit_count_address),
                "receive_count": _runtime_u32(transport.receive_count_address),
                "receive_bytes": _runtime_u32(transport.receive_bytes_address),
                "send_count": _runtime_u32(transport.send_count_address),
                "send_bytes": _runtime_u32(transport.send_bytes_address),
                "last_receive_length": _runtime_u32(transport.last_receive_length_address),
                "last_send_length": _runtime_u32(transport.last_send_length_address),
                "last_peer_ipv4": _runtime_u32(transport.last_peer_ipv4_address),
                "last_peer_port": _runtime_u32(transport.last_peer_port_address),
                "last_peer_family": _runtime_u32(transport.last_peer_family_address),
                "last_poll_action": _runtime_u32(transport.last_poll_action_address),
                "last_submit_result": _runtime_s32(transport.last_submit_result_address),
                "last_receive_preview_hex": runtime_bytes[
                    receive_preview_offset : receive_preview_offset + transport.last_receive_preview_size
                ].hex(),
                "last_send_preview_hex": runtime_bytes[
                    send_preview_offset : send_preview_offset + transport.last_send_preview_size
                ].hex(),
                "open_kd_submit_result": optional_s32(transport.open_kd_submit_result_address),
                "open_kd_callback_result": optional_s32(transport.open_kd_callback_result_address),
                "open_kd_submit_generation": optional_u32(transport.open_kd_submit_generation_address),
                "open_kd_callback_generation": optional_u32(transport.open_kd_callback_generation_address),
                "nwc24_submit_result": _runtime_s32(transport.nwc24_synchronous_result_address),
                "nwc24_submit_generation": optional_u32(transport.nwc24_submit_generation_address),
                "nwc24_callback_generation": optional_u32(transport.nwc24_callback_generation_address),
                "open_ip_submit_result": optional_s32(transport.open_ip_submit_result_address),
                "open_ip_callback_result": optional_s32(transport.open_ip_callback_result_address),
                "open_ip_submit_generation": optional_u32(transport.open_ip_submit_generation_address),
                "open_ip_callback_generation": optional_u32(transport.open_ip_callback_generation_address),
                "open_ip_path_address": open_ip_path_address,
                "open_ip_path_length": open_ip_path_length,
                "open_ip_path_bounded_string": open_ip_path_bounded_string,
                "open_ip_path_bytes_hex": open_ip_path_bytes_hex,
                "open_ip_mode": optional_u32(transport.open_ip_mode_value_address),
                "open_ip_callback_pointer": optional_u32(transport.open_ip_callback_pointer_address),
                "open_ip_context_pointer": optional_u32(transport.open_ip_context_pointer_address),
                "open_ip_callback_exit_count": optional_u32(transport.open_ip_callback_exit_count_address),
                "open_ip_stale_callback_count": optional_u32(transport.open_ip_stale_callback_count_address),
                "open_ip_duplicate_callback_count": optional_u32(
                    transport.open_ip_duplicate_callback_count_address
                ),
                "ip_fd_before_open_ip": optional_s32(transport.ip_fd_before_open_ip_address),
                "open_ip_target_address": (
                    runtime_metadata.retail_ios_wrapper.open_async_address
                    if runtime_metadata.retail_ios_wrapper is not None
                    else None
                ),
                "kd_close_submit_result": optional_s32(transport.kd_close_submit_result_address),
                "kd_close_callback_result": optional_s32(transport.kd_close_callback_result_address),
                "kd_close_submit_generation": optional_u32(transport.kd_close_submit_generation_address),
                "kd_close_callback_generation": optional_u32(transport.kd_close_callback_generation_address),
                "kd_close_submitted_fd": optional_s32(transport.kd_close_submitted_fd_address),
                "kd_fd_before_close": optional_s32(transport.kd_fd_before_close_address),
                "kd_fd_after_close": optional_s32(transport.kd_fd_after_close_address),
                "startup_submit_result": optional_s32(transport.startup_submit_result_address),
                "startup_callback_result": optional_s32(transport.startup_callback_result_address),
                "startup_submit_generation": optional_u32(transport.startup_submit_generation_address),
                "startup_callback_generation": optional_u32(transport.startup_callback_generation_address),
                "startup_target_address": optional_u32(transport.startup_target_address),
                "startup_command": optional_u32(transport.startup_command_address),
                "startup_submitted_fd": optional_s32(transport.startup_submitted_fd_address),
                "startup_callback_pointer": optional_u32(transport.startup_callback_pointer_address),
                "startup_context_pointer": optional_u32(transport.startup_context_pointer_address),
                "startup_callback_exit_count": optional_u32(transport.startup_callback_exit_count_address),
                "startup_stale_callback_count": optional_u32(transport.startup_stale_callback_count_address),
                "startup_duplicate_callback_count": optional_u32(transport.startup_duplicate_callback_count_address),
                "startup_service_started_before_submit": optional_u32(
                    transport.startup_service_started_before_submit_address
                ),
                "startup_service_started_after_completion": optional_u32(
                    transport.startup_service_started_after_completion_address
                ),
                "ip_fd_before_startup": optional_s32(transport.ip_fd_before_startup_address),
                "ip_fd_after_startup": optional_s32(transport.ip_fd_after_startup_address),
                "startup_pending_before_submit": optional_u32(transport.startup_pending_before_submit_address),
                "startup_pending_after_completion": optional_u32(transport.startup_pending_after_completion_address),
                "startup_phase_before_submit": optional_u32(transport.startup_phase_before_submit_address),
                "startup_phase_after_completion": optional_u32(transport.startup_phase_after_completion_address),
                "startup_pre_call_args": (
                    read_transport_u32_vector(
                        transport.startup_pre_call_args_address, transport.startup_pre_call_args_size
                    )
                    if (
                        transport.startup_pre_call_args_address is not None
                        and transport.startup_pre_call_args_size is not None
                    )
                    else None
                ),
                "host_id_submit_result": optional_s32(transport.get_host_id_submit_result_address),
                "host_id_callback_result": optional_s32(transport.get_host_id_callback_result_address),
                "host_id_callback_result_u32": optional_u32_bits_from_s32(
                    transport.get_host_id_callback_result_address
                ),
                "host_id_submit_generation": optional_u32(transport.get_host_id_submit_generation_address),
                "host_id_callback_generation": optional_u32(transport.get_host_id_callback_generation_address),
                "get_host_id_target_address": optional_u32(transport.get_host_id_target_address),
                "get_host_id_command": optional_u32(transport.get_host_id_command_address),
                "get_host_id_submitted_fd": optional_s32(transport.get_host_id_submitted_fd_address),
                "get_host_id_callback_pointer": optional_u32(transport.get_host_id_callback_pointer_address),
                "get_host_id_context_pointer": optional_u32(transport.get_host_id_context_pointer_address),
                "get_host_id_callback_exit_count": optional_u32(transport.get_host_id_callback_exit_count_address),
                "get_host_id_stale_callback_count": optional_u32(transport.get_host_id_stale_callback_count_address),
                "get_host_id_duplicate_callback_count": optional_u32(
                    transport.get_host_id_duplicate_callback_count_address
                ),
                "get_host_id_service_started_before_submit": optional_u32(
                    transport.get_host_id_service_started_before_submit_address
                ),
                "get_host_id_service_started_after_completion": optional_u32(
                    transport.get_host_id_service_started_after_completion_address
                ),
                "ip_fd_before_get_host_id": optional_s32(transport.ip_fd_before_get_host_id_address),
                "ip_fd_after_get_host_id": optional_s32(transport.ip_fd_after_get_host_id_address),
                "get_host_id_pending_before_submit": optional_u32(
                    transport.get_host_id_pending_before_submit_address
                ),
                "get_host_id_pending_after_completion": optional_u32(
                    transport.get_host_id_pending_after_completion_address
                ),
                "get_host_id_phase_before_submit": optional_u32(transport.get_host_id_phase_before_submit_address),
                "get_host_id_phase_after_completion": optional_u32(
                    transport.get_host_id_phase_after_completion_address
                ),
                "get_host_id_pre_call_args": (
                    read_transport_u32_vector(
                        transport.get_host_id_pre_call_args_address, transport.get_host_id_pre_call_args_size
                    )
                    if (
                        transport.get_host_id_pre_call_args_address is not None
                        and transport.get_host_id_pre_call_args_size is not None
                    )
                    else None
                ),
                "socket_submit_result": optional_s32(transport.socket_submit_result_address),
                "socket_callback_result": optional_s32(transport.socket_callback_result_address),
                "socket_callback_result_u32": optional_u32_bits_from_s32(transport.socket_callback_result_address),
                "socket_submit_generation": optional_u32(transport.socket_submit_generation_address),
                "socket_callback_generation": optional_u32(transport.socket_callback_generation_address),
                "socket_target_address": optional_u32(transport.socket_target_address),
                "socket_command": optional_u32(transport.socket_command_address),
                "socket_submitted_fd": optional_s32(transport.socket_submitted_fd_address),
                "socket_callback_pointer": optional_u32(transport.socket_callback_pointer_address),
                "socket_context_pointer": optional_u32(transport.socket_context_pointer_address),
                "socket_callback_exit_count": optional_u32(transport.socket_callback_exit_count_address),
                "socket_stale_callback_count": optional_u32(transport.socket_stale_callback_count_address),
                "socket_duplicate_callback_count": optional_u32(transport.socket_duplicate_callback_count_address),
                "socket_fd_before_submit": optional_s32(transport.socket_fd_before_submit_address),
                "socket_fd_after_completion": optional_s32(transport.socket_fd_after_completion_address),
                "socket_request_address": socket_request_address,
                "socket_request_storage_size": optional_u32(transport.socket_request_storage_size_address),
                "socket_request_logical_size": socket_request_logical_size,
                "socket_request_alignment": optional_u32(transport.socket_request_alignment_address),
                "socket_family_value": optional_u32(transport.socket_family_value_address),
                "socket_type_value": optional_u32(transport.socket_type_value_address),
                "socket_protocol_value": optional_u32(transport.socket_protocol_value_address),
                "socket_descriptor_valid": optional_u32(transport.socket_descriptor_valid_address),
                "socket_ready": optional_u32(transport.socket_ready_address),
                "socket_request_bytes_hex": socket_request_bytes_hex,
                "socket_request_bytes_address": optional_u32(transport.socket_request_bytes_address),
                "socket_request_bytes_size": transport.socket_request_bytes_size,
                "socket_pre_call_args": (
                    read_transport_u32_vector(
                        transport.socket_pre_call_args_address, transport.socket_pre_call_args_size
                    )
                    if (
                        transport.socket_pre_call_args_address is not None
                        and transport.socket_pre_call_args_size is not None
                    )
                    else None
                ),
                "bind_submit_result": optional_s32(transport.bind_submit_result_address),
                "bind_callback_result": optional_s32(transport.bind_callback_result_address),
                "bind_submit_generation": optional_u32(transport.bind_submit_generation_address),
                "bind_callback_generation": optional_u32(transport.bind_callback_generation_address),
                "bind_target_address": optional_u32(transport.bind_target_address),
                "bind_command": optional_u32(transport.bind_command_address),
                "bind_submitted_fd": optional_s32(transport.bind_submitted_fd_address),
                "bind_callback_pointer": optional_u32(transport.bind_callback_pointer_address),
                "bind_context_pointer": optional_u32(transport.bind_context_pointer_address),
                "bind_callback_exit_count": optional_u32(transport.bind_callback_exit_count_address),
                "bind_stale_callback_count": optional_u32(transport.bind_stale_callback_count_address),
                "bind_duplicate_callback_count": optional_u32(transport.bind_duplicate_callback_count_address),
                "bind_request_address": bind_request_address,
                "bind_request_storage_size": optional_u32(transport.bind_request_storage_size_address),
                "bind_request_logical_size": bind_request_logical_size,
                "bind_request_alignment": optional_u32(transport.bind_request_alignment_address),
                "bind_sockaddr_length": optional_u32(transport.bind_sockaddr_length_address),
                "bind_family_value": optional_u32(transport.bind_family_value_address),
                "bind_port_value": optional_u32(transport.bind_port_value_address),
                "bind_address_value": optional_u32(transport.bind_address_value_address),
                "bind_request_bytes_hex": bind_request_bytes_hex,
                "bind_request_bytes_be": bind_request_bytes_be,
                "bind_request_bytes_address": optional_u32(transport.bind_request_bytes_address),
                "bind_request_bytes_size": transport.bind_request_bytes_size,
                "bind_pre_call_args": (
                    read_transport_u32_vector(
                        transport.bind_pre_call_args_address,
                        transport.bind_pre_call_args_size,
                    )
                    if (
                        transport.bind_pre_call_args_address is not None
                        and transport.bind_pre_call_args_size is not None
                    )
                    else None
                ),
                "cleanup_close_submit_result": optional_s32(transport.cleanup_close_submit_result_address),
                "cleanup_close_callback_result": optional_s32(transport.cleanup_close_callback_result_address),
                "cleanup_close_submit_generation": optional_u32(
                    transport.cleanup_close_submit_generation_address
                ),
                "cleanup_close_callback_generation": optional_u32(
                    transport.cleanup_close_callback_generation_address
                ),
                "cleanup_close_target_address": optional_u32(transport.cleanup_close_target_address),
                "cleanup_close_command": optional_u32(transport.cleanup_close_command_address),
                "cleanup_close_submitted_fd": optional_s32(transport.cleanup_close_submitted_fd_address),
                "cleanup_close_callback_pointer": optional_u32(transport.cleanup_close_callback_pointer_address),
                "cleanup_close_context_pointer": optional_u32(transport.cleanup_close_context_pointer_address),
                "cleanup_close_callback_exit_count": optional_u32(
                    transport.cleanup_close_callback_exit_count_address
                ),
                "cleanup_close_stale_callback_count": optional_u32(
                    transport.cleanup_close_stale_callback_count_address
                ),
                "cleanup_close_duplicate_callback_count": optional_u32(
                    transport.cleanup_close_duplicate_callback_count_address
                ),
                "cleanup_close_request_address": cleanup_close_request_address,
                "cleanup_close_request_storage_size": optional_u32(
                    transport.cleanup_close_request_storage_size_address
                ),
                "cleanup_close_request_logical_size": cleanup_close_request_logical_size,
                "cleanup_close_request_alignment": optional_u32(transport.cleanup_close_request_alignment_address),
                "cleanup_close_request_value": optional_s32(transport.cleanup_close_request_value_address),
                "cleanup_close_request_bytes_hex": cleanup_close_request_bytes_hex,
                "cleanup_close_request_bytes_address": optional_u32(
                    transport.cleanup_close_request_bytes_address
                ),
                "cleanup_close_request_bytes_size": transport.cleanup_close_request_bytes_size,
                "cleanup_close_pre_call_args": (
                    read_transport_u32_vector(
                        transport.cleanup_close_pre_call_args_address,
                        transport.cleanup_close_pre_call_args_size,
                    )
                    if (
                        transport.cleanup_close_pre_call_args_address is not None
                        and transport.cleanup_close_pre_call_args_size is not None
                    )
                    else None
                ),
                "bound_flag": optional_u32(transport.bound_flag_address),
                "bound_address": optional_u32(transport.bound_address_address),
                "socket_closed_after_bind_failure": optional_u32(
                    transport.socket_closed_after_bind_failure_address
                ),
                "socket_leak_detected": optional_u32(transport.socket_leak_detected_address),
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
        "live_hook_word": live_hook_word,
        "payload_sha256": payload_sha256,
        "payload_matches_expected": payload_bytes == config.payload_bytes,
        "payload_all_zero": all(item == 0 for item in payload_bytes),
        "payload_classification": _classify_payload(payload_bytes, config.payload_bytes),
        "low_memory_words": low_memory_words,
        "canary": canary,
        "counter": counter,
        "bootstrap_diagnostic": bootstrap_diagnostic,
        "relocated_runtime": relocated_runtime,
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


def _marker_name(value: int) -> str:
    return DIAGNOSTIC_MARKER_NAMES.get(value, f"unknown_0x{value:08X}")


def _phase_name(value: int) -> str:
    return TRANSPORT_PHASE_NAMES.get(value, f"UNKNOWN_PHASE_0x{value:08X}")


def _operation_name(value: int) -> str:
    return TRANSPORT_OPERATION_NAMES.get(value, f"unknown_operation_{value}")


def _diagnostic_counter_consistency(**counts: int) -> str:
    if counts["hook_wrapper_before_poll_count"] > counts["hook_wrapper_entry_count"]:
        return "contradictory"
    if counts["runtime_poll_entry_count"] > counts["hook_wrapper_before_poll_count"]:
        return "contradictory"
    if counts["runtime_poll_exit_count"] > counts["runtime_poll_entry_count"]:
        return "contradictory"
    if counts["state_machine_exit_count"] > counts["state_machine_entry_count"]:
        return "contradictory"
    if counts["retail_veneer_entry_count"] > counts["c_before_veneer_call_count"]:
        return "contradictory"
    if counts["retail_target_return_count"] > counts["retail_veneer_entry_count"]:
        return "contradictory"
    if counts["retail_veneer_exit_count"] > counts["retail_target_return_count"]:
        return "contradictory"
    if counts["c_after_veneer_call_count"] > counts["retail_veneer_exit_count"]:
        return "contradictory"
    if counts["ios_submit_return_count"] > counts["ios_submit_attempt_count"]:
        return "contradictory"
    if counts["callback_exit_count"] > counts["callback_entry_count"]:
        return "contradictory"
    if counts["hook_wrapper_after_poll_count"] > counts["runtime_poll_exit_count"]:
        return "contradictory"
    if counts["hook_wrapper_exit_count"] > counts["hook_wrapper_after_poll_count"]:
        return "contradictory"
    return "consistent"


def _object_as_int(value: object) -> int:
    return cast("int", value)


def _diagnostic_stop_boundary(  # noqa: C901
    *,
    diagnostics: dict[str, object],
    transport: dict[str, object] | None,
    abi_probe: dict[str, object] | None,
    recurring_execution_continuing: bool,
) -> str:
    if diagnostics.get("counter_consistency") == "contradictory":
        return "contradictory_counters"
    if abi_probe is not None and (
        bool(abi_probe.get("target_called"))
        or bool(abi_probe.get("result_flags"))
        or bool(abi_probe.get("return_value"))
    ):
        if bool(abi_probe.get("pass")):
            return "abi_probe_passed"
        if bool(abi_probe.get("target_called")):
            return "abi_probe_failed"
        return "abi_probe_incomplete"
    if transport is not None:
        phase = _object_as_int(transport["phase"])
        if phase == 17:
            if (
                _object_as_int(transport["kd_fd"]) == -1
                and _object_as_int(transport["kd_closed"]) != 0
                and _object_as_int(transport["ip_fd"]) >= 0
                and _object_as_int(transport["socket_fd"]) >= 0
                and _object_as_int(transport["bound_port"]) == 43674
                and (
                    transport.get("bound_flag") is None or _object_as_int(transport["bound_flag"]) != 0
                )
                and (
                    transport.get("bound_address") is None or _object_as_int(transport["bound_address"]) == 0
                )
                and _object_as_int(transport["callback_pending"]) == 0
                and _object_as_int(transport["receive_submit_count"]) == 0
                and _object_as_int(transport["send_submit_count"]) == 0
                and _object_as_int(transport["ip_close_submit_count"]) == 0
                and _object_as_int(transport["socket_close_submit_count"]) == 0
                and recurring_execution_continuing
            ):
                return "bound_no_recv_stable"
            return "bound_no_recv"
        if phase == 4:
            if _object_as_int(transport["last_submit_result"]) < 0:
                return "nwc24_submission_failed"
            if _object_as_int(transport["pending_operation"]) != 0:
                return "waiting_nwc24_callback"
            return "inside_nwc24_call"
        if phase == 0xFE:
            if transport.get("mode") == "retail_wrapper_nwc24_close_open_ip_once":
                if (
                    _object_as_int(transport["open_kd_callback_count"]) == 1
                    and _object_as_int(transport["nwc24_callback_count"]) == 1
                    and _object_as_int(transport["kd_close_submit_result"]) == 0
                    and _object_as_int(transport["kd_close_callback_count"]) == 1
                    and _object_as_int(transport["kd_close_callback_result"]) == 0
                    and _object_as_int(transport["kd_close_submit_generation"])
                    == _object_as_int(transport["kd_close_callback_generation"])
                    and _object_as_int(transport["kd_fd"]) == -1
                    and _object_as_int(transport["kd_closed"]) != 0
                    and _object_as_int(transport["open_ip_submit_result"]) == 0
                    and _object_as_int(transport["open_ip_callback_count"]) == 1
                    and _object_as_int(transport["open_ip_callback_exit_count"]) == 1
                    and _object_as_int(transport["open_ip_callback_result"]) >= 0
                    and _object_as_int(transport["open_ip_submit_generation"])
                    == _object_as_int(transport["open_ip_callback_generation"])
                    and _object_as_int(transport["ip_fd_before_open_ip"]) == -1
                    and _object_as_int(transport["ip_fd"]) == _object_as_int(transport["open_ip_callback_result"])
                    and _object_as_int(transport["pending_operation"]) == 0
                    and _object_as_int(transport["startup_submit_count"]) == 0
                    and _object_as_int(transport["get_host_id_submit_count"]) == 0
                    and _object_as_int(transport["socket_submit_count"]) == 0
                    and _object_as_int(transport["bind_submit_count"]) == 0
                    and _object_as_int(transport["receive_count"]) == 0
                    and _object_as_int(transport["send_count"]) == 0
                    and recurring_execution_continuing
                ):
                    return "ip_open"
                return "open_ip_callback_failed"
            if transport.get("mode") == "retail_wrapper_nwc24_close_kd_once":
                if (
                    _object_as_int(transport["open_kd_callback_count"]) == 1
                    and _object_as_int(transport["nwc24_callback_count"]) == 1
                    and _object_as_int(transport["kd_close_submit_result"]) == 0
                    and _object_as_int(transport["kd_close_callback_count"]) == 1
                    and _object_as_int(transport["kd_close_callback_result"]) == 0
                    and _object_as_int(transport["kd_close_submit_generation"])
                    == _object_as_int(transport["kd_close_callback_generation"])
                    and _object_as_int(transport["kd_fd"]) == -1
                    and _object_as_int(transport["kd_closed"]) != 0
                    and _object_as_int(transport["pending_operation"]) == 0
                    and _object_as_int(transport["open_ip_submit_count"]) == 0
                    and _object_as_int(transport["receive_submit_count"]) == 0
                    and _object_as_int(transport["send_submit_count"]) == 0
                    and recurring_execution_continuing
                ):
                    return "kd_closed"
                return "close_kd_callback_failed"
            if (
                _object_as_int(transport["open_kd_callback_count"]) == 1
                and _object_as_int(transport["kd_fd"]) >= 0
                and _object_as_int(transport["nwc24_synchronous_result"]) == 0
                and _object_as_int(transport["nwc24_callback_count"]) == 1
                and _object_as_int(transport["nwc24_submit_generation"])
                == _object_as_int(transport["nwc24_callback_generation"])
                and _object_as_int(transport["pending_operation"]) == 0
                and _object_as_int(transport["kd_close_submit_count"]) == 0
                and _object_as_int(transport["open_ip_submit_count"]) == 0
                and _object_as_int(transport["receive_submit_count"]) == 0
                and _object_as_int(transport["send_submit_count"]) == 0
                and recurring_execution_continuing
            ):
                return "nwc24_completed"
            return "nwc24_callback_missing"
        if phase == 18:
            if transport.get("mode") == "retail_wrapper_nwc24_close_open_ip_startup_once":
                if (
                    _object_as_int(transport["open_kd_callback_count"]) == 1
                    and _object_as_int(transport["nwc24_callback_count"]) == 1
                    and _object_as_int(transport["kd_close_callback_count"]) == 1
                    and _object_as_int(transport["open_ip_callback_count"]) == 1
                    and _object_as_int(transport["startup_submit_result"]) == 0
                    and _object_as_int(transport["startup_callback_count"]) == 1
                    and _object_as_int(transport["startup_callback_exit_count"]) == 1
                    and _object_as_int(transport["startup_callback_result"]) == 0
                    and _object_as_int(transport["startup_submit_generation"])
                    == _object_as_int(transport["startup_callback_generation"])
                    and _object_as_int(transport["startup_target_address"]) == 0x80504FE0
                    and _object_as_int(transport["startup_command"]) == 31
                    and _object_as_int(transport["startup_submitted_fd"]) == _object_as_int(transport["ip_fd"])
                    and transport.get("startup_pre_call_args") == [
                        _object_as_int(transport["ip_fd"]),
                        31,
                        0,
                        0,
                        0,
                        0,
                        _object_as_int(transport["startup_callback_pointer"]),
                        _object_as_int(transport["startup_context_pointer"]),
                    ]
                    and _object_as_int(transport["startup_service_started_before_submit"]) == 0
                    and _object_as_int(transport["startup_service_started_after_completion"]) != 0
                    and _object_as_int(transport["service_started"]) != 0
                    and _object_as_int(transport["ip_fd_before_startup"]) == _object_as_int(transport["ip_fd"])
                    and _object_as_int(transport["ip_fd_after_startup"]) == _object_as_int(transport["ip_fd"])
                    and _object_as_int(transport["startup_pending_before_submit"]) == 0
                    and _object_as_int(transport["startup_pending_after_completion"]) == 0
                    and _object_as_int(transport["startup_phase_before_submit"]) == 9
                    and _object_as_int(transport["startup_phase_after_completion"]) == 10
                    and _object_as_int(transport["pending_operation"]) == 0
                    and _object_as_int(transport["get_host_id_submit_count"]) == 0
                    and _object_as_int(transport["socket_submit_count"]) == 0
                    and _object_as_int(transport["bind_submit_count"]) == 0
                    and _object_as_int(transport["receive_count"]) == 0
                    and _object_as_int(transport["send_count"]) == 0
                    and recurring_execution_continuing
                    and (
                        transport.get("kd_close_submit_result") is None
                        or _object_as_int(transport["kd_close_submit_result"]) == 0
                    )
                    and (
                        transport.get("kd_close_callback_result") is None
                        or _object_as_int(transport["kd_close_callback_result"]) == 0
                    )
                    and (
                        transport.get("kd_close_submit_generation") is None
                        or transport.get("kd_close_callback_generation") is None
                        or _object_as_int(transport["kd_close_submit_generation"])
                        == _object_as_int(transport["kd_close_callback_generation"])
                    )
                    and (
                        transport.get("open_ip_submit_result") is None
                        or _object_as_int(transport["open_ip_submit_result"]) == 0
                    )
                    and (
                        transport.get("open_ip_callback_result") is None
                        or _object_as_int(transport["open_ip_callback_result"]) >= 0
                    )
                    and (
                        transport.get("open_ip_submit_generation") is None
                        or transport.get("open_ip_callback_generation") is None
                        or _object_as_int(transport["open_ip_submit_generation"])
                        == _object_as_int(transport["open_ip_callback_generation"])
                    )
                ):
                    return "so_started"
                return "so_startup_callback_failed"
            return "startup_completed"
        if phase == 6:
            if _object_as_int(transport["pending_operation"]) != 0:
                return "waiting_kd_close_callback"
            return "inside_kd_close_call"
        if phase == 7:
            if _object_as_int(transport["kd_closed"]) != 0 and _object_as_int(transport["kd_fd"]) == -1:
                return "kd_closed"
            return "nwc24_completed"
        if phase == 8:
            if _object_as_int(transport["pending_operation"]) != 0:
                return "waiting_open_ip_callback"
            return "inside_open_ip_call"
        if phase == 9:
            if transport.get("mode") == "retail_wrapper_nwc24_close_open_ip_startup_once":
                if _object_as_int(transport["last_submit_result"]) < 0:
                    return "so_startup_submission_failed"
                if _object_as_int(transport["startup_submit_count"]) == 0:
                    return "waiting_so_startup_submission"
                return "inside_so_startup_call"
            if _object_as_int(transport["last_submit_result"]) < 0:
                return "startup_submission_failed"
            return "startup_completed"
        if phase == 10:
            if transport.get("mode") == "retail_wrapper_nwc24_close_open_ip_startup_once":
                if _object_as_int(transport["pending_operation"]) != 0:
                    return "waiting_so_startup_callback"
                return "inside_so_startup_call"
            if _object_as_int(transport["pending_operation"]) != 0:
                return "waiting_startup_callback"
            return "inside_startup_call"
        if phase == 11:
            if _object_as_int(transport["last_submit_result"]) < 0:
                return "get_host_id_submission_failed"
            if _object_as_int(transport["get_host_id_submit_count"]) == 0:
                return "waiting_get_host_id_submission"
            return "inside_get_host_id_call"
        if phase == 13:
            if transport.get("mode") in {"retail_wrapper_create_socket_once", "retail_wrapper_bind_once"}:
                if _object_as_int(transport["last_submit_result"]) != 0:
                    return "create_socket_submission_failed"
                if _object_as_int(transport["socket_submit_count"]) == 0:
                    return "waiting_create_socket_submission"
                return "inside_create_socket_call"
            return "inside_get_host_id_call"
        if phase == 12:
            if _object_as_int(transport["pending_operation"]) != 0:
                return "waiting_host_id_callback"
            return "inside_host_id_call"
        if phase == 19:
            if transport.get("mode") == "retail_wrapper_get_host_id_once":
                callback_raw_u32 = transport.get("host_id_callback_result_u32")
                if (
                    _object_as_int(transport["open_kd_callback_count"]) == 1
                    and _object_as_int(transport["nwc24_callback_count"]) == 1
                    and _object_as_int(transport["kd_close_callback_count"]) == 1
                    and _object_as_int(transport["open_ip_callback_count"]) == 1
                    and _object_as_int(transport["startup_callback_count"]) == 1
                    and _object_as_int(transport["get_host_id_submit_count"]) == 1
                    and _object_as_int(transport["get_host_id_callback_count"]) == 1
                    and _object_as_int(transport["get_host_id_callback_exit_count"]) == 1
                    and _object_as_int(transport["get_host_id_target_address"]) == 0x80504FE0
                    and _object_as_int(transport["get_host_id_command"]) == 16
                    and _object_as_int(transport["get_host_id_submitted_fd"]) == _object_as_int(transport["ip_fd"])
                    and transport.get("get_host_id_pre_call_args") == [
                        _object_as_int(transport["ip_fd"]),
                        16,
                        0,
                        0,
                        0,
                        0,
                        _object_as_int(transport["get_host_id_callback_pointer"]),
                        _object_as_int(transport["get_host_id_context_pointer"]),
                    ]
                    and _object_as_int(transport["host_id_submit_result"]) == 0
                    and _object_as_int(transport["host_id_submit_generation"])
                    == _object_as_int(transport["host_id_callback_generation"])
                    and callback_raw_u32 is not None
                    and _object_as_int(callback_raw_u32) != 0
                    and _object_as_int(transport["host_id"]) == _object_as_int(callback_raw_u32)
                    and _object_as_int(transport["host_id_available"]) != 0
                    and _object_as_int(transport["host_id_ready"]) != 0
                    and _object_as_int(transport["kd_fd"]) == -1
                    and _object_as_int(transport["kd_closed"]) != 0
                    and _object_as_int(transport["ip_fd"]) >= 0
                    and _object_as_int(transport["service_started"]) != 0
                    and _object_as_int(transport["pending_operation"]) == 0
                    and _object_as_int(transport["socket_submit_count"]) == 0
                    and _object_as_int(transport["bind_submit_count"]) == 0
                    and _object_as_int(transport["receive_count"]) == 0
                    and _object_as_int(transport["send_count"]) == 0
                    and recurring_execution_continuing
                ):
                    return "host_id_ready"
            return "inside_host_id_call"
        if phase == 14:
            if transport.get("mode") in {"retail_wrapper_create_socket_once", "retail_wrapper_bind_once"}:
                if _object_as_int(transport["pending_operation"]) != 0:
                    return "waiting_create_socket_callback"
                return "inside_create_socket_call"
            if _object_as_int(transport["pending_operation"]) != 0:
                return "waiting_socket_callback"
            return "inside_socket_call"
        if phase == 20:
            if transport.get("mode") in {"retail_wrapper_create_socket_once", "retail_wrapper_bind_once"}:
                if (
                    _object_as_int(transport["open_kd_callback_count"]) == 1
                    and _object_as_int(transport["nwc24_callback_count"]) == 1
                    and _object_as_int(transport["kd_close_callback_count"]) == 1
                    and _object_as_int(transport["open_ip_callback_count"]) == 1
                    and _object_as_int(transport["startup_callback_count"]) == 1
                    and _object_as_int(transport["get_host_id_callback_count"]) == 1
                    and _object_as_int(transport["socket_submit_count"]) == 1
                    and _object_as_int(transport["socket_callback_count"]) == 1
                    and _object_as_int(transport["socket_callback_exit_count"]) == 1
                    and _object_as_int(transport["socket_target_address"]) == 0x80504FE0
                    and _object_as_int(transport["socket_command"]) == 15
                    and _object_as_int(transport["socket_submitted_fd"]) == _object_as_int(transport["ip_fd"])
                    and transport.get("socket_pre_call_args") == [
                        _object_as_int(transport["ip_fd"]),
                        15,
                        _object_as_int(transport["socket_request_address"]),
                        12,
                        0,
                        0,
                        _object_as_int(transport["socket_callback_pointer"]),
                        _object_as_int(transport["socket_context_pointer"]),
                    ]
                    and _object_as_int(transport["socket_submit_result"]) == 0
                    and _object_as_int(transport["socket_submit_generation"])
                    == _object_as_int(transport["socket_callback_generation"])
                    and _object_as_int(transport["socket_request_logical_size"]) == 12
                    and _object_as_int(transport["socket_request_alignment"]) == 0x20
                    and _object_as_int(transport["socket_family_value"]) == 2
                    and _object_as_int(transport["socket_type_value"]) == 2
                    and _object_as_int(transport["socket_protocol_value"]) == 0
                    and transport.get("socket_request_bytes_hex") == "000000020000000200000000"
                    and _object_as_int(transport["socket_callback_result"]) >= 0
                    and _object_as_int(transport["socket_fd"]) == _object_as_int(transport["socket_callback_result"])
                    and _object_as_int(transport["socket_descriptor_valid"]) != 0
                    and _object_as_int(transport["socket_ready"]) != 0
                    and _object_as_int(transport["pending_operation"]) == 0
                    and _object_as_int(transport["kd_fd"]) == -1
                    and _object_as_int(transport["kd_closed"]) != 0
                    and _object_as_int(transport["service_started"]) != 0
                    and _object_as_int(transport["host_id_ready"]) != 0
                    and _object_as_int(transport["bind_submit_count"]) == 0
                    and _object_as_int(transport["receive_count"]) == 0
                    and _object_as_int(transport["send_count"]) == 0
                    and recurring_execution_continuing
                ):
                    return "socket_ready"
                return "create_socket_callback_failed"
            return "inside_socket_call"
        if phase == 15:
            if _object_as_int(transport["last_submit_result"]) != 0:
                return "bind_submission_failed_cleanup_pending"
            if _object_as_int(transport["bind_submit_count"]) == 0:
                return "waiting_bind_submission"
            return "inside_bind_call"
        if phase == 16:
            if _object_as_int(transport["pending_operation"]) != 0:
                return "waiting_bind_callback"
            return "inside_bind_call"
        if phase == 21:
            callback_result = transport.get("bind_callback_result")
            if callback_result is not None and _object_as_int(callback_result) != 0:
                return "bind_callback_failed_cleanup_pending"
            return "waiting_bind_failure_close_submission"
        if phase == 22:
            if _object_as_int(transport["pending_operation"]) != 0:
                return "waiting_bind_failure_close_callback"
            return "inside_bind_failure_close_call"
        if phase == 23:
            return "bind_failed_cleaned"
        if phase == 24:
            return "failed_socket_leak"
        if phase == 0xFF:
            if transport.get("mode") == "retail_wrapper_create_socket_once":
                if _object_as_int(transport["socket_submit_count"]) == 1:
                    if _object_as_int(transport["socket_submit_result"]) != 0:
                        return "create_socket_submission_failed"
                    if _object_as_int(transport["socket_callback_count"]) == 1:
                        return "create_socket_callback_failed"
            if (
                transport.get("mode") == "retail_wrapper_get_host_id_once"
                and _object_as_int(transport["get_host_id_submit_count"]) == 1
                and _object_as_int(transport["get_host_id_callback_count"]) == 1
                and _object_as_int(transport["pending_operation"]) == 0
                and _object_as_int(transport["host_id"]) == 0
            ):
                return "get_host_id_unavailable"
            return "failed_with_result"
    if recurring_execution_continuing:
        return "recurring_execution_continues"
    if _object_as_int(diagnostics["c_before_veneer_call_count"]) > _object_as_int(
        diagnostics["retail_veneer_entry_count"]
    ):
        return "before_veneer"
    if _object_as_int(diagnostics["retail_veneer_entry_count"]) > _object_as_int(
        diagnostics["retail_target_return_count"]
    ):
        marker_name = str(diagnostics["last_execution_marker_name"])
        if marker_name == "retail_veneer_entered":
            return "inside_veneer_before_target"
        return "inside_retail_target"
    if _object_as_int(diagnostics["retail_target_return_count"]) > _object_as_int(
        diagnostics["retail_veneer_exit_count"]
    ):
        return "target_returned_veneer_stuck"
    if _object_as_int(diagnostics["retail_veneer_exit_count"]) > _object_as_int(
        diagnostics["c_after_veneer_call_count"]
    ):
        return "veneer_returned_c_stuck"
    if _object_as_int(diagnostics["callback_entry_count"]) > _object_as_int(diagnostics["callback_exit_count"]):
        return "inside_callback"
    if _object_as_int(diagnostics["runtime_poll_entry_count"]) > _object_as_int(diagnostics["runtime_poll_exit_count"]):
        if _object_as_int(diagnostics["state_machine_entry_count"]) > _object_as_int(
            diagnostics["state_machine_exit_count"]
        ):
            return "inside_state_machine"
        return "inside_runtime_poll"
    if _object_as_int(diagnostics["hook_wrapper_entry_count"]) > _object_as_int(diagnostics["hook_wrapper_exit_count"]):
        return "inside_hook_wrapper"
    if (
        transport is not None
        and _object_as_int(diagnostics["ios_submit_return_count"]) > 0
        and _object_as_int(transport["pending_operation"]) != 0
    ):
        if _object_as_int(diagnostics["callback_entry_count"]) == 0:
            return "callback_pending"
    marker_name = str(diagnostics["last_execution_marker_name"])
    if marker_name == "c_before_veneer_call":
        return "before_veneer"
    if marker_name == "retail_veneer_entered":
        return "inside_veneer_before_target"
    if marker_name == "retail_before_target":
        return "inside_retail_target"
    if marker_name == "retail_target_returned":
        return "target_returned_veneer_stuck"
    if marker_name == "retail_before_lr_restore":
        return "target_returned_veneer_stuck"
    if marker_name == "retail_before_veneer_blr":
        return "veneer_returned_c_stuck"
    if marker_name == "c_after_veneer_call":
        if transport is not None and _object_as_int(transport["pending_operation"]) != 0:
            return "callback_pending"
        return marker_name
    if marker_name == "poll_returning":
        return "poll_returned_before_wrapper_exit"
    if marker_name == "wrapper_restoring_state":
        return "wrapper_restoring_state"
    if marker_name == "wrapper_returning_to_game":
        return "wrapper_returned_to_game"
    return marker_name


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
    if (
        args.checkpoint_name is None
        and args.halt_address is None
        and args.expected_halt_word is None
        and not args.startup_word
    ):
        checkpoint_name = None
    else:
        if args.checkpoint_name is None or not args.checkpoint_name.strip():
            raise ProbeObservationError("Checkpoint observation requires a non-empty --checkpoint-name.")
        if (args.halt_address is None) != (args.expected_halt_word is None):
            raise ProbeObservationError(
                "Checkpoint halt observation requires both --halt-address and --expected-halt-word."
            )
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
        hook_address=args.hook_address,
        expected_hook_word=args.expected_hook_word,
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
