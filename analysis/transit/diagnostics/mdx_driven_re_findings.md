# Transit PSCM — MDX-Driven RE Findings (2026-04-20)

Initial RE pass using the VIN-session FDRS MDX (`730_PSCM.xml` — 106 DIDs,
10 routines, 50 DTCs) to locate dispatch structures and per-DID handlers
in the Transit 2025 PSCM strategy firmware.

## Summary

| Finding | Status | Location |
|---|---|---|
| Primary DID ID dispatch table | **Found** | flash `0x0100DB7A` — 74 entries |
| Secondary DID handlers (scattered) | Partial | distributed in flash |
| DID leaf-handler candidates (in Ghidra) | 9 labeled | see below |
| Routine handlers | 2 labeled | `0xFEB0`, `0x0301` |
| DCM dispatcher | Not yet located | blocked on Ghidra reanalysis |

## Primary DID table (flash `0x0100DB7A`)

74 big-endian u16 DID IDs, stride 2 bytes. Starts with a leading marker
`0x203D` (not in MDX — possibly an ID the firmware treats as a sentinel)
and runs through `0xFD0A`.

Full table in `transit_primary_did_table.json`. Highlights:

| Idx | Flash Addr | DID | Name |
|---|---|---|---|
| 04 | `0x0100DB84` | `0x3020` | Steering Pinion Angle |
| 05 | `0x0100DB86` | `0x330C` | **Steering Shaft Torque Sensor #2** (driver input torque) |
| 11 | `0x0100DB92` | `0xD118` | Motor Current |
| 16 | `0x0100DB9C` | `0xDD09` | Vehicle Speed |
| 17 | `0x0100DB9E` | `0xDE00` | Vehicle Data |
| 19 | `0x0100DBA2` | `0xDE02` | Feature Configuration |
| 20 | `0x0100DBA4` | `0xDE03` | Enable/Disable DTCs |
| 21 | `0x0100DBA6` | `0xEE01` | XCP Enable |
| 22 | `0x0100DBA8` | `0xEE02` | Assist On/Off |
| 25 | `0x0100DBAE` | `0xEE05` | **Final Motor Torque** |
| 32 | `0x0100DBBC` | `0xEE42` | **Active Features** (LKA state byte) |

**The 32 writable-config DIDs (security_03/61) — `0xDE01`-`0xDE03`, `0xEE01`-`0xEE02`,
`0x205A`-`0x205B` — are all in this primary table.**

## DIDs NOT in primary table (55)

Live in separate handlers outside the central dispatch table. Most notable
missing LKA/ADAS DIDs:

- `0xEE07` EPS System State
- `0xEE09` Total EPS Operation Time
- `0xEE24`-`0xEE27` Connected Vehicle counters (LKA-lifetime data)
- `0xEE43` SDM Steering Mode
- `0xEE90` Ford in House ANC/LDW Diagnostic Status
- `0xDE04` Pull Drift Compensation Reset Value
- `0xFDB4` Motor ID
- `0xFDAx` Dual-ECU version triples
- `0xFD11` ASW Production Mode Switch
- `0xFEB0` SHE UID (routine)
- `0xC0xx` Crypto/MAC/auth DIDs

These are handled by per-DID getter functions found elsewhere in flash. 
Zero occurrences as u16 BE in a contiguous run outside the primary table 
confirm there is no centralized secondary table. 

## Ghidra leaf-handler labels (FullLift project, 4813 functions)

Applied via `TransitMdxLabel.java` heuristic "1 DID + cmp opcodes":

| Function | DID | Name |
|---|---|---|
| `FUN_010923e2` | `0xF17C` | NOS Bootloader Generation Tool Ver |
| `FUN_010A76D6` | `0x205B` | Brake Pull Reduction Counter (19 cmp, 136 instr — dispatcher-like) |
| `FUN_010A77F6` / `010A7826` / `010A789A` | `0x205B` | 3 handlers share this DID, likely subfunctions |
| `FUN_010B2CD8` | `0xFEB0` + routine `0xFEB0` | **SHE Key Update** |
| `FUN_010B428E` | `0xFEB1` | Non-Group Key Slot Counters |
| `FUN_010B99F8` | routine `0x0301` | **Activate Secondary Boot-loader** |
| `FUN_010CDD30` | `0xEE20` | Connected Vehicle: LoA Fault Reporting |
| `FUN_010D0EF6` | `0xDE01` | Ford In-House Software Feature Config |

## Why the dispatcher remains unfound

The V850 project in Ghidra has sparse address-resolution. My scanner looked
for `movhi+movea/addi` pairs pointing into the dispatch band
`0x0100DB60..0x0100DD00` and got 0 hits, meaning either:

1. Const-propagation analysis wasn't run against those code regions, OR
2. The dispatcher uses a GP-relative or other addressing mode, OR
3. The dispatch code isn't disassembled yet (some flash is still raw bytes)

## Next steps

1. **Re-run full analysis + SeedFromJarls** against the `transit_pscm_KK21-3F964-AM_full.elf`
   project at `~/Desktop/Transit_2025_PSCM_dump/.../ghidra_project/Transit_AM_FullLift`.
   Then re-run `TransitMdxLabel.java` to pick up resolved xrefs.

2. **Find 0xEE07 getter by RAM-load pattern** — look for functions that
   do a single byte/word load from a RAM address, then `jarl lra`. These
   are the classic Dcm_DspGetDataXxx callbacks.

3. **Trace `0x205B` dispatcher (FUN_010A76D6)** — with 19 cmp and 136
   instructions, it is probably the sub-function dispatcher for the
   writable DID. Decompiling it would reveal how `security_03`/`security_61`
   gating is coded.

4. **Routine 0x3054 Clear Power Steering Lockout** — not yet located.
   Scan for routine ID `0x3054` as BE u16 and for the routine-table
   structure. Would give us the firmware side of the lockout-counter reset
   we could trigger at runtime.

## Driver-override threshold — cal endian + uniqueness (2026-04-21)

Transit cal stores floats as **big-endian**. Confirmed by raw-byte scan:

| Offset | BE float | LE float | Role (hypothesis) |
|---|---|---|---|
| cal+0x29D4 | **+0.8** | garbage | Quiet-gate upper threshold |
| cal+0x29D8 | +0.5 | 0 | Exit-band upper |
| cal+0x29DC | +30.0 | 0 | Hysteresis timeout / frame count |
| cal+0x29E0 | **-0.8** | garbage | Quiet-gate lower threshold |
| cal+0x29E4 | -0.5 | 0 | Exit-band lower |

**The -0.8 BE float byte pattern `BF 4C CC CD` appears exactly once in the entire 1.45 MB Transit ELF** — at cal+0x29E0. +0.8 BE appears 116 times (cal has multiple copies across tables). +1.0 BE has 235. -0.8 BE is a singleton. That uniqueness is extremely strong evidence this is a one-shot threshold constant.

### Blocker: cannot locate the reader

- **0** `movhi 0x00FD` / `0x00FE` / `0x0101` instructions in the strategy
  (searched all 2194+ strategy instructions pairwise for movhi+movea)
- **0** `mov imm32` (6-byte form) loading 0x00FD29D4 or 0x00FD29E0
- **0** `ld.w 0x29D4[*]` or `ld.w 0x29E0[*]` across the 5713-function project
- `ld.w` with nearby displacements (0x2B18, 0x2B38) exist, so the
  instruction family is used elsewhere with different bases.

**Interpretation:** cal is reached via a pre-initialized base register
(likely `gp` r4) that's set up once at startup and referenced by short
displacements throughout the codebase. The override threshold reader
would look like `ld.w (0x29D4 - gp_init)[gp], rN` with a non-obvious
offset.

**To find the reader:** locate the gp-init sequence (typical V850 C
runtime: `movhi/movea` pair into r4 in the `_start` / `__do_global_dtors`
preamble), compute `gp_init`, then search `ld.w` instructions with base
register r4 and displacement `0x29D4 - gp_init`.

### 2026-04-21 follow-up: the cluster is almost certainly DEAD calibration

Two lines of evidence:

**(a) F-150 sanity check.** F-150 has an analogous -0.8 LE singleton at
cal+0x7A5C. A sweep of all 344 F-150 functions containing FPU compare ops
returned ZERO readers of that address. The real F-150 quiet-gate function
`FUN_101a3b84` compares driver torque against `_DAT_fef26382` and
`_DAT_fef263de` — both RAM addresses — as unsigned integers, not floats.
See `/tmp/pscm/cmpf_f150/101a3b84_FUN_101a3b84.c:41`.

**(b) Transit does no float math.** Instruction-mnemonic counts on the
5713-function Transit project:

| Op | F-150 | Transit |
|---|---|---|
| cmpf.s | 848 | 5 |
| addf.s | 418 | 0 |
| mulf.s | 1878 | 0 |
| subf.s | 707 | 0 |
| divf.s | 268 | 0 |
| **TOTAL FPU** | **6017** | **5** |
| divh (fixed) | few | 3231 |
| mulh (fixed) | 452 | 2289 |
| satadd / satsubr / satsubi | 5 | 1489 / 1300 / 1290 |
| mulhi | 452 | 831 |

Transit PSCM is **near-100% fixed-point** (Q-format). It physically cannot
consume float calibration in the normal code path. The BE-float cluster at
cal+0x29D4..29E4 is unreachable from the fixed-point math dominating the
strategy.

### Revised interpretation

- cal+0x29D4..29E4 on Transit (BE float `+0.8, +0.5, +30.0, -0.8, -0.5`)
  and cal+0x7A5C on F-150 (LE float `-0.8`) are **dead/vestigial
  calibration**, most likely inherited from the Nexteer / TKP-Presta
  rack-vendor reference integration where float-based hysteresis was
  prototyped. Ford's shipped firmware reads fixed-point-format
  equivalents in RAM instead.
- Patching these addresses will NOT alter LKA override behavior.
- The real driver-override thresholds are **fixed-point integers**
  populated into RAM at startup. F-150 has them at `_DAT_fef26382`
  (abs-torque threshold) and `_DAT_fef263de` (state hysteresis
  threshold). Transit has analogous RAM addresses — not yet located.

### What to investigate next

1. Find the Transit equivalent of `FUN_101a3b84` — a function that does
   `if (abs(torque) < threshA && state_var < threshB) gate = ...` using
   integer compares.
2. Trace back the RAM write to those thresholds to find their cal source.
   That cal source is the real override tunable — not 0x29D4.
3. On F-150, decompile the SBL / C-runtime init code to find where
   `_DAT_fef26382` and `_DAT_fef263de` get their initial values.

## Artifacts

- `transit_primary_did_table.json` — full 73-entry dispatch table
- `transit_pscm_routines.json` — 10 routines with names
- `transit_pscm_dtcs.json` — 50 DTCs with numeric codes + descriptions
- `/tmp/pscm/transit_mdx/` — Ghidra outputs (dids_by_code, functions_by_hits, etc.)
- `tools/scripts/TransitMdxLabel.java` — headless labeling script
