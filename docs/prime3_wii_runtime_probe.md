# Prime 3 Wii Runtime Probe

## Scope

This workflow verifies only the developer-only probe delivery chain:

- source probe payload
- temporary unhooked `main.dol`
- temporary rebuilt ISO
- re-extracted `main.dol`
- live Dolphin memory observation

It does not install a hook, reserve arena space, or claim any runtime-safe payload address.

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
  --report <temp>\probe-section.json
```

The probe DOL builder:

- starts from the retail `main.dol`
- installs no layout UUID
- installs no hook
- installs no arena reservation patch
- appends the probe payload as a new unused text section at the smallest aligned address above the mapped sections and BSS

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
  --report <temp>\probe-delivery.json
```

Pass:

- intended probe DOL hash equals temporary-root DOL hash
- intended probe DOL hash equals re-extracted final DOL hash
- final extracted DOL keeps the same new text-section entry
- final extracted DOL keeps the same payload bytes

Observed static result for the current probe image:

- original retail `main.dol` SHA-256: `6b550f221602074747a2e61b0aa064203fd493f6865dfb3b1a912682065e6104`
- intended probe `main.dol` SHA-256: `bc3aec3bf0ea27cc6fbd7d7fb07dc15c06480da63a8f523df706197cfe53a2b2`
- re-extracted final `main.dol` SHA-256: `bc3aec3bf0ea27cc6fbd7d7fb07dc15c06480da63a8f523df706197cfe53a2b2`
- rebuilt probe ISO SHA-256: `6b726f78cc072d21b213c9660d7368b5e4b630f6315acf14c0e5872a87d29621`

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
  --startup-word 0x8000633C=0x38000000
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

Observed post-boot read-only result from the exact rebuilt probe ISO:

- game ID matched `RM3E01`
- startup word `0x8000633c` still matched the retail `0x38000000`
- `0x800000f4 = 0x817fc3a0`
- `*(0x817fc3a8) = 0`
- `0x80000034 = 0x817fe3a0`
- `0x80003110 = 0x817fe3a0`
- the full payload range at `0x806843c0` read back as zeroes at the observed post-boot checkpoint
- the canary therefore did not match
- the counter still read `0`

This is not an entrypoint result. It proves only that the payload does not survive unchanged to the observed post-boot checkpoint.

## Entrypoint Breakpoint Procedure

The current repository tooling does not automate a pre-entry breakpoint. Use Dolphin's debugger manually:

1. Launch the exact temporary ISO with a unique Dolphin user directory.
2. Open the debugger before letting emulation continue.
3. Set an execution breakpoint at `0x80006320`.
4. Break before the entry instruction executes.
5. Inspect:
   - `0x8000633C`
   - the appended payload address range
   - canary bytes
   - counter value
   - `0x80000034`
   - `0x80003110`
   - `0x800000F4`
6. Only if `0x800000F4` is valid, inspect `*(0x800000F4 + 0x08)`.

If the payload is missing already at `0x80006320`, conclude either:

- the wrong image booted, or
- the loader did not copy the new section

Do not continue into overwrite or reservation analysis until the image identity and DOL delivery chain are proven.

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

If the payload is already zero at the first observable checkpoint after entry, do not infer the writer. Continue only with a real entry breakpoint and memory-check capture.

## Cleanup

- remove repository-local build artifacts
- keep temporary DOL, ISO, and report files only outside the repository
- if retained for manual debugging, record the retained temporary paths explicitly
