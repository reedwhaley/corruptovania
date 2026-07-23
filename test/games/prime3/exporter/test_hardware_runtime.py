from __future__ import annotations

import base64
import dataclasses
import io
import json
import shutil
import uuid
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions

import randovania
from randovania.games.prime3.exporter import hardware_runtime, probe_delivery
from randovania.games.prime3.exporter.dol_patcher import Prime3DolPatchError, parse_dol_header
from test.games.prime3.exporter.test_dol_patcher import _build_synthetic_dol


def _supported_dol() -> bytes:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    return _build_synthetic_dol(
        version,
        include_build_string=False,
        text_sections=[
            (
                0x100,
                probe_delivery.EXPECTED_ENTRYPOINT,
                probe_delivery.EXPECTED_ENTRY_WORD.to_bytes(4, "big") + b"\x60\x00\x00\x00" * 15,
            ),
            (
                0x200,
                probe_delivery.RECURRING_POLL_HOOK_ADDRESS,
                probe_delivery.RECURRING_POLL_HOOK_EXPECTED_WORD.to_bytes(4, "big") + b"\x60\x00\x00\x00" * 15,
            ),
            (0x300, version.build_string_address, version.build_string + b"\x00" * 0x20),
        ],
        entry_point=probe_delivery.EXPECTED_ENTRYPOINT,
    )


@pytest.fixture(scope="module")
def production_runtime(tmp_path_factory: pytest.TempPathFactory):
    output_dir = tmp_path_factory.mktemp("cp3w-production")
    fixture_path = Path(__file__).with_name("fixtures").joinpath("cp3w_production_runtime.zip.b64")
    fixture_bytes = base64.b64decode(fixture_path.read_text(encoding="ascii").strip(), validate=True)
    with zipfile.ZipFile(io.BytesIO(fixture_bytes)) as fixture:
        for name in ("payload.bin", "payload.json"):
            output_dir.joinpath(name).write_bytes(fixture.read(name))
    output_dir.joinpath("payload.elf").write_bytes(b"\x7fELF\x01\x02synthetic CP3W test fixture")

    assets = hardware_runtime.load_validated_production_runtime_assets(output_dir, require_elf=True)
    return assets.payload, assets.manifest, output_dir


def test_production_runtime_installs_and_validates(production_runtime) -> None:
    payload, manifest, _ = production_runtime
    patched, result = hardware_runtime.patch_prime3_hardware_dol(
        _supported_dol(),
        uuid.UUID("12345678-1234-5678-1234-567812345678"),
        payload=payload,
        manifest=manifest,
    )

    validation = hardware_runtime.validate_prime3_hardware_artifact(patched, payload=payload, manifest=manifest)
    assert validation == result.validation
    assert validation.runtime_mode == hardware_runtime.PRODUCTION_RUNTIME_MODE
    assert validation.udp_port == 43674
    assert validation.game_identity_supported
    assert validation.inventory_supported
    assert validation.runtime_occurrence_count == 1


def test_production_runtime_rejects_duplicate_installation(production_runtime) -> None:
    payload, manifest, _ = production_runtime
    patched, _ = hardware_runtime.patch_prime3_hardware_dol(
        _supported_dol(),
        uuid.UUID(int=0),
        payload=payload,
        manifest=manifest,
    )

    with pytest.raises(Prime3DolPatchError, match="duplicate"):
        hardware_runtime.patch_prime3_hardware_dol(
            patched,
            uuid.UUID(int=1),
            payload=payload,
            manifest=manifest,
        )


def test_production_runtime_validator_rejects_partial_hook(production_runtime) -> None:
    payload, manifest, _ = production_runtime
    patched, _ = hardware_runtime.patch_prime3_hardware_dol(
        _supported_dol(),
        uuid.UUID(int=0),
        payload=payload,
        manifest=manifest,
    )
    mutable = bytearray(patched)
    hook_offset = parse_dol_header(mutable).offset_for_address(probe_delivery.RECURRING_POLL_HOOK_ADDRESS)
    assert hook_offset is not None
    mutable[hook_offset : hook_offset + 4] = probe_delivery.RECURRING_POLL_HOOK_EXPECTED_WORD.to_bytes(4, "big")

    with pytest.raises(Prime3DolPatchError, match="hook"):
        hardware_runtime.validate_prime3_hardware_artifact(bytes(mutable), payload=payload, manifest=manifest)


def test_production_manifest_rejects_configurable_port(production_runtime) -> None:
    payload, manifest, _ = production_runtime
    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = dataclasses.replace(manifest.relocated_runtime.transport, udp_port=12345)
    relocated = dataclasses.replace(manifest.relocated_runtime, transport=transport)
    invalid = dataclasses.replace(manifest, relocated_runtime=relocated)

    with pytest.raises(Prime3DolPatchError, match="43674"):
        hardware_runtime.validate_prime3_hardware_artifact(_supported_dol(), payload=payload, manifest=invalid)


def _copy_production_assets(production_runtime, destination: Path) -> None:
    _, _, source = production_runtime
    destination.mkdir()
    for name in ("payload.elf", "payload.bin", "payload.json"):
        shutil.copy2(source.joinpath(name), destination.joinpath(name))


def test_packaged_runtime_asset_lookup_accepts_valid_assets(production_runtime, tmp_path: Path) -> None:
    asset_dir = tmp_path.joinpath("assets")
    _copy_production_assets(production_runtime, asset_dir)

    assets = hardware_runtime.load_validated_production_runtime_assets(asset_dir, require_elf=True)

    assert assets.payload_sha256 == assets.manifest.payload_sha256
    assert assets.elf_sha256 is not None
    assert assets.manifest.relocated_runtime is not None
    assert assets.manifest.relocated_runtime.transport is not None
    assert assets.manifest.relocated_runtime.transport.mode == hardware_runtime.PRODUCTION_RUNTIME_MODE
    assert assets.manifest.relocated_runtime.transport.udp_port == 43674


def test_packaged_runtime_asset_lookup_reports_missing_prebuild(tmp_path: Path) -> None:
    with pytest.raises(Prime3DolPatchError, match="tools/build_prime3_runtime_assets.py"):
        hardware_runtime.load_validated_production_runtime_assets(tmp_path, require_elf=True)


def test_packaged_runtime_asset_lookup_rejects_invalid_metadata(production_runtime, tmp_path: Path) -> None:
    asset_dir = tmp_path.joinpath("assets")
    _copy_production_assets(production_runtime, asset_dir)
    manifest_path = asset_dir.joinpath("payload.json")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["relocated_runtime"]["transport"]["udp_port"] = 12345
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(Prime3DolPatchError, match="43674"):
        hardware_runtime.load_validated_production_runtime_assets(asset_dir, require_elf=True)


def test_packaged_runtime_asset_lookup_rejects_invalid_payload_hash(production_runtime, tmp_path: Path) -> None:
    asset_dir = tmp_path.joinpath("assets")
    _copy_production_assets(production_runtime, asset_dir)
    payload_path = asset_dir.joinpath("payload.bin")
    payload_path.write_bytes(payload_path.read_bytes() + b"stale")

    with pytest.raises(Prime3DolPatchError, match="SHA-256"):
        hardware_runtime.load_validated_production_runtime_assets(asset_dir, require_elf=True)


@pytest.mark.parametrize("runtime_mode", hardware_runtime.HARDWARE_RUNTIME_MODES)
def test_frozen_package_contains_selected_runtime_assets(
    runtime_mode: hardware_runtime.Prime3HardwareRuntimeMode,
) -> None:
    if not randovania.is_frozen():
        pytest.skip("Runtime asset packaging is validated through the frozen executable.")

    asset_dir = hardware_runtime.runtime_asset_directory(
        randovania.get_data_path().joinpath("prime3_wii_runtime"), runtime_mode
    )
    assets = hardware_runtime.load_validated_hardware_runtime_assets(asset_dir, runtime_mode, require_elf=False)

    assert assets.manifest.relocated_runtime is not None
    assert assets.manifest.relocated_runtime.transport is not None
    assert assets.manifest.relocated_runtime.transport.mode == runtime_mode.value


def test_pyinstaller_spec_only_consumes_prebuilt_runtime_assets() -> None:
    repository_root = Path(__file__).resolve().parents[4]
    spec_text = repository_root.joinpath("randovania.spec").read_text(encoding="utf-8")
    workflow_text = repository_root.joinpath(".github", "workflows", "build-test-publish.yml").read_text(
        encoding="utf-8"
    )

    assert "load_validated_hardware_runtime_assets" in spec_text
    assert "build_production_runtime_payload" not in spec_text
    assert "build_hardware_runtime_payload" not in spec_text
    assert "assets.payload_path" in spec_text
    assert "assets.manifest_path" in spec_text
    assert "for runtime_mode in HARDWARE_RUNTIME_MODES" in spec_text
    assert "runtime_asset_directory(base_dir, runtime_mode)" in spec_text
    assert "path: build/prime3_wii_runtime/production" in workflow_text
    assert "build/prime3_wii_runtime/production/payload.elf" not in workflow_text


@pytest.mark.parametrize("runtime_mode", hardware_runtime.HARDWARE_RUNTIME_MODES)
def test_hardware_runtime_build_uses_mode_configuration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime_mode: hardware_runtime.Prime3HardwareRuntimeMode,
) -> None:
    captured: dict[str, object] = {}

    def fake_build(output_dir: Path, **kwargs: object) -> SimpleNamespace:
        captured["output_dir"] = output_dir
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(hardware_runtime, "build_prime3_runtime_payload", fake_build)

    hardware_runtime.build_hardware_runtime_payload(tmp_path, runtime_mode)

    production = runtime_mode is hardware_runtime.Prime3HardwareRuntimeMode.PRODUCTION
    assert captured == {
        "output_dir": tmp_path,
        "payload_mode": "relocated_continue",
        "enable_recurring_hook_diagnostics": not production,
        "enable_ios_udp_diagnostic": True,
        "ios_udp_mode": runtime_mode.value,
        "ios_udp_loop_count": 0 if production else 1,
        "reserved_high": 0x817E0000,
        "diagnostic_address": 0x817E0100,
    }


def test_diagnostic_manifest_does_not_require_production_protocol_metadata(production_runtime) -> None:
    payload, manifest, _ = production_runtime
    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = dataclasses.replace(
        manifest.relocated_runtime.transport,
        mode=hardware_runtime.Prime3HardwareRuntimeMode.BIND_ONCE.value,
        receive_enabled=False,
        send_enabled=False,
        terminal_phase_value=0x11,
        terminal_phase_name="BOUND_NO_RECV",
        cp3w_game_identity=None,
        cp3w_inventory=None,
    )
    relocated = dataclasses.replace(manifest.relocated_runtime, transport=transport)
    diagnostic = dataclasses.replace(manifest, relocated_runtime=relocated)

    hardware_runtime._validate_hardware_manifest(
        payload,
        diagnostic,
        hardware_runtime.Prime3HardwareRuntimeMode.BIND_ONCE,
    )


def test_selected_runtime_mode_must_match_manifest(production_runtime) -> None:
    payload, manifest, _ = production_runtime

    with pytest.raises(Prime3DolPatchError, match="does not match selected mode"):
        hardware_runtime._validate_hardware_manifest(
            payload,
            manifest,
            hardware_runtime.Prime3HardwareRuntimeMode.RECVFROM_ONCE,
        )


def test_production_manifest_still_requires_protocol_metadata(production_runtime) -> None:
    payload, manifest, _ = production_runtime
    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = dataclasses.replace(
        manifest.relocated_runtime.transport,
        cp3w_game_identity=None,
        cp3w_inventory=None,
    )
    relocated = dataclasses.replace(manifest.relocated_runtime, transport=transport)
    invalid = dataclasses.replace(manifest, relocated_runtime=relocated)

    with pytest.raises(Prime3DolPatchError, match="identity"):
        hardware_runtime._validate_hardware_manifest(
            payload,
            invalid,
            hardware_runtime.Prime3HardwareRuntimeMode.PRODUCTION,
        )


def test_atomic_patcher_loads_selected_runtime_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path.joinpath("main.dol")
    path.write_bytes(b"original")
    selected_mode = hardware_runtime.Prime3HardwareRuntimeMode.GET_HOST_ID_ONCE
    manifest = SimpleNamespace()
    expected_result = SimpleNamespace()
    calls: list[tuple[Path, hardware_runtime.Prime3HardwareRuntimeMode]] = []

    def fake_load(
        output_dir: Path, runtime_mode: hardware_runtime.Prime3HardwareRuntimeMode
    ) -> tuple[bytes, SimpleNamespace]:
        calls.append((output_dir, runtime_mode))
        return b"payload", manifest

    def fake_patch(original_dol: bytes, layout_uuid: uuid.UUID, **kwargs: object) -> tuple[bytes, SimpleNamespace]:
        assert original_dol == b"original"
        assert kwargs == {"payload": b"payload", "manifest": manifest, "runtime_mode": selected_mode}
        return b"patched", expected_result

    monkeypatch.setattr(hardware_runtime, "load_or_build_hardware_runtime", fake_load)
    monkeypatch.setattr(hardware_runtime, "patch_prime3_hardware_dol", fake_patch)
    monkeypatch.setattr(hardware_runtime, "atomic_replace_file", lambda target, data: target.write_bytes(data))

    result = hardware_runtime.patch_prime3_hardware_dol_file_atomic(
        path,
        uuid.UUID(int=0),
        runtime_build_dir=tmp_path.joinpath("runtime"),
        runtime_mode=selected_mode,
    )

    assert calls == [(tmp_path.joinpath("runtime"), selected_mode)]
    assert result is expected_result
    assert path.read_bytes() == b"patched"
