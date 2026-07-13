# Prime 3 Wii Runtime Payload

This directory contains the source-backed Wii PowerPC payload and probe-delivery tooling used to validate the Prime 3 Wii runtime artifact path and entry bootstrap experiments.

Current scope:

- `payload.S` exports `payload_entry`
- direct payload builds support normal, probe, entry-bootstrap, and relocated-runtime proof modes
- `relocated_runtime.S` builds a separate high-MEM1 runtime blob for the relocation proof
- `build_probe_dol.py` and `verify_probe_delivery.py` support static DOL patch/verify runs for the generated payload artifacts
- `observe_probe.py` remains read-only and reports live payload/bootstrap state from Dolphin memory
- recurring poll hook installation is supported for the validated Wii NTSC retail DOL accessor at `0x800BB71C`
- no networking, IOS, or normal exporter integration is included

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
