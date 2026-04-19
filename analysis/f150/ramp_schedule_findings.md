# F-150 Ramp / Rate-Limit Schedule — `cal+0x1520..0x153C`

**Confidence:** Medium (shape + role concrete, exact consumer not attributed, scale strongly suggested)
**Class (from classifier):** `u16_table`
**BDL vs EDL:** **Every value exactly halved in EDL** — strongest "linear retune" signal in the cross-diff

---

## What this is

A 14-entry monotonic u16 schedule that BDL ships at one scale and EDL ships at exactly half that scale. The uniform 2× relationship across all 14 entries is a smoking gun: this is a rate-limit or authority-ramp schedule that Ford deliberately softened for the BlueCruise revision.

## Measured values

```
+0x1520 u16 LE [14]:
  BDL: [32, 64,  96, 128, 192, 256, 320, 512, 768,  960, 1344, 1920, 2304, 2880]
  EDL: [16, 32,  48,  64,  96, 128, 160, 256, 384,  480,  672,  960, 1152, 1440]
                                                   ← every entry = BDL × 0.5
```

Growth differences within each revision are non-linear:
- BDL steps: `32, 32, 32, 64, 64, 64, 192, 256, 192, 384, 576, 384, 576` — geometric-ish acceleration
- EDL steps: `16, 16, 16, 32, 32, 32, 96, 128, 96, 192, 288, 192, 288` — same shape, half scale

## Role — rate-limit / authority ramp schedule

The non-linear geometric growth is classic breakpoint-table behavior. Combined with the uniform 2× BDL→EDL relationship, this is almost certainly an **authority ramp** (how quickly the rack is allowed to build lateral torque or angle command as some upstream variable grows) or a **rate-limit schedule** (max Δ-per-tick allowed).

Halving the schedule makes the rack build authority *more gently* — consistent with BlueCruise's softer, more-human-feeling steering vs the stock LKA's "one tug and done" behavior.

## Unit hypotheses

- **Torque LSBs at ~1/1000 Nm?** BDL max `2880 / 1000 = 2.88 Nm/tick`. At a 1 ms tick, that's `2.88 Nm/ms = 2880 Nm/s`, which is implausibly fast. At a 10 ms tick, `288 Nm/s` — still fast for a steering rack but not outside normal bounds.
- **Angle in centidegrees at a per-tick delta?** BDL max `2880 centideg = 28.8°/tick` — fast but possible for rate-limit ceiling (the schedule likely never actually reaches the top entry in normal operation).
- **Normalized 0..10000?** Max 2880 is ~29% of full scale — doesn't match a clean normalization.

Best-fit: a **torque delta-per-tick** schedule, halved by EDL so BlueCruise can't apply as aggressive per-tick changes.

## Patch candidates

**Authority unlock** — restoring BDL's values in EDL cal (`[32, 64, 96, ...]`) would double BlueCruise's per-tick authority buildup rate. The patch is trivial (28 bytes, single region). Risk: more aggressive steering feel; driver-override dynamics change (less time to react before the rack commits to a command).

**Further softening** — halving again (`[8, 16, 24, ...]`) would soften steering even more than BlueCruise already does.

**Not advised** without pairing against whatever y-axis table is looked up against this schedule. If there is no paired y-axis (i.e., this is itself the output, not an index), then the effect is direct. If it's an index, the pair table lives elsewhere.

## What remains open

- Consumer attribution (same `Rte_Prm` blocker).
- Whether this is itself the y-output of a schedule (rate-limit ceiling) or an x-axis for a further lookup (a breakpoint that selects a gain).
- Whether BlueCruise uses this schedule during hands-on only, hands-off only, or both.

## References

- `analysis/f150/cal_findings.md` Finding 2 key diff "breakpoints exactly halved"
- `analysis/f150/cal_plain_language_map.md` entry for `cal+0x1520..0x153C`
- `analysis/f150/cal_bdl_vs_edl_diff.md` (`0x01520` region)
- `analysis/f150/cal_byte_classification_edl.csv` — `u16_table` row covering this range
