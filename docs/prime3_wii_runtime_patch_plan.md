# Prime 3 Wii Runtime Patch Plan

## Current export and patch path

The current Prime 3 export path is split between Python orchestration and Gollop's bundled patcher assets:

- [`randovania/games/prime3/exporter/game_exporter.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/games/prime3/exporter/game_exporter.py:60) extracts the Wii disc image, optionally applies `main.hdiff` to `DATA/sys/main.dol` for the deflicker toggle, copies selected `.pak` files and `Standard.ntwk` into a temp workspace, runs `MP3Randomizer`, then repacks with `wit`.
- [`randovania/games/prime3/exporter/toolchain.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/games/prime3/exporter/toolchain.py:58) resolves only four helper families: `MP3Randomizer`, `hpatchz`, `wit`, and `nodtool`/Python `nod`.
- [`tools/prime3_patcher/MP3Randomizer/MP3Randomizer/MP3Randomizer.cs`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_patcher/MP3Randomizer/MP3Randomizer/MP3Randomizer.cs:48) builds `Patches`, modifies `.pak` files through `PAK.modify_pak`, and tweaks `Standard.ntwk` through [`NTWK.modify_ntwk`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_patcher/MP3Randomizer/MP3Randomizer/NTWK.cs:8).
- [`tools/prime3_patcher/MP3Randomizer/MP3Randomizer/Patches.cs`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_patcher/MP3Randomizer/MP3Randomizer/Patches.cs:268), [`GeneralPatches.cs`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_patcher/MP3Randomizer/MP3Randomizer/GeneralPatches.cs:5), and [`StartPatches.cs`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_patcher/MP3Randomizer/MP3Randomizer/StartPatches.cs:7) are all script-layer/object/property patch builders. They do not patch PowerPC instructions or `main.dol`.

## Proven findings

1. `main.dol` is currently modified only by `hpatchz` in the export pipeline, and only via the bundled binary diff file `MP3Update/main.hdiff`.
2. The C# Prime 3 patcher does not participate in `main.dol` patching. It only edits `.pak` resources and `Standard.ntwk`.
3. `open_prime_rando` participates only on the host/live-connection side for Corruption. [`randovania/game_connection/connector/corruption_remote_connector.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/game_connection/connector/corruption_remote_connector.py:44) imports `open_prime_rando.dol_patching`, but its Corruption write-path methods are still hard-disabled.
4. Version-specific Corruption DOL metadata is represented as `CorruptionDolVersion` dataclasses in the installed dependency [`open_prime_rando.dol_patching.corruption.dol_versions`](/C:/Users/Reed%20Whaley/AppData/Local/Programs/Python/Python312/Lib/site-packages/open_prime_rando/dol_patching/corruption/dol_versions.py:10). The repo currently knows about three builds: Wii NTSC, Wii PAL, and Wii NTSC-J.
5. No stable executable payload area is proven anywhere in this repository. I found no Corruption free-space map, no code-cave metadata, and no verified empty DOL section reservation for Prime 3.
6. No existing Corruption patch in this repo branches to injected PowerPC code. The existing Prime-family remote execution helper in installed `open_prime_rando` is generic, but Corruption lacks the hook metadata needed to use it.
7. Instruction-cache invalidation after runtime code writes is proven necessary by existing installed helper code. [`open_prime_rando.dol_patching.all_prime_dol_patches.remote_execution_patch_start`](/C:/Users/Reed%20Whaley/AppData/Local/Programs/Python/Python312/Lib/site-packages/open_prime_rando/dol_patching/all_prime_dol_patches.py:104) explicitly emits `icbi`, `sync`, and `isync` after externally overwriting instructions. I found no equally proven Corruption-specific data-cache flush sequence in the current workspace, so D-cache handling remains unresolved.
8. The first supported target should be Wii NTSC. It is the first Corruption version in `ALL_VERSIONS`, the live-connection tests already use it, and bundled patcher assets explicitly reference `RM3E01`.
9. The hook that would service networking often enough without blocking gameplay is not proven. `open_prime_rando` expects a version-defined `string_display.update_hint_state` hook for live remote execution, but all Corruption versions currently set `string_display = None`.
10. No Wii IOS socket, thread, or cache-management imports are present in the repo. Searches for `OSCreateThread`, `socket`, `net_*`, `IOS_*`, `libogc`, `devkitPPC`, and related symbols did not find a supported Wii runtime implementation.
11. The repository does not contain an established PowerPC C, C++, Rust, or assembly payload build chain for Prime 3 Wii. The only PPC-capable tooling present is Python-side `ppc_asm`, which can assemble instruction bytes and edit DOLs, not compile a standalone Wii runtime.
12. Shipping a compiled Wii payload through the current pipeline is therefore still a design task. The only proven insertion mechanisms today are `hpatchz` binary diffs and Python-side `DolEditor`/`ppc_asm` patching used by other Prime-family code.

## Selected protocol source of truth

Because no supported Wii payload language or compiler is present, the safest shared definition is a language-neutral manifest plus deterministic generators:

- [`randovania/game_connection/executor/prime3_wii_protocol.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/game_connection/executor/prime3_wii_protocol.py:1) remains the authoritative behavior.
- [`randovania/game_connection/executor/prime3_wii_protocol_artifacts.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/game_connection/executor/prime3_wii_protocol_artifacts.py:1) generates:
  - a JSON-friendly protocol manifest containing magic, enum values, packet layout, byte order, CRC coverage, and payload layouts
  - deterministic packet vectors with exact encoded hexadecimal
- [`tools/generate_prime3_wii_protocol_artifacts.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/generate_prime3_wii_protocol_artifacts.py:1) is the regeneration entrypoint for future runtime build tooling on Windows, macOS, or Linux.

This avoids maintaining a second handwritten constant table before the runtime language decision is made.

## Runtime payload language and build requirements

No runtime payload language is selected for implementation in this milestone because the repository does not prove one.

- Proven available host tools:
  - Python 3.12
  - installed `open_prime_rando`
  - installed `ppc_asm`
  - C#/.NET tooling for `MP3Randomizer`
- Missing proof:
  - no `devkitPPC` or equivalent Wii SDK/toolchain configuration
  - no `libogc` integration
  - no Wii-target cargo target or linker script
  - no existing Prime 3 runtime object format or binary blob pipeline

As a result, there is no safe host-testable Wii runtime core to add yet without inventing a dead-end toolchain.

## Payload binary format and DOL insertion design

The future payload path should use metadata-driven DOL patching rather than a raw binary diff:

- define version metadata for:
  - hook address
  - hook instruction overwrite size
  - payload load address
  - payload maximum size
  - cache-flush requirements
- produce payload bytes from the eventual chosen Wii toolchain
- embed the payload from Python during export, either by:
  - writing a verified new DOL section with `DolEditor.add_section`, or
  - writing into a separately verified free/executable region
- patch the verified hook site with a deterministic branch into the payload

That design is intentionally not implemented here because neither the hook nor the payload region is currently proven for Corruption.

## Hook, payload region, and threading status

- Verified hook point: none for Corruption.
- Verified payload region: none for Corruption.
- Existing periodic or per-frame hook evidence:
  - only indirect evidence via `open_prime_rando`'s generic `update_hint_state` remote-execution hook model
  - Corruption does not currently expose that metadata
- Separate OS thread creation: unresolved and unsupported by current repo evidence.

Without verified hook metadata, even a synthetic DOL branch proof would require fabricated addresses. This milestone stops short of that.

## Networking behavior target

The already-implemented host protocol establishes the intended runtime contract:

- UDP port: `43674`
- commands: `HELLO`, `READ_MEMORY`, `PING`, `DISCONNECT`, `RESERVED_MAILBOX`
- no arbitrary writes
- range policy currently enforced by the host executor: `0x80000000` through `0x81800000`
- request-ID echo and CRC32 framing already defined

Future runtime expectations:

- initialize LAN-only UDP socket state during runtime startup
- keep socket ownership in the runtime payload, not the game logic
- use non-blocking receive/send behavior on the game thread unless a safe worker-thread model is later proven
- reject malformed packets before any memory dereference
- reset session state on `DISCONNECT`
- allow reconnects without restarting the game

## On-screen status and startup behavior

On-screen IP display is unresolved. The natural mechanism in the existing Prime-family live patch system would be HUD-string injection, but Corruption currently lacks verified `string_display` hook metadata.

Startup failure behavior should therefore be conservative:

- if socket or IOS init fails, remain inert and readable
- do not crash gameplay
- expose failure only through a future verified HUD/debug path

## Cross-platform build and packaging expectations

Windows, macOS, and Linux can all generate the protocol manifest/vectors now because the generator is pure Python.

They cannot yet build a Wii runtime payload from this repository because the required Wii-native compiler/linker stack is not present or documented.

## Licensing and provenance

No external Wii networking code was copied in this milestone. Any future adoption of external runtime code needs:

- license review
- provenance recording
- attribution if required
- explicit justification for adapting it into this repository

## Remaining blockers before IOS UDP runtime work

1. Corruption-specific verified hook metadata is missing.
2. Corruption-specific verified executable/free payload region metadata is missing.
3. No established Wii runtime compiler/linker toolchain exists in the repo.
4. No proven Corruption symbol/import map exists for IOS sockets, threading, memory barriers, or cache helpers.
5. Corruption HUD string-display hook metadata is missing, which blocks reuse of the existing remote execution model.
