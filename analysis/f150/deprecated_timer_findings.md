# F-150 Deprecated Timer Family — `cal+0x1402..0x1416`

**Confidence:** Low-to-Medium (pattern clear, role speculative)
**Class (from classifier):** `u16_table` (BDL) / `reserved_zero` (EDL — Ford zeroed this region)
**BDL vs EDL:** **Entirely deleted in EDL** — this is the strongest "feature removed" signal in the cross-diff

---

## What this is

An 11-entry u16 run that existed in 2022 BDL with a uniform `655` pattern, and was zeroed out in 2021 BlueCruise EDL. The uniform `655` value (`655 × 10 ms = 6.55 s`) has the shape of a timeout/persistence window.

Because EDL zeroed *four copies* of this pattern (at `0x13F0`-range, `0x23xx`-range, `0x32xx`-range, `0x41xx`-range per `cal_findings.md` Finding 2), it's a deliberate feature removal, not a per-trim difference.

## Measured values

```
+0x1402 u16 LE [11]:
  BDL: [655, 655, 655, 655, 655, 655, 655, 655, 655, 655, 0]
  EDL: [  0,   0,   0,   0,   0,   0,   0,   0,   0,   0, 0]
```

The trailing `0` (at `+0x1416`) is the same in both revisions — it's the table terminator, not part of the deleted data.

## Hypothesis: what did Ford remove?

Candidate roles for a 10-entry `6.55 s` uniform table:

1. **Per-state dwell timer** — a 10-entry state machine where every state has the same hold-off. Flattening 10× identical entries implies a degenerate state machine or a template for future use that was never differentiated.
2. **Per-channel fault persistence** — 10 channels, each holding a fault for 6.55 s before asserting. Removing this would make faults assert immediately, which isn't a normal "safer" choice — more likely this was a legacy LKA recovery helper that BlueCruise replaces with a different mechanism.
3. **Driver-override dwell** — 6.55 s is a plausible window for "don't re-engage LKA if driver intervened within the last 6.55 s." BlueCruise's hands-on/off state machine may not use a flat uniform timer.

Best-fit story: BDL inherited a legacy timer-array design that BlueCruise replaced with the context-backed timer records (`ctx+0x6c`, see `eps_supervisor_ghidra_trace.md`). The replacement is more expressive (per-state rather than uniform), and EDL zeroed the old block rather than deleting it — the cal layout still allocates the 22 bytes, it's just unused.

## Cross-copy consistency

`cal_findings.md` Finding 2 states that **four identical copies were zeroed** (at ~`0x13Fx`, ~`0x23xx`, ~`0x32xx`, ~`0x41xx` — matching the "four-variant Ford cal" pattern). This is consistent with a trim/mode-variant table structure: four copies of a uniform 10-entry timer, all simultaneously deprecated.

Our cross-diff at `cal_bdl_vs_edl_diff.md` shows small diff regions in these ranges tagged `reserved_zero` class — confirming EDL's zero-filled state.

## Patch candidates

None useful. The block is already zero in EDL, and restoring the `655` values in BDL style is unlikely to re-enable whatever behavior it used to gate, since downstream consumers would have been updated too.

## What remains open

- Which feature used the `655` timer. Would require either a BDL-era annotated strategy (which we don't have) or a live trace against a BDL cal on a bench module (expensive).
- Whether the zero-filled region is truly unused in EDL or is still read by some dormant code path. Static xref answers "not read via `movhi 0x101D`" but can't rule out `Rte_Prm` indirection pointing at a zero table (which would no-op safely).

## References

- `analysis/f150/cal_findings.md` Finding 2 (key diff: `cal+0x1402..0x1416` zeroed)
- `analysis/f150/cal_plain_language_map.md` entry for `cal+0x1402..0x1416`
- `analysis/f150/cal_bdl_vs_edl_diff.md` (this range shows as `reserved_zero` in EDL)
