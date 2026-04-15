# Phase 4 Notes — Switch Table Detector

## Runtime
Ghidra 12.0.4 ships PyGhidra, but `analyzeHeadless` can't run .py scripts
(requires the separate `pyghidraRun` launcher, and pip-installing the
`pyghidra` package fails on macOS due to Jpype1 build breakage).
Ported the detector to Java: `RH850SwitchTableDetector.java`. Two small
API fixups vs the Python version:
 - `FunctionManager.getFunctionBefore/After` don't exist in 12.0.4. Used
   `fm.getFunctions(addr, forward)` iterator instead.
 - `CodeUnit.PLATE_COMMENT` is deprecated but still works (warning only).

## Baseline (scratch clone `/tmp/ghidra_phase4/Transit`)
total=2194, halt_baddata=1543, bad_bm=679, median_size=11

## Detector result
Tables found: 4, total entries: 19, bytes cleared: 0.

## Post measurement
total=2194, halt_baddata=1543, bad_bm=679 — **zero delta**.

## Diagnosis (why the hypothesis was wrong)
Spot-checked 5 halt_baddata functions (01007b0c, 01008394, 01007c80,
0100d388, 0100cc88). None fall through into a switch jump table.
Patterns observed instead:

1. **Inter-function padding mis-seeded as a function**
   (e.g. 01007b0c): one real instruction, then 20+ NOPs, then a bad byte.
   These are alignment regions the Phase 2 seed list picked up as entry
   points. Splitting / deleting them would help `halt_baddata` counts but
   the functions are harmless — decompile is just `__nop(); ... halt_baddata()`.

2. **Data region disassembled as code** (e.g. 01008394): repetitive
   `divh r16,r16` / `mulh sp,r15` / `sld.h 0x2[ep]` every 2–4 bytes is
   the RH850 decode of calibration constants. Seeded function entry
   points land inside the cal block.

3. **SLEIGH pcode failure on legit instructions** (see
   `/tmp/sleigh_pcode_failures.tsv`): `r1115` unresolved in the v850
   extension is the top bucket (100+ fail sites). Phase 3 reverted the
   fix; that's independent of jump-table detection.

## Next-step recommendation
Jump-table detection is not the lever. Better candidates:
 - Audit the Phase 2 seed JSON and drop entries that land in NOP-padding
   or inside the cal-block address range (0x01d0_0000–0x01ff_ffff-ish).
 - Split or truncate seeded functions so their `body` doesn't extend into
   the first bad byte (CleanupBoundaries already does this by trailing
   byte, but not by "instruction decodes to garbage pattern").
 - Revisit the `r1115` SLEIGH issue in the v850 extension — that alone
   accounts for ~400 of the 1543 halt_baddata functions per
   `sleigh_pcode_failures.tsv`.
