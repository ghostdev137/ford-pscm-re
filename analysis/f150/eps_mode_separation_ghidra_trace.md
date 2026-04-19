# F-150 EPS mode separation trace from Ghidra

**Target:** `firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf`  
**Question:** which calibration and runtime records belong to `LKA`, `LCA/BlueCruise`, and `APA`, and what appears to be shared?  
**Status:** mode-local RAM namespaces and the shared input path are now clear; some higher-level supervisor records remain shared-lateral best fits rather than fully mode-pinned proof

## Summary

The F-150 PSCM does **not** look like one flat "lane centering" controller with a few flags.
It separates cleanly into:

1. **Shared wire/input conversion**
   - common signal getters and the common steering-angle scale path
   - used by every steering mode

2. **Shared lateral supervisor**
   - mixed supervisor / dwell / curve records like `ctx + 0x68`, `+0x6c`, `+0x74`, `+0x78`, `+0x7c`, `+0xa8`
   - currently best fit for the lateral-assist side of the rack
   - proven to feed LKA-adjacent and broader limiter/filter logic

3. **Mode-local controller namespaces**
   - `LKA`: `fef21a**`
   - `LCA / BlueCruise`: `fef238**`, `fef23b**`, `fef23c**`
   - `APA`: `fef211**`, `fef212**`, `fef213**`

That means the right ownership model is:

- some calibrations are clearly **mode-specific**
- some are clearly **shared across all steering-command modes**
- some sit in the middle as **shared lateral supervisor data** used by more than one on-road lateral mode

Torque-source note:

- the `LKA` and `LCA` branches share local processed driver-interaction channels
- current evidence says those channels are **local PSCM signals**, not a private CAN feed into the lateral controllers
- see [torque_sensor_source_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/torque_sensor_source_trace.md)

## What is definitely shared across all steering modes

## 1. Shared steering-angle input scale path

[angle_scale_patch.md](/Users/rossfisher/ford-pscm-re/analysis/f150/angle_scale_patch.md) already proved the most important shared piece:

- the wire-domain steering-angle command is decoded through one common conversion path
- changing the scale factor there affects:
  - `LKA`
  - `LDW`
  - `LCA`
  - `TJA`
  - `APA`
  - `BlueCruise`

That is the strongest "shared by everything" result in the current F-150 work.

### Plain-English meaning

This is the rack's **common steering command ingest path**.  
Every mode can have different downstream gates, ramps, and authority limits, but they all start from the same decoded requested-angle feed.

## 2. Shared low-level signal getters

The three mode-local wrappers all call the same family of short sensor/getter helpers:

- `FUN_100968ea`
- `FUN_10096926`
- `FUN_1009697c`
- `FUN_100969e0`
- `FUN_10096b1e`
- `FUN_10096e72`
- `FUN_10096f38`
- `FUN_10096f40`
- `FUN_10096f70`
- `FUN_10096f80`
- and many sibling `10097xxx` readers

Observed in:

- `FUN_101a4d56` (`LKA`)
- `FUN_101aa05e`, `FUN_101ab934`, `FUN_101ad86c`, `FUN_10186afa` (`LCA / BlueCruise`)
- `FUN_10180044`, `FUN_1018466e`, `FUN_101848ac` (`APA-side path`)

### Plain-English meaning

These helpers are the rack's **common decoded input layer**:

- steering angle / curvature-like requests
- status bitfields
- mode bytes
- low-level measured or commanded vehicle quantities

The mode wrappers consume the same underlying feeds, then normalize them into their own mode-local namespaces.

## What is shared across on-road lateral modes

## 3. Shared lateral supervisor / limiter records

The context-backed records documented in
[eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md)
and
[eps_curve_family_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_curve_family_ghidra_trace.md)
are best treated as **shared lateral-assist records**, not LKA-only records:

- `ctx + 0x68` — mixed continuous-control supervisor record
- `ctx + 0x6c` — packed dwell / debounce / persistence bundle
- `ctx + 0x74` — interpolation / limiter schedule
- `ctx + 0x78`, `+0x7c`, `+0xa8` — filter, limiter, and state-selection records

Why this is the right ownership for now:

- they are seeded globally from `FUN_10055494`
- they feed timer, filter, and interpolation logic above the individual LKA/LCA output globals
- their current proof chain is strongest on the **lateral supervisor** side of the codebase

### Important limit

I do **not** yet have direct proof that `APA` consumes these same context records.
So the safe claim is:

- shared by the **on-road lateral-assist family** (`LKA`, `LCA`, `TJA`, `BlueCruise`)
- not yet proven shared by `APA`

## 4. Timer neighborhoods at `0x07ADC` and `0x07E64`

Current safe ownership:

- `cal+0x07ADC..0x07AE8`
- `cal+0x07D68..0x07E3F`
- `cal+0x07E64..0x07E68`

Best current fit:

- these belong to the **shared lateral supervisor**, not to APA
- they are most likely used by the road-speed lateral modes (`LKA`, `LCA`, `TJA`, `BlueCruise`)

Evidence:

- the directly traced `LKA` timer helper lives here
- the `ctx + 0x68 / 0x6c / 0x74...` model points to the same supervisor family
- no direct APA consumer has been proven against this record family

So these should no longer be described as "the LKA timer block" in isolation.  
They are better described as **shared lateral lockout / dwell / supervisor data with an LKA-proven slice**.

## LKA-specific side

## 5. LKA-local workspace and thresholds

The `LKA` chain is explicit:

- `FUN_1017fbe0`
- `FUN_101a4d56`
- `FUN_101a3b84`
- `FUN_101a4e4a`

Its local namespace is:

- `fef21a62`, `fef21a65`, `fef21a68`, `fef21a6c`, `fef21a6e`, `fef21a70`, `fef21a72`, `fef21a74`, `fef21a75`, `fef21a77`, `fef21a78`

And its directly adjacent calibration family is:

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

### Plain-English role

This is the **LKA-local controller and override family**:

- requested-angle pre-clamp
- driver-override thresholds and hysteresis
- assist-state gating
- final LKA output gain / clamp

## 6. Likely LKA-specific cal blocks

The strongest current LKA ownership is:

- `cal+0x0114 = 10.0` — LKA engage min speed
- `cal+0x00C4 = 10.0` — LDW/LKA-side gate

These should be treated as **LKA / LDW-specific envelope entries**, not shared with APA.

## LCA / BlueCruise side

## 7. LCA / BlueCruise-local namespaces

The LCA / BlueCruise-side wrappers and control chain include:

- `FUN_101a392a` -> `FUN_10186afa`
- `FUN_101aa05e`
- `FUN_101ab934`
- `FUN_101ad86c`
- plus deeper helpers such as `FUN_101ad5a4`, `FUN_101aef34`, `FUN_101aaf16`

Their local runtime families split into:

- `fef238**` — normalized continuous quantities and output-side working floats
- `fef23b**` — input-prep / feature-conditioning values
- `fef23c**` — status, mode, and intermediate controller state

Concrete examples:

- `FUN_101aa05e` populates `fef23b68..fef23c04`
- `FUN_101ad86c` populates `fef23800..fef2384c`
- `FUN_101ab934` is the big LCA/BlueCruise-local controller operating across `fef238**`, `fef239**`, `fef23b**`, and `fef23c**`

### Plain-English role

This is the **LCA / BlueCruise local authority and state machine family**:

- curvature / angle / rate normalization
- limiter inputs
- mode bytes
- output-side shaping and internal state

## 8. Likely LCA-specific calibration

The strongest current LCA ownership is:

- `cal+0x0120 = 10.0` — LCA engage min speed

The repeated authority / limiter curve families are **more likely** to live on this side than on the APA side because:

- the big `FUN_10186afa` pipeline is heavily interpolation-oriented
- the context-backed curve records already look like limiter/filter/state-selection schedules
- the LCA/BlueCruise-local controller is where those kinds of schedules naturally land

But I am keeping that as **medium-confidence** ownership, not final proof.

So the safe wording is:

- repeated breakpoint / limiter curves are **shared lateral or LCA/BlueCruise-side**
- not yet proven APA-side

## APA side

## 9. APA-local namespaces

The APA-side path is clearly separate from LKA and LCA:

- `FUN_1018466e`
- `FUN_101848ac`
- and the upstream prep path at `FUN_10180044`

Its mode-local runtime families are:

- `fef211**`
- `fef212**`
- `fef213**`

Examples:

- `FUN_1018466e` writes `fef2125c..66`, `fef21220..24`, `fef2126f..72`, `fef213a4..ac`
- `FUN_101848ac` consumes `fef21224`, `fef21262`, `fef2126f`, `fef213ae` and updates the APA-side path
- `FUN_10180044` fills a larger APA-side staging space across `fef211**`, `fef212**`, and some shared runtime workspace at `fef208**`

### Plain-English role

This is the **APA parking-speed controller family**:

- low-speed command conditioning
- parking-mode status bits
- parking-specific thresholds and limits
- APA output staging

## 10. APA-specific calibration

The strongest current APA ownership is:

- `cal+0x0140 = 0.5` — APA min engage speed
- `cal+0x0144 = 8.0` — APA max engage speed

And the likely APA-local threshold family in RAM is:

- `fef258**`
- `fef25ea*`
- `fef25eb*`

as seen in `FUN_10180044`, `FUN_1018466e`, and `FUN_101848ac`.

That makes APA the cleanest feature split in the current image: its speed gates and local workspace are already clearly separate from the on-road lateral controllers.

## Working ownership table

| Family | Best current owner |
|---|---|
| shared angle scale / steering-angle ingest | all steering modes |
| short `10096xxx` / `10097xxx` sensor-getter layer | all steering modes |
| `ctx + 0x68 / 0x6c / 0x74 / 0x78 / 0x7c / 0xa8` | shared on-road lateral supervisor |
| `cal+0x07D68..0x07E68` | shared on-road lateral supervisor, LKA-proven slice |
| `cal+0x00C4`, `cal+0x0114` | LKA / LDW side |
| `_DAT_fef263**`, `DAT_fef264**`, `fef21a**` | LKA |
| `cal+0x0120` | LCA |
| `fef238**`, `fef23b**`, `fef23c**` | LCA / BlueCruise |
| repeated breakpoint / limiter curves | shared lateral or LCA/BlueCruise-side, not yet final |
| `cal+0x0140`, `cal+0x0144` | APA |
| `fef211**`, `fef212**`, `fef213**`, `fef258**`, `fef25ea*`, `fef25eb*` | APA |

## Practical takeaway

If the question is "what can I change without touching the others?":

- change `LKA` behavior in the `fef21a**` / `fef263**` / `0x0114` side
- change `LCA` behavior in the `fef238**` / `fef23b**` / `fef23c**` / `0x0120` side
- change `APA` behavior in the `fef211**` / `fef212**` / `fef213**` / `0x0140..0x0144` side

If the question is "what will move multiple modes together?":

- the shared steering-angle scale path definitely will
- the shared lateral supervisor records probably will

That is the right current separation model for this firmware.
