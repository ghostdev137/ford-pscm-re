# F-150 Threshold-Step Family — `cal+0x080C..0x087F`

**Confidence:** Low (role established as threshold schedule, consumer unknown, `fef208xx` mirror proven misleading)
**Class (from classifier):** `u16_table` × 7 contiguous 16-byte records (but see note — these are 18-byte, 9-entry u16 records)
**BDL vs EDL:** **Identical** across all 7 records

---

## What this is

Seven small u16 tables at a constant stride of `0x12` (18 bytes, 9 u16 entries each). The first four are identical; the last three are progressively smaller variants of the same shape. Collectively they look like a step-threshold schedule for a feature that has 4 baseline channels and 3 derated fallback channels.

## Measured values

```
Eight-entry samples (first 8 u16 of each 9-entry record):

+0x080C u16 LE [8]: [10, 20, 30, 80, 100, 100, 100, 100]    \
+0x081E u16 LE [8]: [10, 20, 30, 80, 100, 100, 100, 100]     |  4× identical copies
+0x0830 u16 LE [8]: [10, 20, 30, 80, 100, 100, 100, 100]     |
+0x0842 u16 LE [8]: [10, 20, 30, 80, 100, 100, 100, 100]    /

+0x0854 u16 LE [8]: [ 5, 10, 15, 60,  80,  80,  80,  80]    }  ½ scale
+0x0866 u16 LE [8]: [ 0,  5, 10, 30,  40,  40,  40,  40]    }  ¼ scale (zero-start)
+0x0878 u16 LE [8]: [ 0,  5, 10, 20,  30,  30,  30,  30]    }  ⅛ scale (zero-start)
```

Structure per record: `[x0, x1, x2, x3, ceiling, ceiling, ceiling, ceiling]` — a four-step ramp followed by a four-entry plateau. Classic shape for a "feature grows to a ceiling and then holds."

## Shape & unit hypotheses

- **Units undetermined.** The `100` ceiling and `80/40/30` reduced ceilings are percentage-like, suggesting a normalized authority or gain-percent interpretation.
- **Repeating 4× pattern** aligns with the "4-variant Ford calibration" observation in `cal_findings.md` Finding 2 (trim-dependent or profile-dependent variants).
- **Three fallback variants (`0x0854`, `0x0866`, `0x0878`)** at `50%`, `~33%`, `~25%` of the baseline ceiling — consistent with degraded-state authority scheduling.

## Consumer

**Unknown.** `cal_plain_language_map.md` explicitly flags that the `fef208xx` RAM xrefs produced by naive same-offset matching are misleading — that page is a mutable runtime workspace, not a passive cal mirror (see `cal_access_model.md` §2). The tables are real (they read cleanly and repeat structurally), but consumer attribution requires either `Rte_Prm`-table disassembly or dynamic trace.

## Patch candidates

None established. The four identical baseline copies suggest Ford selects one at runtime based on a mode/variant index; patching only one copy might or might not take effect depending on which mode is active.

## What remains open

- Whether the four identical copies are trim variants, mode variants (LKA / LCA / APA / standby), or redundant safety copies.
- Whether the three smaller variants are active fallback tables or deprecated (only-in-BDL) relics. They're present in *both* BDL and EDL, so deprecation is unlikely.
- Consumer attribution. Same bottleneck as every other `Rte_Prm`-gated table.

## References

- `analysis/f150/cal_undocumented_candidates.md` §2 (original flag)
- `analysis/f150/cal_plain_language_map.md` entry for `cal+0x080C..0x0878`
- `analysis/f150/eps_envelope_threshold_trace.md`
- `analysis/f150/cal_access_model.md` §2 (why `fef208xx` xrefs don't work)
- `analysis/f150/cal_byte_classification_edl.csv` — classifier rows in this range
