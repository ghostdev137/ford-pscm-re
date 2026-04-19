# F-150 PSCM Cal Access Model

**Scope:** How the F-150 (2021 Lariat BlueCruise, `ML34-14D007-EDL`) strategy firmware reaches its calibration partition.

**TL;DR:** Direct `movhi 0x101D` xrefs resolve only a handful of scalar gates (~8 offsets, ~30 bytes). The rest of the 195,584-byte cal is accessed through runtime pointer indirection seeded by the SBL (AUTOSAR `Rte_Prm` pattern). Static attribution alone will leave ~99% of cal unmapped to specific code sites; attribution at scale requires dynamic tracing via emulation or live UDS reads.

This doc is the honest access-pattern reference for anyone trying to answer "which code reads cal+0xNNNN?" for F-150.

---

## Access patterns

### 1. Direct absolute addressing (`movhi 0x101D`) — **attributable statically**

A small number of cal offsets are reached via literal `movhi 0x101D` / `movea` pairs. These are the scalar feature gates.

Known offsets (from `strategy_cal_reads.md`):

| Cal Offset | Abs Address | Type | Value (EDL) | Role |
|---|---|---|---|---|
| `+0x000C4` | `0x101D00C4` | float32 LE | 10.0 | LDW/LKA min-speed gate |
| `+0x00114` | `0x101D0114` | float32 LE | 10.0 | LKA engage min-speed (m/s) |
| `+0x00120` | `0x101D0120` | float32 LE | 10.0 | LCA engage min-speed (m/s) |
| `+0x00140` | `0x101D0140` | float32 LE | 0.5  | APA engage min-speed (kph) |
| `+0x00144` | `0x101D0144` | float32 LE | 8.0  | APA engage max-speed (kph) |
| `+0x07ADC` | `0x101D7ADC` | u16 LE     | 10000 | LKA arm timer (10 s @ 1 ms tick) |
| `+0x07ADE` | `0x101D7ADE` | u16 LE     | 10000 | LKA re-arm timer |
| `+0x07E64` | `0x101D7E64` | u16 LE     | 10000 | ESA/TJA arm timer |

**Attribution status:** HIGH. Each offset has a named `movhi 0x101D` / `movea N` instruction pair and a concrete reader function recoverable via Ghidra xrefs. Ghidra scripts already produced: `F150FindCalInit.java`, `F150CalOffsetsMath.java`, `F150CalMap.java`.

**Coverage:** ~30 bytes of 195,584 — negligible by volume but high-value because these are the enable-or-disable scalars every patch starts with.

---

### 2. `fef2xxxx` RAM mirror family — **partially attributable, not a passive mirror**

The strategy firmware contains many `DAT_fef2xxxx` references. These live in RAM page `0xfef20000..0xfef2ffff`. The initial hypothesis was that this is a passive mirror of cal (i.e., `fef2XXXX` = cal `+0x0XXXX`), but empirical testing proved otherwise:

- Same-offset checks fail: `_DAT_fef208xx` xrefs do **not** produce consumers that match `cal+0x08xx` content (per `cal_findings.md` Finding 11 and `cal_plain_language_map.md` note on `cal+0x080C..0x0878`).
- The `fef2xxxx` page is **mutable workspace**: values written at runtime, not a read-only projection of flash.
- The mirror *is* populated at init with cal-derived values, but it is then updated by strategy code. Post-init snapshots contain a mix of cal-seeded values and runtime state.

**Attribution status:** PARTIAL. Some `DAT_fef2xxxx` symbols trace back to a cal offset at startup; others are pure runtime scratch. Discriminating the two requires:

1. Capturing the SBL-run init sequence that populates the RAM page.
2. Diffing the post-init snapshot against cal to identify which addresses were seeded from cal.
3. Tracking subsequent writes to eliminate offsets that are rewritten during normal operation.

**Coverage upper bound:** unclear without the above analysis. The `fef263xx` driver-override family (`cal_plain_language_map.md`) is the best-documented example where `fef2xxxx` xrefs did yield useful cal attribution (`analysis/f150/driver_override_findings.md`).

---

### 3. GP/EP-relative addressing — **partially attributable**

The F-150 strategy uses `gp` (r4) and `ep` (r30) to form compact displacements for small structs of hot data. The supervisor "context records" (`context + 0x68`, `context + 0x6c`, `context + 0x74`, `+0x78`, `+0x7c`, `+0xa8`) are reached this way.

Scripts present: `F150FindGP.java`, `F150FindGpInit.java`, `F150FindContextStores.java`, `F150FindContextUsers.java`, `F150FindCtx68Users.java`, `F150FindDispWriters.java`.

**What works:** if GP's value after startup is known, every `ld.w N[gp]` becomes `*(u32*)(GP + N)`, which — if `GP + N` falls in the cal mirror range — lets you map the access to a cal offset.

**What fails:** context records are not cal offsets directly. They are *copies of cal* placed into a per-instance context struct at init. The context struct sits in RAM, not at a fixed cal-derived address. So `ctx+0x68` is not `cal+some_offset` — it's a RAM struct field whose *initial value* came from cal.

**Coverage:** the known context-backed families (`ctx+0x68`, `+0x6c`, `+0x74`, `+0x78`, `+0x7c`, `+0xa8`) collectively back ~200–500 bytes of cal. `eps_supervisor_ghidra_trace.md` and `eps_curve_family_ghidra_trace.md` document the field-level roles but not the flash-base offsets they were initialized from.

---

### 4. AUTOSAR `Rte_Prm` pointer-table indirection — **not attributable statically**

Per `strategy_cal_reads.md`:

> "Cal access is done via runtime pointer indirection (AUTOSAR Rte_Prm pattern) initialized by the SBL. Code addresses for each cal read CANNOT be determined from static binary analysis."

AUTOSAR BSW uses `Rte_Prm_*` getter functions that dereference a pointer table. The pointers are set up at SBL/EcuM init to addresses inside the cal partition. Consumers call `Rte_Prm_X()`, which reads `*table[X]`. Static analysis sees only the table lookup; the concrete cal offset is buried in the pointer value assigned at runtime.

**Consequence:** the bulk of the 195,584-byte cal — the repeated breakpoint families, authority profiles, driver-override thresholds, feature envelope blocks — are reached via `Rte_Prm` indirection. Static xref alone cannot say "function `FUN_10055494` reads `cal+0x0DA8`."

**What *can* be done statically:**
- Enumerate the `Rte_Prm` table setup in SBL disassembly.
- Capture the concrete pointer values to identify which cal offsets are *candidate* read targets.
- Match the shape of a read (width, stride, count) to classifier-identified regions to narrow it down.

**What *needs* dynamic tracing:**
- Exact "this function reads this cal offset" attribution.
- Control-flow-dependent reads (a function may read different cal offsets depending on input state).
- Verifying that a candidate table pointer is actually dereferenced at runtime.

---

### 5. Direct embedded `ld.w` to `0x101D....` absolute addresses — **non-existent**

Per `strategy_cal_reads.md` and re-confirmed by `F150FullMap.java` output: **the strategy binary (`ML3V-14D003-BD.VBF`) contains zero direct `movhi 0x101D` instructions other than the ~8 scalar-gate sites above.** There is no scenario in which a naive "scan for absolute cal address" pass finds more than the known ~30-byte set.

---

## Summary: what can we realistically attribute statically?

| Access pattern | Offsets reachable | Attribution quality |
|---|---|---|
| 1. `movhi 0x101D` direct | ~8 scalar gates (~30 B) | **High** |
| 2. `fef2xxxx` RAM mirror | driver_override family (~40 B), plus unknown fraction via init diff | **Partial**, needs init-snapshot work |
| 3. GP/EP context records | ~200–500 B via ctx+0x68/6c/74/78/7c/a8 | **Partial**, field-level only |
| 4. `Rte_Prm` pointer tables | ~everything else (~195 KB) | **Not statically attributable** |
| 5. Other direct | 0 | — |

**Practical coverage ceiling for pure static RE: ~500–1,000 bytes with function-level attribution, out of 195,584.**

The remaining ~99.5% of the live cal (i.e., the ~30 KB that isn't `reserved_zero`) needs:
- **Dynamic trace** (unicorn harness emulation, or live UDS 0x23 reads with instrumentation) to observe actual `Rte_Prm` dereferences and map them to `(PC, cal_offset)` tuples.
- **Cross-vehicle diff** (BDL vs EDL; Transit vs Escape) to infer role by feature delta.
- **Pattern classification** (`tools/cal_classifier.py`) to tag region shape, type, and plausible function family without needing firmware attribution.

---

## Implications for "document entire cal" goal

1. **Classification is the easy win.** 100% of cal bytes are classifiable (reserved vs float_table vs u16_axis vs timer_cluster vs etc.) without any firmware access. This alone covers the "what is this region" question for most offsets.

2. **Semantic labeling is tractable** via the existing `cal_plain_language_map.md` approach: combine shape (from classifier), cross-vehicle delta (from cross-diff), and family priors (LKA/LCA/APA/BlueCruise) to assign plain-language roles even without firmware attribution.

3. **Firmware attribution maxes out at ~1% of cal via static RE alone.** Honest reporting will show most regions as "Medium confidence — consumer: unknown (Rte_Prm-gated)". The remaining attribution needs:
   - **Option A (static-only improvement):** reverse-engineer the `Rte_Prm` table setup in SBL to enumerate pointer tables, then match classifier-identified regions to table entries by shape. Partial attribution.
   - **Option B (dynamic):** extend `tools/unicorn_transit_harness.py` to F-150, trace cal reads under stimulus. High attribution but time-intensive.
   - **Option C (empirical):** instrument a live truck with FORScan + CAN captures, correlate feature state with observed values at specific cal offsets via UDS 0x23. Per-feature attribution but slow.

4. **Pragmatic target:** 100% classified, 80%+ semantically labeled, ~20–30% function-attributed (mostly via option A). The remainder is an honest "unattributed — `Rte_Prm` indirection" bucket.

---

## References

- `analysis/f150/strategy_cal_reads.md` — original finding of Rte_Prm indirection
- `analysis/f150/cal_findings.md` — full catalog of discovered cal structure
- `analysis/f150/cal_plain_language_map.md` — plain-language region roles
- `analysis/f150/sbl_findings.md` — SBL analysis (no RSA, uses HW SHA-256)
- `analysis/f150/eps_supervisor_ghidra_trace.md` — context-backed supervisor records
- `analysis/f150/eps_curve_family_ghidra_trace.md` — context-backed curve family
- `analysis/f150/driver_override_findings.md` — `fef263xx` family attribution
- `tools/scripts/F150FindGP.java`, `F150FindGpInit.java`, `F150FindMirrorUsers.java`, `F150FindCalInit.java`, `F150CalMap.java` — Ghidra scripts used
- `analysis/f150/cal_byte_classification.md` + `.csv` — full byte classification
- `analysis/f150/cal_bdl_vs_edl_diff.md` + `.csv` — BDL vs EDL cross-diff
