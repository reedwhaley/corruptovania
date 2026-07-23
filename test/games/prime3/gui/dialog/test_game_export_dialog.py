from __future__ import annotations

from ipaddress import IPv4Address
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime3.exporter.game_exporter import CorruptionGameExportParams
from randovania.games.prime3.exporter.hardware_runtime import HARDWARE_RUNTIME_MODES, Prime3HardwareRuntimeMode
from randovania.games.prime3.exporter.options import CorruptionPerGameOptions
from randovania.games.prime3.gui.dialog.game_export_dialog import RUNTIME_MODE_CHOICES, CorruptionGameExportDialog


@pytest.fixture
def export_dialog(skip_qtbot, tmp_path: Path) -> CorruptionGameExportDialog:
    input_path = tmp_path.joinpath("input.iso")
    input_path.write_bytes(b"iso")
    options = MagicMock()
    options.auto_save_spoiler = False
    options.options_for_game.return_value = CorruptionPerGameOptions(
        cosmetic_patches=RandovaniaGame.METROID_PRIME_CORRUPTION.data.layout.cosmetic_patches.default(),
        input_path=input_path,
        output_path=tmp_path,
    )
    dialog = CorruptionGameExportDialog(
        options,
        {},
        "HASH",
        False,
        [RandovaniaGame.METROID_PRIME_CORRUPTION],
    )
    skip_qtbot.addWidget(dialog)
    return dialog


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
    assert 'name="beacon_ip_edit"' in ui_text
    assert "UDP port: 43674" in ui_text


def _select_runtime(dialog: CorruptionGameExportDialog, mode: Prime3HardwareRuntimeMode) -> None:
    index = dialog.runtime_mode_combo.findData(mode.value)
    assert index >= 0
    dialog.runtime_mode_combo.setCurrentIndex(index)


def test_beacon_fields_hidden_and_empty_by_default(export_dialog: CorruptionGameExportDialog) -> None:
    assert export_dialog.runtime_mode is Prime3HardwareRuntimeMode.PRODUCTION
    assert export_dialog.beacon_ip_edit.text() == ""
    assert export_dialog.beacon_ip_edit.isHidden()
    assert export_dialog.beacon_ip_label.isHidden()
    assert export_dialog.beacon_port_label.isHidden()


def test_native_beacon_requires_valid_ipv4(export_dialog: CorruptionGameExportDialog) -> None:
    _select_runtime(export_dialog, Prime3HardwareRuntimeMode.NATIVE_WC24_BOOTSTRAP_BEACON_ONCE)

    assert not export_dialog.beacon_ip_edit.isHidden()
    assert not export_dialog.beacon_ip_label.isHidden()
    assert not export_dialog.beacon_port_label.isHidden()
    assert export_dialog.beacon_port_label.text() == "UDP port: 43674"
    assert not export_dialog.beacon_validation_label.isHidden()
    assert not export_dialog.accept_button.isEnabled()

    for invalid in ("example.com", "2001:db8::1", "999.1.2.3"):
        export_dialog.beacon_ip_edit.setText(invalid)
        assert export_dialog.beacon_ip_edit.has_error
        assert not export_dialog.beacon_validation_label.isHidden()
        assert not export_dialog.accept_button.isEnabled()

    export_dialog.beacon_ip_edit.setText("192.0.2.55")
    assert not export_dialog.beacon_ip_edit.has_error
    assert export_dialog.beacon_validation_label.isHidden()
    assert export_dialog.accept_button.isEnabled()
    assert export_dialog.beacon_ipv4 == IPv4Address("192.0.2.55")


def test_selected_beacon_ip_reaches_typed_export_params(export_dialog: CorruptionGameExportDialog) -> None:
    _select_runtime(export_dialog, Prime3HardwareRuntimeMode.NATIVE_WC24_BOOTSTRAP_BEACON_ONCE)
    export_dialog.beacon_ip_edit.setText("198.51.100.22")

    params = export_dialog.get_game_export_params()

    assert isinstance(params, CorruptionGameExportParams)
    assert params.runtime_mode is Prime3HardwareRuntimeMode.NATIVE_WC24_BOOTSTRAP_BEACON_ONCE
    assert params.beacon_ipv4 == IPv4Address("198.51.100.22")
