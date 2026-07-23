from __future__ import annotations

import logging
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions

from randovania.games.prime3.exporter import dol_patcher, game_exporter
from randovania.games.prime3.exporter.game_exporter import (
    CorruptionGameExporter,
    CorruptionGameExportParams,
    CorruptionOutputFormats,
)
from randovania.games.prime3.exporter.hardware_runtime import Prime3HardwareRuntimeMode
from randovania.games.prime3.exporter.toolchain import Prime3Toolchain
from test.games.prime3.exporter.test_dol_patcher import _build_synthetic_dol


def _toolchain() -> Prime3Toolchain:
    return Prime3Toolchain(
        randomizer_command=("randomizer",),
        hpatchz_command=("hpatchz",),
        wit_command=("wit",),
        extractor_command=(),
        uses_python_nod=True,
    )


def _write_prime3_extract_tree(extract_path: Path, main_dol_bytes: bytes) -> None:
    sys_dir = extract_path.joinpath("DATA", "sys")
    files_dir = extract_path.joinpath("DATA", "files")
    video_dir = files_dir.joinpath("Video", "FrontEnd")
    sys_dir.mkdir(parents=True)
    video_dir.mkdir(parents=True)
    sys_dir.joinpath("main.dol").write_bytes(main_dol_bytes)
    for name in [
        "FrontEnd.pak",
        "Logbook.pak",
        "Metroid1.pak",
        "Metroid3.pak",
        "Metroid4.pak",
        "Metroid5.pak",
        "Metroid6.pak",
        "Metroid7.pak",
        "Metroid8.pak",
        "MiscData.pak",
        "UniverseArea.pak",
        "Worlds.pak",
        "Standard.ntwk",
        "InGameAudio.pak",
        "NoARAM.pak",
    ]:
        files_dir.joinpath(name).write_bytes(name.encode("ascii"))


def _patcher_root(tmp_path: Path) -> Path:
    root = tmp_path.joinpath("data", "gollop_mp3_patcher")
    root.joinpath("dummy_attract").mkdir(parents=True)
    root.joinpath("MP3Update").mkdir()
    root.joinpath("dummy_attract", "attract01.thp").write_bytes(b"1")
    root.joinpath("dummy_attract", "Attract02.thp").write_bytes(b"2")
    root.joinpath("MP3Update", "main.hdiff").write_bytes(b"")
    for name in [
        "FrontEnd",
        "InGameAudio",
        "NoARAM",
        "Metroid1",
        "Metroid3",
        "Metroid4",
        "Metroid5",
        "Metroid6",
        "Metroid7",
        "UniverseArea",
    ]:
        root.joinpath("MP3Update", f"{name}.hdiff").write_bytes(b"")
    return root


def _patch_data(*, enable_networking: bool, layout_uuid: str) -> dict:
    return {
        "disable_deflicker": False,
        "mp3_update": False,
        "enable_prime3_wii_networking": enable_networking,
        "layout_uuid": layout_uuid,
        "seed": "SEED123",
        "starting_items": "Missile Expansion",
        "starting_location": "Landing Site",
        "random_door_colors": False,
        "random_welding_colors": False,
        "missile_required_mains": False,
        "ship_missile_required_mains": False,
        "phaaze_skip": False,
    }


def _export_params(
    tmp_path: Path,
    runtime_mode: Prime3HardwareRuntimeMode = Prime3HardwareRuntimeMode.PRODUCTION,
) -> CorruptionGameExportParams:
    return CorruptionGameExportParams(
        spoiler_output=None,
        input_path=tmp_path.joinpath("input.iso"),
        output_path=tmp_path.joinpath("output.iso"),
        output_format=CorruptionOutputFormats.ISO,
        mp3_update=False,
        runtime_mode=runtime_mode,
    )


def _configure_export_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    main_dol_bytes: bytes,
):
    extract_path = tmp_path.joinpath("extract")
    paks_path = tmp_path.joinpath("paks")
    patcher_root = _patcher_root(tmp_path)
    paks_path.mkdir()
    toolchain = _toolchain()
    calls: list[tuple[str, ...]] = []
    hardware_calls: list[tuple[Path, uuid.UUID, Path, Prime3HardwareRuntimeMode]] = []

    def fake_extract_prime3_disc_image(_toolchain_arg, _input_path, destination: Path, _progress_update) -> None:
        _write_prime3_extract_tree(destination, main_dol_bytes)

    def fake_run_process(command: tuple[str, ...], env=None) -> None:
        del env
        calls.append(command)

    def fake_patch_hardware(
        path: Path,
        layout_uuid: uuid.UUID,
        *,
        runtime_build_dir: Path,
        runtime_mode: Prime3HardwareRuntimeMode,
    ):
        hardware_calls.append((path, layout_uuid, runtime_build_dir, runtime_mode))
        patched, _ = dol_patcher.patch_prime3_corruption_dol(path.read_bytes(), layout_uuid)
        path.write_bytes(patched)
        validation = SimpleNamespace(
            payload_sha256="a" * 64,
            version_description="Wii NTSC",
            runtime_section_address=0x80006320,
            entry_hook_target=0x80006320,
            recurring_hook_target=0x81700000,
            udp_port=43674,
        )
        return SimpleNamespace(validation=validation)

    mkdtemp_values = iter([str(extract_path), str(paks_path)])
    monkeypatch.setattr(game_exporter.randovania, "get_data_path", lambda: tmp_path.joinpath("data"))
    monkeypatch.setattr(game_exporter, "resolve_prime3_toolchain", lambda: toolchain)
    monkeypatch.setattr(game_exporter, "extract_prime3_disc_image", fake_extract_prime3_disc_image)
    monkeypatch.setattr(game_exporter, "_run_process", fake_run_process)
    monkeypatch.setattr(game_exporter, "patch_prime3_hardware_dol_file_atomic", fake_patch_hardware)
    monkeypatch.setattr(game_exporter.tempfile, "mkdtemp", lambda: next(mkdtemp_values))
    monkeypatch.setattr(game_exporter.shutil, "rmtree", lambda path, ignore_errors=True: None)

    return extract_path, paks_path, patcher_root, calls, hardware_calls


def test_export_networking_legacy_disabled_flag_still_installs_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    original_main_dol = _build_synthetic_dol(version, section_address=version.build_string_address - 0x20)
    extract_path, _paks_path, _patcher_root, calls, hardware_calls = _configure_export_environment(
        tmp_path, monkeypatch, original_main_dol
    )

    exporter = CorruptionGameExporter()
    exporter._do_export_game(
        _patch_data(enable_networking=False, layout_uuid="12345678-1234-5678-1234-567812345678"),
        _export_params(tmp_path),
        lambda _message, _progress: None,
    )

    assert extract_path.joinpath("DATA", "sys", "main.dol").read_bytes() != original_main_dol
    assert len(hardware_calls) == 1
    assert any(command[0] == "randomizer" for command in calls)
    assert any(command[0] == "wit" for command in calls)


def test_export_networking_enabled_patches_working_copy_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    source_main_dol = _build_synthetic_dol(version, section_address=version.build_string_address - 0x20)
    extract_path, _paks_path, _patcher_root, _calls, hardware_calls = _configure_export_environment(
        tmp_path, monkeypatch, source_main_dol
    )
    layout_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")

    exporter = CorruptionGameExporter()
    exporter._do_export_game(
        _patch_data(enable_networking=True, layout_uuid=str(layout_uuid)),
        _export_params(tmp_path),
        lambda _message, _progress: None,
    )

    patched_bytes = extract_path.joinpath("DATA", "sys", "main.dol").read_bytes()
    patched_offset = dol_patcher.virtual_address_to_file_offset(
        dol_patcher.parse_dol_sections(patched_bytes),
        version.build_string_address,
        len(version.build_string),
    )
    assert source_main_dol[patched_offset : patched_offset + len(version.build_string)] == version.build_string
    assert patched_bytes[patched_offset + 6 : patched_offset + 22] == layout_uuid.bytes
    assert source_main_dol == _build_synthetic_dol(version, section_address=version.build_string_address - 0x20)
    assert hardware_calls[0][1] == layout_uuid
    assert hardware_calls[0][3] is Prime3HardwareRuntimeMode.PRODUCTION


def test_export_propagates_selected_runtime_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    main_dol = _build_synthetic_dol(version, section_address=version.build_string_address - 0x20)
    _extract_path, _paks_path, _patcher_root, _calls, hardware_calls = _configure_export_environment(
        tmp_path, monkeypatch, main_dol
    )

    exporter = CorruptionGameExporter()
    caplog.set_level(logging.INFO)
    exporter._do_export_game(
        _patch_data(enable_networking=True, layout_uuid="12345678-1234-5678-1234-567812345678"),
        _export_params(tmp_path, Prime3HardwareRuntimeMode.BIND_ONCE),
        lambda _message, _progress: None,
    )

    assert hardware_calls[0][3] is Prime3HardwareRuntimeMode.BIND_ONCE
    assert "mode=retail_wrapper_bind_once payload=" + "a" * 64 in caplog.text


def test_export_networking_enabled_rejects_unsupported_dol(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    unsupported_main_dol = _build_synthetic_dol(
        corruption_dol_versions.ALL_VERSIONS[0],
        section_address=corruption_dol_versions.ALL_VERSIONS[0].build_string_address - 0x20,
        build_string_bytes=b"X" * len(corruption_dol_versions.ALL_VERSIONS[0].build_string),
    )
    _configure_export_environment(tmp_path, monkeypatch, unsupported_main_dol)
    monkeypatch.setattr(
        game_exporter,
        "patch_prime3_hardware_dol_file_atomic",
        lambda path, *_args, **_kwargs: dol_patcher.identify_supported_corruption_version(path.read_bytes()),
    )
    exporter = CorruptionGameExporter()

    with pytest.raises(dol_patcher.Prime3DolPatchError, match="Unsupported or unknown"):
        exporter._do_export_game(
            _patch_data(enable_networking=True, layout_uuid="12345678-1234-5678-1234-567812345678"),
            _export_params(tmp_path),
            lambda _message, _progress: None,
        )


def test_export_networking_surfaces_atomic_write_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    main_dol = _build_synthetic_dol(version, section_address=version.build_string_address - 0x20)
    _configure_export_environment(tmp_path, monkeypatch, main_dol)
    monkeypatch.setattr(
        game_exporter,
        "patch_prime3_hardware_dol_file_atomic",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("replace failed")),
    )
    exporter = CorruptionGameExporter()

    with pytest.raises(OSError, match="replace failed"):
        exporter._do_export_game(
            _patch_data(enable_networking=True, layout_uuid="12345678-1234-5678-1234-567812345678"),
            _export_params(tmp_path),
            lambda _message, _progress: None,
        )


def test_export_deflicker_then_networking_compose_cleanly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    original_main_dol = _build_synthetic_dol(version, section_address=version.build_string_address - 0x20)
    extract_path, _paks_path, _patcher_root, calls, _hardware_calls = _configure_export_environment(
        tmp_path, monkeypatch, original_main_dol
    )
    layout_uuid = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    def fake_run_process(command: tuple[str, ...], env=None) -> None:
        del env
        calls.append(command)
        if command[0] == "hpatchz" and command[2].endswith("main.dol"):
            main_dol_path = Path(command[2])
            data = bytearray(main_dol_path.read_bytes())
            data[-1] ^= 0x01
            main_dol_path.write_bytes(bytes(data))

    monkeypatch.setattr(game_exporter, "_run_process", fake_run_process)

    exporter = CorruptionGameExporter()
    patch_data = _patch_data(enable_networking=True, layout_uuid=str(layout_uuid))
    patch_data["disable_deflicker"] = True
    exporter._do_export_game(patch_data, _export_params(tmp_path), lambda _message, _progress: None)

    patched_bytes = extract_path.joinpath("DATA", "sys", "main.dol").read_bytes()
    build_string_offset = dol_patcher.virtual_address_to_file_offset(
        dol_patcher.parse_dol_sections(patched_bytes),
        version.build_string_address,
        len(version.build_string),
    )
    assert patched_bytes[build_string_offset + 6 : build_string_offset + 22] == layout_uuid.bytes
    assert patched_bytes[-1] == (original_main_dol[-1] ^ 0x01)
    assert calls[0][0] == "hpatchz"
