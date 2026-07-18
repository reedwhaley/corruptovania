# MP3 Networking/CDV Wii and Wii U Hardware Integration

Date: 2026-07-18

## Repository Discovery

| Role | Path | Branch | HEAD | Remotes | Initial status |
| --- | --- | --- | --- | --- | --- |
| Active target | `C:\Users\Reed Whaley\Documents\MP3 Networking` | `prime3-wii-networking` | `142667253071376ae468ed40f24e11b166cd2980` | `origin=https://github.com/reedwhaley/corruptovania.git` | clean, tracking origin |
| Read-only reference | `C:\Users\Reed Whaley\Documents\CDV MacOS PR` | `prime3-wii-networking` | `16ac9d5177f5c1e80312f622e92607fc1a871dee` | same origin plus `upstream=https://github.com/Schwork-Corruption/corruptovania.git` | clean, ahead 2 |

The reference checkout remained at the same HEAD and status and was not modified.

## Architecture and Implementation

The active repository already owned the canonical CP3W protocol, DOL profile tables, guarded patch primitives,
relocated runtime, runtime builder, Prime 3 exporter, and shared Prime inventory conversion. The old checkout was
reviewed only for the completed host connection lifecycle.

Ported and reconciled behavior:

- Fixed remote UDP port 43674, validated console IPv4 input, ephemeral local bind, and IP-only persistence.
- HELLO, capability negotiation, GET_GAME_IDENTITY, and GET_INVENTORY with request IDs and serialized requests.
- Retries, bounded reconnect backoff, endpoint filtering, bounded response queue, runtime restart detection,
  duplicate/unexpected/malformed packet diagnostics, sequence gap/reset/wrap handling, transient unavailability, and
  clean disconnect.
- Wii/Wii U choice, connection status, diagnostic presentation, and read-only UI gating.
- Fake runtime/server, loopback, builder, inventory, reconnect, and integration coverage.

Active-architecture work:

- Removed generic READ_MEMORY from client capabilities and reject all arbitrary reads/writes.
- Kept the existing Prime connector's `_inventory_from_raw_values` conversion as the single semantic conversion path,
  including Suit Type behavior.
- Added canonical runtime mode 22, `cp3w_inventory_service`. It reuses the proven mode-21 handlers but is unbounded
  and rearms receive continuously.
- Fixed runtime DISCONNECT handling to clear negotiation and rearm without replying to a socket the synchronous host
  API has already closed.
- Added `hardware_runtime.py` as orchestration around existing builders/patchers, not a second patcher.
- Normal Prime 3 export now always installs and validates CP3W after DOL gameplay/deflicker changes and before ISO/WBFS
  output. The legacy preset field remains readable but cannot disable installation.
- PyInstaller builds and bundles `payload.bin` and `payload.json` at package-build time; generated binaries are not
  tracked.

## Patching and Validation

Supported profile: Prime 3 Corruption Wii NTSC-U revision 3.436 (`Wii NTSC`).

Automatic integration:

1. Identify the supported executable before changing bytes.
2. Build or load the canonical relocated service payload.
3. Patch the layout UUID through the canonical build-string profile.
4. Append one executable text section at `0x806843C0`.
5. Install the guarded entry hook to `0x806843C0`.
6. Install the guarded recurring hook at `0x800BB71C` to wrapper `0x817E1008`.
7. Validate profile, payload/runtime hashes, section size, both branch targets, mode 22, UDP 43674, identity and
   inventory metadata, one runtime occurrence, and absence of partial installation.
8. Atomically replace `main.dol` only after validation succeeds.

Final signatures:

- Payload SHA-256: `766562914b7e590c5925353022a9da26f1ce85b9bc76705bb8b4729ffbb37e3b`
- Embedded runtime SHA-256: `b9ac5c35a6adb50a3db8f80ffc24e96fee6a0f42eb0f41a71805b57617cc171c`
- Patched DOL SHA-256: `54247a49ca73d12871aafa3199aeffc6677986208aff9299139a2c0e7ae6b8f0`

Already or partially patched inputs fail clearly before any atomic replacement; duplicate runtime/hook installation is
not attempted.

## Software and Dolphin Validation

Two independent production builds produced byte-identical `payload.elf`, `payload.bin`, `payload.json`, and
patched DOL files:

- ELF: `8a5d652afe3ec7d084ad984be40b9f39e4048d26002dcad213128525a6d1a075`
- BIN: `766562914b7e590c5925353022a9da26f1ce85b9bc76705bb8b4729ffbb37e3b`
- JSON: `7d06c5614b14352d279d4e94b1d8b76be7f17b06a5f95c44c5d16c561f8a64c2`

Isolated container outputs:

- ISO: `E:\MP3 Networking Hardware Validation 20260718\MP3-CP3W-Hardware-Validation.iso`
  SHA-256 `b3e43cb00d3c6ea772bb2c5cb1e238a3ee372d566c96d7c18cdc5a23b552e6bc`
- WBFS: `E:\MP3 Networking Hardware Validation 20260718\MP3-CP3W-Hardware-Validation.wbfs`
  SHA-256 `3a068b47e07efafa6e8b740b03e1e1aabe53fc04c667fd45abf66759cc94cf6e`

`wit VERIFY` accepted both as encrypted RM3E01 DATA partitions. Extracting `sys/main.dol` from each reproduced the
final DOL hash exactly. The real-DOL proof used the normal integration API; exporter tests prove the normal GUI/CLI
export path invokes it regardless of the legacy flag. The isolated ISO/WBFS proof reused the exporter's exact
`wit COPY` command over an extracted tree rather than running a new randomizer seed through the external randomizer.

Dolphin 2603a booted the generated ISO in an isolated user directory. Live validation observed:

- HELLO success on the first ready attempt with only negotiation, ping, structured error, deterministic session,
  GAME_IDENTITY, and INVENTORY_STATE capabilities.
- GET_GAME_IDENTITY: NTSC_U, WII_NTSC_3_436, profile `0x50334E41`, fingerprint `0x67B00CE6`, build
  `0x50335731`, mode 22.
- GET_INVENTORY: available, 59 records, consecutive sequences.
- Two sessions after DISCONNECT succeeded with sequences 1 through 6, proving receive rearming and reconnect.
- Live Dolphin and CP3W connector inventories were exactly equal for all 59 items; Suit Type matched.
- No crash occurred during the observed boot/title and protocol polling interval.

Load-game and room-transition interaction were not automated in this isolated run. Dolphin was terminated by the test
harness, so graceful in-game shutdown is not claimed.

## Tests and Static Checks

- Focused connection/export/runtime integration: 53 passed.
- Broader relevant suites: 590 passed in 39.79 seconds.
- Ruff on changed Python: passed.
- Ruff formatting on changed Python: passed.
- `py_compile` on changed Python and `randovania.spec`: passed.
- Targeted mypy for `hardware_runtime.py`: passed.
- Configured repository-wide mypy: not clean; 74 pre-existing/environment errors remain, primarily missing generated
  UI modules/stubs and existing protocol typing errors. The only new-file mypy finding was fixed.
- `git diff --check`: passed.
- JSON report parse: passed after report creation.

## Hardware Readiness and Limits

The ISO and WBFS are structurally ready for original Wii and Wii U vWii launch, using the normal RM3E01 filesystem and
fixed CP3W UDP port 43674. Expected CDV setting: **Wii / Wii U (Prime 3)** plus the console IPv4 address only. Expected
behavior is identity validation followed by read-only inventory polling.

No physical Wii or Wii U was available, so physical boot, IOS/network differences, controller-driven load/transition,
and console shutdown remain unvalidated. No inventory writes, item grants, location tracking, generic memory reads, or
generic memory writes were added.

No commit was created and nothing was pushed.
