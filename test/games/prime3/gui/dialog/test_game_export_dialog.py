from __future__ import annotations

from ipaddress import IPv4Address
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime3.exporter.game_exporter import CorruptionGameExportParams
from randovania.games.prime3.exporter.hardware_runtime import Prime3HardwareRuntimeMode
from randovania.games.prime3.exporter.options import CorruptionPerGameOptions
from randovania.games.prime3.gui.dialog import game_export_dialog
from randovania.games.prime3.gui.dialog.game_export_dialog import CorruptionGameExportDialog


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


def test_normal_export_dialog_has_no_runtime_selector() -> None:
    ui_path = (
        Path(__file__)
        .resolve()
        .parents[5]
        .joinpath("randovania", "games", "prime3", "gui", "ui_files", "corruption_game_export_dialog.ui")
    )
    ui_text = ui_path.read_text(encoding="utf-8")

    assert 'name="runtime_mode_combo"' not in ui_text
    assert "Wii Hardware Runtime" not in ui_text
    assert 'name="beacon_ip_edit"' not in ui_text
    assert 'name="cp3w_server_address_edit"' in ui_text
    assert "server port" not in ui_text.lower()


def test_normal_export_always_uses_production_tcp_runtime(export_dialog: CorruptionGameExportDialog) -> None:
    params = export_dialog.get_game_export_params()

    assert isinstance(params, CorruptionGameExportParams)
    assert params.runtime_mode is Prime3HardwareRuntimeMode.PRODUCTION
    assert params.beacon_ipv4 is None
    assert params.enable_cp3w_networking is False
    assert params.cp3w_server_ipv4 is None
    assert export_dialog.cp3w_server_address_edit.isHidden()
    assert export_dialog.cp3w_server_address_label.isHidden()
    assert export_dialog.cp3w_server_address_help_label.isHidden()


def test_networking_export_dialog_shows_and_persists_server_ipv4(
    skip_qtbot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path.joinpath("input.iso")
    input_path.write_bytes(b"iso")
    options = MagicMock()
    options.auto_save_spoiler = False
    per_game = CorruptionPerGameOptions(
        cosmetic_patches=RandovaniaGame.METROID_PRIME_CORRUPTION.data.layout.cosmetic_patches.default(),
        input_path=input_path,
        output_path=tmp_path,
    )
    options.options_for_game.return_value = per_game
    monkeypatch.setattr(game_export_dialog, "discover_cp3w_server_ipv4", lambda: IPv4Address("192.168.50.248"))

    dialog = CorruptionGameExportDialog(
        options,
        {"enable_prime3_wii_networking": True},
        "HASH",
        False,
        [RandovaniaGame.METROID_PRIME_CORRUPTION],
    )
    skip_qtbot.addWidget(dialog)

    assert not dialog.cp3w_server_address_edit.isHidden()
    assert dialog.cp3w_server_address_edit.text() == "192.168.50.248"
    dialog.cp3w_server_address_edit.setText("10.20.30.40")
    params = dialog.get_game_export_params()
    saved_options = dialog.update_per_game_options(per_game)

    assert params.enable_cp3w_networking is True
    assert params.cp3w_server_ipv4 == IPv4Address("10.20.30.40")
    assert saved_options.cp3w_server_ipv4 == "10.20.30.40"

    options.options_for_game.return_value = saved_options
    reopened = CorruptionGameExportDialog(
        options,
        {"enable_prime3_wii_networking": True},
        "HASH",
        False,
        [RandovaniaGame.METROID_PRIME_CORRUPTION],
    )
    skip_qtbot.addWidget(reopened)
    assert reopened.cp3w_server_address_edit.text() == "10.20.30.40"


def test_networking_export_dialog_rejects_invalid_server_ipv4(export_dialog: CorruptionGameExportDialog) -> None:
    export_dialog._cp3w_networking_enabled = True
    export_dialog.cp3w_server_address_edit.setText("127.0.0.1")

    assert export_dialog._cp3w_server_address_invalid()
