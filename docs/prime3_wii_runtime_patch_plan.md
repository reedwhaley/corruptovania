# Prime 3 Wii Runtime Patch Plan

## Scope of this milestone

This milestone establishes a source-backed Wii PowerPC payload build path and a validated payload artifact contract. It does not enable runtime networking, install a production hook, or claim that any Corruption runtime memory reservation is safe.

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

- the exact Corruption routine that finalizes ArenaLo or ArenaHi
- whether a static MEM1 payload above current BSS survives every later game allocator step
- whether a MEM2-backed DOL text section is a safe and supported loader target for this title
- a Corruption-specific executable runtime allocation path with known cache-management semantics
- a REL-safe exclusion boundary for injected code

## Arena and heap findings

No Corruption-specific arena reservation is verified in this milestone.

Evidence quality today:

- generic Wii low-memory arena fields and MEM2 usable-range fields are known
- Corruption-specific DOL header layout is known
- Corruption-specific arena-boundary setter instructions are not yet identified

Because that last step is missing, no production allocation metadata was added. Empty address space above BSS is not treated as safe by default.

## Allocation strategy evaluation

### 1. Static DOL section above existing BSS in MEM1

- theoretical capacity: up to the remaining MEM1 headroom above `0x806843a4`
- branch reachability from startup code: yes
- current status: rejected for production
- blocker: no proof that Corruption excludes the chosen range from later arena or heap allocation

### 2. Static DOL section in a MEM2 range

- theoretical capacity: much larger
- branch reachability from startup entry via single relative branch: no
- current status: rejected for production
- blockers:
  - no Corruption-specific loader proof for MEM2 DOL sections
  - no verified MEM2 reservation for this title
  - would require a proven trampoline or secondary hop strategy

### 3. Reserve memory by reducing an arena boundary

- current status: best long-term candidate class, but not verified
- blocker: no exact version-specific instruction or data write has been proven yet

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
- execution frequency: once
- displacement safety with the current conservative trampoline helper: yes, because this instruction is plain non-control-flow
- stack validity: better than the raw entry instruction because the prologue has already executed, but still not fully ABI-proven for payload entry
- branch reachability:
  - MEM1/BSS-adjacent candidates: yes
  - MEM2 candidates via one direct relative branch: no
- confidence: low
- missing proof:
  - exact startup invariants at this point
  - whether this location occurs after all required OS and arena initialization
  - whether a payload entered here could safely touch any runtime service needed later

An earlier startup address, `0x80006320`, is also exact and easy to identify, but its original instruction is `0x4800016d` (`bl 0x8000648c`), which is a control-flow instruction and therefore rejected by the current conservative single-instruction trampoline builder.

## Verified hook status

No Corruption hook metadata was added to production code.

The minimum proof bar is still unmet because there is no candidate that simultaneously satisfies:

- exact version-specific address
- verified original instruction
- safe displaced semantics
- understood calling context
- proven safe payload memory

## Harmless executable validation result

This milestone did not create a temporary source-built payload DOL copy.

Reason:

- the source-built return-only payload is now valid as an artifact
- the DOL patcher can insert it structurally
- but no safe reserved runtime range has been verified yet

Without a proven reservation, even an unreferenced source-built payload section would encourage the wrong conclusion about runtime safety.

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

1. Identify the exact Corruption arena or heap boundary mechanism that can reserve a payload range explicitly.
2. Prove that the reserved range survives startup and remains excluded from later heap and REL allocation.
3. Upgrade at least one hook candidate from low-confidence evidence to version-specific verified metadata with understood calling context.
4. Only then combine the existing DOL patch primitives with the source-built payload artifact in a temporary, unreferenced, harmless DOL validation.

Until those four steps are complete, the project should stop at source-built artifact generation and validation rather than pretending runtime execution is ready.
