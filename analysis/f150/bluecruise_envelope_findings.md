# F-150 BlueCruise Envelope (BDL → EDL tuning delta)

**Confidence:** Medium (delta is empirical and unambiguous; per-byte role inference is per-region)
**Source:** `analysis/f150/cal_bdl_vs_edl_diff.md` (2,782 byte-level diffs organized into 85 contiguous regions, 9,632 B total, 4.92% of cal)

---

## What this doc is

BDL (`ML34-14D007-BDL`, 2022) is the F-150 EPS baseline calibration. EDL (`ML34-14D007-EDL`, 2021 Lariat BlueCruise) is the BlueCruise-tuned revision. Diffing the two surfaces every byte Ford changed to make BlueCruise behave differently from stock LKA.

This doc consolidates the diff into three buckets: **structural changes** (handled in their own deep-dives), **BlueCruise-only tuning region** (`0x7280..0x7420`, not covered elsewhere), and **end-of-cal deltas** (`0x2FBE0..`).

## Bucket 1 — Structural changes (covered in per-feature deep-dives)

Ford retuned 8 data families in the BDL→EDL transition. Each is 4- or 5-copy repeated under the 4-variant cal pattern. Details are in the per-feature docs:

| Region (first copy) | Stride | Copies | Change | See |
|---|---|---:|---|---|
| `+0x0930` 312-B u16 table | `0xF54` | 5 | retuned | (not yet isolated — see `cal_findings.md` Finding 2 appendix) |
| `+0x0BA2` 675-B u16 table | `0xF54` | 5 | retuned | (same) |
| `+0x0DA8` 19-entry breakpoint axis | `0xF54` | 5 | **retuned + normalized** | [`breakpoint_axis_family_findings.md`](breakpoint_axis_family_findings.md) |
| `+0x0E4A` 276-B u16 table | `0xF54` | 5 | retuned | (same) |
| `+0x10A2` 179-B u16 table | `0xF54` | 4 | retuned | (same) |
| `+0x1402` deprecated 10×`655` timer | `0xF54` | 5 | **zeroed** | [`deprecated_timer_findings.md`](deprecated_timer_findings.md) |
| `+0x1520` 14-entry ramp schedule | `0xF54` | 5 | **halved** | [`ramp_schedule_findings.md`](ramp_schedule_findings.md) |
| `+0x1660` bell-curve authority profile | `0xF54` | 2–3 | **peak reduced 44→32** | [`authority_profile_findings.md`](authority_profile_findings.md) |

The `0x144C`, `0x1600`, `+0x1862` (u16 `1280`), `+0x1870` (15-B float-adjacent), `+0x019E` (u16 `3683`), `+0x0924` (float axis), and `+0x55B2`/`+0x55C0` diffs are smaller incidental retunes in the same 4-copy pattern — most likely sibling fields of the structural changes above.

## Bucket 2 — BlueCruise-only tuning region: `cal+0x7280..0x7424`

This is the **only singleton diff region in the whole cal** (not repeated across the 4 variants). Unlike the structural block at `0x0000..0x5500`, the `0x7280..0x7420` neighborhood is hit *once* — strong evidence that this is a distinct BlueCruise-specific tuning area that doesn't live in the variant system.

Per-offset diff (u16 LE):

| Offset | BDL | EDL | ΔEDL–BDL | Shape |
|---|---:|---:|---:|---|
| `+0x7284` | `35840` | `27648` | −8192 | single u16 |
| `+0x72B4` | `7447` | `12582` | +5135 | 4-entry u16 row, repeats 4× (`+0x72B4`, `+0x72C0`, `+0x72CC`, `+0x72D8`) |
| `+0x72B6` | `12837` | `17978` | +5141 | (row element 2) |
| `+0x72B8` | `19519` | `23891` | +4372 | (row element 3) |
| `+0x72BA` | `29018` | `29030` | +12 | (row element 4) |
| `+0x72E4` | `9501` | `14897` | +5396 | 3-entry u16 row, repeats 6× (`+0x72E4`, `+0x72F0`, ... `+0x7320`) |
| `+0x72E6` | `16178` | `21318` | +5140 | (row element 2) |
| `+0x72E8` | `23116` | `26205` | +3089 | (row element 3) |
| `+0x734C` | `19661` | `42598` | +22937 | u16 single |
| `+0x734E` | `26214` | `39322` | +13108 | u16 single |
| `+0x7350` | `32768` | `39322` | +6554 | u16 single |
| `+0x7352` | `32768` | `45875` | +13107 | u16 single |
| `+0x7360` | `32768` | `40960` | +8192 | u16 single |
| `+0x736C` | `49152` | `39322` | −9830 | u16 single |
| `+0x736E` | `49152` | `42598` | −6554 | u16 single |
| `+0x7372` | `45875` | `40960` | −4915 | u16 single |
| `+0x73B6` | `16384` | `12288` | −4096 | u16 single |
| `+0x73C4` | `14000` | `10800` | −3200 | u16 single |

Single-byte diffs interspersed at `+0x7285`, `+0x7361`, `+0x73B7`, `+0x7421` — flag bytes within structs.

### Interpretation

1. **Two repeated u16 rows** at `+0x72B4..+0x72BA` (4-entry, 4-copy) and `+0x72E4..+0x72E8` (3-entry, 6-copy) look like **gain/threshold tuples** that EDL raised by ~5000 LSBs across the board. The uniform delta across the 4 copies of the first row and the 6 copies of the second confirms Ford treated each copy as a synchronized set — not per-variant tuning.
2. The `+0x7350..+0x7372` cluster looks like a signed/unsigned field pair with EDL *increasing* the lower half and *decreasing* the upper half — possibly a threshold band (`lower` raised, `upper` lowered) narrowing the operating window, or a hysteresis pair being widened.
3. `+0x73B6` (BDL `16384` → EDL `12288`) is a classic Q15 scale reduction: `16384 = 1.0`, so `12288 = 0.75`. Ford reduced some Q15 coefficient by 25% for BlueCruise.
4. `+0x73C4` (BDL `14000` → EDL `10800`) — plausible timer-style reduction from `14.0s` to `10.8s` at 1 ms tick, or a threshold-ms value in the same scale. BlueCruise has a shorter window.

### Best-fit story

`0x7280..0x7420` is the **BlueCruise hands-off supervisor** — the region that governs how BlueCruise-specific behavior (hands-off timing, gains, envelope) differs from stock LKA. Raising gains, widening some threshold pairs, and reducing the Q15 coefficient by 25% is consistent with "BlueCruise steers with more authority but less peak gain, on a slightly shorter supervision window."

### Consumer

Unknown statically — `Rte_Prm`-gated like the rest of cal. A unicorn trace with `0x3D3` and `0x21A` (AccelerationData, typically a BlueCruise-era frame) stimulus would be the cleanest way to attribute these bytes to specific BlueCruise functions.

## Bucket 3 — End-of-cal diffs: `+0x2FBE0..+0x2FBFF`

| Offset | BDL (u16) | EDL (u16) | Length | Class |
|---|---|---|---|---|
| `+0x2FBE0` | `26844, 23744` | different | 4 B | unknown |
| `+0x2FBF0` | `28552` | different | 2 B | unknown |
| `+0x2FBFA` | `47656, 14607, 37676` | different | 6 B | unknown |

This is the last ~32 bytes before the 195,584-byte boundary. Could be a **cal footer / checksum / version stamp**, not functional cal data. Ford stamps cal revision metadata near the tail of the partition in other firmware (e.g., Transit `+0xFFDC` footer). Needs verification but low priority.

## Not-changed-but-related: identical blocks worth noting

Several blocks that we might expect to differ between stock LKA and BlueCruise *don't*:

- `0x00B8..0x0147` feature envelope — identical (see [`feature_envelope_findings.md`](feature_envelope_findings.md)). LKA/LCA/APA gating is unchanged; the BlueCruise feature uses the same min-speed thresholds.
- `0x06BA` scheduler axis — identical (see [`scheduler_axis_findings.md`](scheduler_axis_findings.md)).
- `0x080C..0x087F` threshold family — identical (see [`threshold_family_findings.md`](threshold_family_findings.md)).
- `0x07ADC` LKA timer record — identical. BlueCruise keeps the same arm/re-arm timing.
- `0x07D68..0x07E3F` supervisor float block — identical. Continuous-control supervisor unchanged between revisions.
- `0x07E64` sibling timer — identical.

**Implication:** BlueCruise is not a fundamentally different supervisor — it reuses the LKA timer framework, the feature envelope, the continuous-control record, and the threshold schedules. What it retunes is the *authority-scheduling* side of the rack (breakpoint family, bell-curve profile, ramp schedule) plus a BlueCruise-specific supervisor region at `0x7280..0x7420`.

## References

- `analysis/f150/cal_bdl_vs_edl_diff.md` + `.csv` — full diff dataset
- `analysis/f150/cal_findings.md` Finding 2 (original BDL→EDL observations)
- `analysis/f150/breakpoint_axis_family_findings.md`
- `analysis/f150/ramp_schedule_findings.md`
- `analysis/f150/authority_profile_findings.md`
- `analysis/f150/deprecated_timer_findings.md`
