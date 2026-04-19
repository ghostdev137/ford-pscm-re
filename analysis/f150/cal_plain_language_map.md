# F-150 EPS Calibration Plain-Language Map

This is the master plain-language catalog for the 2021 F-150 BlueCruise PSCM calibration.

Use this page first when the question is:

- "what does this table do?"
- "is this a lockout timer, a torque schedule, or a feature gate?"
- "what would lowering or zeroing this block do on the rack?"

For proof, field-level reasoning, and decompile context, follow the linked deep-dive notes.

Mode ownership cross-reference:

- [eps_mode_separation_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_mode_separation_ghidra_trace.md) — which blocks look `LKA`-specific, `LCA/BlueCruise`-specific, `APA`-specific, or shared
- [eps_dbc_message_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_dbc_message_trace.md) — DBC-level message map for `LKA`, `LCA/BlueCruise`, `APA`, and shared PSCM feedback

## Confidence ladder

- **High**: direct code path or consumer behavior is proven.
- **Medium**: subsystem role is clear, but some field-level details are still unresolved.
- **Low**: structure strongly suggests the role, but a direct consumer path is still missing.

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

- **Plain-language role:** LDW/LKA-related minimum-speed gate.
- **EPS subsystem:** feature-enable gating.
- **What the rack is deciding:** whether a lane-related feature is allowed to run above a minimum vehicle-speed threshold.
- **Likely unit/type:** `float32`, currently `10.0`.
- **Lower / higher / zero effect:** lower or zero makes the feature eligible at lower speed; raising it delays engagement.
- **Confidence:** **High**.
- **Proof links:** [cal_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_findings.md), [strategy_cal_reads.md](/Users/rossfisher/ford-pscm-re/analysis/f150/strategy_cal_reads.md)

### `cal+0x0100..0x015C`

- **Plain-language role:** dense feature envelope block for LKA/LCA/APA-style gates, caps, and small gains.
- **EPS subsystem:** feature gating and authority envelope.
- **What the rack is deciding:** the operating window for several steering features, including minimum speeds, related upper bounds, and nearby small gain / hysteresis terms.
- **Likely unit/type:** mostly `float32`; includes known anchors `10.0`, `0.5`, `8.0`, `0.05`, `20.0`, `40.0`, `100.0`, `85.0`.
- **Lower / higher / zero effect:** lowering the gate-like entries broadens low-speed eligibility; raising the larger envelope entries likely expands caps or allowable range; zeroing the small gain terms would be riskier because they may remove hysteresis or damping.
- **Confidence:** **Medium**.
- **Notes:** direct same-offset `fef201xx` mirror xrefs do **not** prove this block in the current image; it is still best treated as a real feature-envelope neighborhood accessed indirectly through gp/context-backed records.
- **Proof links:** [cal_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_findings.md), [eps_envelope_threshold_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_envelope_threshold_trace.md)

### Driver-override threshold family: `_DAT_fef263de/_d0/_d2/_da/_dc`, `DAT_fef26405/6`

- **Plain-language role:** driver-override threshold, banding, and persistence family.
- **EPS subsystem:** hands-on / takeover / yield logic.
- **What the rack is deciding:** whether the driver is interacting with the wheel strongly enough, or persistently enough, to soften or drop lane-centering assist.
- **Likely unit/type:** calibrated scalar thresholds mirrored into RAM; physical units are still unresolved because the controller consumes processed interaction channels, not a raw torque scalar.
- **Lower / higher / zero effect:** lowering these thresholds would make override easier to trigger; raising them would make the rack more resistant to yielding; zeroing the hysteresis terms would likely make the state machine unstable or chatter-prone.
- **Confidence:** **High** for the subsystem role, **Medium** for exact physical interpretation.
- **Notes:** this is **not** one clean "driver torque Nm" scalar; the rack uses multiple thresholds plus state logic.
- **Proof links:** [driver_override_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/driver_override_findings.md)

### `cal+0x06BA`

- **Plain-language role:** fixed-point scheduler axis.
- **EPS subsystem:** lookup-axis support.
- **What the rack is deciding:** unknown exact consumer, but it looks like the X-axis for one small fixed-point schedule rather than a raw flag bundle or timer.
- **Likely unit/type:** monotonic `u16` axis `[0, 640, 1920, 3840, 7680, 10240, 12800, 15360, 19200]`.
- **Lower / higher / zero effect:** reshapes where some schedule transitions happen on its input axis.
- **Confidence:** **Low**.
- **Proof links:** [cal_undocumented_candidates.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_undocumented_candidates.md), [eps_envelope_threshold_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_envelope_threshold_trace.md)

### `cal+0x07D68..0x07E3F`

- **Plain-language role:** continuous-control supervisor record with angle-like thresholds, fallback magnitudes, and filter-shape terms.
- **EPS subsystem:** rack supervisor and continuous-control tuning.
- **What the rack is deciding:** how tightly to validate internal supervisory estimates, what fallback magnitudes to apply when a validation chain fails, and how aggressively to filter or decay those signals around lateral-assist state transitions.
- **Likely unit/type:** mixed float/int neighborhood with short monotonic float runs and nearby structured constants; best-fit values include `5 deg`, `10 deg`, `0.7`, `0.008`, `36.1111`, `5.5556`, `90.0`, `1.2`, and `5.0`.
- **Lower / higher / zero effect:** lowering the angle-like thresholds or fallback magnitudes would make the supervisor switch to its fallback behavior sooner; lowering the filter term would speed up the response; zeroing the small coefficients risks removing damping or numerical conditioning.
- **Confidence:** **Medium**.
- **Notes:** this is tied to the same supervisor family as the timer neighborhoods and the mixed `ctx + 0x68` record. The mid-range field mapping is now stronger than the low-end flash base proof, so treat the role as solid but the exact record start as still slightly unresolved.
- **Proof links:** [cal_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_findings.md), [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md)

### `cal+0x07ADC..0x07AE8`

- **Plain-language role:** lateral supervisor timing record with arm / re-arm / settle terms.
- **EPS subsystem:** lockout, qualify, and re-entry timing.
- **What the rack is deciding:** how long it waits before re-arming or re-entering parts of the lateral supervisor after state changes or driver interaction.
- **Likely unit/type:** mixed `u16`, `u8`, and nearby float/int values; includes `10000`, `10000`, `1500`, `300`, and adjacent `0x01/0x01` timer bytes.
- **Lower / higher / zero effect:** lowering or zeroing the larger time-like terms shortens or removes waiting / lockout behavior; zeroing the smaller settle terms would likely make transitions more abrupt.
- **Confidence:** **Medium**.
- **Notes:** the exact direct mapping is nuanced: the adjacent `0x01/0x01` bytes are the best current fit for the directly proven `u8 * 10000 ms` substate timers, while the `10000/10000` pair still best fits higher-level arm/re-arm timing in the same neighborhood.
- **Proof links:** [lka_timer_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lka_timer_ghidra_trace.md), [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md)

### `ctx + 0x6c` packed record, flash base unresolved

- **Plain-language role:** packed dwell / debounce / persistence timer bundle.
- **EPS subsystem:** watchdog / qualifier / supervisor timing.
- **What the rack is deciding:** how long a condition must remain true before it asserts, how long it stays latched, and how long it is retained after reset or decay.
- **Likely unit/type:** packed `u16 * 10 ms` fields.
- **Lower / higher / zero effect:** lowering these timers makes faults or state changes assert or clear faster; raising them makes the rack slower to respond and more persistent once latched.
- **Confidence:** **High**.
- **Notes:** this is a separate timing family from the mixed `0x07ADC` record and should not be collapsed into one “LKA timer” scalar.
- **Proof links:** [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md)

### `cal+0x07E64..0x07E68`

- **Plain-language role:** sibling supervisor timer block, probably for another lateral-assist supervisor path.
- **EPS subsystem:** sibling lockout / dwell behavior.
- **What the rack is deciding:** a second arm / settle / dwell pattern adjacent to the main LKA-style timing neighborhood.
- **Likely unit/type:** `u16` values `10000`, `300`, `1500`.
- **Lower / higher / zero effect:** same general effect as the main lockout record: lower means quicker re-entry and shorter dwell, higher means more conservative timing.
- **Confidence:** **Medium**.
- **Notes:** best current fit is ESA/TJA-side or another sibling supervisor path, not a duplicate of the exact same helper.
- **Proof links:** [cal_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_findings.md)

### `cal+0x080C..0x0878`

- **Plain-language role:** threshold / gain-step schedules.
- **EPS subsystem:** step scheduling and thresholding.
- **What the rack is deciding:** where a scheduler steps between small discrete thresholds or gains for one or more control paths.
- **Likely unit/type:** compact `u16` tables such as `[10, 20, 30, 80, 100, 100, 100, 100]`.
- **Lower / higher / zero effect:** shifts the step points or the magnitude of discrete scheduled thresholds.
- **Confidence:** **Low**.
- **Notes:** the flash tables look real, but same-offset `fef208xx` xrefs are misleading because that RAM page is a live runtime workspace, not a passive cal mirror.
- **Proof links:** [cal_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_findings.md), [eps_envelope_threshold_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_envelope_threshold_trace.md)

### Repeated curve family: `cal+0x0DA8`, `0x1CFC`, `0x2C50`, `0x3BA4`, `0x4AF8`

- **Plain-language role:** repeated breakpoint axis family for authority / limiter schedules.
- **EPS subsystem:** torque / limiter scheduling.
- **What the rack is deciding:** where the rack moves between different authority or limiter regions as the scheduled input grows.
- **Likely unit/type:** repeated monotonic `u16` breakpoint axes, retuned between BDL and EDL.
- **Lower / higher / zero effect:** compresses or stretches the scheduled authority curve; lower breakpoints make the limiter transition earlier, higher breakpoints delay it.
- **Confidence:** **Medium**.
- **Notes:** these are now much more defensible as live EPS scheduling data because the downstream consumers are interpolation-driven; exact per-pointer flash mapping is still unresolved.
- **Proof links:** [cal_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_findings.md), [eps_curve_family_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_curve_family_ghidra_trace.md)

### Context-backed curve records: `ctx + 0x74`, `+0x78`, `+0x7c`, `+0xa8`

- **Plain-language role:** limiter, blend, threshold, and state-selection curves.
- **EPS subsystem:** authority shaping, filtering, and mode selection.
- **What the rack is deciding:** how much output is allowed, how quickly it is blended or filtered, and when the rack changes between limiter/authority states.
- **Likely unit/type:** interpolation records copied into the live context from gp-backed sources.
- **Lower / higher / zero effect:** lowering the limiting scales makes the rack more conservative; lowering filter terms speeds up response; changing state-selection margins changes when the rack switches control modes.
- **Confidence:** **High** for the runtime role, **Medium** for the exact backing flash family.
- **Proof links:** [eps_curve_family_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_curve_family_ghidra_trace.md)

### `cal+0x1402..0x1416`

- **Plain-language role:** deprecated or disabled timer-like family.
- **EPS subsystem:** old dwell / lockout behavior.
- **What the rack is deciding:** likely an older persistence or timeout path that Ford zeroed in the newer EDL revision.
- **Likely unit/type:** repeated timer-like values, older BDL using repeated `655`, newer EDL zeroing them.
- **Lower / higher / zero effect:** zero removes the delay entirely; larger values restore a longer wait or persistence window.
- **Confidence:** **Low**.
- **Proof links:** [cal_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_findings.md)

### `cal+0x1520..0x153C`

- **Plain-language role:** ramp-up / rate-limit schedule.
- **EPS subsystem:** torque / authority ramping.
- **What the rack is deciding:** how quickly steering authority is allowed to build or change across a scheduled operating range.
- **Likely unit/type:** monotonic `u16` schedule; EDL halves the entire BDL family.
- **Lower / higher / zero effect:** lower values make the rack build authority more gently or more slowly; higher values make intervention more aggressive.
- **Confidence:** **Medium**.
- **Proof links:** [cal_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_findings.md)

### `cal+0x1660` mirrored family

- **Plain-language role:** bell-shaped steering-authority profile.
- **EPS subsystem:** authority shaping.
- **What the rack is deciding:** how much steering authority to allow across a normalized region, with a shaped peak rather than a flat cap.
- **Likely unit/type:** repeated `u16` bell-like profile; EDL lowers the peak compared with BDL.
- **Lower / higher / zero effect:** lower peak values soften intervention; higher values increase steering authority; flattening it would distort the intended steering feel.
- **Confidence:** **Medium**.
- **Proof links:** [cal_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_findings.md)

## How to use this map

- If you need **faster re-arm or less waiting**, start with the lockout / dwell families:
  - `cal+0x07ADC..0x07AE8`
  - `ctx + 0x6c`
  - `cal+0x07E64..0x07E68`
- If you need **different low-speed eligibility**, start with:
  - `cal+0x00C4`
  - `cal+0x0100..0x015C`
- If you need **more or less steering authority**, start with:
  - repeated curve family at `0x0DA8...`
  - `ctx + 0x74/+0x78/+0x7c/+0xa8`
  - `cal+0x1520..0x153C`
  - `cal+0x1660`
- If you need **less nuisance driver override**, start with:
  - driver-override threshold family `_DAT_fef263de/_d0/_d2/_da/_dc`, `DAT_fef26405/6`

When an entry is only **Medium** or **Low** confidence, treat the plain-language label as the best current rack-level role, not a final field-by-field engineering name.
