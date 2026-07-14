# Prime 3 Wii Runtime Payload

This directory contains the source-backed Wii PowerPC payload and probe-delivery tooling used to validate the Prime 3 Wii runtime artifact path and entry bootstrap experiments.

Current scope:

- `payload.S` exports `payload_entry`
- direct payload builds support normal, probe, entry-bootstrap, and relocated-runtime proof modes
- `relocated_runtime.S` plus `relocated_runtime.c` build a separate high-MEM1 runtime blob for the relocation proof
- `build_probe_dol.py` and `verify_probe_delivery.py` support static DOL patch/verify runs for the generated payload artifacts
- `observe_probe.py` remains read-only and reports live payload/bootstrap state from Dolphin memory
- recurring poll hook installation is supported for the validated Wii NTSC retail DOL accessor at `0x800BB71C`
- the relocated runtime now includes a developer-only retail-wrapper IOS-open diagnostic path plus the bounded transport state machine scaffolding behind it
- no CP3W parser, mailbox, memory read/write surface, or normal exporter integration is included

Transport recon status:

- Skyward Sword source evidence now confirms that its Wii UDP support is a custom direct-IOS transport, not a libogc `net_*` call path
- the relevant provenance is documented in `docs/prime3_wii_skyward_sword_transport_recon.md`
- that transport still uses dynamic IOS-heap allocation, alarms, and an unbounded receive loop, so it was not a safe drop-in for the current Prime 3 bounded-poll runtime
- the earlier raw direct-submit `IOS_OpenAsync` experiment is no longer treated as functional
- the current Prime 3 runtime now calls Prime 3 NTSC's own retail IOS wrapper cluster, starting with verified `IOS_OpenAsync` at `0x80504668`
- the verified asynchronous ioctl wrapper is `0x80504FE0`; `0x80504A08` is asynchronous read and is not an ioctl target
- `--ios-nwc24-via-retail-ioctl-once` is a developer-only, terminal diagnostic mode: it opens `/dev/net/kd/request`, submits exactly command `6` through the retail ioctl veneer, records its callback, and performs no close or IP/socket operation
- `--ios-close-kd-once` is the next developer-only proof: after the successful NWC24 callback, it calls verified `close_async` at `0x805048A0` with `r3=fd`, `r4=callback`, and `r5=project-owned context`, then stops at `KD_CLOSED` without opening IP
- `--ios-open-ip-once` now selects the combined proof sequence `OPEN_KD -> NWC24_STARTUP -> CLOSE_KD -> OPEN_IP -> IP_OPEN`; it uses `/dev/net/ip/top`, records the `r3..r6` open arguments in runtime state, and stops at terminal `IP_OPEN` without issuing `SO_STARTUP`, `GET_HOST_ID`, socket creation, bind, receive, or send
- the retail-wrapper metadata is guarded to the NTSC `main.dol` SHA-256 `6b550f221602074747a2e61b0aa064203fd493f6865dfb3b1a912682065e6104`

## Supported local toolchain

This milestone validates the official devkitPro Wii toolchain installed through the devkitPro package repositories, with the following package set present locally:

- `devkitPPC r47.1-1`
- `libogc 2.13.0-1`
- `gamecube-tools 1.0.7-1`
- `wii-pkg-config 0.28-5`

The build logic requires `DEVKITPRO` and `DEVKITPPC` and validates the resolved compiler target and versions before compiling.

Official Wii ABI flags are taken from devkitPro's Wii rules and CMake support:

- `-DGEKKO`
- `-mrvl`
- `-mcpu=750`
- `-meabi`
- `-mhard-float`
- `-mbig-endian`

Because the initial payload is pure assembly, it does not rely on libc, libogc linking, constructors, exceptions, RTTI, TLS, or small-data sections.

## Build commands

From the repository root:

```powershell
python tools/prime3_wii_runtime/build_payload.py
```

Entry bootstrap and relocated-runtime proof modes require explicit mode flags plus reserved high-memory metadata:

```powershell
python tools/prime3_wii_runtime/build_payload.py --bootstrap-halt --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-copy-halt --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-return-halt --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-open-via-retail-wrapper-once --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-nwc24-once --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-nwc24-via-retail-ioctl-once --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-close-kd-once --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-open-ip-once --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
```

Artifacts are written to `build/prime3_wii_runtime/` or the requested `--output-dir`:

- `payload.o`
- `payload.elf`
- `payload.bin`
- `payload.map`
- `payload.json`

These outputs are build artifacts only and must not be committed.

Static DOL patch and verification helpers:

```powershell
python tools/prime3_wii_runtime/build_probe_dol.py --original-dol <main.dol> --output-dol <probe.dol> --payload-bin <payload.bin> --payload-manifest <payload.json> --report <probe-report.json> --payload-address 0x806843C0 --install-relocated-runtime
python tools/prime3_wii_runtime/verify_probe_delivery.py --original-dol <main.dol> --probe-dol <probe.dol> --extracted-final-dol <probe.dol> --payload-bin <payload.bin> --payload-manifest <payload.json> --report <verify-report.json> --payload-address 0x806843C0 --install-relocated-runtime
python tools/prime3_wii_runtime/build_probe_dol.py --original-dol <main.dol> --output-dol <probe.dol> --payload-bin <payload.bin> --payload-manifest <payload.json> --report <probe-report.json> --payload-address 0x806843C0 --install-recurring-poll-hook
python tools/prime3_wii_runtime/verify_probe_delivery.py --original-dol <main.dol> --probe-dol <probe.dol> --extracted-final-dol <probe.dol> --payload-bin <payload.bin> --payload-manifest <payload.json> --report <verify-report.json> --payload-address 0x806843C0 --install-recurring-poll-hook
```

Retail IOS wrapper recon helper:

```powershell
python tools/prime3_wii_runtime/analyze_ios_wrappers.py E:\ROMS\Corruption Extract\DATA\sys\main.dol
```

For the supported NTSC retail DOL, the analyzer fingerprint-validates and reports the complete operation `3..7` sequence: read, write, seek, ioctl, and vector ioctl in asynchronous and synchronous forms. The actual asynchronous ioctl wrapper is `0x80504FE0` with arguments in `r3..r10`; the former `0x80504A08` target is confirmed as five-argument asynchronous read. The analyzer also reports the `0x40`-byte lower request field map and compatible direct callers.

This classification is developer-only metadata. The only enabled ioctl consumer is the explicit terminal one-shot developer mode, which calls `0x80504FE0` with all eight register arguments and a project-owned persistent completion context. The retail dispatcher owns and frees its lower `0x40`-byte request; the relocated runtime never frees it.

The current `--ios-open-ip-once` proof was validated end to end against the rebuilt ISO launched in Dolphin. The live reports show `r3 = 0x817E3970` pointing to `/dev/net/ip/top\0`, `r4 = 0`, `r5 = 0x817E1B5C`, `r6 = 0x817E3A60`, target `0x80504668`, synchronous result `0`, one callback returning descriptor `11`, and stable terminal `IP_OPEN` with `kd_fd = -1`, `kd_closed = true`, `ip_fd = 11`, and zero `SO_STARTUP`, `GET_HOST_ID`, socket, bind, receive, or send submissions.

## Manifest contract

`payload.json` is deterministic for a fixed source state and records:

- schema version
- target architecture, endianness, and ABI
- compiler and linker identity/version
- payload hash and size
- required alignment
- entry symbol name and offset
- source digest
- protocol artifact version
- unresolved relocation count
- dynamic section count
- optional bootstrap metadata for entry-bootstrap and relocated-runtime modes
- optional relocated-runtime metadata for the compound low-bootstrap plus high-runtime proof artifact

The Python consumer side validates the manifest and raw payload before converting it into the typed `Prime3PayloadArtifact` used by the DOL patcher.
