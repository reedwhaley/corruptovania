from __future__ import annotations

from pathlib import Path

import pytest

from randovania.games.prime3.exporter import runtime_toolchain
from randovania.games.prime3.exporter.dol_patcher import Prime3DolPatchError


def _make_devkit_tree(
    tmp_path: Path,
    *,
    executable_suffix: str = ".exe",
    installed_ini: bool = True,
) -> tuple[Path, Path]:
    devkitpro = tmp_path.joinpath("devkitPro")
    devkitppc = devkitpro.joinpath("devkitPPC")
    devkitppc.joinpath("bin").mkdir(parents=True)
    if installed_ini:
        devkitpro.joinpath("installed.ini").write_text("[WiiDev]\nEnabled=1\n", encoding="utf-8")
    for name in (
        "powerpc-eabi-gcc",
        "powerpc-eabi-ld",
        "powerpc-eabi-objcopy",
        "powerpc-eabi-readelf",
        "powerpc-eabi-objdump",
    ):
        devkitppc.joinpath("bin", f"{name}{executable_suffix}").write_text("", encoding="utf-8")
    return devkitpro, devkitppc


def test_resolve_prime3_runtime_toolchain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    devkitpro, devkitppc = _make_devkit_tree(tmp_path)
    commands = {
        str(devkitppc.joinpath("bin", "powerpc-eabi-gcc.exe")) + " -dumpmachine": "powerpc-eabi",
        str(devkitppc.joinpath("bin", "powerpc-eabi-gcc.exe")) + " --version": (
            "powerpc-eabi-gcc.exe (devkitPPC release 47.1) 15.1.0\n"
        ),
        str(devkitppc.joinpath("bin", "powerpc-eabi-ld.exe")) + " --version": "GNU ld (GNU Binutils) 2.44\n",
        str(devkitppc.joinpath("bin", "powerpc-eabi-objcopy.exe")) + " --version": "GNU objcopy (GNU Binutils) 2.44\n",
        str(devkitppc.joinpath("bin", "powerpc-eabi-readelf.exe")) + " --version": "GNU readelf (GNU Binutils) 2.44\n",
        str(devkitppc.joinpath("bin", "powerpc-eabi-objdump.exe")) + " --version": "GNU objdump (GNU Binutils) 2.44\n",
    }

    monkeypatch.setattr(
        runtime_toolchain,
        "_run_tool",
        lambda command: commands[" ".join(command)],
    )

    toolchain = runtime_toolchain.resolve_prime3_runtime_toolchain(
        {
            "DEVKITPRO": str(devkitpro),
            "DEVKITPPC": str(devkitppc),
        }
    )

    assert toolchain.target_triple == "powerpc-eabi"
    assert toolchain.devkitppc_release == "47.1"
    assert toolchain.compiler_version == "15.1.0"
    assert toolchain.binutils_version == "2.44"
    assert toolchain.required_machine_flags == runtime_toolchain.REQUIRED_MACHINE_FLAGS


def test_resolve_prime3_runtime_toolchain_from_pacman_layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    devkitpro, devkitppc = _make_devkit_tree(tmp_path, executable_suffix="", installed_ini=False)
    monkeypatch.setattr(runtime_toolchain.platform, "system", lambda: "Linux")

    def fake_run(command: list[str]) -> str:
        if command[-1] == "-dumpmachine":
            return "powerpc-eabi"
        if command[0].endswith("powerpc-eabi-gcc"):
            return "powerpc-eabi-gcc (devkitPPC release 47.1) 15.1.0"
        tool_name = Path(command[0]).name.split("-")[-1]
        return f"GNU {tool_name} (GNU Binutils) 2.44"

    monkeypatch.setattr(runtime_toolchain, "_run_tool", fake_run)
    toolchain = runtime_toolchain.resolve_prime3_runtime_toolchain(
        {"DEVKITPRO": str(devkitpro), "DEVKITPPC": str(devkitppc)}
    )

    assert toolchain.compiler_path.name == "powerpc-eabi-gcc"
    assert toolchain.devkitppc_release == "47.1"


def test_resolve_prime3_runtime_toolchain_requires_compiler(tmp_path: Path) -> None:
    devkitpro, devkitppc = _make_devkit_tree(tmp_path)
    devkitppc.joinpath("bin", "powerpc-eabi-gcc.exe").unlink()

    with pytest.raises(Prime3DolPatchError, match="Missing powerpc-eabi-gcc"):
        runtime_toolchain.resolve_prime3_runtime_toolchain(
            {
                "DEVKITPRO": str(devkitpro),
                "DEVKITPPC": str(devkitppc),
            }
        )


def test_resolve_prime3_runtime_toolchain_rejects_wrong_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    devkitpro, devkitppc = _make_devkit_tree(tmp_path)

    def fake_run(command: list[str]) -> str:
        if command[-1] == "-dumpmachine":
            return "powerpc-linux-gnu"
        return "powerpc-eabi-gcc.exe (devkitPPC release 47.1) 15.1.0"

    monkeypatch.setattr(runtime_toolchain, "_run_tool", fake_run)

    with pytest.raises(Prime3DolPatchError, match="Unsupported powerpc-eabi-gcc target"):
        runtime_toolchain.resolve_prime3_runtime_toolchain(
            {
                "DEVKITPRO": str(devkitpro),
                "DEVKITPPC": str(devkitppc),
            }
        )


def test_resolve_prime3_runtime_toolchain_rejects_unsupported_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    devkitpro, devkitppc = _make_devkit_tree(tmp_path)

    def fake_run(command: list[str]) -> str:
        if command[-1] == "-dumpmachine":
            return "powerpc-eabi"
        if command[0].endswith("powerpc-eabi-gcc.exe"):
            return "powerpc-eabi-gcc.exe (devkitPPC release 48.0) 15.1.0"
        tool_name = Path(command[0]).stem.removesuffix(".exe").split("-")[-1]
        return f"GNU {tool_name} (GNU Binutils) 2.44"

    monkeypatch.setattr(runtime_toolchain, "_run_tool", fake_run)

    with pytest.raises(Prime3DolPatchError, match="Unsupported devkitPPC release 48.0"):
        runtime_toolchain.resolve_prime3_runtime_toolchain(
            {
                "DEVKITPRO": str(devkitpro),
                "DEVKITPPC": str(devkitppc),
            }
        )


def test_resolve_prime3_runtime_toolchain_rejects_malformed_version_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    devkitpro, devkitppc = _make_devkit_tree(tmp_path)

    def fake_run(command: list[str]) -> str:
        if command[-1] == "-dumpmachine":
            return "powerpc-eabi"
        if command[0].endswith("powerpc-eabi-gcc.exe"):
            return "gcc without expected release line"
        return "GNU ld (GNU Binutils) 2.44"

    monkeypatch.setattr(runtime_toolchain, "_run_tool", fake_run)

    with pytest.raises(Prime3DolPatchError, match="Unable to parse powerpc-eabi-gcc version output"):
        runtime_toolchain.resolve_prime3_runtime_toolchain(
            {
                "DEVKITPRO": str(devkitpro),
                "DEVKITPPC": str(devkitppc),
            }
        )
