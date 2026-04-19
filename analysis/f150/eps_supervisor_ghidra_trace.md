# F-150 EPS supervisor config trace from Ghidra

**Target:** `firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf`  
**Method:** headless Ghidra trace on the saved `F150TimerOffsets` project  
**Status:** enough code is now traced to separate the main EPS supervisor config families; exact flash base for every pointer is still not fully pinned

## Summary

The F-150 EPS lateral/supervisor logic is not driven by one monolithic "LKA timer table". The proven config families behind the state logic split into at least three pointer-backed records:

- `context + 0x68`: mixed float/int continuous-control block
- `context + 0x6c`: packed `u16` debounce/persistence block
- `context + 0x74`: lookup-table / curve block

The important correction is:

- the old `0x07ADC/0x07ADE = 10000/10000` pair sits in a **mixed supervisor record**
- the live state machines also consume a **separate packed dwell-timer bundle**
- those two ideas should not be collapsed into one "LKA timer scalar"

## Proven context initializer bridge

`FUN_10055494` is now the concrete initializer that seeds several live context fields from gp-backed globals before the later EPS logic runs.

That gives a stable bridge between the later consumer functions and the runtime config records:

| Context field | GP-backed source in `FUN_10055494` |
|---|---|
| `ctx + 0x68` | `gp - 0x15660` |
| `ctx + 0x6c` | `gp - 0x1565c` |
| `ctx + 0x74` | `gp - 0x15248` |
| `ctx + 0x78` | `gp - 0x156b0` |
| `ctx + 0x7c` | `gp - 0x156a8` |

This still does not prove the final flash address for each record, but it does prove that the later `ctx + 0x68` and `ctx + 0x6c` consumers are reading deliberately initialized runtime config records, not incidental local structs.

## Proven `context + 0x6c` behavior: packed debounce/persistence bundle

The `context + 0x6c` pointer is consumed heavily by two watchdog-like state machines:

- `FUN_1005dbc8`
- `FUN_1005ea9c`

The proof is straightforward from the decompile:

- nearly every low-offset access is `*(ushort *)(cfg6c + off) * 10`
- those products are compared against elapsed milliseconds from `FUN_10090586`
- the outputs are latched booleans and timeout-driven event reports, not continuous control values

So this record is best described as a **packed dwell / debounce / hold-time bundle**.

### Offset roles inside `cfg6c`

These are relative offsets within the `context + 0x6c` struct:

| Offset | Proven behavior | Main consumer(s) | Meaning in EPS terms |
|---|---|---|---|
| `+0x3a` | `u16 * 10 ms` timeout before `0x104` report is asserted in one branch | `FUN_1005dac4` | assert / dwell window for one supervisor fault path |
| `+0x3c` | `u16 * 10 ms` window where prior latch state is preserved after reset | `FUN_1005dbc8` | sticky-hold persistence for a combined fault/qualifier state |
| `+0x40` | `u16 * 10 ms` follower timeout | `FUN_1005d9d0` | release timer for one latched condition |
| `+0x42` | `u16 * 10 ms` follower timeout | `FUN_1005d9d0` | release timer for a second latched condition |
| `+0x46` | `u16 * 10 ms` timeout before event `0x102` is reported | `FUN_1005dbc8` | delay before escalating another supervisor condition |
| `+0x4a` | `u16 * 10 ms` timeout before `0x103` report is asserted | `FUN_1005dac4` | assert / dwell window for sibling supervisor fault path |
| `+0x4c` | `u16 * 10 ms` master dwell before downstream booleans can become active | `FUN_1005dfa6` | top-level qualify timer for a multi-signal supervisor gate |
| `+0x50` | `u16 * 10 ms` clear timer for one output latch | `FUN_1005e91e` | hold time before output 1 is cleared |
| `+0x52` | `u16 * 10 ms` retain-last-value window | `FUN_1005e16a` | keep prior output-1 state alive briefly after reset |
| `+0x56` | `u16 * 10 ms` clear timer for one output latch | `FUN_1005e884` | hold time before output 2 is cleared |
| `+0x58` | `u16 * 10 ms` retain-last-value window | `FUN_1005e16a` | keep prior output-2 state alive briefly after reset |
| `+0x5c` | `u16 * 10 ms` clear timer for one output latch | `FUN_1005e778` | hold time before output 4 is cleared |

There are also two halfword fields consumed through still-opaque helper macros:

- one used where `FUN_1005d9d0` derives the first boolean timeout
- one used by `FUN_1005e778`, `FUN_1005e9b8`, and `FUN_1005e16a` as another clear/retain timer pair

Even without the exact disassembly cleanup for those helper reads, the behavior is still clear: they belong to the same packed dwell bundle and serve the same debounce / retain / clear role as the surrounding `u16 * 10 ms` fields.

### Secondary exported timing groups from `cfg6c`

Two small helpers export nominal timing sets from the same record:

- `FUN_1005d8d8`
- `FUN_1005e114`

Those helpers copy several low offsets out of `cfg6c` and fall back to hard-coded defaults when the feature is disabled.

The defaults are:

- `5000`
- `5000`
- `0x1162` (`4450`)
- `0x136a` (`4970`)

That reinforces the interpretation that this record is a collection of **milliseconds-scale EPS dwell thresholds**, not breakpoint axes or gains.

## Proven `context + 0x68` behavior: mixed continuous-control block

The `context + 0x68` pointer behaves very differently. It is used as a mixed float/int record in control-law setup and filter initialization:

- `FUN_100a92ba`
- several neighboring `0x68` readers in the same scheduler family

The strongest code-backed fields are:

| Offset | Proven behavior | Meaning in EPS terms |
|---|---|---|
| `+0x10` / `+0x14` | positive / negative gains applied to an internal delta `(iVar9+0x2e0) - (iVar9+0x2e4)` before comparison to a live signal | slope / gain pair for validating or bounding a dynamic estimate |
| `+0x34` | copied into six globals whenever one validation chain fails | fallback limit / gain / default target for a six-channel block |
| `+0x48` | copied into another six globals on invalidity | second fallback limit / gain / default target |
| `+0x4c` | scaled by `1e-9` before storage | very small numerical tuning constant, likely for a continuous-time or rate-related calculation |
| `+0x5c` | used in `exp(-2*pi*0.002*f)` | filter frequency or pole location for a low-pass / decay term |

This is not a timer table. It is a **continuous-control / filter / fallback-parameter block**.

## Best current fit to the flash neighborhoods

The best current mapping is:

- `context + 0x68` most likely lands in or near the mixed block around `cal+0x07ADC`
- `context + 0x6c` is a different packed timing struct whose exact flash base still needs to be pinned

Why `0x07ADC` is the best current fit for `context + 0x68`:

- the neighborhood is clearly mixed int/float
- relative float offsets line up plausibly with the proven `cfg68` reads:
  - `base + 0x34 = 0.7`
  - `base + 0x48 = 36.1111`
  - `base + 0x4c = 5.5556`
  - `base + 0x5c = 1.2`
- those values are reasonable as fallback gains, limits, and filter constants in an EPS supervisor
- `FUN_10055494` now proves that `ctx + 0x68` is a top-level initialized config record, which makes the mixed `0x07ADC` neighborhood fit better than before

That is still a best-fit, not final proof, because the exact initializer for `context + 0x68` has not been isolated the same way the `0xa4` family was.

## Proven `context + 0x74` behavior: lookup-table / curve block

The `context + 0x74` pointer is consumed like a lookup/curve record rather than a timer bundle:

- `FUN_100b8078` reads:
  - `cfg74 + 0x40` as a scale factor
  - `cfg74 + 0x2b4`
  - `cfg74 + 0x2c8`
  - `cfg74 + 0x2d4`
  - `cfg74 + 0x2e0`
  - `cfg74 + 0x2ec`
- it uses `FUN_1008fb5c` interpolation on those arrays
- it conditionally scales the final output by `cfg74 + 0x40`

That makes `cfg74` the likely home for one or more authority/rate scheduling curves. It is the right place to keep looking when tying the repeated breakpoint families to live EPS behavior.

## Practical interpretation

The F-150 EPS supervisor data now separates cleanly into:

1. **Mixed float supervisor/control record**
   - likely near `0x07ADC`
   - contains the previously noticed `10000/10000` pair
   - also contains real float gains and filter constants

2. **Packed dwell/debounce record**
   - exact flash base still unresolved
   - definitely holds many `u16 * 10 ms` timers used by watchdog-like state machines

3. **Curve/lookup record**
   - likely where authority/rate breakpoints live
   - consumed through interpolation rather than elapsed-time compares

That is the right mental model for the rack firmware: envelope and dwell logic are split across multiple config records, not one flat "LKA timer cluster".
