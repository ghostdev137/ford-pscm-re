# F-150 Breakpoint Axis Family — `cal+0x0DA8 / 0x1CFC / 0x2C50 / 0x3BA4 / 0x4AF8`

**Confidence:** Medium (role strongly established, exact scale and consumer partially pinned)
**Class (from classifier):** `u16_table` at each of the 5 copies (classifier currently tags these as `u16_table` rather than `u16_axis` because the growth isn't strict-increment-monotonic under its heuristic — the curves *are* monotonic, just non-linear)
**BDL vs EDL:** **All five copies retuned** — Ford shifted this entire family in the BlueCruise revision

---

## What this is

A 19-entry u16 monotonic breakpoint axis, replicated at five cal offsets spaced roughly `0xF54` apart. The shape is geometric/exponential growth. This is the headline finding from `cal_findings.md` Finding 3 and Finding 7.

The repeated layout matches the "four-variant Ford calibration" pattern (`cal_findings.md` Finding 2) — base copy + four trim/mode variants — with one extra copy at `0x1CFC` that was an outlier in BDL and has been normalized to the others in EDL.

Attribution-quality upgrade from `eps_curve_family_ghidra_trace.md`: the runtime consumers are proven-interpolation functions (`FUN_100b8078`, `FUN_100b7918`, `FUN_100b7e96`, `FUN_100b87ae`) initialized by `FUN_10055494`. So although the flash→function pointer isn't directly attributable, the *role* is now concrete: this family is consumed by the authority/limiter/filter/state-selection side of the rack, not by feature arm/disarm timers.

## Measured values

### BDL (2022 baseline)

Four of the five copies share this shape:
```
+0x0DA8, +0x2C50, +0x3BA4, +0x4AF8 (BDL):
[0, 51, 66, 78, 100, 135, 182, 240, 307, 387, 479, 582, 735, 897, 1067, 1245, 1434, 1628, 1831]
```

One outlier copy:
```
+0x1CFC (BDL):
[0, 53, 61, 72,  92, 121, 162, 215, 276, 348, 430, 524, 666, 817,  975, 1145, 1321, 1507, 1704]
```

### EDL (2021 BlueCruise)

**All five copies normalized to the same shape, retuned relative to BDL:**
```
+0x0DA8, +0x1CFC, +0x2C50, +0x3BA4, +0x4AF8 (EDL):
[0, 23, 37, 66, 111, 170, 244, 332, 436, 553, 686, 850, 1026, 1219, 1423, 1645, 1882, 2132, 2398]
```

## Shape analysis

- BDL's 4-identical-copies shape has non-linear growth with differences `51, 15, 12, 22, 35, 47, 58, 67, 80, 92, 103, 153, 162, 170, 178, 189, 194, 203`. The fourth-onward differences grow smoothly; the first three (`51, 15, 12`) are a different regime.
- EDL's normalized shape has differences `23, 14, 29, 45, 59, 74, 88, 104, 117, 133, 164, 176, 193, 204, 222, 237, 250, 266`. Still non-linear, smoother in the early regime.
- **EDL extends the range upward** (peak `2398` vs `1831`, +31%). Under the "lateral authority scheduling" hypothesis, this is consistent with BlueCruise needing to schedule authority out to higher angles/inputs than stock LKA does.
- **EDL also starts smaller** (second entry `23` vs `51`, -55%), meaning more granular scheduling at low inputs.

## Unit hypotheses

No direct static attribution gives us the scale. Plausible interpretations given the shape and known BlueCruise tuning:

- **Torque in LSBs at ~1/4096 Nm scale?** `2398 / 4096 ≈ 0.585 Nm` — feels too small.
- **Angle in millidegrees?** `2398 milli° ≈ 2.4°` — plausible for LKA-regime wheel angle.
- **Curvature 1/km?** `2398 / 1000 ≈ 2.4 1/km` = radius ~417 m — matches highway-curve scheduling.
- **Speed in 0.01 kph?** `2398 × 0.01 = 24 kph` — implausibly low for a 19-entry axis.

Best current guess: **steering wheel angle or road-curvature scheduling** at a fine-grained scale, consistent with lateral authority scheduling.

## Patch candidates

**Authority expansion** — making the BDL curve reach the EDL peak (`2398` vs `1831`) would likely broaden the authority-scheduling range. This is a candidate patch for a vehicle-level "lateral authority" change, but the downstream `y`-axis (the authority value selected at each `x` bin) is the harder question.

**Downward compression** — halving the entire axis would force the lookup to saturate earlier and lock the rack into the upper plateau sooner. Effect depends entirely on the paired Y-axis table(s).

No safe-direction call can be made without pairing the axis to its Y-axis(es) — the authority values at each bin.

## What remains open

- The paired Y-axis (the authority/limiter/filter values that are looked up against this X-axis). Probably lives near each of the 5 copies, but not yet identified.
- Unit scale. Candidate answer: run a unicorn trace varying steering wheel angle from `0°` to `720°` and observe which bin is selected at each step.
- Which of the 5 copies is actually live. The 4-identical + 1-variant-normalized pattern in EDL strongly suggests Ford collapsed variants in the BlueCruise revision.

## References

- `analysis/f150/cal_findings.md` Finding 3 (original discovery) and Finding 7 (BDL→EDL retune)
- `analysis/f150/cal_plain_language_map.md` entry for the repeated curve family
- `analysis/f150/eps_curve_family_ghidra_trace.md` (runtime consumer proof)
- `analysis/f150/cal_undocumented_candidates.md` §1 Candidate A (pre-upgrade flag)
- `analysis/f150/cal_bdl_vs_edl_diff.md` — five entries for the retuned copies (each 38+ B in the "largest diffs first" table)
