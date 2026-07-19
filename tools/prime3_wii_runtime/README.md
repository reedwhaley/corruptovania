# Prime 3 Wii Runtime Payload

This directory contains the canonical source-backed Wii PowerPC CP3W payload used by normal Prime 3 exports and by developer probe-delivery tooling.

Current scope:

- `payload.S` exports `payload_entry`
- direct payload builds support normal, probe, entry-bootstrap, and relocated-runtime proof modes
- `relocated_runtime.S` plus `relocated_runtime.c` build a separate high-MEM1 runtime blob for the relocation proof
- `build_probe_dol.py` and `verify_probe_delivery.py` support static DOL patch/verify runs for the generated payload artifacts
- `observe_probe.py` remains read-only and reports live payload/bootstrap state from Dolphin memory
- recurring poll hook installation is supported for the validated Wii NTSC retail DOL accessor at `0x800BB71C`
- the relocated runtime includes bounded developer diagnostics plus unbounded production mode `cp3w_inventory_service`
- production mode implements HELLO, capability negotiation, `GET_GAME_IDENTITY`, and read-only `GET_INVENTORY` on fixed UDP port 43674
- normal Prime 3 export builds or loads this canonical artifact, installs both guarded hooks, and validates the finished DOL
- no inventory writes, grants, location tracking, or arbitrary memory read/write surface is included
- production networking has delayed startup, persistent retry/socket recovery, post-bind endpoint verification, and a fixed `CP3D` diagnostic/control block

Hardware diagnostics, state values, control offsets, probe usage, and the validation sequence are documented in `docs/prime3_wii_hardware_network_validation.md`.

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
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-cp3w-frame-validation --ios-cp3w-frame-validation-count 6 --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-cp3w-ping-pong --ios-cp3w-ping-pong-count 8 --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-recurring-hook-diagnostics --enable-ios-udp-diagnostic --ios-cp3w-hello-session --ios-cp3w-hello-session-count 10 --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
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

The current `--ios-get-host-id-once` proof was also validated end to end against the rebuilt ISO launched in Dolphin. The live reports show exact async ioctl call shape `r3 = 11`, `r4 = 16`, `r5 = 0`, `r6 = 0`, `r7 = 0`, `r8 = 0`, `r9 = 0x817E1C20`, and `r10 = 0x817E4080` at target `0x80504FE0`, with synchronous result `0`, one callback, matching generation `6`, preserved callback bits `0x1AD38AB6`, host-ID bytes `1A D3 8A B6`, dotted IPv4 `26.211.138.182`, retained `ip_fd = 11`, `service_started = 1`, and stable terminal `HOST_ID_READY` with zero socket, bind, receive, or send submissions. Callback result `0` means host ID unavailable. Results whose high byte is not `0xFF` are preserved as IPv4 bits even when their signed `s32` view is negative; the `0xFFxxxxxx` range is retained as an IOS error result.

Continuous receive modes account for asynchronous hardware interface readiness and follow the relevant libogc `net_init` order: open `/dev/net/ip/top`, open `/dev/net/kd/request`, run NWC24 startup, close the KD descriptor, run `SO_STARTUP`, and poll `SO_GETHOSTID`. NWC24 result `-29` enters phase `95=WAIT_NWC24_READY` and retries every 6 gameplay polls; `-15` is accepted as already started. After `SO_STARTUP`, a zero host ID or an IOS error enters phase `94=WAIT_NETWORK_READY` instead of permanently failing before `socket()` and `bind()`. The recurring gameplay hook reissues `SO_GETHOSTID` every 60 polls until a usable address is present, then creates one UDP socket and binds the verified `INADDR_ANY:43674` request. The fixed runtime transport structure exposes this path through `startup_submit_count`/`startup_callback_result`, cumulative NWC24 and `get_host_id` submit/callback counts and results, `last_socket_error`, `phase`, socket and bind callback results, `socket_fd`, bind state, receive/send counters, and the most recent CP3W request ID. The observer reports phase 94 as `network_interface_not_ready` or `network_interface_retry_after_error`.

The current `--ios-create-socket-once` proof was also validated end to end against the rebuilt ISO launched in Dolphin. The live reports show exact async ioctl call shape `r3 = 11`, `r4 = 15`, `r5 = 0x817E4AA0`, `r6 = 12`, `r7 = 0`, `r8 = 0`, `r9 = 0x817E1C20`, and `r10 = 0x817E4AC0` at target `0x80504FE0`, with synchronous result `0`, one callback, matching generation `7`, request bytes `00 00 00 02 00 00 00 02 00 00 00 00`, request storage size `32`, request alignment `32`, retained `ip_fd = 11`, retained `host_id = 0x1AD38AB6`, and stable terminal `SOCKET_READY` with `socket_fd = 0`, `descriptor_valid = 1`, `socket_ready = 1`, and zero bind, receive, or send submissions. For this mode, callback descriptors use signed socket semantics, so descriptor `0` is accepted as valid and negative callback results remain socket-creation errors.

The current `--ios-bind-once` proof reaches terminal `BOUND_NO_RECV` with no receive or send work. The verified 36-byte bind request for socket descriptor `0`, port `43674`, and `INADDR_ANY` is `00000000000000010802AA9A000000000000000000000000000000000000000000000000`; this keeps descriptor `0` at offset `0`, marker `1` at offset `4`, sockaddr length `8`, family `2`, and corrected port bytes `AA 9A` instead of the earlier incorrect `9A AA`. The current bind mode uses `INADDR_ANY` for Dolphin, Wii, vWii, and Corruptovania interoperability. The observer intentionally reports `bound_no_recv` on the immediate terminal transition and `bound_no_recv_stable` once recurring polling continues across repeated reads. Cleanup-after-failure is covered by synthetic tests only; live proof so far covers successful bind with `socket_fd = 0`, `receive_count = 0`, and `send_count = 0`.

The current `--ios-recv-send-loop` proof extends that bounded sequence through `SUBMIT_RECEIVE_ONCE -> WAIT_RECEIVE -> SUBMIT_SEND_ONCE -> WAIT_SEND -> REARM_RECEIVE` until the configured exchange limit is reached, then stops terminally at `LOOP_COMPLETE`. `--ios-recv-send-loop-count` must be in the inclusive range `1..100`; the current live proof uses `3`. For count `3`, the expected stable terminal counters are `receive_submit_count = 3`, `receive_arm_count = 3`, `receive_rearm_count = 2`, `receive_count = 3`, `send_submit_count = 3`, `send_count = 3`, `completed_exchange_count = 3`, `loop_complete_transition_count = 1`, and no fourth receive or reply. Rearm occurs only from poll context after a successful non-final send; callbacks never submit IOS work, cleanup remains disabled, and one-shot recv-only or recv-send-once modes do not rearm.

The current `--ios-cp3w-frame-validation` proof reuses that bounded receive/reply transport but inserts a CP3W parser and framed fixed reply before send submission. `--ios-cp3w-frame-validation-count` defaults to `6`, accepts only `1..100`, rejects `0`, negatives, non-integers, use without the framing flag, and conflicting diagnostic modes. The CP3W-specific runtime phases are `50=CP3W_VALIDATE_FRAME`, `51=CP3W_FRAME_VALID`, `52=CP3W_FRAME_REJECTED`, `53=CP3W_SUBMIT_RESPONSE`, `54=CP3W_WAIT_RESPONSE`, and `55=CP3W_FRAME_LOOP_COMPLETE`.

The current `--ios-cp3w-ping-pong` proof builds directly on that framing runtime and adds bounded command dispatch for canonical CP3W `PING` and structured unsupported-command replies. `--ios-cp3w-ping-pong-count` defaults to `8`, accepts only `1..100`, rejects `0`, negatives, non-integers, use without the ping/pong flag, and conflicting diagnostic modes. The added phases are `56=CP3W_DISPATCH_REQUEST`, `57=CP3W_HANDLE_PING`, `58=CP3W_HANDLE_UNSUPPORTED_COMMAND`, `59=CP3W_SUBMIT_DISPATCH_RESPONSE`, `60=CP3W_WAIT_DISPATCH_RESPONSE`, and `61=CP3W_PING_PONG_LOOP_COMPLETE`.

The current `--ios-cp3w-hello-session` proof builds on the established CP3W framing and ping/pong dispatch path and adds deterministic HELLO/session negotiation before session-required commands may execute. `--ios-cp3w-hello-session-count` defaults to `10`, accepts only `1..100`, rejects `0`, negatives, non-integers, use without the HELLO/session flag, and conflicting diagnostic modes. The added phases are `62=CP3W_PROCESS_HELLO`, `63=CP3W_NEGOTIATE_HELLO_VERSION`, `64=CP3W_HANDLE_HELLO_SUCCESS`, `65=CP3W_HANDLE_HELLO_REJECTED`, `66=CP3W_HANDLE_DUPLICATE_HELLO`, `67=CP3W_HANDLE_RENEGOTIATION_REJECTED`, `68=CP3W_HANDLE_NOT_NEGOTIATED`, and `69=CP3W_HELLO_SESSION_LOOP_COMPLETE`.

HELLO/session protocol behavior:

- supported CP3W protocol version: `1`
- HELLO command value: `1`
- PING command value: `3`
- runtime capability mask: `0x0F`
- runtime build ID: `0x50335731`
- response statuses: `0=OK`, `1=ERROR`
- structured error codes used by this milestone: `3=UNSUPPORTED_VERSION`, `4=UNKNOWN_COMMAND`, `9=NOT_NEGOTIATED`, `10=INVALID_STATE`
- HELLO request fixed layout: `>BBII` followed by `client_name_length:uint8` and bounded UTF-8 bytes
- HELLO response fixed layout: `>BIIIIBB` followed by `runtime_name_length:uint8` and bounded UTF-8 bytes
- accepted capabilities are computed as the bitwise intersection of client capabilities and runtime capabilities
- Deterministic session-ID derivation uses big-endian CRC32 over `selected_protocol_version:uint8`, `client_nonce:uint32`, `runtime_build_id:uint32`, `runtime_capabilities:uint32`, and `accepted_client_capabilities:uint32`
- pre-HELLO command gating precedence is: malformed frame `->` no response, HELLO `->` negotiate/reject, known session-required command before HELLO `->` `NOT_NEGOTIATED`, unknown command `->` `UNKNOWN_COMMAND`, known command after HELLO `->` normal dispatch
- pre-HELLO PING returns exactly one structured `NOT_NEGOTIATED` error with message `Negotiation required before PING.`
- unsupported-version HELLO returns exactly one structured `UNSUPPORTED_VERSION` error with message `Unsupported protocol version range.` and does not negotiate a session
- successful HELLO negotiates protocol version `1`, records the client nonce and capability mask, exposes runtime capabilities, returns runtime name `Prime3 Wii Runtime`, returns runtime build ID `0x50335731`, and computes the deterministic session ID exactly once
- identical duplicate HELLO returns another successful HELLO response with the new request ID but the same negotiated session ID and stored session state
- changed HELLO after negotiation returns exactly one structured `INVALID_STATE` error with message `Session is already negotiated.`
- post-HELLO PING executes normally and echoes binary payload bytes exactly, including zero bytes
- unsupported but well-formed commands return exactly one structured `UNKNOWN_COMMAND` error with message `Command is unsupported`
- malformed frames such as invalid magic and bad CRC receive no response

Observer expectations for HELLO/session mode:

- `cp3w_hello_requests_received`
- `cp3w_hello_successes`
- `cp3w_hello_version_rejections`
- `cp3w_hello_responses_submitted`
- `cp3w_hello_responses_completed`
- `cp3w_hello_duplicate_requests`
- `cp3w_hello_renegotiation_rejections`
- `cp3w_pre_hello_gated_commands`
- `cp3w_not_negotiated_responses_submitted`
- `cp3w_not_negotiated_responses_completed`
- `cp3w_negotiated_flag`
- `cp3w_selected_protocol_version`
- `cp3w_client_nonce`
- `cp3w_client_capabilities`
- `cp3w_runtime_capabilities`
- `cp3w_accepted_capabilities`
- `cp3w_session_id`
- `cp3w_runtime_build_id`
- terminal phase `CP3W_HELLO_SESSION_LOOP_COMPLETE` with no further receive or send submission after the final reply completes

CP3W packet format:

- big-endian, fixed `16`-byte header plus payload plus trailing `4`-byte CRC32
- `0x00..0x03`: magic `CP3W`
- `0x04`: protocol version `1`
- `0x05`: packet kind (`1=request`, `2=response`)
- `0x06`: command (`127`, reserved mailbox)
- `0x07`: response status (`0` for the current request and fixed response)
- `0x08..0x0B`: request id
- `0x0C..0x0F`: payload length
- request payload ASCII: `P3_FRAME_TEST_20260717`
- fixed response payload ASCII: `P3_FRAME_ACK_20260717`

CRC32 semantics:

- reflected polynomial `0xEDB88320`
- init `0xFFFFFFFF`
- final XOR `0xFFFFFFFF`
- CRC covers the header and payload bytes only
- the trailing CRC field itself is excluded from coverage

Framing-mode behavior:

- exactly one classification is recorded per received datagram
- accepted frames increment `cp3w_frames_valid`, prepare one retained framed response, and submit exactly one send
- rejected frames increment exactly one rejection counter and do not submit a send
- receive rearm occurs only from poll context after a rejected frame or a successful non-final reply
- callbacks remain evidence-only; they do not parse, submit IOS work, or rearm receive
- stale and duplicate callback counters are expected to remain `0` in successful runs
- terminal count `N` means `cp3w_datagrams_processed == N`, no receive beyond `N`, and terminal phase `CP3W_FRAME_LOOP_COMPLETE`

Ping/pong-mode behavior:

- valid `PING` requests receive a CP3W response packet with response command `PING`, response status `OK`, the original request id, and an exact payload echo
- unsupported but otherwise well-formed commands such as `DISCONNECT` receive a structured CP3W error response with response status `ERROR`, error code `UNKNOWN_COMMAND`, the original request command, and UTF-8 message `Command is unsupported`
- malformed packets still follow the framing rejection path and do not submit a reply
- dispatch bookkeeping records request count, ping count, pong submit/complete counts, unsupported-command count, unsupported reply submit/complete counts, last command, last response status, last ping payload length, and last dispatch result
- terminal count `N` means `cp3w_datagrams_processed == N`, no receive beyond `N`, and terminal phase `CP3W_PING_PONG_LOOP_COMPLETE`

`observe_probe.py` now supports `--poll-ms` with a default of `500` and a minimum of `10`. The report includes the first and second observation timestamps, the existing transport counters, and the CP3W metadata when the manifest exports it. During scripted injection, use `--poll-ms 50` for denser snapshots; `--repeat-delay-ms` remains accepted as a compatibility alias for the same interval.

Live CP3W validation procedure:

1. Build the framing payload with `--ios-cp3w-frame-validation --ios-cp3w-frame-validation-count 6`.
2. Patch a copied CDV `main.dol` with `build_probe_dol.py --install-recurring-poll-hook --enable-ios-udp-diagnostic`.
3. Rebuild the ISO, round-trip extract it, and verify the patched DOL hash matches exactly.
4. Launch the rebuilt ISO in Dolphin and wait for transport phase `WAIT_RECEIVE`.
5. Use `python host/udp_cp3w_frame_test.py --host 127.0.0.1 --port 43674` to inject the deterministic sequence: valid request id `1`, invalid magic, truncated packet, payload length mismatch, unsupported command, bad CRC, valid request id `42`.
6. Verify that the two valid packets receive exact framed CP3W replies, every malformed packet times out, and the runtime reaches terminal `CP3W_FRAME_LOOP_COMPLETE` with stable counters and no extra replies.

Live CP3W ping/pong validation procedure:

1. Build the dispatch payload with `--ios-cp3w-ping-pong --ios-cp3w-ping-pong-count 8`.
2. Patch a copied CDV `main.dol` with `build_probe_dol.py --install-recurring-poll-hook --enable-ios-udp-diagnostic`.
3. Rebuild the ISO, round-trip extract it, and verify the patched DOL hash matches exactly.
4. Launch the rebuilt ISO in Dolphin and wait for transport phase `WAIT_RECEIVE`.
5. Use `python host/udp_cp3w_ping_pong_test.py --host 127.0.0.1 --port 43674` to inject one canonical `PING` request and one canonical unsupported `DISCONNECT` request.
6. Verify that the `PING` request receives an echoed `PING` response, the unsupported request receives a structured `UNKNOWN_COMMAND` error response with message `Command is unsupported`, and the runtime reaches terminal `CP3W_PING_PONG_LOOP_COMPLETE` with stable dispatch counters and no extra replies.

Live CP3W HELLO/session validation procedure:

1. Build the HELLO/session payload with `--ios-cp3w-hello-session --ios-cp3w-hello-session-count 10`.
2. Patch a copied CDV `main.dol` with `build_probe_dol.py --install-recurring-poll-hook --enable-ios-udp-diagnostic`.
3. Rebuild the ISO, round-trip extract it, and verify the patched DOL hash matches exactly.
4. Launch the rebuilt ISO in Dolphin and wait for transport phase `WAIT_RECEIVE`.
5. Use `python host/udp_cp3w_hello_session_test.py --host 127.0.0.1 --port 43674` to inject the deterministic ten-datagram sequence: pre-HELLO PING, unsupported-version HELLO, valid HELLO, identical duplicate HELLO, changed HELLO, post-HELLO PING, unsupported command, invalid magic, bad CRC, and final zero-byte PING.
6. Verify that the runtime reaches terminal `CP3W_HELLO_SESSION_LOOP_COMPLETE`, returns no reply for malformed frames, returns exactly one reply for every structurally valid handled request, preserves request IDs, returns the expected structured error messages, derives the deterministic session ID correctly, and remains stable with no extra replies after the terminal hold.

### CP3W GET_GAME_IDENTITY

`GET_GAME_IDENTITY` is the first typed, read-only service after HELLO. It establishes the supported executable/profile and proves whether volatile game, player, and inventory-root pointers are currently safe before any later inventory service is attempted. It does not read the 59 inventory entries, poll locations, write memory, grant items, or start event streaming.

Build mode `20` with a default terminal sequence length of `12`:

```powershell
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-ios-udp-diagnostic --ios-cp3w-game-identity --ios-cp3w-game-identity-count 12 --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python host/udp_cp3w_game_identity_test.py --host 127.0.0.1 --port 43674
```

`--ios-cp3w-game-identity-count` accepts `1..100`; explicit use without `--ios-cp3w-game-identity`, zero, negatives, non-integers, and conflicting diagnostic modes are rejected. Added phases are `70=CP3W_GAME_IDENTITY_VALIDATE_REQUEST`, `71=...VALIDATE_CAPABILITY`, `72=...VALIDATE_EXECUTABLE`, `73=...RESOLVE_GAME_STATE`, `74=...RESOLVE_PLAYER_STATE`, `75=...BUILD_RESPONSE`, `76=...SUBMIT_RESPONSE`, `77=...RESPONSE_COMPLETE`, `78=...HANDLE_ERROR`, and `79=CP3W_GAME_IDENTITY_LOOP_COMPLETE`.

## CP3W inventory snapshot

`GET_INVENTORY` is command `6`, gated by `INVENTORY_STATE` (`1 << 12`) after HELLO. The request payload is empty. The version-1 response is fixed-width and big-endian: `>BBBBII` header (`schema=1`, `count=59`, `record_size=8`, zero reserved byte, availability flags, u32 sequence) followed by 59 `>II` amount/capacity records. The arithmetic is 12 + 59 * 8 = 484 payload bytes and 504 bytes including the 16-byte CP3W header and 4-byte CRC. Records follow native item IDs `0..42, 44..46, 48..52, 62..69`; synthetic resource IDs at 1000 and above are not on the wire.

```powershell
python tools/prime3_wii_runtime/build_payload.py --relocated-continue --enable-ios-udp-diagnostic --ios-cp3w-inventory --ios-cp3w-inventory-count 14 --reserved-high 0x817E0000 --diagnostic-address 0x817E0100
python host/udp_cp3w_inventory_test.py --help
```

Mode `21` is `cp3w_inventory`; `--ios-cp3w-inventory-count` accepts `1..100`. Phases `80..93` cover request/capability/identity validation, game-state and root resolution, range validation, record reads, root revalidation, response submission/completion, unavailable/error handling, and terminal completion. The static send buffer is 512 bytes; PING remains independently limited to 44 payload bytes.

The runtime validates the NTSC-U executable marker, aligned MEM1 game-state/root pointers, and the complete root range through native item ID 69. It reads only each slot's amount and capacity, then rereads the game-state and inventory-root chain. A changed root produces a successful response with zero records, `TEMPORARILY_UNAVAILABLE` and `INCONSISTENT_SNAPSHOT`, and no `SNAPSHOT_AVAILABLE`. Other temporary pointer loss also returns zero records with `TEMPORARILY_UNAVAILABLE`. The u32 sequence advances for every constructed inventory response, including unavailable responses, wraps naturally, and resets with the runtime.

Host Python maps the structural IDs to `ItemResourceInfo`, validates capacities, constructs `InventoryItem`, filters host-only resources, and retains Corruption's `SuitType >= 5` ownership transform. Existing dolphin-memory-engine reads remain available and feed the same semantic conversion. Inventory polling remains the connector's 2.5-second non-overlapping update loop and is used only after HELLO, negotiated identity/inventory capabilities, and accepted identity. No location state, item grants, writes, subscriptions, or arbitrary production memory service are added.

Before HELLO, GET_INVENTORY returns `NOT_NEGOTIATED`; without the capability it returns `CAPABILITY_NOT_NEGOTIATED`; a nonempty request returns `INVALID_PAYLOAD_LENGTH`; malformed frames receive no response. Dolphin validation uses an isolated user directory. Physical Wii behavior is not validated by this diagnostic milestone, and screenshots are intentionally skipped.

Protocol contract:

- the `GAME_IDENTITY` capability is advertised only by this implemented service mode and must be requested and accepted during HELLO
- command `5=GET_GAME_IDENTITY`; HELLO capability `0x00000800=GAME_IDENTITY`; request payload is exactly zero bytes
- identity schema version `1`; response layout `>BBBBHBBIIIII`, fixed at `28` bytes
- offsets: schema `0`, game `1`, platform `2`, region `3`, revision `4`, protocol `6`, runtime mode `7`, profile ID `8`, profile fingerprint `12`, runtime build ID `16`, availability `20`, reserved `24`
- static IDs: game `1=METROID_PRIME_3_CORRUPTION`, platform `1=WII`, region `1=NTSC_U`, revision `1=WII_NTSC_3_436`, profile `0x50334E41`, runtime build `0x50335731`
- profile fingerprint `0x67B00CE6` is CRC32 over big-endian `>BBBHIIIII`: game, platform, region, revision, profile ID, game-state root, CStateManager root, CPlayer vtable, and expected DOL SHA-256 prefix `0x6B550F22`; it is a profile fingerprint, not a full runtime DOL hash
- availability bits: `0x01=EXECUTABLE_RECOGNIZED`, `0x02=GAME_STATE_POINTER_VALID`, `0x04=PLAYER_STATE_POINTER_VALID`, `0x08=INVENTORY_ROOT_AVAILABLE`, `0x10=WORLD_STATE_AVAILABLE`
- the final reserved `uint32` is always zero; static fields are deterministic while availability may change during a real game transition

The executable check directly validates the NTSC build marker `!#$M` at `0x805822B0`. Every pointer is non-null, 4-byte aligned, bounded to MEM1 `0x80000000..0x81800000`, and checked for offset overflow before dereference. The game-state root is read from `0x8067DC0C`; the inventory root is validated only through `*(game_state+0x24)` with enough bounded space for the `+0x54` data start. Player validation follows `*(0x805C4F70+0x28)+0x2184` and requires vtable `0x80592C78`. The runtime does not infer save-loaded or loading-state flags. A missing player or inventory root is a successful identity response with those availability bits clear, not a protocol failure.

Processing precedence is malformed frame with no reply, HELLO, pre-HELLO `NOT_NEGOTIATED`, unaccepted capability error `11=CAPABILITY_NOT_NEGOTIATED`, non-empty request error `5=INVALID_PAYLOAD_LENGTH`, unknown command, then one successful dispatch. Rejected requests perform no game-memory reads and do not mutate the session. Observer output includes canonical names and values, decoded availability, validation pointers/results, identity/error counters, request/status fields, transport/callback generations, and terminal state. Terminal completion occurs only after the twelfth datagram's final response callback completes; no receive is rearmed and no extra packet is emitted.

Validation is Dolphin-only; physical Wii behavior is not validated and screenshots are intentionally skipped. Inventory snapshots, location state/deltas, writes, item grants, reconnect reconciliation, authentication, and subscriptions remain explicitly deferred.

Known limitations:

- this remains a developer-only diagnostic transport path
- the current CP3W request/response pair is fixed and does not implement gameplay mailbox semantics yet
- callback evidence is live-proven in Dolphin, but physical-Wii behavior is not yet validated
- normal exporter-driven bidirectional game integration is still future work

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
