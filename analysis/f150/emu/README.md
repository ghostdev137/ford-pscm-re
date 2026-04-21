# F-150 LKA override — Unicorn emulation harness

Empirical validation of the `FUN_101a3b84` override-threshold hypotheses
from `analysis/f150/driver_override_findings.md`, using the vendored
`unicorn-pr1918` RH850 build.

## Harness

`tools/unicorn_f150_override_harness.py` — loads the F-150 ELF into a
Unicorn RH850 instance, maps the `0xFEF00000` RAM region, seeds the LKA
workspace (`fef21a6e`, `fef21a70`, `fef21a72`, `fef21a77`) and threshold
mirrors (`fef263de`, `fef26382`, etc.), and calls `FUN_101a3b84` as a
leaf.

- `setup_machine()` / `seed_defaults()` — RAM + register init
- `call_function(uc, entry, arg0)` — runs with sentinel-LP return, block
  hook for progress tracking, unmapped-memory trap
- Important constants: RH850 uses `Uc(UC_ARCH_RH850, 0)` (not
  `UC_MODE_LITTLE_ENDIAN`), and `UC_HOOK_CODE` doesn't fire — use
  `UC_HOOK_BLOCK` for instruction-flow observation.

## Observability bit

After `FUN_101a3b84` runs, watch byte **`0xFEF21A64`**:

- stays `0x00` → execution stayed in the quiet/okay path
- flips to `0x01` → quiet-gate failed, override monitoring escalated

Byte `0xFEF21A65` flips to `0x01` on every run (function-reached marker,
not useful for gate diagnosis).

## Sweep results

`f150_sweep.py` varies angle, chan_a, chan_b, status across a grid with
default thresholds `fef263de=0x40`, `fef26382=0x400`.

Findings from the sweep (stock-seeded thresholds):

| Input varied | Boundary | Matches cal mirror |
|---|---|---|
| `angle` (fef21a6e) with chan=0 | flips at `0x400` | `fef26382 = 0x400` ✓ |
| `chan_a` (fef21a70) with angle=0 | flips at `0x40` | `fef263de = 0x40` ✓ |
| `chan_b` (fef21a72) with angle=0 | flips at `0x40` | `fef263de = 0x40` ✓ |
| `status == 5` | separate deny-path, 74 blocks, r10=0 | matches doc |

Status byte `3 → 5` flips the whole return path (different block count,
no workspace writes) — matches `driver_override_findings.md` claim that
`fef21a77==3` is permit, `==5` is deny.

## Threshold patch validation

`f150_threshold_test.py` sweeps `_DAT_fef263de` across `[0x10, 0x200]` and
finds the first `chan_a` value that trips the quiet gate:

```
threshold_de    first_flip    last_quiet
  0x0010             0x0010        0x0000
  0x0020             0x0020        0x0010
  0x0040             0x0040        0x0030   ← stock
  0x0080             0x0080        0x0070
  0x0100             0x0100        0x00f0
  0x0200             0x0200        0x01f0
```

**Result: linear 1:1 shift.** The patch target is correct; a 4× raise to
`0x100` gives openpilot 4× more interaction-channel headroom before the
quiet-gate fails.

## What this proves and doesn't

**Proved**

- `_DAT_fef263de` is the earliest shared channel threshold, applied to
  both `fef21a70` and `fef21a72`
- `_DAT_fef26382` is the angle quiet-gate threshold
- Status byte `fef21a77` gates a separate deny path
- Unicorn RH850 emulation of `FUN_101a3b84` produces deterministic,
  input-sensitive output observable via `fef21a64`

**Not proved**

- Engineering units: we don't know what `chan = 0x40` means in Nm on the
  car. The ratio is valid; the absolute dose needs a UDS-23 live dump
  during a failing turn (see `pscm_full_dump.py`)
- Downstream consequence: `FUN_101a4e4a` (output writer to
  `fef21a78`) never fires in isolated leaf runs because it depends on
  upstream wrapper state, so the eventual effect on the motor command
  is inferred from the control-flow divergence, not measured directly
- Rate detector / persistence stages: only the stage-1 quiet gate is
  clearly exercised by single-shot runs; the rate detector
  (`DAT_fef26406`) and persistence (`fef263da/dc`) need multi-call
  scenarios where previous values in the controller struct come from
  prior invocations

## Next experiments

1. Sweep `DAT_fef26406` with non-zero previous values (already partially
   tested — no visible flip in single-shot). Will need a driver that
   calls `FUN_101a3b84` twice with differing inputs.
2. Sweep `fef263d0/d2` to find the band boundaries.
3. Add a parallel harness for `FUN_10065b7c` (the `0x3CA` unpack helper)
   to validate `LaRefAng_No_Req` + `LaCurvature_No_Calc` decoding.
4. Diff `fef26382` empirically against stock cal value — if the stock
   value in EDL cal at file offset differs from our seeded `0x400`, the
   on-car quiet-angle threshold may be different.
