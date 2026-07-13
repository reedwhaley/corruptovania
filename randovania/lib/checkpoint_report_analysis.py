from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence


@dataclasses.dataclass(frozen=True)
class CheckpointReport:
    checkpoint_name: str
    halt_active: bool
    payload_matches_expected: bool
    repeated_read_stable: bool
    low_memory_word_80000034: int
    low_memory_word_80003110: int

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> CheckpointReport:
        low_memory_words = _mapping(data, "low_memory_words")
        return cls(
            checkpoint_name=_string(data, "checkpoint_name"),
            halt_active=_bool(data, "halt_active"),
            payload_matches_expected=_bool(data, "payload_matches_expected"),
            repeated_read_stable=_bool(data, "repeated_read_stable"),
            low_memory_word_80000034=_int(low_memory_words, "0x80000034"),
            low_memory_word_80003110=_int(low_memory_words, "0x80003110"),
        )


@dataclasses.dataclass(frozen=True)
class CheckpointInterval:
    label: str
    last_checkpoint_name: str | None
    first_checkpoint_name: str | None


@dataclasses.dataclass(frozen=True)
class CheckpointTransitionAnalysis:
    payload_transition_interval: CheckpointInterval
    low_memory_80000034_transition_interval: CheckpointInterval
    low_memory_80003110_transition_interval: CheckpointInterval
    both_low_memory_words_transition_together: bool | None
    payload_transition_coincides_with_low_memory_transition: bool
    unstable_checkpoints: tuple[str, ...]
    unreachable_checkpoints: tuple[str, ...]
    contradictory_checkpoints: tuple[str, ...]

    @property
    def last_report_with_exact_payload_match(self) -> str | None:
        return self.payload_transition_interval.last_checkpoint_name

    @property
    def first_report_without_exact_payload_match(self) -> str | None:
        return self.payload_transition_interval.first_checkpoint_name

    @property
    def last_report_before_80000034_changes(self) -> str | None:
        return self.low_memory_80000034_transition_interval.last_checkpoint_name

    @property
    def first_report_after_80000034_changes(self) -> str | None:
        return self.low_memory_80000034_transition_interval.first_checkpoint_name

    @property
    def last_report_before_80003110_changes(self) -> str | None:
        return self.low_memory_80003110_transition_interval.last_checkpoint_name

    @property
    def first_report_after_80003110_changes(self) -> str | None:
        return self.low_memory_80003110_transition_interval.first_checkpoint_name


def analyze_checkpoint_reports(reports: Sequence[Mapping[str, object]]) -> CheckpointTransitionAnalysis:
    parsed_reports = tuple(CheckpointReport.from_mapping(report) for report in reports)
    unstable_checkpoints = tuple(report.checkpoint_name for report in parsed_reports if not report.repeated_read_stable)
    unreachable_checkpoints = tuple(report.checkpoint_name for report in parsed_reports if not report.halt_active)
    reachable_reports = tuple(report for report in parsed_reports if report.halt_active and report.repeated_read_stable)

    contradictions: list[str] = []
    payload_interval = _transition_interval(
        "payload_exact_match",
        reachable_reports,
        selector=lambda report: report.payload_matches_expected,
        contradictory_checkpoints=contradictions,
    )
    low_34_interval = _transition_interval(
        "0x80000034",
        reachable_reports,
        selector=lambda report: report.low_memory_word_80000034,
        contradictory_checkpoints=contradictions,
    )
    low_3110_interval = _transition_interval(
        "0x80003110",
        reachable_reports,
        selector=lambda report: report.low_memory_word_80003110,
        contradictory_checkpoints=contradictions,
    )

    both_low_memory_words_transition_together = None
    if low_34_interval.first_checkpoint_name is not None or low_3110_interval.first_checkpoint_name is not None:
        both_low_memory_words_transition_together = (
            low_34_interval.last_checkpoint_name == low_3110_interval.last_checkpoint_name
            and low_34_interval.first_checkpoint_name == low_3110_interval.first_checkpoint_name
        )

    payload_transition_coincides_with_low_memory_transition = False
    if payload_interval.first_checkpoint_name is not None:
        payload_transition_coincides_with_low_memory_transition = any(
            payload_interval.last_checkpoint_name == interval.last_checkpoint_name
            and payload_interval.first_checkpoint_name == interval.first_checkpoint_name
            for interval in (low_34_interval, low_3110_interval)
        )

    return CheckpointTransitionAnalysis(
        payload_transition_interval=payload_interval,
        low_memory_80000034_transition_interval=low_34_interval,
        low_memory_80003110_transition_interval=low_3110_interval,
        both_low_memory_words_transition_together=both_low_memory_words_transition_together,
        payload_transition_coincides_with_low_memory_transition=payload_transition_coincides_with_low_memory_transition,
        unstable_checkpoints=unstable_checkpoints,
        unreachable_checkpoints=unreachable_checkpoints,
        contradictory_checkpoints=tuple(dict.fromkeys(contradictions)),
    )


def _transition_interval(
    label: str,
    reports: Sequence[CheckpointReport],
    *,
    selector: Callable[[CheckpointReport], object],
    contradictory_checkpoints: list[str],
) -> CheckpointInterval:
    if not reports:
        return CheckpointInterval(label=label, last_checkpoint_name=None, first_checkpoint_name=None)

    baseline = selector(reports[0])
    last_baseline = reports[0].checkpoint_name
    first_changed: str | None = None
    changed_value: Any | None = None

    for report in reports[1:]:
        value = selector(report)
        if first_changed is None:
            if value == baseline:
                last_baseline = report.checkpoint_name
            else:
                first_changed = report.checkpoint_name
                changed_value = value
        else:
            if value == baseline or value != changed_value:
                contradictory_checkpoints.append(report.checkpoint_name)

    return CheckpointInterval(
        label=label,
        last_checkpoint_name=last_baseline,
        first_checkpoint_name=first_changed,
    )


def _mapping(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = data[key]
    if not isinstance(value, dict):
        raise TypeError(f"Checkpoint report field {key!r} must be a mapping.")
    return value


def _string(data: Mapping[str, object], key: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise TypeError(f"Checkpoint report field {key!r} must be a string.")
    return value


def _bool(data: Mapping[str, object], key: str) -> bool:
    value = data[key]
    if not isinstance(value, bool):
        raise TypeError(f"Checkpoint report field {key!r} must be a boolean.")
    return value


def _int(data: Mapping[str, object], key: str) -> int:
    value = data[key]
    if not isinstance(value, int):
        raise TypeError(f"Checkpoint report field {key!r} must be an integer.")
    return value
