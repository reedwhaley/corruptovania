from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from randovania.games.prime3.exporter.runtime_payload import Prime3RuntimePayloadManifest


def _load_module():
    module_path = Path(__file__).resolve().parents[2].joinpath("tools", "prime3_wii_runtime", "observe_probe.py")
    spec = importlib.util.spec_from_file_location("prime3_wii_runtime_observe_probe_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeBackend:
    def __init__(self, memory: dict[int, bytes], *, hooked: bool = True, hook_success: bool = True):
        self.memory = memory
        self._hooked = hooked
        self._hook_success = hook_success

    def is_hooked(self) -> bool:
        return self._hooked

    def hook(self) -> None:
        self._hooked = self._hook_success

    def un_hook(self) -> None:
        self._hooked = False

    def read_bytes(self, address: int, size: int) -> bytes:
        data = self.memory.get(address, b"")
        return data[:size]


def _manifest(payload_bytes: bytes) -> Prime3RuntimePayloadManifest:
    return Prime3RuntimePayloadManifest(
        schema_version=1,
        target_architecture="powerpc",
        target_endianness="big",
        target_abi="eabi",
        compiler_identity="synthetic",
        compiler_version="1.0",
        linker_identity="synthetic",
        linker_version="1.0",
        payload_sha256=__import__("hashlib").sha256(payload_bytes).hexdigest(),
        payload_size=len(payload_bytes),
        required_alignment=0x20,
        entry_symbol_name="payload_entry",
        entry_symbol_offset=0,
        source_digest="deadbeef",
        protocol_artifact_version=1,
        unresolved_relocation_count=0,
        dynamic_section_count=0,
        canary_start_offset=0x10,
        canary_size=0x10,
        counter_offset=0x20,
        counter_size=4,
    )


def _config(module, payload_address: int = 0x817F0000, startup_word: int = 0x38000000):
    payload_bytes = b"\x00" * 0x10 + b"CANARY-CANARY-16" + b"\x00" * 0x10 + b"\x00\x00\x00\x00"
    return module.ProbeObservationConfig(
        expected_game_id=b"RM3E01",
        payload_address=payload_address,
        payload_bytes=payload_bytes,
        manifest=_manifest(payload_bytes),
        startup_words=(module.StartupWordExpectation(address=0x8000633C, expected_word=startup_word),),
    )


def _memory_for_config(module, config, *, startup_word: int = 0x38000000, short_payload: bool = False):
    payload_bytes = config.payload_bytes[:-1] if short_payload else config.payload_bytes
    return {
        module.GAME_ID_ADDRESS: b"RM3E01",
        0x8000633C: startup_word.to_bytes(4, "big"),
        config.payload_address: payload_bytes,
        module.BOOT_INFO_POINTER_ADDRESS: (0x817FC3A0).to_bytes(4, "big"),
        0x80000034: (0x817FEC60).to_bytes(4, "big"),
        0x80003110: (0x81800000).to_bytes(4, "big"),
        0x817FC3A8: (0).to_bytes(4, "big"),
    }


def test_observe_probe_reads_complete_payload() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend(_memory_for_config(module, config))

    result = module.observe_probe_memory(backend, config)

    assert result["payload_matches_expected"] is True
    assert result["counter"]["value"] == 0


def test_observe_probe_reports_wrong_startup_word() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend(_memory_for_config(module, config, startup_word=0x60000000))

    result = module.observe_probe_memory(backend, config)

    assert result["startup_words"]["0x8000633C"]["matches"] is False


def test_observe_probe_rejects_short_payload_read() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend(_memory_for_config(module, config, short_payload=True))

    with pytest.raises(module.ProbeObservationError, match="Short read for payload bytes"):
        module.observe_probe_memory(backend, config)


def test_observe_probe_reports_canary_match() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend(_memory_for_config(module, config))

    result = module.observe_probe_memory(backend, config)

    assert result["canary"]["matches_expected"] is True


def test_observe_probe_reports_canary_mismatch() -> None:
    module = _load_module()
    config = _config(module)
    memory = _memory_for_config(module, config)
    corrupted = bytearray(config.payload_bytes)
    corrupted[0x10] ^= 0x01
    memory[config.payload_address] = bytes(corrupted)
    backend = FakeBackend(memory)

    result = module.observe_probe_memory(backend, config)

    assert result["canary"]["matches_expected"] is False


def test_observe_probe_rejects_wrong_game_build() -> None:
    module = _load_module()
    config = _config(module)
    memory = _memory_for_config(module, config)
    memory[module.GAME_ID_ADDRESS] = b"RM3P01"
    backend = FakeBackend(memory)

    with pytest.raises(module.ProbeObservationError, match="Unexpected game ID"):
        module.observe_probe_memory(backend, config)


def test_observe_probe_rejects_disconnected_emulator() -> None:
    module = _load_module()
    config = _config(module)
    backend = FakeBackend({}, hooked=False, hook_success=False)

    with pytest.raises(module.ProbeObservationError, match="Unable to connect to Dolphin"):
        module.observe_probe_memory(backend, config)


def test_observe_probe_module_exposes_no_write_api() -> None:
    module = _load_module()

    assert not hasattr(module, "write_bytes")


def test_observe_probe_cli_writes_json_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    config = _config(module)
    payload_path = tmp_path.joinpath("payload.bin")
    manifest_path = tmp_path.joinpath("payload.json")
    report_path = tmp_path.joinpath("report.json")
    payload_path.write_bytes(config.payload_bytes)
    manifest_path.write_text(config.manifest.to_json_text(), encoding="utf-8")
    monkeypatch.setattr(module, "dolphin_memory_engine", FakeBackend(_memory_for_config(module, config)))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "observe_probe.py",
            "--payload-address",
            hex(config.payload_address),
            "--payload-bin",
            str(payload_path),
            "--payload-manifest",
            str(manifest_path),
            "--report",
            str(report_path),
            "--startup-word",
            "0x8000633C=0x38000000",
        ],
    )

    module.main()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["payload_matches_expected"] is True
