# F-150 LKA path findings

**Target:** `firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf`  
**Question:** what is the detailed `LKA` path in the 2021 F-150 PSCM, from mailbox family through local controller state, override logic, and calibration ownership?  
**Status:** this is the canonical F-150 `LKA` path note; the direct command chain, local workspace, and driver-override family are now clear; the exact mailbox-local unpack wrapper around `0x3CA` remains a best current fit rather than final dispatcher proof

## Summary

The current best model for the F-150 `LKA` path is:

- `0x3CA Lane_Assist_Data1` is the direct `LKA` steering-command PDU
- `FUN_10065b7c` is the best current unpack-helper fit for the key `0x3CA` steering fields
- the explicit local controller chain is `FUN_1017fbe0 -> FUN_101a4d56 -> FUN_101a3b84 -> FUN_101a4e4a`
- the local runtime family is `fef21a**`
- the directly adjacent `LKA` calibration family is `_DAT_fef263**` / `DAT_fef264**`
- the strongest current feature-envelope gates are `cal+0x0114 = 10.0` and `cal+0x00C4 = 10.0`

What is directly pinned in code:

- `FUN_101a4d56`, `FUN_101a3b84`, and `FUN_101a4e4a` are the core `LKA` local controller family
- the `LKA` local workspace clusters in `fef21a**`
- `FUN_101a4d56` feeds the override state machine with:
  - requested-angle-like `_DAT_fef21a6e`
  - processed interaction channels `_DAT_fef21a70` and `_DAT_fef21a72`
  - status byte `DAT_fef21a77`
- `FUN_101a3b84` compares those channels against `_DAT_fef263de`, `_DAT_fef263d0`, `_DAT_fef263d2`, `_DAT_fef263da`, `_DAT_fef263dc`, `DAT_fef26405`, and `DAT_fef26406`

The important structural result is that the F-150 rack does not treat `LKA` as a raw requested-angle plus one override scalar. It looks like:

- a direct `0x3CA` command family
- a dedicated `LKA`-local controller namespace
- an upstream driver-interaction classification path
- a local threshold / band / hysteresis state machine that decides whether assist stays active

## Message family and confidence

The mailbox family that matters to `LKA` in this image is:

| CAN ID | Role in the current model | Confidence |
|---|---|---|
| `0x3CA Lane_Assist_Data1` | direct `LKA` steering request from the camera-side lane-assist stack | high |
| `0x3CC Lane_Assist_Data3_FD1` | PSCM transmit availability / deny / hands-off feedback for lane assist | descriptor-slot proof only for the exact TX path |

Why `0x3CA` is the direct `LKA` fit:

- the DBC fields match direct lane-assist steering semantics
- the best current unpack helper decodes one angle-shaped field and one curvature-shaped field with the right scales
- the decoded values land in the explicit `LKA` local chain rather than the `LCA` or `APA` namespaces

The safe wording is:

- `0x3CA` is the direct `LKA` command path
- `FUN_10065b7c` is the best current unpack-helper fit, not yet a mailbox-local dispatcher proof

## Top-level execution chain

The current `LKA` path is best read as:

1. `0x3CA` lane-assist command data is decoded through a best-fit helper family that includes `FUN_10065b7c`
2. `FUN_1017fbe0` acts as the upstream `LKA` task wrapper
3. `FUN_101a4d56` snapshots and normalizes the local `LKA` inputs into `fef21a**`
4. `FUN_101a3b84` runs the core `LKA` controller and driver-override state machine
5. `FUN_101a4e4a` writes the final local `LKA` output `_DAT_fef21a78`

That chain is distinct from:

- the `LCA / BlueCruise` family in `fef238**`, `fef23b**`, `fef23c**`
- the `APA` family in `fef211**`, `fef212**`, `fef213**`

## Function roles

### `FUN_10065b7c`

`FUN_10065b7c` is the best current unpack-helper fit for the direct `LKA` message edge.

What is directly shown:

- one decoded field uses `(raw * 5e-06) - 0.01024`, which matches `LaCurvature_No_Calc`
- one decoded field uses `(raw * 0.05) - 102.4`, which matches `LaRefAng_No_Req`

Plain-English role:

- likely unpack the requested angle and curvature sideband from the direct `0x3CA` lane-assist frame before the `LKA` local chain consumes them

This should still be treated as a best current fit rather than final mailbox-wrapper proof.

### `FUN_1017fbe0`

This is the upstream `LKA` wrapper in the current controller chain.

What is safe to say:

- it is part of the explicit `LKA` execution path
- it sits above the local input snapshot and controller stages

Plain-English role:

- `LKA` task / wrapper entry before local normalization and state-machine logic run

### `FUN_101a4d56`

`FUN_101a4d56` is the `LKA` local input snapshot and normalization stage.

What is directly shown:

- `DAT_fef21a77 = FUN_100978bc()`
- `_DAT_fef21a6e` comes from `FUN_100968ea()` and is clamped to `±0x2800`
- `_DAT_fef21a72` comes from `FUN_10096f40()`
- `_DAT_fef21a70` comes from `FUN_10096f38()`
- both `_DAT_fef21a72` and `_DAT_fef21a70` are scaled and clamped before later use

That matters because:

- the interaction channels used by the override logic are already processed internal channels
- they are not yet pinned as a clean raw wheel-torque float in engineering units

Plain-English role:

- load the current requested-angle, processed interaction channels, and mode/status byte into the `LKA` local workspace

### `FUN_101a3b84`

`FUN_101a3b84` is the main `LKA` controller and driver-override state machine.

What is directly shown:

- it checks:
  - `abs(_DAT_fef21a6e)` against `_DAT_fef26382`
  - `_DAT_fef21a72` against `_DAT_fef263de`
  - `_DAT_fef21a70` against `_DAT_fef263de`
- it compares current and previous interaction-channel values and uses `DAT_fef26406` as a small-change / recent-activity threshold
- it bands an internal combined interaction metric using `_DAT_fef263d0` and `_DAT_fef263d2`
- it applies persistence / hysteresis logic using `_DAT_fef263da` and `_DAT_fef263dc`
- final assist-state transitions also depend on:
  - `DAT_fef21a74`
  - `DAT_fef21a75`
  - `DAT_fef21a77`
- `DAT_fef21a77 == 3` is a permissive path into stronger assist states
- `DAT_fef21a77 == 5` is a block / deny path

Plain-English role:

- decide whether `LKA` stays active, yields softly, or drops toward deny / no-assist states based on processed driver-interaction evidence plus state and hysteresis thresholds

This is the core reason the override model should not be described as “one torque scalar.”

### `FUN_101a4e4a`

`FUN_101a4e4a` is the local output-stage writer for the `LKA` family.

What is directly shown:

- it writes the final `LKA`-local output `_DAT_fef21a78`

Plain-English role:

- commit the final `LKA` command/result after the local controller and override logic settle the state

## Runtime namespace ownership

The `LKA` local runtime state lives primarily in `fef21a**`.

The core local cluster is:

- `fef21a62`
- `fef21a65`
- `fef21a68`
- `fef21a6c`
- `fef21a6e`
- `fef21a70`
- `fef21a72`
- `fef21a74`
- `fef21a75`
- `fef21a77`
- `fef21a78`

The current concrete mapping is:

| Namespace / slot | Current role | Main proven writer / consumer |
|---|---|---|
| `_DAT_fef21a6e` | requested-angle-like local command value | `FUN_101a4d56`, then `FUN_101a3b84` |
| `_DAT_fef21a70`, `_DAT_fef21a72` | processed driver-interaction channels | `FUN_101a4d56`, then `FUN_101a3b84` |
| `DAT_fef21a77` | mode / availability status byte | `FUN_101a4d56`, then `FUN_101a3b84` |
| `_DAT_fef21a78` | final local `LKA` output | `FUN_101a4e4a` |

This is the key ownership split:

- `LKA` owns `fef21a**`
- `LCA / BlueCruise` owns `fef238**`, `fef23b**`, `fef23c**`
- `APA` owns `fef211**`, `fef212**`, `fef213**`

## Calibration ownership

### Confirmed / strong `LKA` gates

The strongest current `LKA`-side feature-envelope ownership is:

- `cal+0x0114 = 10.0` — `LKA` engage minimum speed
- `cal+0x00C4 = 10.0` — `LDW / LKA`-side envelope gate

These should be treated as `LKA / LDW` envelope entries, not `APA` or generic shared-lateral fields.

### `LKA` local threshold and hysteresis family

The directly adjacent `LKA` threshold family is:

- `_DAT_fef26382`
- `_DAT_fef263d0`
- `_DAT_fef263d2`
- `_DAT_fef263da`
- `_DAT_fef263dc`
- `_DAT_fef263de`
- `DAT_fef26405`
- `DAT_fef26406`
- `_DAT_fef26428`
- `_DAT_fef2642c`
- `DAT_fef2642e`

Why this family belongs with `LKA`:

- `FUN_101a3b84` uses it directly as threshold, banding, and hysteresis state
- the family sits immediately adjacent to the `LKA` local workspace
- the same group is already surfaced in the mode-separation and plain-language cal notes as the `LKA` override family

Safe wording:

- this is the `LKA` local threshold / hysteresis / override family
- exact engineering-unit meaning for each scalar is still not fully field-pinned

### What is not yet field-pinned

Still unresolved:

- exact Ford signal names and physical units for `0xFEF2197A` and `0xFEF2197C`
- whether one of those channels corresponds more closely to wheel torque, hands-on confidence, or a higher-level override-confidence channel
- exact mailbox-local dispatcher proof for `FUN_10065b7c` as the `0x3CA` unpack wrapper

So the safe model remains:

- direct `LKA` message edge through `0x3CA`
- explicit local `LKA` controller family in `fef21a**`
- local override decision from processed interaction channels plus threshold / hysteresis logic

## Transmit feedback and closure path

`0x3CC Lane_Assist_Data3_FD1` belongs to the same overall `LKA` story because it is the visible PSCM transmit feedback for lane-assist availability and hands-off state.

What is directly pinned:

- `0x3CC` occupies one concrete low-flash TX descriptor slot at `0x100416ea`
- it sits inside a contiguous `0x082 -> 0x3CC -> 0x417` list

What remains open:

- the exact PSCM packer for `0x3CC`

Plain-English meaning:

- the rack clearly publishes lane-assist availability and deny state back out
- the descriptor is proven even though the packer body is not yet isolated

## Practical takeaway

If the goal is to change F-150 `LKA` behavior without touching `LCA` or `APA`, the highest-value ownership targets are:

- the direct `LKA` command family around `0x3CA`
- the local `LKA` workspace in `fef21a**`
- the `LKA` threshold and hysteresis family in `_DAT_fef263**` / `DAT_fef264**`
- the envelope gates at `cal+0x0114` and `cal+0x00C4`

If the goal is to reduce nuisance driver override specifically, the best current threshold candidates are:

- `_DAT_fef263de`
- `_DAT_fef263d0`
- `_DAT_fef263d2`
- `_DAT_fef263da`
- `_DAT_fef263dc`
- `DAT_fef26405`
- `DAT_fef26406`

## Cross-links

- [eps_dbc_message_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_dbc_message_trace.md)
- [eps_mode_separation_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_mode_separation_ghidra_trace.md)
- [driver_override_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/driver_override_findings.md)
- [torque_sensor_source_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/torque_sensor_source_trace.md)
- [lka_timer_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lka_timer_ghidra_trace.md)
- [strategy_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/strategy_findings.md)
