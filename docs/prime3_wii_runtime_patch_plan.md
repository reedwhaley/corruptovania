# Prime 3 Wii Runtime Patch Plan

## Scope of this milestone

This milestone establishes source-backed infrastructure for future Prime 3 Wii runtime injection. It does not enable runtime networking, select a production hook, or claim that Wii networking is operational.

Implemented foundations now live in [`randovania/games/prime3/exporter/dol_patcher.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/games/prime3/exporter/dol_patcher.py:1):

- DOL header parsing for all 7 text slots and 11 data slots
- deterministic executable text-section insertion
- guarded instruction-word replacement
- PowerPC opcode-18 unconditional branch encoding
- conservative single-instruction trampoline planning
- payload artifact metadata with deterministic JSON serialization and SHA-256 validation
- existing layout-UUID patch support

## Current export and patch path

- [`randovania/games/prime3/exporter/game_exporter.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/games/prime3/exporter/game_exporter.py:60) extracts the Wii image, optionally applies `main.hdiff`, stages `Standard.ntwk` and `.pak` updates, runs `MP3Randomizer`, and repacks with `wit`.
- [`randovania/games/prime3/exporter/toolchain.py`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/randovania/games/prime3/exporter/toolchain.py:58) resolves only `MP3Randomizer`, `hpatchz`, `wit`, and `nodtool`/Python `nod`.
- [`tools/prime3_patcher/MP3Randomizer/MP3Randomizer/Patches.cs`](/C:/Users/Reed%20Whaley/Documents/MP3%20Networking/tools/prime3_patcher/MP3Randomizer/MP3Randomizer/Patches.cs:268) and related C# assets patch `.pak` and `Standard.ntwk`, not PowerPC instructions.
- The source-backed Python DOL patcher is now the only repo-supported place for deterministic `main.dol` mutation beyond the bundled `main.hdiff`.

## DOL executable-section insertion strategy

`append_executable_text_section(...)` adds one new file-backed executable section only when the caller provides all placement metadata explicitly:

- `payload_bytes`
- `payload_virtual_address`
- `required_alignment`
- optional `entry_symbol_offset`

The API guarantees:

- all text and data section table entries are parsed and preserved
- the first genuinely empty text slot is selected
- insertion fails if no empty text slot exists
- appended file offset is aligned to the requested power-of-two alignment
- virtual overlap with any existing text/data section is rejected
- file-range overlap with any existing mapped section is rejected
- BSS overlap is rejected
- 32-bit address and size overflow are rejected
- malformed or truncated DOL headers are rejected
- duplicate/conflicting insertion is rejected through the overlap and slot-availability checks
- the result reports slot index, file offset, virtual address, payload size, alignment padding, resulting file size, and optional entry symbol address

Production code must continue to require `payload_virtual_address` explicitly. Analysis helpers may suggest candidates, but no automatic address selection is safe enough to ship.

## Branch encoding constraints

`encode_ppc_unconditional_branch(...)` currently supports PowerPC opcode 18 only:

- relative branch
- relative branch-and-link
- absolute branch when the target is representable in the 26-bit absolute encoding

Guardrails:

- source and destination must be 4-byte aligned
- relative displacement must stay within the signed 26-bit range
- absolute targets are limited to `0x00000000..0x01fffffc`
- unsupported or overflowing forms fail explicitly instead of truncating bits

Tests round-trip generated instructions through the existing DOL analyzer decoder so the encoded branch semantics are checked against the repo’s analysis tooling.

## Guarded hook requirements

`patch_guarded_instruction_word(...)` is the future hook-installation primitive. It only patches a single mapped executable-text instruction when:

- the target address resolves through the DOL section table
- the target lies in a text section
- the target is 4-byte aligned
- the current instruction exactly matches `expected_original_word`

It rejects:

- unmapped targets
- data-section targets
- truncated instructions
- unexpected originals
- already-replaced instructions

It does not search heuristically for patterns. Future production hook metadata must carry an exact version-specific address and exact original instruction word.

## Trampoline limitations

`build_single_instruction_trampoline(...)` only plans the smallest safe trampoline shape:

1. branch from the hook to the payload entry
2. copy one displaced instruction into the trampoline location
3. branch from the trampoline back to the return address

This helper is intentionally conservative. It rejects at least:

- conditional branches
- unconditional branches
- PC-relative control-flow instructions
- selected opcode-19 branch forms (`bclr`, `bcctr`)
- missing or ambiguous trampoline placement
- branch range failures

This is enough to validate patch structure without claiming that arbitrary PowerPC instructions are relocation-safe.

## Payload artifact contract

`Prime3PayloadArtifact` defines the source-backed payload metadata contract. The serialized form carries:

- raw payload bytes as base64
- required virtual load address
- entry-symbol offset
- required alignment
- payload SHA-256
- protocol-manifest version
- build-tool identity
- build-tool version
- source-tree digest

Host-machine paths are intentionally excluded. Validation enforces:

- power-of-two alignment
- entry offset inside the payload
- SHA-256 match
- 32-bit address arithmetic safety for the payload and entry symbol

Because there is no supported compiler pipeline yet, the artifact contract is currently exercised with synthetic payload fixtures only.

## Compiler and toolchain findings

Repository-supported build tooling does not currently include a Wii-native PowerPC compiler or linker.

Verified repository-supported tooling:

- Python 3.12
- installed `open_prime_rando`
- installed `ppc_asm`
- .NET build flow for `MP3Randomizer`
- helper packaging for `wit`, `hpatchz`, and `nodtool`

Not proven in the repo, CI, or release packaging:

- `powerpc-eabi-gcc`
- `powerpc-eabi-ld`
- `powerpc-eabi-objcopy`
- `devkitPPC`
- `clang`/LLVM configured for `powerpc-none-eabi`
- `libogc`
- a linker script or deterministic raw-binary emission path for Prime 3 runtime code

Local PATH checks also did not find the common PPC tool names. `ppc_asm` is useful for instruction assembly and DOL editing, but it is not a repository-backed native payload compiler pipeline.

Conclusion: this milestone must stop at artifact metadata, insertion primitives, and synthetic validation. The remaining toolchain decision is still a blocker for any real source-built Wii runtime payload.

## Real NTSC DOL section-slot analysis

The user-provided retail NTSC DOL at `E:\ROMS\Corruption Extract\DATA\sys\main.dol` was inspected from a temporary copy only.

Verified header layout:

- used text slots: `text0`, `text1`
- unused text slots: `text2`, `text3`, `text4`, `text5`, `text6`
- used data slots: `data0` through `data7`
- unused data slots: `data8`, `data9`, `data10`
- highest mapped text end: `0x80575680`
- highest mapped data end: `0x80684380`
- BSS range: `0x805c0800..0x806843a4`

Theoretical non-overlapping virtual gaps after excluding all mapped sections and BSS:

- `0x80575f60..0x80575f80` size `0x20`
- `0x805c07e0..0x805c0800` size `0x20`

Both of those tiny gaps are within relative-branch reach of existing text sections, but they are only 32 bytes each. They are not a viable long-term runtime allocation strategy.

Raw mapped-section gaps that looked larger at first glance are not safe candidates once BSS is excluded. In particular, the apparent `0x805c07e0..0x806781c0` section-table gap is mostly consumed by BSS and must not be used for injected code.

File append behavior for the temp validation used `0x20` alignment. The appended payload landed at file offset `0x005c4100`, which required no extra padding because the retail file size was already aligned.

## Temporary unreferenced payload-section validation

A harmless synthetic validation was performed against a temporary copy only:

- payload bytes: four `nop` instructions, 16 bytes total
- payload virtual address: `0x80575f60`
- selected text slot: `text2`
- payload file offset: `0x005c4100`
- entry symbol address: `0x80575f60`

Analyzer verification on the temporary copy showed:

- one new appended payload region only
- header changes limited to the new text-slot mapping fields
- no existing mapped-section bytes changed
- no decoded branch changes
- no hook instruction changes

The original retail DOL remained untouched and no proprietary payload bytes entered Git.

## Hook reconnaissance status

No Corruption hook is verified for production use in this milestone.

Current evidence still stops short of the required bar:

- no version-specific hook address is proven against the retail NTSC DOL
- no exact original instruction word is committed as production metadata
- no per-frame or otherwise suitable lifecycle hook is proven with sufficient ABI context
- no confirmed payload placement larger than the tiny 32-byte header gaps is available

The repo and installed `open_prime_rando` metadata continue to show that Corruption lacks the `string_display.update_hint_state` hook metadata used by the existing remote-execution model in other Prime titles.

Status:

- verified hook: none
- candidate hooks worth future investigation: main-loop, startup, and state-manager update paths only at the evidence level, not as production addresses

## CI and release packaging implications

Current CI and release packaging can validate:

- Python patch logic
- protocol manifests and vectors
- analyzer behavior
- exporter integration

Current CI and release packaging cannot validate:

- PowerPC payload compilation
- linker-script correctness
- deterministic raw Wii binary emission
- cache-management or IOS import behavior inside retail Corruption

Until a supported native toolchain is added to repo policy and CI, all runtime-payload work must remain at the metadata and synthetic-fixture layer.

## Exact next blocker

The next blocker before real runtime networking code is not hook patching logic anymore. It is the missing repository-supported Wii payload build strategy.

That blocker must be resolved together with:

- a CI-supported compiler/linker path
- a larger verified executable payload allocation strategy for Corruption
- a version-specific verified hook site with exact original instruction data

Only after those three pieces are proven should the project start adding native runtime behavior such as IOS networking, sockets, threads, mailbox handling, or item/location delivery.
