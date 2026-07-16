# Prime 3 Wii Runtime Probe

## Scope

This workflow verifies only the developer-only probe delivery chain:

- source probe payload
- temporary unhooked `main.dol`
- temporary rebuilt ISO
- re-extracted `main.dol`
- live Dolphin memory observation
- a developer-only entry gate at `0x80006320` when requested

It does not install a hook, reserve arena space, or claim any runtime-safe payload address.

Networking note:

- the current probe workflow still validates relocation and recurring-poll delivery only
- the runtime now carries developer-only retail-wrapper metadata and a terminal NWC24 one-shot diagnostic; probe delivery remains separate from normal exporter behavior
- Skyward Sword transport provenance is now documented separately in [`docs/prime3_wii_skyward_sword_transport_recon.md`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/docs/prime3_wii_skyward_sword_transport_recon.md:1)
- any future network probe must remain developer-only, fixed-storage, and bounded to one receive or send step per recurring poll

## Expected Probe Values

For the current developer probe build:

- payload SHA-256: `aad91d2d09ecb59f1f86dba8c6b806640e687ce57d53c96a336708e969d821c2`
- payload size: `148`
- appended text slot: `text2`
- payload address: `0x806843c0`
- entry address: `0x806843c0`
- canary address: `0x80684440`
- canary size: `16`
- counter address: `0x80684450`
- counter size: `4`
- expected initial counter value: `0`

The developer-only entry gate replaces the retail first entry instruction at `0x80006320`:

- original word: `0x4800016d`
- gated word: `0x48000000`

## Probe DOL Generation

Build the probe payload:

```powershell
python tools/prime3_wii_runtime/build_payload.py --probe --output-dir <temp>\payload
```

Build the temporary unhooked probe DOL:

```powershell
python tools/prime3_wii_runtime/build_probe_dol.py `
  --original-dol <original main.dol> `
  --output-dol <temp>\probe-main.dol `
  --payload-bin <temp>\payload\payload.bin `
  --payload-manifest <temp>\payload\payload.json `
  --report <temp>\probe-section.json `
  --payload-address <probe payload virtual address> `
  --halt-at-entry
```

Recurring poll validation uses the relocated runtime plus the Wii NTSC accessor hook at `0x800BB71C` instead of an entry gate:

```powershell
python tools/prime3_wii_runtime/build_probe_dol.py `
  --original-dol <original main.dol> `
  --output-dol <temp>\probe-main.dol `
  --payload-bin <temp>\payload\payload.bin `
  --payload-manifest <temp>\payload\payload.json `
  --report <temp>\probe-section.json `
  --payload-address 0x806843C0 `
  --install-recurring-poll-hook
```

The probe DOL builder:

- starts from the retail `main.dol`
- installs no layout UUID
- installs no hook
- installs no arena reservation patch
- appends the probe payload as a new unused text section at the smallest aligned address above the mapped sections and BSS
- optionally replaces the first retail entry instruction with a self-branch gate for a halted-entry observation point

## Final-Image Verification

Use the existing Prime 3 exporter toolchain route:

1. Copy the extracted retail root to an operating-system temporary directory.
2. Replace only `DATA\sys\main.dol` with the probe DOL.
3. Rebuild a temporary ISO using the existing `wit COPY` command.
4. Re-extract that exact ISO using the existing Prime 3 extractor path.
5. Verify the original, intended probe, and final extracted DOLs:

```powershell
python tools/prime3_wii_runtime/verify_probe_delivery.py `
  --original-dol <original main.dol> `
  --probe-dol <temp>\probe-main.dol `
  --extracted-final-dol <temp>\reextract\DATA\sys\main.dol `
  --payload-bin <temp>\payload\payload.bin `
  --payload-manifest <temp>\payload\payload.json `
  --report <temp>\probe-delivery.json `
  --payload-address <probe payload virtual address> `
  --halt-at-entry
```

For the recurring poll path, swap `--halt-at-entry` for `--install-recurring-poll-hook`.

Pass:

- intended probe DOL hash equals temporary-root DOL hash
- intended probe DOL hash equals re-extracted final DOL hash
- final extracted DOL keeps the same new text-section entry
- final extracted DOL keeps the same payload bytes

Observed static result for the current gated probe images:

- original retail `main.dol` SHA-256: `6b550f221602074747a2e61b0aa064203fd493f6865dfb3b1a912682065e6104`
- low halted-entry probe `main.dol` SHA-256: `c50d988ee25d597a058041459127a01c6fc4e49509c34839d4d976b06a490f14`
- low re-extracted final `main.dol` SHA-256: `c50d988ee25d597a058041459127a01c6fc4e49509c34839d4d976b06a490f14`
- low rebuilt probe ISO SHA-256: `d10437cc6e4d3ec35fde1a00ce7bce41476ce0787027810eabade6686518da75`
- high halted-entry probe `main.dol` SHA-256: `cf2e22867cea45a92f36cb7c27fa5affd98b2fe6e0abc5696638823d1438cf2d`
- high re-extracted final `main.dol` SHA-256: `cf2e22867cea45a92f36cb7c27fa5affd98b2fe6e0abc5696638823d1438cf2d`
- high rebuilt probe ISO SHA-256: `97527033ecb0ee221d363bce38375ecaae7c22ce5c6c14d976c43a05119f81a0`
- deterministic probe payload `payload.bin` SHA-256: `aad91d2d09ecb59f1f86dba8c6b806640e687ce57d53c96a336708e969d821c2`
- deterministic probe payload `payload.elf` SHA-256: `efb5bd3448b3605991cabcf7dac013c35489c01cbd33e5787aa19a0c35da1a56`
- deterministic probe payload `payload.json` SHA-256: `868d3d3db7942fe6454aaed3cc53d110e2dcb4a707ef19ce212c79d1f8dadd65`

Failure:

- if the intended probe DOL differs from the temporary-root DOL, replacement failed
- if the re-extracted DOL differs from the intended probe DOL, ISO build or extraction changed the image
- if the final DOL lacks the appended section, do not draw live-memory conclusions from Dolphin

## Proving Dolphin Booted The Intended Image

Use all of these together:

- launch Dolphin with an explicit absolute ISO path
- use a unique temporary ISO filename
- use a unique Dolphin `--user` directory
- record the exact ISO SHA-256 before launch
- confirm the running Dolphin process command line still points at that exact ISO path
- re-extract the exact launched ISO path, not a similarly named prior image

Do not trust only the GUI title or recent-file list.

The observed successful image-identity method for this milestone was:

- exact Dolphin command line with the rebuilt ISO absolute path
- unique temporary Dolphin user directory
- ISO SHA-256 recorded before launch
- re-extraction of that same launched ISO path

## Read-Only Memory Observation

The repository already depends on `dolphin_memory_engine`, so the supported read-only observer is:

```powershell
python tools/prime3_wii_runtime/observe_probe.py `
  --payload-address <probe payload virtual address> `
  --payload-bin <temp>\payload\payload.bin `
  --payload-manifest <temp>\payload\payload.json `
  --report <temp>\probe-memory.json `
  --startup-word 0x80006320=0x48000000 `
  --startup-word 0x8000633C=0x38000000
```

For the recurring poll path, observe the installed retail hook word and sample the relocated runtime state over time:

```powershell
python tools/prime3_wii_runtime/observe_probe.py `
  --payload-address 0x806843C0 `
  --payload-bin <temp>\payload\payload.bin `
  --payload-manifest <temp>\payload\payload.json `
  --report <temp>\probe-memory.json `
  --hook-address 0x800BB71C `
  --expected-hook-word <probe-report recurring_poll_hook hook_replacement_instruction> `
  --repeat-delay-ms 1000
```

It reads only:

- game ID at `0x80000000`
- expected startup words
- the complete probe payload range
- canary bytes
- counter value
- low-memory words at:
  - `0x80000034`
  - `0x80003110`
  - `0x800000F4`
- `*(0x800000F4 + 0x08)` when the boot-info pointer is non-zero

Observed halted-entry result from the exact rebuilt probe ISOs:

- both Dolphin launches used the exact absolute rebuilt ISO paths and unique Dolphin user directories
- both running Dolphin process command lines still referenced the exact launched ISO paths
- both runs reported game ID `RM3E01`
- both runs reported the gated startup words:
  - `0x80006320 = 0x48000000`
  - `0x8000633c = 0x38000000`
- both runs reported:
  - `0x800000f4 = 0x817fc3a0`
  - `*(0x817fc3a8) = 0`
  - `0x80000034 = 0x817fe3a0`
  - `0x80003110 = 0x817fe3a0`
- low-address halted-entry result at `0x806843c0`:
  - full payload SHA-256 matched `aad91d2d09ecb59f1f86dba8c6b806640e687ce57d53c96a336708e969d821c2`
  - canary matched
  - counter remained `0`
- high-address halted-entry result at `0x817e0000`:
  - full payload range read back as zeroes
  - live payload SHA-256 was `3b18c58c739716e76429634a61375c45b3b5cd470c22ab6d3e14cee23dd992e1`
  - canary did not match
  - counter remained `0`

This is now an entry-gated result, not a later post-boot snapshot. It proves that Dolphin's Wii DOL loader copied the appended low-address text section before the retail entry instruction but did not present the appended high-address text section intact at that same halted-entry state.

## Later Checkpoints

After confirming the payload exists at `0x80006320`, re-check the same payload range at:

- `0x8000633C`
- `0x80006434`
- the end of the startup stub
- title screen

If the payload changes, use Dolphin memory checks or write breakpoints on:

- the payload range
- `0x80000034`
- `0x80003110`

Capture:

- earliest changed checkpoint
- writer PC
- written address range
- whether the write matches BSS clear, arena init, heap init, REL loading, or another clear path

If a later checkpoint zeroes the low-address payload, capture the earliest changed checkpoint and the writer PC before drawing overwrite conclusions.

For the bounded Wii transport proof, the expected initialization-only terminal state is now:

- `phase = BOUND_NO_RECV`
- `kd_fd = -1`
- `kd_closed = true`
- valid retained `ip_fd` and `socket_fd`
- zero receive, send, IP-close, and socket-close submissions

For `--ios-bind-once`, the verified live bind contract is now:

- target `0x80504FE0`
- command `2`
- exact pre-call ABI `r3 = ip_fd`, `r4 = 2`, `r5 = bind request`, `r6 = 36`, `r7 = 0`, `r8 = 0`, `r9 = bind callback`, `r10 = bind context`
- exact 36-byte request for descriptor `0`, port `43674`, and `INADDR_ANY`:
  - `00000000000000010802AA9A000000000000000000000000000000000000000000000000`
- corrected port bytes `AA 9A`; the earlier `9A AA` serialization was wrong
- success requires synchronous result `0` and callback result `0`
- positive callback results are rejected as anomalous
- the observer intentionally reports immediate `bound_no_recv` and later `bound_no_recv_stable` once recurring polling continues across repeated reads
- synthetic coverage now also tracks later-poll command-`3` cleanup after bind failure and the distinct leak terminal when cleanup submission or callback fails

For `--ios-nwc24-via-retail-ioctl-once`, the narrower terminal state is `NWC24_COMPLETE` (`0xFE`): `/dev/net/kd/request` remains open, exactly one command-6 ioctl has been submitted via `0x80504FE0`, and no close, IP, socket, receive, or send operation is submitted. The wrapper ABI is `r3..r10 = fd, command, input, input_length, output, output_length, callback, userdata`; `0x80504A08` remains classified as async read.

For `--ios-close-kd-once`, the sequence extends only through `KD_CLOSED` (`0xFE`). The verified async close wrapper is `0x805048A0..0x80504960`, operation `2`, with `r3=fd`, `r4=completion`, and `r5=userdata`. The retail dispatcher owns the lower request; the relocated close context remains allocated until its callback. The successful local proof returned `0` synchronously and through one callback, then retained `kd_fd=-1`, `kd_closed=true`, and zero IP/receive/send submissions.

For `--ios-open-ip-once`, the prerequisite lifecycle is now proven through `IP_OPEN` (`0xFE`) without entering any later socket startup phase. The runtime opens `/dev/net/kd/request`, submits the verified async ioctl wrapper at `0x80504FE0`, closes the retained KD descriptor through `0x805048A0`, and then calls verified `open_async` at `0x80504668` for the persistent NUL-terminated `/dev/net/ip/top` path. The live Dolphin proof recorded `r3 = 0x817E3970` for `/dev/net/ip/top\0`, `r4 = 0`, `r5 = 0x817E1B5C`, and `r6 = 0x817E3A60` immediately before the retail call. The `OPEN_IP` submission returned `0`, exactly one callback returned descriptor `11`, generations matched at `4`, `ip_fd` transitioned from `-1` to `11`, and the terminal reports remained stable for more than fifteen seconds with `kd_fd = -1`, `kd_closed = true`, recurring polling still advancing, balanced hook/poll counters, and zero `SO_STARTUP`, `GET_HOST_ID`, socket, bind, receive, or send activity.

For `--ios-so-startup-once`, the prerequisite lifecycle is now proven one step farther through terminal `SO_STARTED` (`18`) and still stops before any host-ID or socket work. The runtime opens `/dev/net/kd/request`, submits NWC24 command `6` via `0x80504FE0`, closes the retained KD descriptor through `0x805048A0`, opens `/dev/net/ip/top` through `0x80504668`, and then submits `IOCTL_SO_STARTUP` through the verified async ioctl wrapper at `0x80504FE0` with exact live ABI `r3 = 11`, `r4 = 31`, `r5 = 0`, `r6 = 0`, `r7 = 0`, `r8 = 0`, `r9 = 0x817E1C20`, and `r10 = 0x817E4080`. The `SO_STARTUP` submission returned `0`, exactly one callback returned `0`, generations matched at `5`, `service_started` transitioned from `0` to `1`, `ip_fd` remained `11`, and three reports collected over more than fifteen seconds remained stable at classification `so_started` with `phase = SO_STARTED`, `pending_operation = none`, `kd_fd = -1`, `kd_closed = true`, balanced hook/poll counters, and zero `GET_HOST_ID`, socket, bind, receive, or send activity.

For `--ios-create-socket-once`, the prerequisite lifecycle is now proven one step farther through terminal `SOCKET_READY` (`20`) and still stops before bind. The runtime reuses the same verified prerequisite chain through `HOST_ID_READY`, then submits command `15` through `0x80504FE0` with exact live ABI `r3 = 11`, `r4 = 15`, `r5 = 0x817E4AA0`, `r6 = 12`, `r7 = 0`, `r8 = 0`, `r9 = 0x817E1C20`, and `r10 = 0x817E4AC0`. The persistent request storage at `0x817E4AA0` is `32` bytes and `32`-byte aligned, but the logical submitted request length remains `12` bytes, with exact first bytes `00 00 00 02 00 00 00 02 00 00 00 00` for signed big-endian `family = 2`, `type = 2`, and `protocol = 0`. The submission returned `0`, exactly one callback returned signed descriptor `0`, callback raw bits remained `0x00000000`, generations matched at `7`, `socket_fd` transitioned from `-1` to `0`, `descriptor_valid = true`, and `socket_ready = true`. Three reports collected over more than fifteen seconds remained stable at classification `socket_ready` with `phase = SOCKET_READY`, `pending_operation = none`, `kd_fd = -1`, `kd_closed = true`, `ip_fd = 11`, `service_started = true`, `host_id_u32 = 0x1AD38AB6`, recurring polling still advancing, and zero bind, receive, or send activity.

For `--ios-get-host-id-once`, the prerequisite lifecycle is now proven one step farther through terminal `HOST_ID_READY` (`19`) and still stops before any socket work. The runtime opens `/dev/net/kd/request`, submits NWC24 command `6` via `0x80504FE0`, closes the retained KD descriptor through `0x805048A0`, opens `/dev/net/ip/top` through `0x80504668`, submits `IOCTL_SO_STARTUP` through `0x80504FE0`, and then submits `IOCTL_SO_GETHOSTID` through the same verified async ioctl wrapper with exact live ABI `r3 = 11`, `r4 = 16`, `r5 = 0`, `r6 = 0`, `r7 = 0`, `r8 = 0`, `r9 = 0x817E1C20`, and `r10 = 0x817E4080`. The `GET_HOST_ID` submission returned `0`, exactly one callback occurred, generations matched at `6`, raw callback bits were preserved as `0x1AD38AB6`, `host_id_u32` matched that same nonzero value, host-ID bytes were `1A D3 8A B6`, the observer formatted dotted IPv4 `26.211.138.182`, and three reports collected over more than fifteen seconds remained stable at classification `host_id_ready` with `phase = HOST_ID_READY`, `pending_operation = none`, `kd_fd = -1`, `kd_closed = true`, `ip_fd = 11`, `service_started = true`, `host_id_available = true`, `host_id_ready = true`, balanced hook/poll counters, and zero socket, bind, receive, or send activity. For this operation, callback result `0` is host ID unavailable; any nonzero 32-bit pattern remains valid even when its signed `s32` view would be negative.

## Cleanup

- remove repository-local build artifacts
- keep temporary DOL, ISO, and report files only outside the repository
- if retained for manual debugging, record the retained temporary paths explicitly
