---
title: F-150 Calibration Map
nav_order: 24
---

# F-150 PSCM Calibration Map

**Target cal:** `ML34-14D007-EDL` (2021 Lariat 502A BlueCruise).
Also available for cross-diff: `ML34-14D007-BDL` (2022 baseline).
**Size:** 195,584 bytes. **Endianness:** little-endian. **Flash base:** `0x101D0000`.

This is the master reference for the F-150 PSCM calibration partition. It catalogs every identified region, links to the per-feature deep-dive, and reports what can and can't be attributed to specific firmware code statically.

## Coverage summary

From `tools/cal_classifier.py` run on `cal_edl_raw.bin`:

| Class | Regions | Bytes | % of cal |
|---|---:|---:|---:|
| `reserved_zero` | 113 | 164,820 | **84.27%** |
| `u16_table` | 381 | 21,896 | 11.20% |
| `unknown` | 486 | 3,508 | 1.79% |
| `float_table` | 40 | 2,460 | 1.26% |
| `timer_cluster` | 31 | 1,462 | 0.75% |
| `u16_axis` | 46 | 720 | 0.37% |
| `float_scalar` | 90 | 360 | 0.18% |
| `float_axis` | 20 | 296 | 0.15% |
| `packed_bytes` | 6 | 38 | 0.02% |
| `reserved_ff` | 4 | 24 | 0.01% |
| **total** | **1,217** | **195,584** | **100.00%** |

**Only ~15.7% of cal is live data (~30,700 bytes).** The rest is reserved/unused.

Semantic labels exist for ~500–1,000 bytes with **high** confidence (statically attributed scalar gates) and for most `float_axis`, `timer_cluster`, `u16_axis`, and the repeated `u16_table` families with **medium** confidence (shape + role established via cross-vehicle inference).

## How cal is accessed

Static analysis can only attribute ~0.5% of cal to specific reader functions, because most access goes through runtime `Rte_Prm` pointer tables set up by the SBL (AUTOSAR pattern). See [cal access model](../analysis/f150/cal_access_model.md) for the full breakdown.

## Regions by feature

### Feature gating — `cal+0x00B8..0x0147`

Dense 144-byte float32 block defining LKA/LCA/APA engage windows. Three of its scalar fields are the only statically-attributed offsets in the entire cal (`+0x00C4`, `+0x0114`, `+0x0120`, `+0x0140`, `+0x0144`).

→ [`feature_envelope_findings.md`](../analysis/f150/feature_envelope_findings.md)

### Lateral supervisor timer record — `cal+0x07ADC..0x07AF0`

LKA arm/re-arm timers (`10 s` @ 1 ms tick) plus packed debounce/hysteresis fields. Identical between BDL and EDL — BlueCruise keeps the same LKA supervisor timing.

→ [`lka_timer_ghidra_trace.md`](../analysis/f150/lka_timer_ghidra_trace.md), [`eps_supervisor_ghidra_trace.md`](../analysis/f150/eps_supervisor_ghidra_trace.md)

### Continuous-control supervisor — `cal+0x07D68..0x07E3F`

Seven short float32 tables defining supervisor gains, angle thresholds (`5°`, `10°`), fallback magnitudes, and filter coefficients. Identical between BDL and EDL.

→ [`eps_supervisor_ghidra_trace.md`](../analysis/f150/eps_supervisor_ghidra_trace.md)

### Sibling supervisor timer — `cal+0x07E64..0x07E6C`

Second arm/settle/dwell timer block, likely ESA/TJA-side. Identical between BDL and EDL.

→ [`cal_plain_language_map.md`](../analysis/f150/cal_plain_language_map.md) §`cal+0x07E64`

### Driver-override threshold family — `_DAT_fef263xx`

Driver-override threshold, banding, and persistence. Best-documented `fef2xxxx` RAM family; identified via `F150DumpReader.java` and cross-referenced into cal content.

→ [`driver_override_findings.md`](../analysis/f150/driver_override_findings.md)

### Authority scheduling (the retuned BlueCruise side)

Four families that Ford retuned to make BlueCruise behave differently from stock LKA:

| Family | Offset | Change | Deep-dive |
|---|---|---|---|
| Breakpoint axis (5 copies) | `+0x0DA8 / 0x1CFC / 0x2C50 / 0x3BA4 / 0x4AF8` | retuned + normalized | [`breakpoint_axis_family_findings.md`](../analysis/f150/breakpoint_axis_family_findings.md) |
| Ramp / rate-limit schedule (5 copies) | `+0x1520 / +0x2474 / +0x33C8 / +0x431C / +0x5270` | halved in EDL | [`ramp_schedule_findings.md`](../analysis/f150/ramp_schedule_findings.md) |
| Bell-curve authority profile | `+0x1660 / +0x25B4 / +0x350C` | peak `44 → 32` | [`authority_profile_findings.md`](../analysis/f150/authority_profile_findings.md) |
| BlueCruise-specific supervisor | `+0x7280..+0x7424` | retuned (singleton, not repeated) | [`bluecruise_envelope_findings.md`](../analysis/f150/bluecruise_envelope_findings.md) |

### Threshold / step schedules — `cal+0x080C..0x087F`

Seven 9-entry u16 tables at 18-byte stride; four baseline + three derated fallback variants. Identical across revisions.

→ [`threshold_family_findings.md`](../analysis/f150/threshold_family_findings.md)

### Scheduler axis — `cal+0x06BA`

Single monotonic 10-entry u16 axis; likely steering-angle X-axis for one downstream lookup. Identical across revisions.

→ [`scheduler_axis_findings.md`](../analysis/f150/scheduler_axis_findings.md)

### Deprecated timer block — `cal+0x1402..0x1416`

Formerly a 10×`655` (6.55 s) timer array in BDL; zeroed in EDL. Four repeated copies, all simultaneously deprecated.

→ [`deprecated_timer_findings.md`](../analysis/f150/deprecated_timer_findings.md)

### Mode separation (LKA / LCA / APA)

Which tables belong to which feature, based on Ghidra context analysis.

→ [`eps_mode_separation_ghidra_trace.md`](../analysis/f150/eps_mode_separation_ghidra_trace.md)

### DBC message mapping

CAN message catalog for LKA, LCA/BlueCruise, APA, and shared PSCM feedback.

→ [`eps_dbc_message_trace.md`](../analysis/f150/eps_dbc_message_trace.md)

### Torque-sensor source trace

Where driver-torque sensor data enters the strategy and how it feeds override logic.

→ [`torque_sensor_source_trace.md`](../analysis/f150/torque_sensor_source_trace.md)

### Angle-scale patch

Firmware-side angle scaler analysis (companion to Transit's `mulhi 0x67c2` finding).

→ [`angle_scale_patch.md`](../analysis/f150/angle_scale_patch.md)

## BDL → EDL cross-diff

**4.92% of cal (9,632 bytes in 85 regions) changed** between BDL and EDL. 95.8% of changes are in `u16_table` regions.

→ [`cal_bdl_vs_edl_diff.md`](../analysis/f150/cal_bdl_vs_edl_diff.md)
→ [`bluecruise_envelope_findings.md`](../analysis/f150/bluecruise_envelope_findings.md) (summary + singleton BlueCruise region)

## Tooling

- [`tools/cal_classifier.py`](../tools/cal_classifier.py) — classifies every byte; outputs CSV + markdown summary.
- [`tools/cal_cross_diff.py`](../tools/cal_cross_diff.py) — classifier-aware byte-diff between two cal blobs.
- [`tools/scripts/F150*.java`](../tools/scripts/) — ~50 Ghidra headless scripts for F-150 static RE.

## Open questions

1. **`Rte_Prm` pointer-table contents** — enumerate the pointer array set up by the SBL to convert "function X reads `Rte_Prm_Y()`" into "function X reads cal offset Z" for the ~99% of cal that's not statically attributable.
2. **Unicorn dynamic trace** — extend `tools/unicorn_transit_harness.py` for F-150 so cal reads can be attributed to PCs and stimuli.
3. **Unit scale of retuned axes** — the breakpoint family `+0x0DA8` and ramp schedule `+0x1520` have their shapes characterized but not their units. Live UDS 0x23 reads under a known stimulus would answer this.
4. **BlueCruise singleton region** — `+0x7280..+0x7424` clearly houses BlueCruise-specific tuning but no code attribution yet; candidate region for a focused unicorn trace.
5. **Flashability** — the F-150 VBF trailer includes a 256-byte RSA signature. SBL analysis ([`sbl_findings.md`](../analysis/f150/sbl_findings.md)) concluded the SBL does NOT verify it (no embedded public key, no bignum code, uses HW SHA-256 only). Patched cal with correct SHA-256 in trailer should be flashable, but **untested on a real module.**

## Related

- [Transit calibration map](calibration-map.html) — Transit PSCM cal reference for cross-platform comparison.
- [Firmware versions](firmware-versions.html) — VBF inventory across all vehicles.
- [VBF patches](vbf-patches.html) — patched VBFs built for F-150 (see `F150_Lariat_BlueCruise/` subdirectory in `firmware/patched/`).
