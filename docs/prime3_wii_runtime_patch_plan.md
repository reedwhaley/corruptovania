# Prime 3 Wii Runtime Patch Plan

## Scope of this milestone

This milestone establishes a source-backed Wii PowerPC payload build path and a validated payload artifact contract. It does not enable runtime networking, install a production hook, or claim that any Corruption runtime memory reservation is safe.

Transport recon update:

- Skyward Sword's console UDP implementation has now been traced to a direct-IOS transport layer rather than libogc `net_*` wrappers
- the detailed provenance report lives in [`docs/prime3_wii_skyward_sword_transport_recon.md`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/docs/prime3_wii_skyward_sword_transport_recon.md:1)
- that source evidence removes the earlier "unknown transport plumbing" blocker, but it does not make the Skyward Sword runtime code a safe drop-in for Prime 3
- the active Skyward Sword transport still relies on `IOS_HEAP` allocation, alarms, and an unbounded receive loop, which conflicts with the current Prime 3 requirement of fixed storage plus one bounded network step per recurring poll
- the earlier Prime 3 raw direct-submit `IOS_OpenAsync` experiment was incorrect and is now demoted to failed diagnostic history
- Prime 3 NTSC's own retail IOS wrapper cluster is now identified in the retail `main.dol`, with `IOS_OpenAsync` at `0x80504668`
- the runtime payload now carries guarded retail-wrapper metadata for NTSC `main.dol` SHA-256 `6b550f221602074747a2e61b0aa064203fd493f6865dfb3b1a912682065e6104`

Selected transport direction after recon:

- keep the existing CP3W host protocol and executor
- reuse Skyward Sword only as MIT-licensed IOS transport provenance and structure reference
- do not import Skyward Sword's gameplay protocol, write-memory behavior, or loop structure
- implement any future Prime 3 transport as a project-owned direct-IOS state machine on port `43674`

Implemented code now covers:

- executable DOL section insertion and guarded patch primitives in [`randovania/games/prime3/exporter/dol_patcher.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/games/prime3/exporter/dol_patcher.py:1)
- devkitPPC discovery and version validation in [`randovania/games/prime3/exporter/runtime_toolchain.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/games/prime3/exporter/runtime_toolchain.py:1)
- payload manifest loading and validation in [`randovania/games/prime3/exporter/runtime_payload.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/games/prime3/exporter/runtime_payload.py:1)
- a return-only source payload project in [`tools/prime3_wii_runtime/`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_wii_runtime)

## Selected toolchain strategy

The selected build path is the official devkitPro `devkitPPC` toolchain, discovered through `DEVKITPRO` and `DEVKITPPC` and validated against the local installation metadata and tool versions.

Verified local package set:

- `devkitPPC r47.1-1`
- `libogc 2.13.0-1`
- `gamecube-tools 1.0.7-1`
- `wii-pkg-config 0.28-5`

Verified local tool versions:

- `powerpc-eabi-gcc` `15.1.0`
- GNU binutils `2.44` for `ld`, `objcopy`, `readelf`, and `objdump`
- compiler target triple `powerpc-eabi`

Official Wii ABI and CPU assumptions are taken directly from devkitPro's Wii rules and CMake support:

- `-DGEKKO`
- `-mrvl`
- `-mcpu=750`
- `-meabi`
- `-mhard-float`
- `-mbig-endian`

The resolver intentionally rejects:

- missing `DEVKITPRO` or `DEVKITPPC`
- missing required executables
- unsupported target triples
- malformed version output
- version drift away from the pinned `r47.1` / `15.1.0` / `2.44` environment

This is now a reproducible developer dependency path. It is not yet wired into repository CI, so CI availability remains a blocker for broad runtime rollout.

## Rejected toolchain strategies

- undocumented global `PATH` lookup only: rejected
- ad hoc local LLVM/Clang cross-compilation: not proven
- committed compiler binaries: rejected
- Docker/Podman-based route: not established in this repo
- speculative native source without a validated build path: rejected

## Payload source layout

The current source-backed runtime payload project is:

- [`tools/prime3_wii_runtime/payload.S`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_wii_runtime/payload.S:1)
- [`tools/prime3_wii_runtime/payload.ld`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_wii_runtime/payload.ld:1)
- [`tools/prime3_wii_runtime/build_payload.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_wii_runtime/build_payload.py:1)
- [`tools/prime3_wii_runtime/README.md`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_wii_runtime/README.md:1)

Additional transport evidence now documented:

- device paths `/dev/net/kd/request` and `/dev/net/ip/top`
- request command `6` for `IOCTL_NWC24_STARTUP`
- socket commands `31`, `16`, `15`, `2`, `12`, `13`, and `3` for startup, host IP, socket create, bind, receive, send, and close
- aligned `sockaddr`-compatible request layout and big-endian peer encoding
- direct `IOS_OpenAsync`, `IOS_IoctlAsync`, and `IOS_IoctlvAsync` usage without libogc `net_*`
- corrected initialization order for the bounded Prime 3 proof path:
  - open `/dev/net/kd/request`
  - issue `IOCTL_NWC24_STARTUP` with an aligned `0x20`-byte output buffer
  - close the temporary request descriptor after the callback completes
  - open `/dev/net/ip/top`
  - issue `IOCTL_SO_STARTUP`
- successful bind-only completion now requires `kd_fd = -1` plus a separate `kd_closed` flag; retaining `kd_fd` after bind is no longer considered correct

The minimal payload:

- exports `payload_entry`
- consists only of `blr`
- returns immediately
- has no libc, libogc, allocator, TLS, constructor, exception, or RTTI dependency
- performs no memory writes outside the normal return path
- performs no IOS or networking operation

Because the payload is pure assembly in this milestone, it avoids small-data assumptions by construction rather than by C compiler flags.

## Exact build command

From the repository root:

```powershell
python tools/prime3_wii_runtime/build_payload.py
```

The build emits:

- `payload.o`
- `payload.elf`
- `payload.bin`
- `payload.map`
- `payload.json`

under `build/prime3_wii_runtime/`. These are build artifacts only and are not committed.

## Artifact contract

The raw source build produces:

1. an ELF for structural inspection
2. a raw payload binary
3. a deterministic JSON manifest

The manifest records:

- schema version
- target architecture
- target endianness
- ABI
- compiler identity and version
- linker identity and version
- payload SHA-256
- payload size
- required alignment
- entry symbol name
- entry symbol offset
- source digest
- protocol artifact version
- unresolved relocation count
- dynamic section count

The Python consumer side validates:

- schema version
- architecture `powerpc`
- big-endian output
- ABI `eabi`
- payload hash
- payload size
- entry offset bounds
- unresolved relocation count is zero
- dynamic section count is zero

Only after those checks does it construct the existing typed `Prime3PayloadArtifact`. The final load address still has to be supplied explicitly by the caller because no safe runtime reservation has been verified.

## Reproducibility findings

The current minimal payload build is reproducible in the practical sense required for this milestone:

- repeated builds from unchanged sources produced byte-identical `payload.bin`
- repeated builds from unchanged sources produced byte-identical `payload.elf`
- repeated builds from unchanged sources produced byte-identical `payload.json`
- repeated builds did not produce byte-identical linker map files, so the map file is treated as diagnostic output rather than a reproducibility target

ELF validation on the built payload confirmed:

- `ELF32`
- big-endian
- `Machine: PowerPC`
- executable type
- entry symbol at offset `0`
- no relocations
- no dynamic section

## Real DOL memory map and current static image

The supplied retail NTSC `main.dol` still maps only into MEM1.

Verified from the real DOL header:

- entry point: `0x80006320`
- mapped text range: `0x80004000..0x80575680`
- mapped data range: `0x800066c0..0x80684380`
- BSS range: `0x805c0800..0x806843a4`
- no DOL section currently maps into `0x90000000+` MEM2 space

The earlier section-table gap analysis remains valid:

- `0x80575f60..0x80575f80`
- `0x805c07e0..0x805c0800`

Those are real non-overlapping static gaps, but both are only 32 bytes and therefore insufficient for a runtime payload.

## MEM1 and MEM2 findings

System memory references used for this milestone align on the following model:

- MEM1 cached: `0x80000000..0x817fffff`
- MEM2 cached: `0x90000000..0x93ffffff`
- low-memory global fields expose MEM1 and MEM2 arena bounds and IOS-reserved MEM2 ranges

Corruption-specific findings from the retail DOL:

- all mapped DOL text/data/BSS currently live in MEM1
- BSS ends at `0x806843a4`
- generic headroom from BSS end to MEM1 ceiling is `0x0117bc5c` bytes

What is not yet proven:

- whether a static MEM1 payload above current BSS survives every later game allocator step
- whether a MEM2-backed DOL text section is a safe and supported loader target for this title
- a Corruption-specific executable runtime allocation path with known cache-management semantics
- a REL-safe exclusion boundary for injected code

## Arena and heap findings

No production-safe Corruption-specific arena reservation is verified in this milestone.

Evidence quality today:

- generic Wii low-memory arena fields and MEM2 usable-range fields are known
- Corruption-specific DOL header layout is known
- the retail startup stub at `0x800063c4..0x8000642c` writes the same aligned pointer to:
  - `0x80000034`, which generic Dolphin OS memory maps document as `ArenaHi`
  - `0x80003110`, which Wii low-memory maps document as MEM1 arena end
- later OS init code at `0x804de1d8..0x804de278` reads `0x80003110`, `0x80003124`, and `0x80003128` and copies those values into internal allocator globals
- no later direct store to `0x80000034` or `0x80003110` was found in the retail DOL text sections
- a live Dolphin observation on a temporary hooked ISO found:
  - `0x800000f4 = 0x817fc3a0`
  - the word at `0x817fc3a8` was `0`
  - therefore the observed control flow takes the `beq 0x80006434` path and skips the later `0x80006410..0x8000642c` store sequence entirely
  - `0x80000034` read as `0x817fec60`
  - `0x80003110` read as `0x81800000`

What this proves:

- adding a DOL section above current BSS does not by itself reserve that range from later MEM1 allocation
- the presence of the `0x80006410..0x8000642c` writes in the retail DOL is not enough to treat them as the active retail MEM1 reservation path

What this still does not prove:

- that a lowered `ArenaHi` / MEM1 arena end value is sufficient for Corruption's later heap, REL, and game allocator behavior
- that no later non-text-side write from IOS, apploader state, or runtime data initialization can still affect the same effective reservation
- that a chosen MEM1 payload span above BSS is large enough and harmless for real gameplay startup across this title's full boot path

Because those survival and ownership questions are still open, no production allocation metadata was added. Empty address space above BSS is not treated as safe by default.

## Allocation strategy evaluation

### 1. Static DOL section above existing BSS in MEM1

- theoretical capacity: up to the remaining MEM1 headroom above `0x806843a4`
- branch reachability from startup code: yes
- current status: rejected for production
- blocker: a new section above BSS remains inside the default MEM1 arena unless the startup-written high boundary is reduced explicitly

### 2. Static DOL section in a MEM2 range

- theoretical capacity: much larger
- branch reachability from startup entry via single relative branch: no
- current status: rejected for production
- blockers:
  - no Corruption-specific loader proof for MEM2 DOL sections
  - no verified Corruption-owned MEM2 reservation write was identified; the retail DOL only reads the IOS/apploader-provided MEM2 bounds at `0x80003124` and `0x80003128`
  - would require a proven trampoline or secondary hop strategy

### 3. Reserve memory by reducing an arena boundary

- current status: rejected for the observed retail boot path
- reason:
  - the observed boot-info structure leaves `*(0x800000f4 + 0x08) == 0`
  - the retail startup path therefore branches to `0x80006434` and skips the suspected `ArenaHi` store sequence
- consequence:
  - patching the `addi r15, r6, 4` source instruction does not establish a verified live reservation path for this title
- remaining blocker:
  - a version-specific MEM1 reservation point that actually executes on the retail boot path still has not been identified

### 4. Runtime allocation from a known executable-capable arena

- current status: rejected for production
- blocker: no proven executable-capable Corruption allocation path and no validated cache-management sequence for runtime-generated code

### 5. Extend an existing mapped text section

- current status: rejected for production
- blocker: would still need a safe virtual reservation and would couple payload growth to existing retail section boundaries

### 6. Separate loader stub plus runtime allocation

- current status: rejected for production
- blocker: depends on both a verified hook and a verified allocator/reservation path

## Verified allocation strategy

None.

The current codebase deliberately refuses to claim that any runtime payload address is safe merely because it is outside the retail DOL's presently mapped sections.

## Hook candidate evidence

No hook is fully verified for production use, but one evidence-backed startup candidate now exists from direct static disassembly of the retail DOL entry stub.

Candidate:

- address: `0x8000633c`
- containing function: DOL entry/startup stub beginning at `0x80006320`
- expected original instruction word: `0x38000000`
- mnemonic: `li r0, 0`
- execution timing: startup only
- execution frequency: one inbound branch from the DOL entry stub was found, and no other in-DOL branch target to `0x8000633c` was found
- displacement safety with the current conservative trampoline helper: yes, because this instruction is plain non-control-flow
- stack validity: better than the raw entry instruction because the prologue has already executed, but still not fully ABI-proven for payload entry
- startup context:
  - executes after register/base setup at `0x8000648c` and section/BSS init at `0x8000651c`
  - executes before the later OS init fan-out at `0x804c5160` and `0x804de05c`
- branch reachability:
  - MEM1/BSS-adjacent candidates: yes
  - MEM2 candidates via one direct relative branch: no
- confidence: low
- missing proof:
  - exact startup invariants at this point
  - whether a payload entered here can safely rely on any OS service, heap state, or arena state
  - whether a payload entered here could safely touch any runtime service needed later

An earlier startup address, `0x80006320`, is also exact and easy to identify, but its original instruction is `0x4800016d` (`bl 0x8000648c`), which is a control-flow instruction and therefore rejected by the current conservative single-instruction trampoline builder.

## Probe payload status

The source-backed payload project now supports a developer-only probe build mode.

Verified probe-artifact properties:

- deterministic `payload.bin`, `payload.elf`, and `payload.json`
- optional manifest metadata for:
  - canary start offset
  - canary size
  - execution-counter offset
  - execution-counter size
- an explicit assembly wrapper that preserves startup state, reproduces the displaced `li r0, 0`, and returns
- a developer-only entry gate at `0x80006320` that replaces `0x4800016d` with `0x48000000` for halted-entry observation

What is not verified:

- that the current `0x8000633c` hook candidate reaches that payload in the retail title

## Static probe delivery-chain result

The gated probe-section image path is now verified structurally for both tested placements.

Observed temporary-image result:

- original retail `main.dol` SHA-256: `6b550f221602074747a2e61b0aa064203fd493f6865dfb3b1a912682065e6104`
- deterministic probe payload `payload.bin` SHA-256: `aad91d2d09ecb59f1f86dba8c6b806640e687ce57d53c96a336708e969d821c2`
- deterministic probe payload `payload.elf` SHA-256: `efb5bd3448b3605991cabcf7dac013c35489c01cbd33e5787aa19a0c35da1a56`
- deterministic probe payload `payload.json` SHA-256: `868d3d3db7942fe6454aaed3cc53d110e2dcb4a707ef19ce212c79d1f8dadd65`
- low halted-entry probe `main.dol` SHA-256: `c50d988ee25d597a058041459127a01c6fc4e49509c34839d4d976b06a490f14`
- low re-extracted final `main.dol` SHA-256: `c50d988ee25d597a058041459127a01c6fc4e49509c34839d4d976b06a490f14`
- low rebuilt probe ISO SHA-256: `d10437cc6e4d3ec35fde1a00ce7bce41476ce0787027810eabade6686518da75`
- high halted-entry probe `main.dol` SHA-256: `cf2e22867cea45a92f36cb7c27fa5affd98b2fe6e0abc5696638823d1438cf2d`
- high re-extracted final `main.dol` SHA-256: `cf2e22867cea45a92f36cb7c27fa5affd98b2fe6e0abc5696638823d1438cf2d`
- high rebuilt probe ISO SHA-256: `97527033ecb0ee221d363bce38375ecaae7c22ce5c6c14d976c43a05119f81a0`

Verified appended section metadata:

- low placement:
  - text slot: `text2`
  - virtual address: `0x806843c0`
  - file offset: `0x005c46e0`
  - payload size: `148`
  - entry address: `0x806843c0`
  - canary address: `0x80684440`
  - counter address: `0x80684450`
- high placement:
  - text slot: `text2`
  - virtual address: `0x817e0000`
  - file offset: `0x005c46e0`
  - payload size: `148`
  - entry address: `0x817e0000`
  - canary address: `0x817e0080`
  - counter address: `0x817e0090`
- gated entry word:
  - gate address: `0x80006320`
  - original word: `0x4800016d`
  - replacement word: `0x48000000`

Static pass result:

- low and high probe payload builds were deterministic across two independent rebuilds
- low and high gated probe DOL builds were deterministic across two independent rebuilds
- low and high intended probe DOLs matched their re-extracted final DOLs byte-for-byte
- the only original-to-probe DOL changes were the entry-gate word, the new text-section header entry, and the appended payload bytes
- no hook instruction or arena-reservation patch was installed in either image

Therefore the image-build and ISO-delivery path is proven for both gated probe placements. The remaining uncertainty is now strictly about what the Wii loader and startup path make visible in live memory.

## Verified hook status

No Corruption hook metadata was added to production code.

The minimum proof bar is still unmet because there is no candidate that simultaneously satisfies:

- exact version-specific address
- verified original instruction
- safe displaced semantics
- understood calling context
- proven safe payload memory

## Live probe observation result

What is verified from the exact rebuilt halted-entry probe ISOs:

- Dolphin was launched with the exact absolute rebuilt ISO paths
- the running Dolphin process command lines still referenced those exact paths
- both runs halted with the gated startup words still in memory:
  - `0x80006320 = 0x48000000`
  - `0x8000633c = 0x38000000`
- both runs reported live game ID `RM3E01`
- both runs reported:
  - `0x800000f4 = 0x817fc3a0`
  - `*(0x817fc3a8) = 0`
  - `0x80000034 = 0x817fe3a0`
  - `0x80003110 = 0x817fe3a0`
- low appended-text placement at `0x806843c0` was fully present at the halted-entry state:
  - payload SHA-256 matched `aad91d2d09ecb59f1f86dba8c6b806640e687ce57d53c96a336708e969d821c2`
  - canary matched
  - counter remained `0`
- high appended-text placement at `0x817e0000` was already absent at that same halted-entry state:
  - the full `148`-byte range read back as zeroes
  - live payload SHA-256 was `3b18c58c739716e76429634a61375c45b3b5cd470c22ab6d3e14cee23dd992e1`
  - canary did not match
  - counter remained `0`

What this proves:

- Dolphin's Wii DOL loader copied the appended low-address text section before the retail entry instruction executed
- the same loader/startup path did not leave the appended high-address text section intact at that halted-entry state

What is not verified:

- the exact loader rule that rejects or clears the high-address placement
- the writer PC that eventually changes a valid low-address payload at later checkpoints
- the writer PCs for `0x80000034` and `0x80003110`

## CI and packaging implications

What is now source-backed and testable:

- toolchain discovery and version validation
- deterministic payload manifest generation
- payload artifact validation
- source digest tracking
- reproducibility checks where devkitPPC is present

What is still missing from repository-wide support:

- CI installation of the pinned devkitPPC package set
- a checked-in workflow that builds the payload on CI
- cross-platform verification on macOS and Linux for this new payload path

## Exact remaining blockers before a harmless executable hook test

1. Re-check the low-address payload at later checkpoints after releasing the entry gate and capture the earliest point where it changes.
2. Capture the writer PC for the first change to the low-address payload range.
3. Determine why the high-address appended section is already zero at the halted-entry state.
4. Capture the actual writer PCs for `0x80000034` and `0x80003110` on the active retail boot path.
5. Only after those live-writer facts are known should arena-reservation candidates or a harmless hook be revisited.

Until those five steps are complete, the project should stop at source-built artifact generation and validated halted-entry observation rather than pretending runtime execution is ready.

## Retail IPC wrapper correction

The NTSC retail wrapper sequence is now statically classified through operation `7`. The former ioctl labels at `0x80504A08..0x80504D10` were incorrect: those four functions are the async/sync read and write pairs. Seek follows at `0x80504E18/0x80504EF8`; the actual async/sync ioctl pair is `0x80504FE0/0x80505118`; vector preparation is at `0x80505248`; and async/sync vector ioctl is at `0x80505384/0x80505468`.

The lower request is `0x40` bytes aligned to `0x20`. Proven common fields are operation `+0x00`, completion result `+0x04`, fd `+0x08`, operation-specific union fields `+0x0c..+0x1c`, completion function `+0x20`, completion userdata `+0x24`, and a special vector flag at `+0x28`. For ioctl, the union stores command, input pointer/length, and output pointer/length in that order. The completion dispatcher calls `request+0x20(request+0x04, request+0x24)` and then frees the request.

The explicit developer-only `--ios-nwc24-via-retail-ioctl-once` implementation targets `0x80504FE0`, guarded by the retail DOL and function fingerprints. It opens `/dev/net/kd/request`, submits command `6` exactly once with `r3..r10 = fd, command, input, input_length, output, output_length, callback, userdata`, and enters `NWC24_COMPLETE` after the callback. Its project-owned callback context and `0x20`-byte output buffer remain valid through completion. It does not submit CLOSE_KD, OPEN_IP, receive, send, CP3W, or mailbox work; the old async-read target `0x80504A08` remains unreachable as ioctl.

`--ios-close-kd-once` extends that proof by exactly one operation. It validates the successful NWC24 completion before calling retail `close_async` at `0x805048A0` with `r3=fd`, `r4=completion`, and `r5=project-owned close context`; the supported DOL fingerprint and the close-wrapper fingerprint guard this interface. A successful callback records the descriptor transition from the retained KD fd to `-1`, sets `kd_closed`, and enters terminal `KD_CLOSED`. It does not advance to OPEN_IP.

`--ios-open-ip-once` now extends the same prerequisite chain through `OPEN_IP`. It remains developer-only and still starts with `OPEN_KD -> NWC24_STARTUP -> CLOSE_KD`, but after the successful close callback it calls retail `open_async` at `0x80504668` with `r3 = persistent "/dev/net/ip/top"` storage, `r4 = 0`, `r5 = runtime_ios_callback`, and `r6 = project-owned open-IP context`. The runtime records the submitted path pointer, bounded path length, callback pointer, context pointer, callback-exit count, stale/duplicate callback counts, and `ip_fd` before submission into manifest-backed runtime state so the read-only observer can prove the exact ABI without enabling any later network phase. The verified live result is a single successful callback returning descriptor `11`, terminal `IP_OPEN` (`0xFE`), `kd_fd = -1`, `kd_closed = true`, and no `SO_STARTUP`, host-id, socket, bind, receive, send, CP3W, or mailbox activity.

`--ios-so-startup-once` extends that same developer-only proof by exactly one additional operation and then stops before `GET_HOST_ID`. After the successful `OPEN_IP` callback, it calls the verified retail async ioctl wrapper at `0x80504FE0` with `r3 = ip_fd`, `r4 = 31`, `r5 = 0`, `r6 = 0`, `r7 = 0`, `r8 = 0`, `r9 = runtime_ios_callback`, and `r10 = project-owned persistent startup context`. The runtime records the target, command, submitted fd, callback/context pointers, `r3..r10` pre-call snapshot, callback exit count, stale/duplicate callback counts, `service_started` before/after, `ip_fd` before/after, and pending/phase transitions into manifest-backed runtime state. The verified live Dolphin result is synchronous result `0`, one callback with result `0`, matching generation `5`, retained `ip_fd = 11`, `service_started = true`, and terminal `SO_STARTED` (`18`) with no `GET_HOST_ID`, socket, bind, receive, send, CP3W, or mailbox activity.
