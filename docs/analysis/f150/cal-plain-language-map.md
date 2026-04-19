---
title: F-150 Calibration Plain-Language Map
parent: F-150 Analysis
nav_order: 2
---

# F-150 EPS Calibration Plain-Language Map

This page is the quick lookup for the 2021 F-150 BlueCruise PSCM calibration.

Use it when the question is:

- "what does this table do?"
- "is this a lockout timer, a torque schedule, or a feature gate?"
- "what happens if I lower or zero this block?"

## Confidence ladder

- **High**: direct code path or consumer behavior is proven.
- **Medium**: subsystem role is clear, but some field-level details are unresolved.
- **Low**: table shape strongly suggests the role, but a direct consumer path is still missing.

## Quick lookup

| Offsets / family | Plain-language role | EPS subsystem | Confidence |
|---|---|---|---|
| `cal+0x00C4` | LDW/LKA-related minimum-speed gate | feature gating | High |
| `cal+0x0100..0x015C` | feature envelope block for LKA/LCA/APA-style gates and limits | feature gating / authority envelope | Medium |
| `_DAT_fef263de/_d0/_d2/_da/_dc`, `DAT_fef26405/6` | driver-override threshold + hysteresis family | takeover / override logic | High |
| `cal+0x06BA` | fixed-point axis for an unresolved scheduler | lookup axis | Low |
| `cal+0x07D68..0x07E3F` | supervisor gains / hysteresis / filter-shape block | rack supervisor | Medium |
| `cal+0x07ADC..0x07AE8` | lateral supervisor timing record with arm / re-arm / settle terms | lockout / re-arm behavior | Medium |
| `ctx + 0x6c` record, flash base unresolved | packed dwell / debounce / persistence timer bundle | watchdog / supervisor timing | High |
| `cal+0x07E64..0x07E68` | sibling supervisor timer block, likely ESA/TJA-side | sibling lockout / dwell behavior | Medium |
| `cal+0x080C..0x0878` | threshold / gain-step schedules | step scheduling / thresholds | Low |
| `cal+0x0DA8`, `0x1CFC`, `0x2C50`, `0x3BA4`, `0x4AF8` | repeated breakpoint axis family for authority / limiter schedules | torque / limiter scheduling | Medium |
| `ctx + 0x74`, `+0x78`, `+0x7c`, `+0xa8` records | limiter, blend, threshold, and state-selection curves | authority / filtering / mode selection | High |
| `cal+0x1402..0x1416` | deprecated or disabled timer-like family | old dwell / lockout behavior | Low |
| `cal+0x1520..0x153C` | ramp-up / rate-limit schedule | torque / authority ramping | Medium |
| `cal+0x1660` mirrored family | bell-shaped authority profile | steering authority shaping | Medium |

## Detailed catalog

### `cal+0x00C4`

- **Role:** LDW/LKA-related minimum-speed gate.
- **What the rack is deciding:** whether a lane-related feature is allowed to run above a minimum vehicle-speed threshold.
- **Likely type:** `float32`, currently `10.0`.
- **Patch effect:** lower or zero makes the feature eligible at lower speed; raising it delays engagement.

### `cal+0x0100..0x015C`

- **Role:** dense feature envelope block for LKA/LCA/APA-style gates, caps, and small gains.
- **What the rack is deciding:** the operating window for several steering features, including minimum speeds, related upper bounds, and nearby small gain / hysteresis terms.
- **Likely type:** mostly `float32`; includes known anchors `10.0`, `0.5`, `8.0`, `0.05`, `20.0`, `40.0`, `100.0`, `85.0`.
- **Patch effect:** lowering the gate-like entries broadens low-speed eligibility; changing the small-gain terms is riskier because they may remove hysteresis or damping.
- **Note:** this block still looks real, but it is not accessed through a simple same-offset `fef201xx` mirror in the current image.

### Driver-override threshold family: `_DAT_fef263de/_d0/_d2/_da/_dc`, `DAT_fef26405/6`

- **Role:** driver-override threshold, banding, and persistence family.
- **What the rack is deciding:** whether the driver is interacting with the wheel strongly enough, or persistently enough, to soften or drop lane-centering assist.
- **Likely type:** calibrated thresholds mirrored into RAM; physical units are still unresolved because the controller uses processed interaction channels, not a single raw torque scalar.
- **Patch effect:** lowering these thresholds makes override easier to trigger; raising them makes the rack more resistant to yielding.

### `cal+0x06BA`

- **Role:** fixed-point scheduler axis.
- **What the rack is deciding:** unresolved exact consumer, but it looks like an X-axis for a small fixed-point schedule rather than a flag bundle or timer.
- **Likely type:** monotonic `u16` axis `[0, 640, 1920, 3840, 7680, 10240, 12800, 15360, 19200]`.

### `cal+0x07D68..0x07E3F`

- **Role:** supervisor gains / hysteresis / filter-shape block.
- **What the rack is deciding:** how strongly to weight, filter, decay, or saturate internal supervisory signals around lateral-assist state transitions.
- **Likely type:** short monotonic float runs, including signed values and small positive coefficients.

### `cal+0x07ADC..0x07AE8`

- **Role:** lateral supervisor timing record with arm / re-arm / settle terms.
- **What the rack is deciding:** how long it waits before re-arming or re-entering parts of the lateral supervisor after state changes or driver interaction.
- **Likely type:** mixed `u16`, `u8`, and nearby float/int values; includes `10000`, `10000`, `1500`, `300`, and adjacent `0x01/0x01` timer bytes.
- **Patch effect:** lowering or zeroing the larger time-like terms shortens or removes waiting / lockout behavior.

### `ctx + 0x6c` packed record, flash base unresolved

- **Role:** packed dwell / debounce / persistence timer bundle.
- **What the rack is deciding:** how long a condition must remain true before it asserts, how long it stays latched, and how long it is retained after reset or decay.
- **Likely type:** packed `u16 * 10 ms` fields.
- **Patch effect:** lowering these timers makes faults or state changes assert or clear faster; raising them makes the rack slower to respond and more persistent once latched.

### `cal+0x07E64..0x07E68`

- **Role:** sibling supervisor timer block, probably for another lateral-assist supervisor path.
- **What the rack is deciding:** a second arm / settle / dwell pattern adjacent to the main LKA-style timing neighborhood.
- **Likely type:** `u16` values `10000`, `300`, `1500`.

### `cal+0x080C..0x0878`

- **Role:** threshold / gain-step schedules.
- **What the rack is deciding:** where a scheduler steps between small discrete thresholds or gains for one or more control paths.
- **Likely type:** compact `u16` tables such as `[10, 20, 30, 80, 100, 100, 100, 100]`.
- **Note:** the same-offset `fef208xx` RAM page is a live runtime workspace, not a passive mirror of these flash tables.

### Repeated curve family: `cal+0x0DA8`, `0x1CFC`, `0x2C50`, `0x3BA4`, `0x4AF8`

- **Role:** repeated breakpoint axis family for authority / limiter schedules.
- **What the rack is deciding:** where it moves between different authority or limiter regions as the scheduled input grows.
- **Likely type:** repeated monotonic `u16` breakpoint axes, retuned between BDL and EDL.

### Context-backed curve records: `ctx + 0x74`, `+0x78`, `+0x7c`, `+0xa8`

- **Role:** limiter, blend, threshold, and state-selection curves.
- **What the rack is deciding:** how much output is allowed, how quickly it is blended or filtered, and when the rack changes between limiter/authority states.
- **Likely type:** interpolation records copied into the live context from gp-backed sources.

### `cal+0x1402..0x1416`

- **Role:** deprecated or disabled timer-like family.
- **What the rack is deciding:** likely an older persistence or timeout path that Ford zeroed in the newer EDL revision.
- **Likely type:** repeated timer-like values, older BDL using repeated `655`, newer EDL zeroing them.

### `cal+0x1520..0x153C`

- **Role:** ramp-up / rate-limit schedule.
- **What the rack is deciding:** how quickly steering authority is allowed to build or change across a scheduled operating range.
- **Likely type:** monotonic `u16` schedule; EDL halves the entire BDL family.

### `cal+0x1660` mirrored family

- **Role:** bell-shaped steering-authority profile.
- **What the rack is deciding:** how much steering authority to allow across a normalized region, with a shaped peak rather than a flat cap.
- **Likely type:** repeated `u16` bell-like profile; EDL lowers the peak compared with BDL.

## Source notes

The full proof notes remain in the repository under `analysis/f150/`, including:

- `cal_findings.md`
- `strategy_findings.md`
- `driver_override_findings.md`
- `lka_timer_ghidra_trace.md`
- `eps_supervisor_ghidra_trace.md`
- `eps_curve_family_ghidra_trace.md`
- `eps_envelope_threshold_trace.md`
