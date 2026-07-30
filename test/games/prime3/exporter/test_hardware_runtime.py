from __future__ import annotations

import base64
import dataclasses
import hashlib
import io
import json
import shutil
import uuid
import zipfile
from ipaddress import IPv4Address
from pathlib import Path

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions

import randovania
from randovania.games.prime3.exporter import hardware_runtime, probe_delivery
from randovania.games.prime3.exporter.dol_patcher import Prime3DolPatchError, parse_dol_header
from randovania.games.prime3.exporter.runtime_payload import Prime3RuntimeTransportMetadata
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
    assert assets.manifest.relocated_runtime is not None
    transport = assets.manifest.relocated_runtime.transport
    assert isinstance(transport, Prime3RuntimeTransportMetadata)
    assert transport.transport_kind == "tcp"
    assert transport.server_ipv4_size == 4
    assert transport.server_port_size == 2
    assert transport.server_ipv4_byte_order == "big"
    assert transport.server_port_byte_order == "big"
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


def test_patch_cp3w_tcp_endpoint_writes_manifest_defined_fields(production_runtime) -> None:
    payload, manifest, _ = production_runtime
    assert manifest.relocated_runtime is not None
    relocated = manifest.relocated_runtime
    blob_offset = relocated.embedded_runtime_blob_offset
    tcp_transport = Prime3RuntimeTransportMetadata(
        transport_kind="tcp",
        protocol_magic_hex="43503357",
        protocol_version=1,
        frame_size=64,
        diagnostics_enabled=False,
        inbound_queue_depth=4,
        outbound_queue_depth=4,
        cp3c_config_offset=0x20,
        cp3c_config_size=0x20,
        server_ipv4_offset=0x2C,
        server_ipv4_size=4,
        server_ipv4_byte_order="big",
        server_port_offset=0x30,
        server_port_size=2,
        server_port_byte_order="big",
        inventory_tracker_capability=True,
        tracker_snapshot_capability=True,
        tracker_delta_capability=True,
        resync_capability=True,
    )
    source = bytearray(payload)
    source[blob_offset + 0x2C : blob_offset + 0x30] = b"\0\0\0\0"
    source[blob_offset + 0x30 : blob_offset + 0x32] = b"\xaa\x9a"
    source_payload = bytes(source)
    tcp_relocated = dataclasses.replace(
        relocated,
        transport=tcp_transport,
        embedded_runtime_blob_sha256=hashlib.sha256(
            source_payload[blob_offset : blob_offset + relocated.embedded_runtime_blob_size]
        ).hexdigest(),
    )
    tcp_manifest = dataclasses.replace(
        manifest,
        payload_sha256=hashlib.sha256(source_payload).hexdigest(),
        relocated_runtime=tcp_relocated,
        beacon_ipv4_patch=None,
    )

    first_payload, first_manifest = hardware_runtime.patch_cp3w_tcp_endpoint(
        source_payload, tcp_manifest, IPv4Address("192.168.50.248")
    )
    second_payload, _ = hardware_runtime.patch_cp3w_tcp_endpoint(
        source_payload, tcp_manifest, IPv4Address("10.20.30.40")
    )

    assert first_payload[blob_offset + 0x2C : blob_offset + 0x30] == b"\xc0\xa8\x32\xf8"
    assert first_payload[blob_offset + 0x30 : blob_offset + 0x32] == b"\xaa\x9a"
    assert second_payload[blob_offset + 0x2C : blob_offset + 0x30] == b"\x0a\x14\x1e\x28"
    assert second_payload[blob_offset + 0x30 : blob_offset + 0x32] == b"\xaa\x9a"
    assert first_manifest.payload_sha256 == hashlib.sha256(first_payload).hexdigest()
    changed_offsets = [
        offset
        for offset, (before, after) in enumerate(zip(first_payload, second_payload, strict=True))
        if before != after
    ]
    assert changed_offsets == list(range(blob_offset + 0x2C, blob_offset + 0x30))

    invalid_transport = dataclasses.replace(tcp_transport, server_port_size=4)
    invalid_manifest = dataclasses.replace(
        tcp_manifest,
        relocated_runtime=dataclasses.replace(tcp_relocated, transport=invalid_transport),
    )
    with pytest.raises(Prime3DolPatchError, match="invalid CP3C endpoint field metadata|invalid widths"):
        hardware_runtime.patch_cp3w_tcp_endpoint(source_payload, invalid_manifest, IPv4Address("192.168.50.248"))


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


def test_production_manifest_rejects_invalid_tcp_endpoint_metadata(production_runtime) -> None:
    payload, manifest, _ = production_runtime
    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = dataclasses.replace(manifest.relocated_runtime.transport, server_port_size=4)
    relocated = dataclasses.replace(manifest.relocated_runtime, transport=transport)
    invalid = dataclasses.replace(manifest, relocated_runtime=relocated)

    with pytest.raises(Prime3DolPatchError, match="CP3C endpoint fields have invalid widths"):
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
    transport = assets.manifest.relocated_runtime.transport
    assert isinstance(transport, Prime3RuntimeTransportMetadata)
    assert transport.transport_kind == "tcp"
    assert transport.diagnostics_enabled is False
    assert transport.cp3c_config_size == 32
    assert transport.server_ipv4_size == 4
    assert transport.server_port_size == 2
    assert transport.server_ipv4_byte_order == "big"
    assert transport.server_port_byte_order == "big"


def test_packaged_runtime_asset_lookup_reports_missing_prebuild(tmp_path: Path) -> None:
    with pytest.raises(Prime3DolPatchError, match="tools/build_prime3_runtime_assets.py"):
        hardware_runtime.load_validated_production_runtime_assets(tmp_path, require_elf=True)


def test_packaged_runtime_asset_lookup_rejects_invalid_metadata(production_runtime, tmp_path: Path) -> None:
    asset_dir = tmp_path.joinpath("assets")
    _copy_production_assets(production_runtime, asset_dir)
    manifest_path = asset_dir.joinpath("payload.json")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["relocated_runtime"]["transport"]["server_port_size"] = 4
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises((Prime3DolPatchError, ValueError), match="port|CP3C|width"):
        hardware_runtime.load_validated_production_runtime_assets(asset_dir, require_elf=True)


def test_packaged_runtime_asset_lookup_rejects_legacy_transport_metadata(production_runtime, tmp_path: Path) -> None:
    asset_dir = tmp_path.joinpath("assets")
    _copy_production_assets(production_runtime, asset_dir)
    manifest_path = asset_dir.joinpath("payload.json")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["relocated_runtime"]["transport"] = {
        "mode": "cp3w_inventory_service",
        "udp_port": 43674,
    }
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(Prime3DolPatchError, match="TCP/CP3C|payload"):
        hardware_runtime.load_validated_production_runtime_assets(asset_dir, require_elf=True)


def test_packaged_runtime_asset_lookup_rejects_invalid_payload_hash(production_runtime, tmp_path: Path) -> None:
    asset_dir = tmp_path.joinpath("assets")
    _copy_production_assets(production_runtime, asset_dir)
    payload_path = asset_dir.joinpath("payload.bin")
    payload_path.write_bytes(payload_path.read_bytes() + b"stale")

    with pytest.raises(Prime3DolPatchError, match="SHA-256"):
        hardware_runtime.load_validated_production_runtime_assets(asset_dir, require_elf=True)


def test_frozen_package_contains_canonical_tcp_runtime_assets() -> None:
    if not randovania.is_frozen():
        pytest.skip("Runtime asset packaging is validated through the frozen executable.")

    assets = hardware_runtime.load_validated_production_runtime_assets(
        randovania.get_data_path().joinpath("prime3_wii_runtime"),
        require_elf=True,
    )

    assert assets.manifest.relocated_runtime is not None
    transport = assets.manifest.relocated_runtime.transport
    assert isinstance(transport, hardware_runtime.Prime3RuntimeTransportMetadata)
    assert transport.transport_kind == "tcp"
    assert assets.elf_path is not None


def test_pyinstaller_spec_only_consumes_prebuilt_runtime_assets() -> None:
    repository_root = Path(__file__).resolve().parents[4]
    spec_text = repository_root.joinpath("randovania.spec").read_text(encoding="utf-8")
    workflow_text = repository_root.joinpath(".github", "workflows", "build-test-publish.yml").read_text(
        encoding="utf-8"
    )

    assert "load_validated_hardware_runtime_assets" not in spec_text
    assert "build_production_runtime_payload" not in spec_text
    assert "build_hardware_runtime_payload" not in spec_text
    assert "assets.payload_path" in spec_text
    assert "assets.manifest_path" in spec_text
    assert "assets.elf_path" in spec_text
    assert "load_validated_production_runtime_assets" in spec_text
    assert "runtime_asset_directory" not in spec_text
    assert "Prime3HardwareRuntimeMode" not in spec_text
    assert "retail_wrapper_startup_once" not in spec_text
    assert '"randovania.games.prime3.exporter.cp3w_endpoint"' in spec_text
    assert '"randovania.games.prime3.exporter.runtime_payload"' in spec_text
    assert "path: build/prime3_wii_runtime/production" in workflow_text
