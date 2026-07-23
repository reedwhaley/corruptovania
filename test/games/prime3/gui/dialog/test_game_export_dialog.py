from __future__ import annotations

from pathlib import Path

from randovania.games.prime3.exporter.hardware_runtime import HARDWARE_RUNTIME_MODES, Prime3HardwareRuntimeMode
from randovania.games.prime3.gui.dialog.game_export_dialog import RUNTIME_MODE_CHOICES


def test_hardware_runtime_mode_choices_are_complete_and_production_first() -> None:
    assert tuple(mode for _label, mode in RUNTIME_MODE_CHOICES) == HARDWARE_RUNTIME_MODES
    assert RUNTIME_MODE_CHOICES[0] == ("Production CP3W service", Prime3HardwareRuntimeMode.PRODUCTION)
    assert RUNTIME_MODE_CHOICES[-1] == (
        "Native WiiConnect24 bootstrap beacon",
        Prime3HardwareRuntimeMode.NATIVE_WC24_BOOTSTRAP_BEACON_ONCE,
    )


def test_hardware_runtime_mode_combo_is_in_ui_file() -> None:
    ui_path = (
        Path(__file__)
        .resolve()
        .parents[5]
        .joinpath("randovania", "games", "prime3", "gui", "ui_files", "corruption_game_export_dialog.ui")
    )
    ui_text = ui_path.read_text(encoding="utf-8")

    assert 'name="runtime_mode_combo"' in ui_text
    assert "Wii Hardware Runtime" in ui_text
