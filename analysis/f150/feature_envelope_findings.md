# F-150 Feature Envelope Block — `cal+0x00B8..0x0147`

**Confidence:** Medium (role established, field-level semantics partially pinned)
**Class (from classifier):** mostly `float_scalar` with short `float_axis` runs
**BDL vs EDL:** **Identical** — Ford did not retune this block between revisions

---

## What this block is

A dense 144-byte run of `float32` little-endian values that collectively define the speed/angle/torque *window* within which F-150's lateral-assist features (LKA, LCA/BlueCruise, APA) are allowed to engage. The two smaller sub-blocks — `0x00B8..0x00F3` and `0x00F4..0x0147` — look like two parallel feature-config records with the same shape (`[MAX_speed, MIN_speed, gain, flag]` repeated).

The three known scalar gates statically attributed via `movhi 0x101D` (`0x00C4`, `0x0114`, `0x0120`) all live inside this block. Everything else in it is reached via `Rte_Prm` indirection (see `cal_access_model.md`) and therefore cannot be tied to a specific reader function by static analysis alone.

## Measured values (BDL = EDL)

### Sub-block A: `0x00B8..0x00F3`

| Offset | Value | Plausible role |
|---|---|---|
| `+0x00B8` | `0.800` | gain/scalar |
| `+0x00BC` | `0.500` | gain/scalar |
| `+0x00C0` | `200.0` | LKA max-speed (kph)? |
| **`+0x00C4`** | **`10.0`** | **LDW/LKA min-speed gate (m/s) — statically attributed** |
| `+0x00C8` | `3.5` | hysteresis or threshold |
| `+0x00CC` | `0.055` | small gain/deadband |
| `+0x00D0` | `55.0` | speed-kph midpoint? |
| `+0x00D4` | `3.6` | threshold |
| `+0x00D8` | `1.5` | small-gain |
| `+0x00DC` | `30.0` | speed-kph? |
| `+0x00E0` | `55.0` | speed-kph? |
| `+0x00E4` | `1440.0` | ms/ticks/angle* |
| `+0x00E8` | `5.0` | count/period |
| `+0x00EC` | `0.0` | disabled/reserved |
| `+0x00F0` | `0.0` | disabled/reserved |
| `+0x00F4` | `2.5` | threshold |
| `+0x00F8` | `0.5` | hysteresis |
| `+0x00FC` | `0.1` | small-gain |

*1440 could be "1440 ms" (1.44 s) or a 1/4° resolution of 360°; no direct consumer yet.*

### Sub-block B: `0x0100..0x0147`

| Offset | Value | Plausible role |
|---|---|---|
| `+0x0100` | `40.0` | kph? |
| `+0x0104` | `40.0` | kph? |
| `+0x0108` | `250.0` | kph (absolute max) |
| `+0x010C` | `40.0` | kph? |
| `+0x0110` | `40.0` | kph? |
| **`+0x0114`** | **`10.0`** | **LKA engage min-speed (m/s) — statically attributed** |
| `+0x0118` | `1.0` | flag/scalar=1 |
| `+0x011C` | `200.0` | max-speed (kph) |
| **`+0x0120`** | **`10.0`** | **LCA engage min-speed (m/s) — statically attributed** |
| `+0x0124` | `1.0` | flag |
| `+0x0128` | `66.0` | kph |
| `+0x012C` | `50.0` | kph |
| `+0x0130` | `0.004` | rate/ramp coefficient |
| `+0x0134` | `1.0` | flag |
| `+0x0138` | `1.0` | flag |
| `+0x013C` | `0.3` | small-gain |
| **`+0x0140`** | **`0.5`** | **APA engage min-speed (kph) — statically attributed** |
| **`+0x0144`** | **`8.0`** | **APA engage max-speed (kph) — statically attributed** |

## Shape observations

- Sub-blocks A and B share `[MAX_speed, MIN_speed, gain/flag]` tuples. Likely two features (LKA and LCA), or two modes of one feature (e.g., standard LKA vs BlueCruise hands-free). The triple at `+0x0108..+0x0118` (`250, 40, 40, 10`) parallels the triple at `+0x011C..+0x0124` (`200, 10, 1.0, 200`) — different-width windows for different activation contexts.
- `200.0` kph appears twice as a likely "absolute upper bound" sentinel.
- `250.0` kph appears once — possibly the "no upper gate" placeholder (~155 mph, above any real-world cap).
- `10.0` m/s ≈ 22.37 mph, matching the user's reported "~23 mph minimum speed."

## Cross-vehicle comparison

- **Transit (`LK41-14D007-AH`, big-endian, 65,520 B) has no structurally equivalent block.** Transit's LKA min-speed lives at `+0x0690` as a single `float32 BE` scalar, not in a dense envelope block.
- **Escape (`LX6C-14D007-ABH`, big-endian) not diffed at this range yet** — same platform as Transit, so likely same `+0x0690` layout. The F-150 feature envelope is platform-specific to the ML34 layout.

## Patch candidates

Lowering any of the `10.0` gates to ~0.5 m/s makes LKA/LCA eligible at near-standstill. The `0.5`/`8.0` APA pair expands to `0.0`/`200.0` in the prepared `APA_UNLOCK.VBF` patch (see `docs/vbf-patches.md`). Other entries are risky to touch — the `0.055`, `0.004`, `0.3` small coefficients are likely hysteresis/damping terms whose role isn't pinned.

## What remains open

- Exact field role for every `kph` or `m/s`-plausible entry. Statically impossible without `Rte_Prm` attribution (see `cal_access_model.md`).
- Whether sub-block A is LKA and sub-block B is LCA, or something else. A unicorn trace with `0x3D3 LateralMotionControl` stimulus would answer this.
- Whether any of the `1.0` flags are feature-enable bits that AS-built flips.

## References

- `analysis/f150/cal_findings.md` Finding 1 (original discovery)
- `analysis/f150/cal_plain_language_map.md` entries for `cal+0x00C4` and `cal+0x0100..0x015C`
- `analysis/f150/strategy_cal_reads.md` (the 3 statically-attributed offsets)
- `analysis/f150/cal_byte_classification_edl.csv` — classifier output for this range
