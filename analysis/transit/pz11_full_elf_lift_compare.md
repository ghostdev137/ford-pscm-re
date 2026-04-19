# Escape 2024 `PZ11` full-ELF lift vs Transit

**Date:** 2026-04-16

This note records a direct Ghidra headless lift comparison between:

- Transit full synthetic ELF:
  - `/Users/rossfisher/Desktop/Transit_2025_PSCM_dump/set_05_cal_AM_strategy_AM_cal_AH/decompressed/transit_pscm_KK21-3F964-AM_full.elf`
- Escape 2024 synthetic full ELF:
  - `/tmp/pz11_pscm_full.elf`

## Why this test exists

A block0-only comparison is too optimistic. The question here was whether
Escape 2024 (`PZ11`) lifts cleanly **as a combined image**, comparable to the
Transit full image, when loaded into Ghidra with the repo's patched
`v850e3:LE:32:default` language.

## `PZ11` full ELF used

There is no checked-in `PZ11` full ELF in the repo, so a synthetic ELF was
built from the unique VBF payload families on disk:

- `PZ11-14D003-FB`
- `PZ11-14D005-AA`
- `PZ11-14D004-FAB`

Two important observations about the raw files:

- `PZ11-14D003-FB` and `PZ11-14D005-AB` are byte-identical on disk.
- `PZ11-14D005-AA` and `PZ11-14D007-EBC` are byte-identical on disk.

The synthetic ELF therefore used these 12 PT_LOAD segments:

```text
0xC0074000  1178112  RX
0xC0193A00      300  RW
0xC0194000    63744  RW
0xC01A3A00      300  RW
0xC01A4000    63744  RW
0xC01B3A00      300  RW
0xD0074000  1178112  RX
0xD0193A00      300  RW
0xD0194000    63744  RW
0xD01A3A00      300  RW
0xD01A4000    63744  RW
0xD01B3A00      300  RW
```

Entry point used:

- `0xC0074000`

## Method

Used a minimal headless Ghidra script set:

- `SetOptions.java`
- `SampleProjectLift.java`

Processor:

- `v850e3:LE:32:default`

### Transit command

```bash
/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/analyzeHeadless \
  /tmp/transit_full_sample30_proj TransitFullSample30 \
  -import /Users/rossfisher/Desktop/Transit_2025_PSCM_dump/set_05_cal_AM_strategy_AM_cal_AH/decompressed/transit_pscm_KK21-3F964-AM_full.elf \
  -processor "v850e3:LE:32:default" \
  -scriptPath /tmp/ghidra_miniscripts \
  -preScript SetOptions.java \
  -postScript SampleProjectLift.java 0x01000000 0x20FFFFFF 30 40 \
  -deleteProject
```

### `PZ11` command

```bash
/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/analyzeHeadless \
  /tmp/pz11_full_sample30_proj PZ11FullSample30 \
  -import /tmp/pz11_pscm_full.elf \
  -processor "v850e3:LE:32:default" \
  -scriptPath /tmp/ghidra_miniscripts \
  -preScript SetOptions.java \
  -postScript SampleProjectLift.java 0xC0000000 0xDFFFFFFF 30 40 \
  -deleteProject
```

## Result

### Transit

Transit completed normally.

From `/tmp/transit_full_sample30.log`:

```text
RESULT total_fns=889 sampled=30 clean=4 warnings=26 baddata=0 failed=0
```

Transit auto-analysis time in the same log was about:

```text
Total Time   11 secs
```

### Escape 2024 `PZ11`

`PZ11` did **not** complete cleanly under the same full-image workflow in a
reasonable amount of time.

Observed during the run:

- headless Ghidra stayed active for well over 2 minutes on the same 2 GB heap
- resident memory reached about 1.0 GB
- the log did not reach a final `RESULT` line in the attempted full-image
  sample run

The warning pattern is also different from Transit:

- many `Unable to resolve constructor at c0.../d0...`
- many `Failed to resolve varnode <R1115pair>`
- many `Failed to resolve varnode <SR1115_...>`
- some `Could not follow disassembly flow into non-existing memory`

In other words:

- Transit full-image lift is noisy but converges.
- `PZ11` full-image lift currently does **not** converge cleanly under the same
  workflow.

## Practical conclusion

For current repo tooling:

- **Transit full ELF:** workable
- **Escape 2024 `PZ11` full ELF:** not yet clean/workable in the same way

That does **not** prove the architecture is fundamentally unsupported. It does
show that the current patched SLEIGH + analysis workflow is tuned for
Transit/LX6C and is not yet good enough to treat `PZ11` as equally liftable.

Best current plain-language answer:

- `PZ11` is **closer than F-150 at the platform motif level**
- but **worse than Transit and worse than Escape 2022 as a practical RE target**
  under the current decompiler workflow
