from __future__ import annotations

import dataclasses

import pytest

import host.udp_cp3w_game_identity_test as game_identity_test
from host.udp_cp3w_game_identity_test import (
    build_capability_omission_scenarios,
    build_primary_scenarios,
    validate_identity_response,
)
from randovania.game_connection.executor.prime3_wii_protocol import (
    GAME_IDENTITY_PAYLOAD_SIZE,
    GameIdentityPayload,
    InvalidPayloadLengthError,
    Prime3WiiAvailability,
    Prime3WiiCommand,
    Prime3WiiGameId,
    Prime3WiiPlatformId,
    Prime3WiiRegionId,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    Prime3WiiRevisionId,
    UnsupportedIdentitySchemaError,
    encode_game_identity_payload,
)


def _response(identity: GameIdentityPayload, *, request_id: int = 4) -> Prime3WiiResponse:
    return Prime3WiiResponse(
        Prime3WiiCommand.GET_GAME_IDENTITY,
        request_id,
        Prime3WiiResponseStatus.OK,
        encode_game_identity_payload(identity),
    )


def test_primary_sequence_is_exactly_twelve_datagrams() -> None:
    scenarios = build_primary_scenarios()
    assert len(scenarios) == 12
    assert [item.name for item in scenarios] == [
        "pre_hello_identity",
        "unsupported_version_hello",
        "valid_hello",
        "first_identity",
        "second_identity",
        "ping_regression",
        "invalid_identity_payload",
        "unsupported_command",
        "invalid_magic",
        "bad_crc",
        "binary_ping",
        "final_identity",
    ]
    assert scenarios[-1].request_id == 12
    assert scenarios[-1].expected == "identity"


def test_capability_omission_sequence_is_separate() -> None:
    scenarios = build_capability_omission_scenarios()
    assert [item.expected for item in scenarios] == ["hello_without_identity", "capability_not_negotiated"]


def test_only_capability_omission_skips_primary_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run_sequence(**kwargs: object) -> dict[str, object]:
        scenarios = kwargs["scenarios"]
        assert isinstance(scenarios, list)
        calls.append([scenario.name for scenario in scenarios])
        return {"scenario_order": calls[-1]}

    monkeypatch.setattr(game_identity_test, "_run_sequence", fake_run_sequence)

    report = game_identity_test.run_validation(
        host="127.0.0.1",
        port=42042,
        timeout_seconds=0.1,
        only_capability_omission=True,
    )

    assert list(report) == ["capability_omission"]
    assert calls == [["baseline_hello", "identity_without_capability"]]


def test_validate_identity_response_decodes_all_fields_and_availability() -> None:
    identity = GameIdentityPayload(
        availability_flags=(
            Prime3WiiAvailability.EXECUTABLE_RECOGNIZED | Prime3WiiAvailability.INVENTORY_ROOT_AVAILABLE
        )
    )
    assert validate_identity_response(_response(identity), request_id=4) == identity


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("game_id", Prime3WiiGameId(1)),
        ("platform_id", Prime3WiiPlatformId(1)),
        ("region_id", Prime3WiiRegionId(1)),
        ("revision_id", Prime3WiiRevisionId(1)),
    ],
)
def test_identity_known_enums_remain_accepted(field: str, value: object) -> None:
    identity = dataclasses.replace(GameIdentityPayload(), **{field: value})
    validate_identity_response(_response(identity), request_id=4)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("profile_id", 0),
        ("profile_fingerprint", 0),
        ("runtime_build_id", 0),
        ("protocol_version", 2),
        ("runtime_mode", 19),
    ],
)
def test_validate_identity_response_rejects_static_mismatch(field: str, value: int) -> None:
    with pytest.raises(RuntimeError, match=field):
        validate_identity_response(
            _response(dataclasses.replace(GameIdentityPayload(), **{field: value})), request_id=4
        )


def test_validate_identity_response_rejects_wrong_command_status_request_and_length() -> None:
    payload = encode_game_identity_payload(GameIdentityPayload())
    with pytest.raises(RuntimeError, match="command"):
        validate_identity_response(
            Prime3WiiResponse(Prime3WiiCommand.PING, 4, Prime3WiiResponseStatus.OK, payload),
            request_id=4,
        )
    with pytest.raises(RuntimeError, match="status"):
        validate_identity_response(
            Prime3WiiResponse(Prime3WiiCommand.GET_GAME_IDENTITY, 4, Prime3WiiResponseStatus.ERROR, payload),
            request_id=4,
        )
    with pytest.raises(RuntimeError, match="request ID"):
        validate_identity_response(_response(GameIdentityPayload(), request_id=5), request_id=4)
    with pytest.raises(RuntimeError, match="payload length"):
        validate_identity_response(
            Prime3WiiResponse(
                Prime3WiiCommand.GET_GAME_IDENTITY,
                4,
                Prime3WiiResponseStatus.OK,
                b"\0" * (GAME_IDENTITY_PAYLOAD_SIZE - 1),
            ),
            request_id=4,
        )


def test_validate_identity_response_rejects_schema_and_reserved() -> None:
    payload = bytearray(encode_game_identity_payload(GameIdentityPayload()))
    payload[0] = 2
    with pytest.raises(UnsupportedIdentitySchemaError):
        validate_identity_response(
            Prime3WiiResponse(
                Prime3WiiCommand.GET_GAME_IDENTITY,
                4,
                Prime3WiiResponseStatus.OK,
                bytes(payload),
            ),
            request_id=4,
        )
    payload[0] = 1
    payload[-1] = 1
    with pytest.raises(InvalidPayloadLengthError, match="reserved"):
        validate_identity_response(
            Prime3WiiResponse(
                Prime3WiiCommand.GET_GAME_IDENTITY,
                4,
                Prime3WiiResponseStatus.OK,
                bytes(payload),
            ),
            request_id=4,
        )


def test_unknown_availability_bits_are_preserved() -> None:
    identity = GameIdentityPayload(availability_flags=Prime3WiiAvailability(1 << 31))
    assert int(validate_identity_response(_response(identity), request_id=4).availability_flags) == 1 << 31
