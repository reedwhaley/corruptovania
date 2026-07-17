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
- `--ios-so-startup-once` now extends that developer-only sequence through `OPEN_KD -> NWC24_STARTUP -> CLOSE_KD -> OPEN_IP -> SO_STARTUP -> SO_STARTED`; it submits command `31` against the retained `/dev/net/ip/top` descriptor via `0x80504FE0`, records `r3..r10` plus callback/context evidence in runtime state, and stops terminally at `SO_STARTED` without issuing `GET_HOST_ID`, socket creation, bind, receive, or send
- `--ios-get-host-id-once` now extends that same developer-only sequence through `OPEN_KD -> NWC24_STARTUP -> CLOSE_KD -> OPEN_IP -> SO_STARTUP -> GET_HOST_ID -> HOST_ID_READY`; it submits command `16` against the retained `/dev/net/ip/top` descriptor via `0x80504FE0` with exact `NULL, 0, NULL, 0` request arguments, preserves the callback result as an unsigned 32-bit host ID when nonzero, and stops terminally at `HOST_ID_READY` without issuing socket creation, bind, receive, or send
- `--ios-create-socket-once` now extends that same developer-only sequence through `OPEN_KD -> NWC24_STARTUP -> CLOSE_KD -> OPEN_IP -> SO_STARTUP -> GET_HOST_ID -> CREATE_SOCKET -> SOCKET_READY`; it submits command `15` against the retained `/dev/net/ip/top` descriptor via `0x80504FE0` with a persistent `0x20`-aligned request object whose first 12 bytes are the signed big-endian values `2`, `2`, and `0`, accepts callback descriptor `0` as valid, and stops terminally at `SOCKET_READY` without issuing bind, receive, or send
- `--ios-bind-once` now extends that same developer-only sequence through `OPEN_KD -> NWC24_STARTUP -> CLOSE_KD -> OPEN_IP -> SO_STARTUP -> GET_HOST_ID -> CREATE_SOCKET -> BIND_SOCKET -> BOUND_NO_RECV`; it submits command `2` against the retained `/dev/net/ip/top` descriptor via `0x80504FE0` with exact live ABI `r3=ip_fd`, `r4=2`, `r5=<persistent 32-byte-aligned request>`, `r6=36`, `r7=0`, `r8=0`, `r9=<bind callback>`, and `r10=<bind context>`, requires synchronous result `0` plus callback result `0`, rejects positive callback results as anomalous, and schedules command `3` later-poll socket cleanup after bind failure instead of closing inside the bind callback
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
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-so-startup-once --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-get-host-id-once --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-create-socket-once --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-bind-once --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-recv-send-loop --ios-recv-send-loop-count 3 --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
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

The current `--ios-so-startup-once` proof was also validated end to end against the rebuilt ISO launched in Dolphin. The live reports show exact async ioctl call shape `r3 = 11`, `r4 = 31`, `r5 = 0`, `r6 = 0`, `r7 = 0`, `r8 = 0`, `r9 = 0x817E1C20`, and `r10 = 0x817E4080` at target `0x80504FE0`, with synchronous result `0`, one callback returning `0`, matching generation `5`, retained `ip_fd = 11`, `service_started = 1`, and stable terminal `SO_STARTED` with zero `GET_HOST_ID`, socket, bind, receive, or send submissions.

The current `--ios-get-host-id-once` proof was also validated end to end against the rebuilt ISO launched in Dolphin. The live reports show exact async ioctl call shape `r3 = 11`, `r4 = 16`, `r5 = 0`, `r6 = 0`, `r7 = 0`, `r8 = 0`, `r9 = 0x817E1C20`, and `r10 = 0x817E4080` at target `0x80504FE0`, with synchronous result `0`, one callback, matching generation `6`, preserved callback bits `0x1AD38AB6`, host-ID bytes `1A D3 8A B6`, dotted IPv4 `26.211.138.182`, retained `ip_fd = 11`, `service_started = 1`, and stable terminal `HOST_ID_READY` with zero socket, bind, receive, or send submissions. For this mode, callback result `0` means host ID unavailable; any nonzero 32-bit bit pattern is preserved exactly and is not rejected because its signed `s32` view could be negative.

The current `--ios-create-socket-once` proof was also validated end to end against the rebuilt ISO launched in Dolphin. The live reports show exact async ioctl call shape `r3 = 11`, `r4 = 15`, `r5 = 0x817E4AA0`, `r6 = 12`, `r7 = 0`, `r8 = 0`, `r9 = 0x817E1C20`, and `r10 = 0x817E4AC0` at target `0x80504FE0`, with synchronous result `0`, one callback, matching generation `7`, request bytes `00 00 00 02 00 00 00 02 00 00 00 00`, request storage size `32`, request alignment `32`, retained `ip_fd = 11`, retained `host_id = 0x1AD38AB6`, and stable terminal `SOCKET_READY` with `socket_fd = 0`, `descriptor_valid = 1`, `socket_ready = 1`, and zero bind, receive, or send submissions. For this mode, callback descriptors use signed socket semantics, so descriptor `0` is accepted as valid and negative callback results remain socket-creation errors.

The current `--ios-bind-once` proof reaches terminal `BOUND_NO_RECV` with no receive or send work. The verified 36-byte bind request for socket descriptor `0`, port `43674`, and `INADDR_ANY` is `00000000000000010802AA9A000000000000000000000000000000000000000000000000`; this keeps descriptor `0` at offset `0`, marker `1` at offset `4`, sockaddr length `8`, family `2`, and corrected port bytes `AA 9A` instead of the earlier incorrect `9A AA`. The current bind mode uses `INADDR_ANY` for Dolphin and Corruptovania interoperability, while a future physical-Wii fallback may need host-ID-based binding after the current bounded bind-once milestone. The observer intentionally reports `bound_no_recv` on the immediate terminal transition and `bound_no_recv_stable` once recurring polling continues across repeated reads. Cleanup-after-failure is covered by synthetic tests only; live proof so far covers successful bind with `socket_fd = 0`, `receive_count = 0`, and `send_count = 0`.

The current `--ios-recv-send-loop` proof extends that bounded sequence through `SUBMIT_RECEIVE_ONCE -> WAIT_RECEIVE -> SUBMIT_SEND_ONCE -> WAIT_SEND -> REARM_RECEIVE` until the configured exchange limit is reached, then stops terminally at `LOOP_COMPLETE`. `--ios-recv-send-loop-count` must be in the inclusive range `1..100`; the current live proof uses `3`. For count `3`, the expected stable terminal counters are `receive_submit_count = 3`, `receive_arm_count = 3`, `receive_rearm_count = 2`, `receive_count = 3`, `send_submit_count = 3`, `send_count = 3`, `completed_exchange_count = 3`, `loop_complete_transition_count = 1`, and no fourth receive or reply. Rearm occurs only from poll context after a successful non-final send; callbacks never submit IOS work, cleanup remains disabled, and one-shot recv-only or recv-send-once modes do not rearm.

`observe_probe.py` now supports `--poll-ms` with a default of `500` and a minimum of `10`. The report includes the first and second observation timestamps plus the loop transport counters when the manifest exports them. `--repeat-delay-ms` remains accepted as a compatibility alias for the same interval.

Live loop validation procedure:

1. Build the loop payload with `--ios-recv-send-loop --ios-recv-send-loop-count 3`.
2. Patch a copied CDV `main.dol` with `build_probe_dol.py --install-recurring-poll-hook --enable-ios-udp-diagnostic`.
3. Rebuild the ISO, round-trip extract it, and verify the patched DOL hash matches exactly.
4. Launch the rebuilt ISO in Dolphin and wait for transport phase `WAIT_RECEIVE`.
5. Send exactly three sequential host UDP payloads such as `P3_LOOP_TEST_01_20260717`, `P3_LOOP_TEST_02_20260717`, and `P3_LOOP_TEST_03_20260717`.
6. Verify three exact `P3_SENDTO_LOOP_REPLY_20260717` replies, terminal `LOOP_COMPLETE`, continued poll-count growth, and no fourth receive submission.

Known limitations:

- This remains a developer-only diagnostic transport path.
- CP3W packet parsing, mailbox integration, and general exporter/runtime gameplay integration are not implemented yet.
- Physical-Wii behavior is not proven by the current Dolphin-only loop milestone.

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
