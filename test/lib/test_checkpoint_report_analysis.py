from __future__ import annotations

from randovania.lib.checkpoint_report_analysis import analyze_checkpoint_reports


def _report(
    checkpoint_name: str,
    *,
    halt_active: bool = True,
    payload_matches_expected: bool = True,
    repeated_read_stable: bool = True,
    low_34: int = 0,
    low_3110: int = 0,
) -> dict[str, object]:
    return {
        "checkpoint_name": checkpoint_name,
        "halt_active": halt_active,
        "payload_matches_expected": payload_matches_expected,
        "repeated_read_stable": repeated_read_stable,
        "low_memory_words": {
            "0x80000034": low_34,
            "0x80003110": low_3110,
        },
    }


def test_payload_remains_intact_throughout() -> None:
    analysis = analyze_checkpoint_reports((_report("a"), _report("b"), _report("c")))

    assert analysis.last_report_with_exact_payload_match == "c"
    assert analysis.first_report_without_exact_payload_match is None
    assert analysis.contradictory_checkpoints == ()


def test_payload_transition_is_bounded_once() -> None:
    analysis = analyze_checkpoint_reports(
        (
            _report("entry"),
            _report("before-clear"),
            _report("after-clear", payload_matches_expected=False),
            _report("later", payload_matches_expected=False),
        )
    )

    assert analysis.last_report_with_exact_payload_match == "before-clear"
    assert analysis.first_report_without_exact_payload_match == "after-clear"


def test_payload_return_is_flagged_as_contradictory() -> None:
    analysis = analyze_checkpoint_reports(
        (
            _report("entry"),
            _report("cleared", payload_matches_expected=False),
            _report("unexpected-return", payload_matches_expected=True),
        )
    )

    assert analysis.first_report_without_exact_payload_match == "cleared"
    assert analysis.contradictory_checkpoints == ("unexpected-return",)


def test_low_memory_words_can_transition_together() -> None:
    analysis = analyze_checkpoint_reports(
        (
            _report("a", low_34=1, low_3110=1),
            _report("b", low_34=1, low_3110=1),
            _report("c", low_34=2, low_3110=2),
        )
    )

    assert analysis.last_report_before_80000034_changes == "b"
    assert analysis.first_report_after_80000034_changes == "c"
    assert analysis.last_report_before_80003110_changes == "b"
    assert analysis.first_report_after_80003110_changes == "c"
    assert analysis.both_low_memory_words_transition_together is True


def test_low_memory_words_can_transition_separately() -> None:
    analysis = analyze_checkpoint_reports(
        (
            _report("a", low_34=1, low_3110=1),
            _report("b", low_34=2, low_3110=1),
            _report("c", low_34=2, low_3110=3),
        )
    )

    assert analysis.first_report_after_80000034_changes == "b"
    assert analysis.first_report_after_80003110_changes == "c"
    assert analysis.both_low_memory_words_transition_together is False


def test_no_low_memory_transition_is_reported() -> None:
    analysis = analyze_checkpoint_reports((_report("a", low_34=5, low_3110=7), _report("b", low_34=5, low_3110=7)))

    assert analysis.first_report_after_80000034_changes is None
    assert analysis.first_report_after_80003110_changes is None
    assert analysis.both_low_memory_words_transition_together is None


def test_unstable_reads_are_flagged() -> None:
    analysis = analyze_checkpoint_reports((_report("a"), _report("b", repeated_read_stable=False)))

    assert analysis.unstable_checkpoints == ("b",)


def test_unreachable_checkpoint_is_reported() -> None:
    analysis = analyze_checkpoint_reports((_report("a"), _report("branch-not-taken", halt_active=False), _report("c")))

    assert analysis.unreachable_checkpoints == ("branch-not-taken",)
    assert analysis.last_report_with_exact_payload_match == "c"


def test_contradictory_low_memory_ordering_is_flagged() -> None:
    analysis = analyze_checkpoint_reports(
        (
            _report("a", low_34=1),
            _report("b", low_34=2),
            _report("c", low_34=3),
        )
    )

    assert analysis.contradictory_checkpoints == ("c",)


def test_payload_transition_interval_can_coincide_with_low_memory_transition() -> None:
    analysis = analyze_checkpoint_reports(
        (
            _report("a", low_34=1),
            _report("b", low_34=1),
            _report("c", payload_matches_expected=False, low_34=2),
        )
    )

    assert analysis.payload_transition_interval.last_checkpoint_name == "b"
    assert analysis.payload_transition_interval.first_checkpoint_name == "c"
    assert analysis.payload_transition_coincides_with_low_memory_transition is True
