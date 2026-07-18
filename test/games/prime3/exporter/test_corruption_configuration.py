from __future__ import annotations

import dataclasses
import uuid

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.preset import Preset
from randovania.layout.preset_migration import convert_to_current_version


@pytest.fixture
def default_corruption_preset():
    return PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_PRIME_CORRUPTION).get_preset()


def test_corruption_configuration_default_networking_flag(default_corruption_preset) -> None:
    assert default_corruption_preset.configuration.enable_prime3_wii_networking is True


def test_corruption_configuration_json_round_trip(default_corruption_preset) -> None:
    configuration = dataclasses.replace(default_corruption_preset.configuration, enable_prime3_wii_networking=True)

    round_trip = configuration.from_json(configuration.as_json, game=RandovaniaGame.METROID_PRIME_CORRUPTION)

    assert round_trip.enable_prime3_wii_networking is True


def test_corruption_configuration_old_json_defaults_true(default_corruption_preset) -> None:
    data = default_corruption_preset.configuration.as_json
    data.pop("enable_prime3_wii_networking", None)

    round_trip = default_corruption_preset.configuration.from_json(data, game=RandovaniaGame.METROID_PRIME_CORRUPTION)

    assert round_trip.enable_prime3_wii_networking is True


def test_corruption_configuration_preset_migration_defaults_true() -> None:
    preset = {
        "schema_version": 99,
        "game": "prime3",
        "configuration": {"MP3Update": False, "disable_deflicker": False},
    }

    migrated = convert_to_current_version(preset, RandovaniaGame.METROID_PRIME_CORRUPTION)

    assert migrated["configuration"]["enable_prime3_wii_networking"] is True


def test_corruption_configuration_permalink_round_trip(
    default_corruption_preset,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("randovania.layout.generator_parameters.game_db_hash", lambda _game: 120)
    random_uuid = uuid.uuid4()
    monkeypatch.setattr("uuid.uuid4", lambda: random_uuid)
    preset = Preset(
        name=f"{default_corruption_preset.game.long_name} Custom",
        description="A customized preset.",
        uuid=random_uuid,
        game=default_corruption_preset.game,
        configuration=dataclasses.replace(default_corruption_preset.configuration, enable_prime3_wii_networking=True),
    )

    params = GeneratorParameters(seed_number=1000, spoiler=True, presets=[preset])

    after = GeneratorParameters.from_bytes(params.as_bytes)

    assert after.presets[0].configuration.enable_prime3_wii_networking is True


def test_corruption_configuration_non_prime3_games_unchanged(default_echoes_preset) -> None:
    assert not hasattr(default_echoes_preset.configuration, "enable_prime3_wii_networking")


def test_corruption_configuration_fork_preserves_flag(default_corruption_preset) -> None:
    preset = dataclasses.replace(
        default_corruption_preset,
        configuration=dataclasses.replace(default_corruption_preset.configuration, enable_prime3_wii_networking=True),
    )

    forked = preset.fork()

    assert forked.configuration.enable_prime3_wii_networking is True
