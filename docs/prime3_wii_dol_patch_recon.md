# Prime 3 Wii `main.dol` Patch Recon

## Scope

This document records a reconnaissance pass over the existing Prime 3 Wii `main.dol` patch artifact shipped in this repository. The goal was to determine whether the current `main.hdiff` already establishes a safe runtime-code hook, a reusable executable payload seam, or any source-backed injection point for future Wii networking work.

This pass is limited to:

- local repository history and shipped artifacts
- structural analysis of the original DOL and a locally patched temporary copy
- synthetic tests for the analysis tooling

This pass does not claim behavior that was not directly observed in the binary diff.

## Inputs And Method

- Original DOL path: `E:\ROMS\Corruption Extract\DATA\sys\main.dol`
- Patch artifact: `randovania/data/gollop_mp3_patcher/MP3Update/main.hdiff`
- Patch tool path: `C:\Users\Reed Whaley\Documents\MP3 Networking\randovania\data\gollop_mp3_patcher\hpatchz.exe`
- Analyzer script: `tools/prime3_patcher/analyze_main_dol_patch.py`

Procedure:

1. Copy the original `main.dol` to a temporary directory outside the repository.
2. Apply `main.hdiff` to the temporary copy with `hpatchz.exe`.
3. Compare the original and patched DOLs with `tools/prime3_patcher/analyze_main_dol_patch.py`.
4. Record DOL header structure, changed ranges, changed branch instructions, and zero-filled candidate regions.
5. Cross-check the binary artifact against local repository history and accompanying update notes.

Exact patch command used:

```powershell
& 'C:\Users\Reed Whaley\Documents\MP3 Networking\randovania\data\gollop_mp3_patcher\hpatchz.exe' `
  -f '<temp>\main.patched.dol' `
  'C:\Users\Reed Whaley\Documents\MP3 Networking\randovania\data\gollop_mp3_patcher\MP3Update\main.hdiff' `
  '<temp>\main.patched.dol'
```

`hpatchz.exe` reported:

- old size: `6045952`
- diff size: `81`
- new size: `6045952`
- result: `patch ok`

## Build Identification

The original DOL matches the Wii NTSC Corruption build expected by `open_prime_rando.dol_patching.corruption.dol_versions.ALL_VERSIONS[0]`, based on the build string at virtual address `0x805822B0`.

Observed file hashes:

- Original SHA-256: `6b550f221602074747a2e61b0aa064203fd493f6865dfb3b1a912682065e6104`
- Patched SHA-256: `05bfd79478121fe32a72a64b9ef0c701088e80aea0cc4c57907ea7e9d14f0f32`

## DOL Structure Summary

The original and patched DOL headers are structurally identical:

- entry point: `0x80006320`
- BSS address: `0x805C0800`
- BSS size: `0x0C3BA4`
- section mappings changed: `false`
- file size delta: `0`

Mapped sections observed in the binary:

| Section | File Offset | Virtual Address | Size |
| --- | --- | --- | ---: |
| `text0` | `0x100` | `0x80004000` | `0x26C0` |
| `text1` | `0x27C0` | `0x80006EA0` | `0x56E7E0` |
| `data0` | `0x570FA0` | `0x800066C0` | `0x360` |
| `data1` | `0x571300` | `0x80006A20` | `0x480` |
| `data2` | `0x571780` | `0x80575680` | `0x8C0` |
| `data3` | `0x572040` | `0x80575F40` | `0x20` |
| `data4` | `0x572060` | `0x80575F80` | `0x19200` |
| `data5` | `0x58B260` | `0x8058F180` | `0x31660` |
| `data6` | `0x5BC8C0` | `0x806781C0` | `0x1E80` |
| `data7` | `0x5BE740` | `0x8067E9C0` | `0x59C0` |

No additional mapped sections were introduced by the patch.

## Observed Binary Changes

The analysis found exactly four changed ranges. All four are in `data5` and each range is seven bytes long.

| File Offset | Virtual Address | Length | Classification | Section |
| --- | --- | ---: | --- | --- |
| `0x5A20EA` | `0x805A600A` | `7` | `data` | `data5` |
| `0x5A2162` | `0x805A6082` | `7` | `data` | `data5` |
| `0x5A219E` | `0x805A60BE` | `7` | `data` | `data5` |
| `0x5A21DA` | `0x805A60FA` | `7` | `data` | `data5` |

Additional observed facts:

- no text-section bytes changed
- no header bytes changed
- no file-growth or appended payload region was introduced
- no section table entries were added, removed, or resized
- no changed unconditional `b` or `bl` instructions were detected

The repeated replacement pattern is consistent with a very small in-place data-table tweak rather than code injection. That is an inference from the byte-diff shape, not a proven semantic decode.

## Hook And Payload Assessment

### Existing Runtime Hook

No executable hook is proven by this patch.

Reasoning:

- every observed change is in a data section
- no changed instructions were found in text sections
- no branch rewrite was detected
- no executable file growth was introduced

### Existing Payload Region

No safe executable payload region is proven by this patch.

Reasoning:

- the patch does not expand the DOL
- the patch does not remap or grow any executable section
- the analysis did not establish that any observed zero-filled region is intentionally reserved for injected code

### Reusable Injection Seam

No reusable injection seam is established by the current `main.hdiff`.

The artifact is a tiny, in-place, data-only patch. It should not be treated as evidence of an existing source-backed runtime-patching framework for Prime 3 Wii.

## Relationship To Known Corruption Runtime Metadata

The observed changed addresses do not overlap the known `open_prime_rando` Corruption metadata points used elsewhere in the codebase:

- build string: `0x805822B0`
- `CStateManager` global: `0x805C4F70`
- game state pointer: `0x8067DC0C`
- string display pointer: `None` for this build metadata set

The changed addresses are clustered around `0x805A600A` through `0x805A60FA`, which is separate from the metadata locations above.

## Patch Provenance In This Repository

Local repository history shows:

- `randovania/data/gollop_mp3_patcher/MP3Update/main.hdiff` was introduced by commit `b8718d189` (`bump mp3 update again`)
- `randovania/data/gollop_mp3_patcher/MP3Update.bat` is older and does not patch `main.dol`; it patches `.pak` assets only
- exporter-side DOL patch behavior is tied to the later Prime 3 exporter path, with the relevant refactor landing in commit `9ae9897d6` (`add flicker support and refactor exporting`)

This means the currently shipped DOL patch is not part of the older batch-file patch flow. It is an exporter-side addition layered on later.

## Source Correlation

No local source file was found that directly describes the exact seven-byte replacements in `main.hdiff`.

What is available locally:

- the binary patch artifact itself
- repository history showing when the artifact appeared
- update notes in `randovania/data/gollop_mp3_patcher/README.txt`

One relevant update note says the patch set removed a black line visible in the main menu at resolutions above native. That aligns with the idea that this DOL patch may be related to display or filter behavior, but it does not prove the exact semantics of the four seven-byte edits.

## Conclusions

- The existing Prime 3 Wii `main.hdiff` is a tiny data-only patch.
- It does not prove a code hook, branch trampoline, payload region, or executable extension point.
- It does not provide a verified safe place to attach a future Wii networking runtime payload.
- It does not overlap the known Corruption runtime metadata addresses already used by `open_prime_rando`.

## Recommended Next Step

Do not build a new runtime payload on top of this `main.hdiff`.

The next engineering step should be one of:

1. obtain the original source or design notes that produced this DOL patch, if they exist
2. design a new, source-backed DOL patch path specifically for the Wii networking payload
3. separately verify a real hook site and a real executable payload allocation strategy before adding any runtime metadata seam to the repository

Until one of those paths is completed, there is no evidence-backed reason to treat the current Prime 3 Wii DOL patch as reusable runtime-hook infrastructure.
