from __future__ import annotations

from pathlib import Path


def test_prime3_wii_runtime_readme_mentions_cp3w_validation_workflow() -> None:
    readme = Path(__file__).resolve().parents[2].joinpath("tools", "prime3_wii_runtime", "README.md").read_text(
        encoding="utf-8"
    )

    required_snippets = (
        "--ios-cp3w-frame-validation",
        "--ios-cp3w-frame-validation-count 6",
        "--ios-cp3w-ping-pong",
        "--ios-cp3w-ping-pong-count 8",
        "CP3W_FRAME_LOOP_COMPLETE",
        "CP3W_PING_PONG_LOOP_COMPLETE",
        "P3_FRAME_TEST_20260717",
        "P3_FRAME_ACK_20260717",
        "host/udp_cp3w_ping_pong_test.py",
        "0xEDB88320",
        "host/udp_cp3w_frame_test.py",
        "E:\\Temp\\p3-ios-*",
        "C:\\Temp",
    )

    for snippet in required_snippets:
        assert snippet in readme
