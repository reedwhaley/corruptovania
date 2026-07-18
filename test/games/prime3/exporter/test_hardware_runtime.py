from __future__ import annotations

import dataclasses
import json
import shutil
import uuid
from pathlib import Path

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions

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
    try:
        manifest = hardware_runtime.build_production_runtime_payload(output_dir)
    except RuntimeError as exc:
        if "devkitPPC" in str(exc) or "toolchain" in str(exc).lower():
            pytest.skip(f"devkitPPC is unavailable: {exc}")
        raise
    return output_dir.joinpath("payload.bin").read_bytes(), manifest, output_dir


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


def test_pyinstaller_spec_only_consumes_prebuilt_runtime_assets() -> None:
    spec_text = Path(__file__).resolve().parents[4].joinpath("randovania.spec").read_text(encoding="utf-8")

    assert "load_validated_production_runtime_assets" in spec_text
    assert "build_production_runtime_payload" not in spec_text
    assert "assets.payload_path" in spec_text
    assert "assets.manifest_path" in spec_text
