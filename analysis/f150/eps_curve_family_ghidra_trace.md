# F-150 EPS curve-family trace from Ghidra

**Target:** `firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf`  
**Method:** headless Ghidra trace on the saved `F150TimerOffsets` project  
**Status:** the live interpolation paths are now explicit; exact flash base for some curve records is still unresolved

## Summary

The curve-heavy side of the rack calibration is now partially grounded in code:

- `FUN_10055494` initializes the live context record with gp-backed pointer fields
- later EPS logic consumes those pointer fields as interpolation records, not timer bundles
- the repeated monotonic u16 tables in cal are now more defensible as **authority / limiter / filter scheduling curves**, not generic candidate axes

The important split is:

- `ctx + 0x6c` = debounce / persistence timers
- `ctx + 0x68` = mixed float/int supervisor values
- `ctx + 0x74`, `+0x78`, `+0x7c`, and `+0xa8` = interpolation-oriented records

## Proven initializer path

`FUN_10055494` is the first solid bridge between the gp-backed globals and the live context record.

It copies gp-relative globals into the context struct fields used later by the EPS logic:

| Context field | GP-backed source in `FUN_10055494` | Proven downstream use |
|---|---|---|
| `ctx + 0x68` | `gp - 0x15660` | mixed supervisor/control record |
| `ctx + 0x6c` | `gp - 0x1565c` | packed dwell/debounce record |
| `ctx + 0x74` | `gp - 0x15248` | lookup table / limiter schedule |
| `ctx + 0x78` | `gp - 0x156b0` | filter / lag / blend record |
| `ctx + 0x7c` | `gp - 0x156a8` | small threshold / 2-point limiter record |
| `ctx + 0xa4` | dynamic, via `FUN_100af112` neighborhood | smaller 4-state timer helper |
| `ctx + 0xa8` | dynamic sibling of `ctx + 0xa4` | interpolation-heavy curve record |

This does **not** yet prove the final flash addresses for every gp-backed pointer, but it does prove that these records are intentionally assembled into one live EPS context instead of being unrelated decompiler artifacts.

## Proven curve consumers

### 1. `FUN_100b8078`: `ctx + 0x74` is a limiter/authority schedule

This function reads:

- `ctx74 + 0x40` as a final scale factor
- `ctx74 + 0x2b4`
- `ctx74 + 0x2c8`
- `ctx74 + 0x2d4`
- `ctx74 + 0x2e0`
- `ctx74 + 0x2ec`

It then:

- interpolates with `FUN_1008fb5c`
- applies smoothing on the selected path
- multiplies the final result by `ctx74 + 0x40` in one enable path

Plain-English EPS read:

- this is a **scheduled limit/authority block**
- it is shaping how much output is allowed and how fast it can move, not deciding whether the feature is armed

### 2. `FUN_100b7918` and `FUN_100b7e96`: `ctx + 0x78` is a filter/blend record

These functions read:

- `ctx78 + 0x8c` as a filter frequency term in `exp(-2*pi*0.002*f)`
- `ctx78 + 0x5dc` as state storage for a filter helper
- `ctx78 + 0x5e8` / `+0x5ec` as follow-up validation terms
- `ctx78 + 0x198` as the Y table for a 12-point interpolation driven by `ctx + 0xa8`

Plain-English EPS read:

- this is a **dynamic lag / blend / smoothing record**
- it is governing how a commanded quantity is filtered and blended, not a timer or a simple threshold

### 3. `FUN_100b7e96`: `ctx + 0x7c` is a small 2-point limiter record

This function reads:

- `ctx7c + 0x9ce`
- `ctx7c + 0x9d2`
- `ctx7c[1]`

and uses them as a tiny interpolation / clamp stage inside a blended output path.

Plain-English EPS read:

- `ctx + 0x7c` is a **small threshold / limiter record** that participates in blend selection
- it looks like a secondary clamp, not a main breakpoint axis

### 4. `FUN_100b87ae`: `ctx + 0xa8` is a state-selection curve record

This function uses:

- `ctxa8 + 0x8b4`
- `ctxa8 + 0x8bc`
- `ctxa8 + 0x8fe` with a 4-byte stride

It interpolates those values and then chooses output states `1`, `2`, `3`, or `4` based on:

- the interpolated margin
- several runtime signals
- thresholds from `ctx + 0x70` and `ctx + 0x7c`

Plain-English EPS read:

- `ctx + 0xa8` is a **mode-selection / margin schedule**
- it is helping decide which limiter/authority state the rack should be in

This is a stronger interpretation than “some repeated u16 curve”: the consumer is clearly stateful and control-oriented.

## Best current mapping back to cal

The repeated monotonic u16 families remain the best current flash candidates for the curve records, especially:

- `0x0DA8`
- `0x0DF8`
- `0x0F3C`
- sibling repeated copies at `0x1CFC`, `0x2C50`, `0x3BA4`, `0x4AF8`

Why these are still the strongest candidates:

- they are monotonic and interpolation-friendly
- they sit in dense u16 curve neighborhoods, not random scalar blocks
- Ford materially retuned them between `BDL` and `EDL`
- the live consumers above are explicitly interpolation-driven and need curve-like backing data

What is still unresolved:

- the exact flash base for `ctx + 0xa8`
- which specific repeated family maps to `ctx + 0xa8 + 0x8b4` vs `+0x8bc` vs `+0xf3c`

So the safe conclusion is:

- the repeated curve families are now **very likely active EPS scheduling data**
- the exact per-pointer flash mapping is still a follow-up task

## Practical EPS meaning

The curve-heavy records are not feature-enable gates. They look like:

- authority schedules
- limiter margins
- filter/blend gains
- state-selection curves

In rack terms, these records are answering:

- how much output is allowed
- how fast it can move
- how hard to blend between paths
- when to switch between limiter/authority states

That is a materially better model than “maybe breakpoint tables” and explains why Ford retuning these curves would change steering feel and intervention behavior without changing headline speed gates.
