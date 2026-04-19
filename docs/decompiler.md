---
title: Decompiler Setup
nav_order: 31
---

# Ghidra + Patched V850/RH850 SLEIGH

## Why stock Ghidra fails on Transit

The Transit PSCM (2025) runs Renesas RH850 — the V850 family with extended 32-bit instruction encodings. Ghidra 12's stock V850 spec (`v850e2`) does not know these extensions and emits `halt_baddata()` for ~660 instruction instances in the Transit firmware, causing the decompiler to fail or produce garbage on affected functions.

The F-150 PSCM (2022/2021) is still a V850-family target, but in **this**
Ghidra extension/workflow the full ELF lifts materially better when imported as
`v850e3:LE:32:default` than as plain `v850:LE:32:default`.

## Our patched SLEIGH

Location: `tools/ghidra_v850_patched/`  
Fork of: [esaulenka/ghidra_v850](https://github.com/esaulenka/ghidra_v850)

### Patches applied

1. **Case fix** in `loop` (`v850e3.sinc`): `r0004` → `R0004` — matched attach table.
2. **Stub decoders** for 7 undocumented RH850 extended ops (`op2126 = 0x03, 0x0A, 0x0D, 0x31, 0x32, 0x37, 0x39`). Covers ~660 Transit firmware instances.
3. **Extended `sttc.sr`/`stvc.sr`** for selID 8–31 (was 0–7 only).
4. **FPU register-pair fix** (`v850_float.sinc`): `floorf.dw`, `floorf.duw`, `mulf.d` use plain `R1115`/`R0004`.
5. **Register-field casing fixes** across several `.sinc` files.

### Results

| Spec | Clean decompile (100-function sample) |
|---|---|
| Stock Ghidra 12 V850 | 0 / 48 (wrong spec) |
| esaulenka baseline | 42 / 100 |
| **This patch (v850e3)** | **90 / 100** |

Remaining 10 failures are `jr` tail-calls into flash banks not loaded — not SLEIGH bugs.

## Install

```bash
cp -r tools/ghidra_v850_patched ~/Library/ghidra/ghidra_<VERSION>_PUBLIC/Extensions/ghidra_v850
cd tools/ghidra_v850_patched
$(brew --prefix)/Cellar/ghidra/*/libexec/support/sleigh data/languages/v850e2.slaspec
$(brew --prefix)/Cellar/ghidra/*/libexec/support/sleigh data/languages/v850e3.slaspec
```

Restart Ghidra. Language picker shows `v850e3:LE:32:default` — use this for
Transit firmware.  
For the F-150 full ELF in this repo, also use `v850e3:LE:32:default`.
`v850:LE:32:default` is measurably worse on the same image.

Measured on `f150_pscm_ML34-14D007-BDL_full.elf`:

| Processor | Clean | Warnings | Baddata | Failed |
|---|---|---|---|---|
| `v850e3:LE:32:default` | 3349 | 716 | 34 | 5 |
| `v850:LE:32:default` | 2691 | 965 | 383 | 2 |

## Headless scripts

All scripts live in `tools/scripts/`. Use Ghidra's `analyzeHeadless`:

```bash
BASE=$(brew --prefix)/Cellar/ghidra/*/libexec/support/analyzeHeadless
BIN=/tmp/pscm/transit_AH_blk0_0x01000000.bin

# Test clean-decompile rate (ProbeWithSeed = halfword-seeder + clean/bad probe)
$BASE /tmp/proj TestRun \
  -import $BIN -loader BinaryLoader -loader-baseAddr 0x01000000 \
  -processor "v850e3:LE:32:default" \
  -scriptPath tools/scripts \
  -postScript ProbeWithSeed.java -deleteProject 2>&1 | grep RESULT

# Dump every clean decompile to decompiles_clean/<addr>.c
$BASE /tmp/proj DumpRun \
  -import $BIN -loader BinaryLoader -loader-baseAddr 0x01000000 \
  -processor "v850e3:LE:32:default" \
  -scriptPath tools/scripts \
  -postScript DumpDecomps.java -deleteProject

# Hunt for CAN ID references (0x3A8, 0x3CA, 0x213)
$BASE /tmp/proj HuntRun \
  -import $BIN -loader BinaryLoader -loader-baseAddr 0x01000000 \
  -processor "v850e3:LE:32:default" \
  -scriptPath tools/scripts \
  -postScript HuntLKA2.java -deleteProject
```

## Canonical Lift Check

The repo now has one checked-in entrypoint for repeatable headless checks:

```bash
make lift-check
```

That runs:

- Transit block0 seeded lift check using:
  `SetOptions.java -> SeedFromJarls.java -> RH850SwitchTableDetector.java -> CleanupBoundaries.java -> MeasureQuality.java -> SampleProjectLift.java`
- F-150 full-ELF regression check using `F150LiftReport.java`

Artifacts go to `analysis/headless_lift/summary.json` plus per-run log folders.
Transit thresholds default to `clean >= 90`, `baddata <= 10`, `failed <= 10`
on the 100-function post-cleanup sample. F-150 defaults to `clean >= 3200`,
`baddata <= 80`, `failed <= 20`.
The Transit regression project import is intentionally run with `-noanalysis`
so it measures the explicit seeded workflow rather than waiting on Ghidra's
full auto-analysis queue.

The default regression path skips the expensive switch-target expansion inside
`SeedFromJarls.java` so the check stays fast and repeatable. Re-enable it only
when you are actively working on Transit switch recovery:

```bash
python tools/ghidra_lift_regression.py --with-switch-seeding --skip-f150
```

You can also run the wrapper directly:

```bash
python tools/ghidra_lift_regression.py \
  --transit-block0 firmware/Transit_2025/decompressed/AM/block0_strategy.bin \
  --f150-elf firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf
```

### Script inventory

| Script | Purpose |
|---|---|
| `ProbeWithSeed.java` | Halfword-seeder + clean/bad decompile probe — canonical baseline test |
| `DumpDecomps.java` | Dump every clean-decompile function to `decompiles_clean/<addr>.c` |
| `DumpClean.java` | Smaller variant — prints 3 sample clean functions to stdout |
| `HuntLKA2.java` | Scan functions for scalar operands matching CAN IDs (`0x3A8`, `0x3CA`, `0x213`) |
| `Dump3A8Funcs.java` | Find functions by raw-byte occurrence of a CAN ID |
| `ProbeWithBanks.java` | Variant that loads blk1/blk2 alongside blk0 |

## AI annotation pipeline

`tools/pipeline/annotate.py` sends Ghidra decompile output to a local LLM for variable renaming and struct recovery.

```bash
python tools/pipeline/annotate.py \
  --input /tmp/pscm/decompiled/ \
  --endpoint http://100.69.219.3:8000/v1 \
  --model glm-4-flash
```

Runs unattended (parallel). Endpoint is GLM-4.7-Flash on the 5090 workstation (Tailscale `100.69.219.3:8000`). Compatible with any OpenAI-format API.

## Cached outputs

Bulk outputs on disk (regenerate via scripts above):

| Path | Contents |
|---|---|
| `/tmp/pscm/decompiled/` | 2,738 `.c` files, one per function |
| `/tmp/pscm/disasm/` | 2,738 `.asm` files, one per function |
| `/tmp/pscm/transit_{AH,AM,AL}_blk*.bin` | Extracted strategy blocks |
| `/tmp/pscm/Transit_AH.bin` | Extracted calibration blob |

Ghidra project at `~/.ghidra/.../PSCM/` with GhidraMCP plugin (built from source against 12.0.4).
