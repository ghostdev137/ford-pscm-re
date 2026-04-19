# F-150 Scheduler Axis — `cal+0x06BA`

**Confidence:** Low (shape established, consumer unknown)
**Class (from classifier):** `u16_axis` (monotonic increasing)
**BDL vs EDL:** **Identical**

---

## What this is

A single 10-entry monotonic u16 axis used as the X-axis for a downstream lookup. Not a flag bundle, not a timer cluster — the geometric-ish growth is characteristic of a breakpoint table for an interpolation function.

## Measured values

```
+0x06BA u16 LE [10]: [0, 640, 1920, 3840, 7680, 10240, 12800, 15360, 19200, 23040]
                      identical between BDL and EDL
```

Differences between successive entries: `640, 1280, 1920, 3840, 2560, 2560, 2560, 3840, 3840`. The first four entries form a power-of-2-weighted expansion (`0, 1×640, 3×640, 6×640, 12×640`) then it plateaus at `16×640, 20×640, 24×640, 30×640, 36×640`. Base unit appears to be `640`.

## Unit hypotheses

- **`640 = 0.5 kph in 1/1280 scaling`?** Doesn't match any known Ford CAN scale.
- **Degrees × 1/32 resolution?** `23040 / 32 = 720°` — plausible for steering-wheel angle. `640 / 32 = 20°` first-meaningful-step, `19200 / 32 = 600°`, `15360 / 32 = 480°`. Consistent with an axis over steering-wheel angle (which goes lock-to-lock ~720°).
- **`millidegrees` or `deci-degrees`?** `23040 milli° = 23.04°` or `23040 deci° = 2304°`. The latter is implausible; the former is a small angle for lateral assist operation.

Best current guess: an axis over **steering-wheel angle** at ~1/32° resolution (range ~0–720°), or possibly torque/current at a similar scale.

## Consumer

**Unknown.** No static `movhi 0x101D` xref hits `+0x06BA`. `fef206ba` produced no live consumers. This is an `Rte_Prm`-gated axis like most cal data (see `cal_access_model.md`).

Strong structural suggestion (from `eps_curve_family_ghidra_trace.md`): the context-backed curve records at `ctx+0x74/+0x78/+0x7c/+0xa8` use monotonic axes of exactly this shape for limiter/blend/threshold schedules. `+0x06BA` may be the flash-backed source for one of those contexts, but no direct init-time copy has been traced.

## Patch candidates

Low-risk: none established, because the consumer is unknown. Compressing this axis (e.g., halving every value) *would* change how fast a scheduled output grows against its input — but until the scheduled output is identified, effects are speculative.

## What remains open

- Consumer attribution. Requires either unicorn dynamic trace with a stimulus varying steering-wheel angle across the [0, 23040] range of the hypothesized unit, or tracing the `Rte_Prm` pointer that selects this table.
- Unit confirmation. Same dynamic trace would answer "what scale is the X-axis?" by correlating CAN-reported steering angle with which bin this axis selects.

## References

- `analysis/f150/cal_undocumented_candidates.md` §1 Candidate B (original flag)
- `analysis/f150/cal_plain_language_map.md` entry for `cal+0x06BA`
- `analysis/f150/eps_curve_family_ghidra_trace.md` (context-backed sibling curves)
- `analysis/f150/cal_byte_classification_edl.csv` — classifier row for `0x06BA`
