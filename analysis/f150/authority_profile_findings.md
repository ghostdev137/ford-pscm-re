# F-150 Bell-Curve Authority Profile — `cal+0x1660`, `0x25B4`, `0x350C`

**Confidence:** Medium (shape + role concrete, exact consumer not attributed)
**Class (from classifier):** `u16_table` at each site
**BDL vs EDL:** **Peak authority reduced ~27%** in EDL (`44 → 32`), bell shape preserved

---

## What this is

A 12-entry u16 bell-shaped curve repeated at two full-size sites (`0x1660`, `0x25B4`) and one shifted/truncated version (`0x350C`). The shape is unambiguously a "ramp up to a peak, then decay" — classic normalized authority profile.

This is the `cal_findings.md` Finding 4 data, now also in `cal_plain_language_map.md` at Medium confidence under the "`cal+0x1660` mirrored family" entry.

## Measured values

```
+0x1660 u16 LE [12]:
  BDL: [14, 25, 32, 40, 43, 44, 42, 33, 23, 14, 9, 0]
  EDL: [10, 19, 23, 29, 31, 32, 31, 23, 16, 10, 6, 0]

+0x25B4 u16 LE [12]:  (identical to 0x1660)
  BDL: [14, 25, 32, 40, 43, 44, 42, 33, 23, 14, 9, 0]
  EDL: [10, 19, 23, 29, 31, 32, 31, 23, 16, 10, 6, 0]

+0x350C u16 LE [12]:  (shifted — truncates the ramp-up side)
  BDL: [32, 40, 43, 44, 42, 33, 23, 14, 9, 0, 0, 0]
  EDL: [23, 29, 31, 32, 31, 23, 16, 10, 6, 0, 0, 0]
```

## Shape analysis

- Peak position: **index 5** (of 0..11) for the full profile — slightly past center.
- Peak value: **BDL 44 → EDL 32** (reduction of 12, ~27%).
- Shape preserved: scaling factor per-entry is `[0.71, 0.76, 0.72, 0.73, 0.72, 0.73, 0.74, 0.70, 0.70, 0.71, 0.67, —]` — roughly uniform 0.71× reduction, not a linear shift.
- Trailing zeros confirm the profile always terminates at zero — this is a *finite-support* authority profile, not an open-ended schedule.
- The `+0x350C` copy starts at the *peak-region* values and zero-pads the tail, i.e., it's the same profile with a different origin — suggesting it's consumed at a different lookup offset.

## Role — normalized authority / blend profile

The "ramp up, peak, decay, zero" shape is how lateral assist systems apply authority across a normalized region (often normalized angle, normalized error, or progression within a maneuver). Example usage patterns:

- **Lane-change torque envelope** — authority grows as the rack commits to the lane change, peaks mid-maneuver, decays as lateral error approaches zero.
- **Angle-vs-authority shaper** — applies the most torque at moderate lateral-offset angles; less at small angles (driver is roughly centered) and less at large angles (likely already yielding to driver).
- **Convergence envelope** — time-based profile for how assist is applied during engage/disengage ramps.

All three interpretations are consistent with "BlueCruise wants less peak authority than stock LKA" — BlueCruise is hands-off and needs to feel more human, so peak authority is conservative. The stock LKA's `44` peak is aggressive "help once, then stop" behavior.

## Cross-site relationship

`0x1660` and `0x25B4` are **identical copies** — strides of `0xF54` between them, matching the 4-variant pattern (but only two copies here, not four). The third site `0x350C` at a stride of `0xF58` from `0x25B4` is the shifted variant.

Hypothesis: `0x1660` and `0x25B4` are two variants (maybe LKA vs LCA, or two speed regimes) of the same lane-assist profile, and `0x350C` is a different feature's consumption of the same shape with a different origin.

## Patch candidates

**Authority raise** — restoring BDL's values in EDL cal (`[14, 25, 32, 40, 43, 44, ...]`) would give BlueCruise the stock LKA peak authority. Same shape, higher peak.

**Selective asymmetry** — raising only the ramp-up side (indices 0–5) would make BlueCruise commit authority faster while keeping the decay conservative. Useful if the issue is "too slow to apply" rather than "too weak at peak."

**Keep-EDL-shape** — this is the recommended no-touch option. EDL's profile is Ford-validated for the BlueCruise feature set.

## What remains open

- Consumer attribution. Required to answer "what's the X-axis?" — which determines *when* each bin is selected.
- Whether the `0x350C` shifted copy is actually consumed, or dormant leftover.
- Why there are only two full copies (not four) — `0x1660` and `0x25B4` — when the rest of the 4-variant families have four. Possibly the `0x350C` and another absent site are the remaining "variants" of the same feature, with the offset/shift encoding mode differences.

## References

- `analysis/f150/cal_findings.md` Finding 4 (bell-curve authority profile)
- `analysis/f150/cal_plain_language_map.md` entry for `cal+0x1660` mirrored family
- `analysis/f150/cal_bdl_vs_edl_diff.md` (three entries covering `0x1660`, `0x25B4`, `0x350C`)
- `analysis/f150/eps_curve_family_ghidra_trace.md` (interpolation consumers that likely consume profiles of this shape)
