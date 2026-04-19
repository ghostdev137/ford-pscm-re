# F-150 APA path findings

**Target:** `firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf`  
**Question:** what is the detailed `APA` path in the 2021 F-150 PSCM, from mailbox family through local controller state, speed gates, and runtime-workspace ownership?  
**Status:** this is the canonical F-150 `APA` path note; the local controller family, mode-local namespaces, and speed-gate ownership are now clear; the exact message-edge unpack detail around `0x3A8` is still less pinned than the downstream local path

## Summary

The current best model for the F-150 `APA` path is:

- `0x3A8 ParkAid_Data` is the `APA` steering-angle request and handshake PDU
- `FUN_1017fd92` is the small `APA` task wrapper that sequences the receive / normalize / apply stages
- `FUN_10183a8a` is the best-known `0x3A8` handler anchor in the repo
- the proven local controller chain is `FUN_10180044 -> FUN_1018466e -> FUN_101848ac`
- the local runtime family is `fef211**`, `fef212**`, `fef213**`
- the strongest current `APA` feature gates are `cal+0x0140 = 0.5` and `cal+0x0144 = 8.0`

What is directly pinned in code and notes:

- `FUN_1018466e` and `FUN_101848ac` manipulate `APA`-local state and output bytes only
- `FUN_10180044` fills a larger `APA` staging space across `fef211**`, `fef212**`, `fef213**`, plus some shared runtime workspace at `fef208**`
- `FUN_1018466e` writes `fef2125c..66`, `fef21220..24`, `fef2126f..72`, `fef213a4..ac`
- `FUN_101848ac` consumes `fef21224`, `fef21262`, `fef2126f`, `fef213ae`
- `FUN_10180842` repacks `DAT_fef20800..0f` into `fef212b6..c5`

The important structural result is:

- `APA` has a cleanly separate local controller family
- the `fef208xx` page is real but should not be treated as an `APA` calibration mirror
- it is a live runtime workspace shared with broader rack-control logic

## Message family and confidence

The mailbox family that matters to `APA` in this image is:

| CAN ID | Role in the current model | Confidence |
|---|---|---|
| `0x3A8 ParkAid_Data` | steering-angle request and `APA` mode handshake from the parking-assist side | high at subsystem role and ownership |
| `0x082 EPAS_INFO` | shared rack feedback frame that includes `APA`-relevant handshake state | shared feedback |

Why `0x3A8` is the `APA` fit:

- the DBC semantics match parking-assist steering requests and active-state handshakes
- the best-known handler anchor and the downstream controller chain land entirely in the `APA`-local namespaces
- the local RAM family is distinct from both the `LKA` and `LCA / BlueCruise` workspaces

The safe wording is:

- `0x3A8` is the `APA` request path
- `FUN_10183a8a` is the best-known handler anchor rather than a fully field-pinned unpack function

## Top-level execution chain

The current `APA` path is best read as:

1. `0x3A8` parking-assist command data reaches the `APA` mailbox family
2. `FUN_1017fd92` sequences the `APA` receive / normalize / apply stages
3. `FUN_10183a8a` is the best-known handler anchor in that receive path
4. `FUN_10180044` prepares the broader `APA` staging state
5. `FUN_1018466e` writes the local `APA` control and status workspace
6. `FUN_101848ac` consumes that workspace and updates the `APA`-side path/output

That path is distinct from:

- the `LKA` local family in `fef21a**`
- the `LCA / BlueCruise` local family in `fef238**`, `fef23b**`, `fef23c**`

## Function roles

### `FUN_1017fd92`

`FUN_1017fd92` is the small `APA`-only wrapper in the current proof chain.

What is directly shown:

- it calls `FUN_1018466e()`, then `FUN_10183a8a()`, then `FUN_101848ac()`

Plain-English role:

- `APA` task wrapper that sequences the receive / normalize / apply stages for the parking-assist path

### `FUN_10183a8a`

`FUN_10183a8a` is the best-known F-150 `0x3A8` handler anchor.

What is safe to say:

- it belongs to the `APA` receive side
- it sits directly inside the `FUN_1017fd92`-sequenced path

Plain-English role:

- best current `APA` message-edge handler anchor for the parking-assist steering request family

### `FUN_10180044`

`FUN_10180044` is the upstream `APA` staging/prep function.

What is directly shown:

- it fills a larger staging space across `fef211**`, `fef212**`, and some shared runtime workspace at `fef208**`
- it computes `_DAT_fef20830` as a filtered live signal

Plain-English role:

- prepare the parking-assist-local staging values and some shared control-side runtime quantities before the more local `APA` controller stages run

### `FUN_1018466e`

`FUN_1018466e` is the strongest local `APA` writer in the current traces.

What is directly shown:

- it writes:
  - `fef2125c..66`
  - `fef21220..24`
  - `fef2126f..72`
  - `fef213a4..ac`

Plain-English role:

- populate the main `APA` local state, status, and intermediate control bytes for the downstream parking-assist path

### `FUN_101848ac`

`FUN_101848ac` is the downstream local `APA` consumer/update stage.

What is directly shown:

- it consumes:
  - `fef21224`
  - `fef21262`
  - `fef2126f`
  - `fef213ae`
- it updates the `APA`-side path using those local values

Plain-English role:

- apply the prepared `APA` state to the downstream parking-assist control/output path

### `FUN_10180842`

This function matters because it clarifies the role of the `fef208xx` page.

What is directly shown:

- it repacks `DAT_fef20800..0f` into `fef212b6..c5`

Plain-English role:

- bridge some live shared runtime state into a local `APA`-side record, which reinforces that `fef208xx` is active workspace rather than a passive flash mirror

## Runtime namespace ownership

The `APA` local runtime state lives primarily in:

- `fef211**`
- `fef212**`
- `fef213**`

The core current mapping is:

| Namespace / slot | Current role | Main proven writer / consumer |
|---|---|---|
| `fef211**` | broader `APA` staging space | `FUN_10180044` |
| `fef21220..24`, `fef2125c..66`, `fef2126f..72` | local `APA` control / status bytes | `FUN_1018466e`, then `FUN_101848ac` |
| `fef213a4..ac` | downstream `APA` local state | `FUN_1018466e`, then `FUN_101848ac` |
| `fef212b6..c5` | repacked shared runtime slice for `APA` use | `FUN_10180842` |

The likely `APA`-side threshold family in RAM is:

- `fef258**`
- `fef25ea*`
- `fef25eb*`

This is the key ownership split:

- `APA` owns `fef211**`, `fef212**`, `fef213**`
- `LKA` owns `fef21a**`
- `LCA / BlueCruise` owns `fef238**`, `fef23b**`, `fef23c**`

## `fef208xx` workspace caveat

The `fef208xx` page shows up near the `APA` path, but it should not be treated as an `APA`-local calibration mirror.

What is directly shown:

- `FUN_101a5c4a` uses `DAT_fef20809`, `DAT_fef2080b`, `DAT_fef2080c`, `DAT_fef20828`, `DAT_fef20829` as supervisor state
- `FUN_1017fda6`, `FUN_10180044`, `FUN_10180ca8`, `FUN_10181270` update `fef2081c`, `fef2081e`, `fef20830`, `fef20854`, `fef20878`, and siblings
- `FUN_10180842` repacks `DAT_fef20800..0f` into an `APA`-side record

Plain-English meaning:

- `fef208xx` is a live runtime workspace shared with broader rack-control logic
- direct xrefs into `fef208xx` do not prove same-offset consumption of flash tables like `cal+0x080C..0x0878`

This matters because earlier same-offset mirror models for the `0x0100..0x015C` and `0x080C..0x0878` flash families are now known to be misleading.

## Calibration ownership

### Confirmed / strong `APA` gates

The strongest current `APA`-specific feature-envelope ownership is:

- `cal+0x0140 = 0.5` — `APA` minimum engage speed
- `cal+0x0144 = 8.0` — `APA` maximum engage speed

These are high-confidence `APA` gates at the value/feature level even though the exact runtime accessor path remains indirect.

### `APA`-side threshold families

The likely `APA`-side threshold family in RAM is:

- `fef258**`
- `fef25ea*`
- `fef25eb*`

Why this family belongs with `APA`:

- it appears alongside the explicit `APA` controller path in `FUN_10180044`, `FUN_1018466e`, and `FUN_101848ac`
- the cleanest feature split in the image is still the `APA` speed-gate and local-workspace side

Safe wording:

- `cal+0x0140` and `cal+0x0144` are the strongest current `APA` envelope entries
- the broader local threshold family is `APA`-side, but not every scalar is field-pinned yet

### What is not yet field-pinned

Still unresolved:

- exact message-edge unpack detail beyond `FUN_10183a8a` as the handler anchor
- exact engineering meaning of each `fef258**` / `fef25ea*` / `fef25eb*` threshold value
- exact indirect accessor path from flash envelope tables into runtime state

So the safe model remains:

- direct `APA` message edge through `0x3A8`
- explicit local `APA` controller family in `fef211**`, `fef212**`, `fef213**`
- strong `APA` feature gating at `cal+0x0140` / `cal+0x0144`
- shared `fef208xx` workspace nearby, but not owned as a passive `APA` cal mirror

## Practical takeaway

If the goal is to change F-150 `APA` behavior without touching `LKA` or `LCA`, the highest-value ownership targets are:

- the `APA` request family around `0x3A8`
- the local `APA` workspaces `fef211**`, `fef212**`, `fef213**`
- the speed gates at `cal+0x0140` and `cal+0x0144`
- the likely `APA` threshold family in `fef258**`, `fef25ea*`, `fef25eb*`

If the goal is to reason about flash-table ownership, avoid treating `fef208xx` as proof of direct same-offset mirror reads.

## Cross-links

- [eps_dbc_message_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_dbc_message_trace.md)
- [eps_mode_separation_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_mode_separation_ghidra_trace.md)
- [eps_envelope_threshold_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_envelope_threshold_trace.md)
- [strategy_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/strategy_findings.md)
- [lca_path_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lca_path_findings.md)
