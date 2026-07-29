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
from types import SimpleNamespace

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions

import randovania
from randovania.games.prime3.exporter import hardware_runtime, probe_delivery
from randovania.games.prime3.exporter.dol_patcher import Prime3DolPatchError, parse_dol_header
from randovania.games.prime3.exporter.runtime_payload import (
    Prime3RuntimePayloadManifest,
    Prime3RuntimePayloadPatchField,
    Prime3RuntimeTransportMetadata,
)
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


def _native_runtime_fixture(production_runtime) -> tuple[bytes, Prime3RuntimePayloadManifest]:
    payload, manifest, _ = production_runtime
    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    relocated = manifest.relocated_runtime
    offset = relocated.embedded_runtime_blob_offset + 16
    patch_field = Prime3RuntimePayloadPatchField(
        payload_offset=offset,
        expected_original_bytes=payload[offset : offset + 4].hex(),
        field_size=4,
        byte_order="big",
    )
    transport = dataclasses.replace(
        relocated.transport,
        mode=hardware_runtime.Prime3HardwareRuntimeMode.NATIVE_WC24_BOOTSTRAP_BEACON_ONCE.value,
        receive_enabled=False,
        send_enabled=True,
        nwc24_startup_enabled=True,
        kd_close_enabled=False,
        terminal_phase_value=115,
        terminal_phase_name="NATIVE_BEACON_COMPLETE",
        cp3w_game_identity=None,
        cp3w_inventory=None,
    )
    native_relocated = dataclasses.replace(relocated, transport=transport)
    native_manifest = dataclasses.replace(
        manifest,
        relocated_runtime=native_relocated,
        beacon_ipv4_patch=patch_field,
    )
    hardware_runtime._validate_hardware_manifest(
        payload,
        native_manifest,
        hardware_runtime.Prime3HardwareRuntimeMode.NATIVE_WC24_BOOTSTRAP_BEACON_ONCE,
    )
    return payload, native_manifest


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
    assert "for runtime_mode in (Prime3HardwareRuntimeMode.PRODUCTION,)" in spec_text
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
        "native_beacon_ipv4": 0xC0A832F8,
        "reserved_high": 0x817E0000,
        "diagnostic_address": 0x817E0100,
    }


def test_native_bootstrap_beacon_endpoint_is_configurable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_build(output_dir: Path, **kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(hardware_runtime, "build_prime3_runtime_payload", fake_build)

    hardware_runtime.build_hardware_runtime_payload(
        tmp_path,
        hardware_runtime.Prime3HardwareRuntimeMode.NATIVE_WC24_BOOTSTRAP_BEACON_ONCE,
        native_beacon_ipv4=0xC0000201,
    )

    assert captured["native_beacon_ipv4"] == 0xC0000201


def test_diagnostic_manifest_does_not_require_production_protocol_metadata(production_runtime) -> None:
    payload, manifest, _ = production_runtime
    assert manifest.relocated_runtime is not None
    assert manifest.relocated_runtime.transport is not None
    transport = dataclasses.replace(
        manifest.relocated_runtime.transport,
        mode=hardware_runtime.Prime3HardwareRuntimeMode.BIND_ONCE.value,
        receive_enabled=False,
        send_enabled=False,
        nwc24_startup_enabled=True,
        kd_close_enabled=True,
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
        output_dir: Path,
        runtime_mode: hardware_runtime.Prime3HardwareRuntimeMode,
        *,
        beacon_ipv4: IPv4Address | None,
    ) -> tuple[bytes, SimpleNamespace]:
        assert beacon_ipv4 is None
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


def test_native_beacon_payload_patch_changes_only_ipv4_field(production_runtime) -> None:
    payload, manifest = _native_runtime_fixture(production_runtime)
    address = IPv4Address("203.0.113.27")

    patched, patched_manifest = hardware_runtime.patch_native_beacon_ipv4(payload, manifest, address)

    assert manifest.beacon_ipv4_patch is not None
    offset = manifest.beacon_ipv4_patch.payload_offset
    assert payload[offset : offset + 4] != address.packed
    assert patched[offset : offset + 4] == address.packed
    assert payload[:offset] == patched[:offset]
    assert payload[offset + 4 :] == patched[offset + 4 :]
    assert patched_manifest.payload_sha256 == hashlib.sha256(patched).hexdigest()
    assert manifest.payload_sha256 == hashlib.sha256(payload).hexdigest()


def test_native_beacon_payload_patch_rejects_expected_byte_mismatch(production_runtime) -> None:
    payload, manifest = _native_runtime_fixture(production_runtime)
    assert manifest.beacon_ipv4_patch is not None
    invalid = dataclasses.replace(
        manifest,
        beacon_ipv4_patch=dataclasses.replace(
            manifest.beacon_ipv4_patch,
            expected_original_bytes="00000000",
        ),
    )

    with pytest.raises(Prime3DolPatchError, match="expected bytes"):
        hardware_runtime.patch_native_beacon_ipv4(payload, invalid, IPv4Address("192.0.2.1"))


@pytest.mark.parametrize(
    ("field_size", "byte_order", "message"),
    [(3, "big", "exactly 4 bytes"), (4, "little", "big-endian")],
)
def test_native_beacon_payload_patch_rejects_invalid_metadata(
    production_runtime, field_size: int, byte_order: str, message: str
) -> None:
    payload, manifest = _native_runtime_fixture(production_runtime)
    assert manifest.beacon_ipv4_patch is not None
    invalid = dataclasses.replace(
        manifest,
        beacon_ipv4_patch=dataclasses.replace(
            manifest.beacon_ipv4_patch,
            field_size=field_size,
            byte_order=byte_order,
        ),
    )

    with pytest.raises(Prime3DolPatchError, match=message):
        hardware_runtime.patch_native_beacon_ipv4(payload, invalid, IPv4Address("192.0.2.1"))


def test_packaged_native_beacon_patch_needs_no_toolchain(
    production_runtime, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload, manifest = _native_runtime_fixture(production_runtime)
    packaged = tmp_path.joinpath(
        "prime3_wii_runtime",
        hardware_runtime.Prime3HardwareRuntimeMode.NATIVE_WC24_BOOTSTRAP_BEACON_ONCE.value,
    )
    packaged.mkdir(parents=True)
    packaged.joinpath("payload.bin").write_bytes(payload)
    packaged.joinpath("payload.json").write_text(manifest.to_json_text(), encoding="utf-8")
    original_payload = packaged.joinpath("payload.bin").read_bytes()
    monkeypatch.setattr(hardware_runtime.randovania, "get_data_path", lambda: tmp_path)
    monkeypatch.setattr(
        hardware_runtime,
        "build_hardware_runtime_payload",
        lambda *_args, **_kwargs: pytest.fail("packaged export must not compile"),
    )

    patched, patched_manifest = hardware_runtime.load_or_build_hardware_runtime(
        tmp_path.joinpath("build"),
        hardware_runtime.Prime3HardwareRuntimeMode.NATIVE_WC24_BOOTSTRAP_BEACON_ONCE,
        beacon_ipv4=IPv4Address("198.51.100.9"),
    )

    assert packaged.joinpath("payload.bin").read_bytes() == original_payload
    assert patched != original_payload
    assert patched_manifest.relocated_runtime is not None
    assert patched_manifest.relocated_runtime.transport is not None
    assert patched_manifest.relocated_runtime.transport.udp_port == 43674
