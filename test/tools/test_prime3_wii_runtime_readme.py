from __future__ import annotations

from pathlib import Path


def test_prime3_wii_runtime_readme_mentions_cp3w_validation_workflow() -> None:
    readme = (
        Path(__file__)
        .resolve()
        .parents[2]
        .joinpath("tools", "prime3_wii_runtime", "README.md")
        .read_text(encoding="utf-8")
    )

    required_snippets = (
        "--ios-cp3w-frame-validation",
        "--ios-cp3w-frame-validation-count 6",
        "--ios-cp3w-ping-pong",
        "--ios-cp3w-ping-pong-count 8",
        "--ios-cp3w-hello-session",
        "--ios-cp3w-hello-session-count 10",
        "--ios-cp3w-game-identity",
        "--ios-cp3w-game-identity-count 12",
        "CP3W_FRAME_LOOP_COMPLETE",
        "CP3W_PING_PONG_LOOP_COMPLETE",
        "CP3W_HELLO_SESSION_LOOP_COMPLETE",
        "CP3W_GAME_IDENTITY_LOOP_COMPLETE",
        "GET_GAME_IDENTITY",
        "`GAME_IDENTITY` capability",
        "0x67B00CE6",
        "host/udp_cp3w_game_identity_test.py",
        "Inventory snapshots, location state/deltas, writes, item grants",
        "P3_FRAME_TEST_20260717",
        "P3_FRAME_ACK_20260717",
        "Negotiation required before PING.",
        "Unsupported protocol version range.",
        "Session is already negotiated.",
        "Prime3 Wii Runtime",
        "0x50335731",
        "host/udp_cp3w_hello_session_test.py",
        "Deterministic session-ID derivation",
        "screenshots are intentionally skipped",
        "Physical Wii behavior is not validated",
        "host/udp_cp3w_ping_pong_test.py",
        "0xEDB88320",
        "host/udp_cp3w_frame_test.py",
        "GET_INVENTORY",
        "No location state, item grants, writes",
    )

    for snippet in required_snippets:
        assert snippet in readme
