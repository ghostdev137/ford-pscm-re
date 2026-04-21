# SeedFromPointerTables — function discovery via flash pointer scan

Complements `SeedFromJarls.java`. Walks every 4-byte-aligned word in
every initialized memory block and creates a function at each value
that lands inside an executable band (`0x01000000..0x01100000`,
`0x20FF0000..0x21050000`, `0x00F9C000..0x00FD0000`), filtering out
odd-aligned values.

## Why it helps

Transit AUTOSAR firmware keeps large Rte/Dem/Dcm callback arrays in
rodata. Those targets are reached by indirect load (`ld.w 0[rX], rY;
jarl rY, lp`) rather than direct `jarl imm22`, so Ghidra's
auto-analyzer doesn't treat them as function starts.

## Impact on Transit_AM_FullLift (AM strategy)

| Stage | Functions |
|---|---|
| Before (post SeedFromJarls + full-lift cleanup) | 4813 |
| After SeedFromPointerTables.java (+165 direct seeds) | 4978 |
| After follow-up auto-analysis re-run | **5713** |

**+900 functions (+18.7%)** from one script + one re-analysis pass.
Most of the delta comes from the re-analysis propagating new call/return
edges from the seeded leaves.

## Run

```bash
analyzeHeadless PROJECT_DIR PROJECT_NAME \
  -process <program.elf> \
  -scriptPath tools/ghidra_v850_patched/seeds \
  -postScript SeedFromPointerTables.java
# then re-run auto-analysis to propagate
analyzeHeadless PROJECT_DIR PROJECT_NAME \
  -process <program.elf> \
  -scriptPath tools/scripts \
  -postScript CountFunctions.java
```

Idempotent; re-runs skip existing functions.

## Tuning

`EXEC_BANDS[][]` controls which pointer targets count. Extend the list
if loading additional blocks (e.g., SBL at `0x00F9C000`, block2 at
`0x20FF0000`). Odd-aligned pointers are always rejected because V850
instructions are 2-byte aligned.

## What it *doesn't* do

- Won't recover functions whose entry is only reached by
  constant-propagated `movhi + movea` (those need Ghidra's
  Decompiler-based constant propagation, kept ON by
  `SetOptionsAggressive.java`).
- Won't recover callt-dispatched handlers (use the CTBP table at
  `0x0100220C` for that — separate tooling needed).
- Will false-positive on non-pointer data that coincidentally looks
  like a code address. Follow up with `CleanupBoundaries.java` if
  the false-positive rate gets noisy.
