# -*- mode: python -*-
import os
import platform
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

import randovania
from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime3.exporter.hardware_runtime import (
    PRODUCTION_RUNTIME_ASSET_DIR,
    load_validated_production_runtime_assets,
)

block_cipher = None

icon_path = "randovania/data/icons/executable_icon.ico"

pickup_databases = [
    (f"randovania/games/{game.value}/pickup_database", f"games/{game.value}/pickup_database") for game in RandovaniaGame
]
presets = [(f"randovania/games/{game.value}/presets", f"games/{game.value}/presets") for game in RandovaniaGame]
game_assets = [
    (f"randovania/games/{game.value}/assets", f"games/{game.value}/assets")
    for game in RandovaniaGame
    if game.data_path.joinpath("assets").exists()
]


def collect_prime3_runtime_assets():
    assets = load_validated_production_runtime_assets(Path(PRODUCTION_RUNTIME_ASSET_DIR), require_elf=True)
    destination = Path("data/prime3_wii_runtime")
    assert assets.elf_path is not None
    return [
        (os.fspath(assets.payload_path), os.fspath(destination)),
        (os.fspath(assets.manifest_path), os.fspath(destination)),
        (os.fspath(assets.elf_path), os.fspath(destination)),
    ]


def collect_prime3_macos_assets():
    datas = []
    binaries = []
    macos_root = Path("randovania/data/gollop_mp3_patcher/macos")
    if not macos_root.exists():
        return datas, binaries

    for source_path in macos_root.rglob("*"):
        if not source_path.is_file():
            continue

        relative_path = source_path.relative_to(macos_root)
        destination = Path("data/gollop_mp3_patcher/macos").joinpath(relative_path)
        entry = (os.fspath(source_path), os.fspath(destination.parent))

        # Split .NET runtimes are installed into the finished app manually.
        # Passing their Mach-O files through Analysis causes PyInstaller to
        # classify and relocate them into Contents/Frameworks.
        is_dotnet_runtime_file = (
            bool(relative_path.parts)
            and relative_path.parts[0] in {"dotnet-x64", "dotnet-arm64"}
        )

        if is_dotnet_runtime_file:
            continue

        if source_path.suffix == ".dylib" or os.access(source_path, os.X_OK):
            binaries.append(entry)
        else:
            datas.append(entry)

    return datas, binaries


prime3_common_datas = [
    ("randovania/data/gollop_mp3_patcher/MP3Update", "data/gollop_mp3_patcher/MP3Update"),
    ("randovania/data/gollop_mp3_patcher/dummy_attract", "data/gollop_mp3_patcher/dummy_attract"),
    ("randovania/data/gollop_mp3_patcher/CHANGELOG.txt", "data/gollop_mp3_patcher"),
    ("randovania/data/gollop_mp3_patcher/LICENSE", "data/gollop_mp3_patcher"),
    ("randovania/data/gollop_mp3_patcher/LICENSE.txt", "data/gollop_mp3_patcher"),
    ("randovania/data/gollop_mp3_patcher/MIT-LICENSE.txt", "data/gollop_mp3_patcher"),
    ("randovania/data/gollop_mp3_patcher/README.md", "data/gollop_mp3_patcher"),
    ("randovania/data/gollop_mp3_patcher/README.txt", "data/gollop_mp3_patcher"),
    ("randovania/data/gollop_mp3_patcher/lzokay/LICENSE", "data/gollop_mp3_patcher/lzokay"),
    ("randovania/data/gollop_mp3_patcher/nodtool/LICENSE", "data/gollop_mp3_patcher/nodtool"),
]
prime3_macos_datas, prime3_macos_binaries = collect_prime3_macos_assets()
prime3_runtime_datas = collect_prime3_runtime_assets()

datas = [
    ("randovania/data/configuration.json", "data/"),
    ("randovania/data/binary_data", "data/binary_data"),
    ("randovania/data/gui_assets", "data/gui_assets"),
    ("randovania/data/icons", "data/icons"),
    ("randovania/data/nintendont", "data/nintendont"),
    ("randovania/data/dotnet_runtime", "data/dotnet_runtime"),
    *pickup_databases,
    *presets,
    *game_assets,
    *prime3_runtime_datas,
    ("README.md", "data/"),
]
if platform.system() != "Darwin":
    datas.append(("randovania/data/gollop_mp3_patcher", "data/gollop_mp3_patcher"))
else:
    datas += prime3_common_datas
    datas += prime3_macos_datas
if platform.system() != "Darwin":
    datas.append(("randovania/data/ClarisPrimeRandomizer", "data/ClarisPrimeRandomizer"))

datas += copy_metadata("randovania", recursive=True)
if platform.system() == "Linux":
    linux_datas = [("randovania/data/xdg_assets", "xdg_assets")]
    datas += linux_datas


a = Analysis(
    ["randovania/__main__.py", "randovania/cli/__init__.py"],
    pathex=[],
    binaries=prime3_macos_binaries if platform.system() == "Darwin" else [],
    datas=datas,
    hiddenimports=[
        "randovania.game_connection.connector.corruption_remote_connector",
        "randovania.game_connection.connector.echoes_remote_connector",
        "randovania.game_connection.connector.prime1_remote_connector",
        "randovania.game_connection.executor.prime3_wii_protocol_artifacts",
        "randovania.game_connection.executor.prime3_wii_runtime_diagnostics",
        "randovania.lib.checkpoint_report_analysis",
        "open_prime_rando.dol_patching.prime1.dol_versions",
        "unittest.mock",
    ],
    hookspath=[
        # https://github.com/pyinstaller/pyinstaller/issues/4040
        "tools/additional-pyinstaller-hooks",
    ],
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "randovania.server",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)


pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="corruptovania",
    debug=False,
    strip=False,
    upx=False,
    icon=icon_path,
    console=True,
    target_arch="universal2" if platform.system() == "Darwin" else None,
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name="corruptovania")
app = BUNDLE(
    coll,
    name="Corruptovania.app",
    icon="tools/rdv_logo.icns",
    bundle_identifier="run.metroidprime.randovania",
    info_plist={
        "LSBackgroundOnly": False,
        "CFBundleShortVersionString": randovania.VERSION,
    },
)

