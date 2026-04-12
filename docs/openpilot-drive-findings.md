---
layout: default
title: Drive analysis — openpilot-on-LKA limits
nav_order: 80
---

# Drive analysis: openpilot-on-LKA authority limits

Findings from two real-world drives of a 2025 Ford Transit MK5 (VIN `1FTBF8XG0SKA96907`) running `ghostdev137/openpilot@ford-lka`, with `LKA_NO_LOCKOUT.VBF` flashed to the PSCM. This doc is for the firmware agent to consider what further cal/strategy patches could lift the remaining authority limits.

---

## Setup under test

| Component | Value |
|---|---|
| Vehicle | 2025 Transit MK5, CAN (non-CANFD), Q3 harness |
| PSCM firmware | `KK21-14D003-AM` with `LKA_NO_LOCKOUT.VBF` cal patch (timer table `+0x06B0..06C2` zeroed) |
| Camera (IPMA) | `NK3T-14F397-AB` — stock, no patch |
| openpilot branch | `ghostdev137/openpilot@ford-lka` commit `8389a6aa3` |
| opendbc branch | `ghostdev137/opendbc@ford-lka` commit `f4bfa254` |
| Steering strategy | LKA channel (`Lane_Assist_Data1`, 0x3CA) with `LaRefAng_No_Req` in mrad + `LkaActvStats_D2_Req` direction bit (2=L, 4=R) |
| LMC strategy | `LateralMotionControl` (0x3D3) passthrough of camera's values with `LatCtl_D_Rq=0` — heartbeat only |

openpilot runs stock-radar long (`openpilotLongitudinalControl=True`, `ACCDATA` emitted by pandad at 50 Hz).

---

## What works

**LKA cal patch: confirmed active.**

- Sustained 36 s engagement (route `074a9a28f2` at 100.6–136.4 s).
- `lkas_available` (= `Lane_Assist_Data3_FD1.LaActAvail_D_Actl == 3`) held True 100 % of engagement — no timer-based dropout.
- Tracking error vs. time-since-engage is flat / improving, not decaying. Four-second bins:

  | t-engage | `mean \|cmd−actual\|` | max err |
  |----------|---------------------|---------|
  | 0–4 s | 0.90° | 2.34° |
  | 4–8 s | 1.34° | 3.45° (driver turn) |
  | 8–12 s | 0.52° | 1.55° |
  | 12–16 s | 0.31° | 1.04° |
  | 16–20 s | 0.46° | 1.49° |
  | 20–24 s | 0.61° | 1.49° |
  | 24–28 s | 0.30° | 1.27° |
  | 28–32 s | 0.45° | 1.45° |
  | 32–36 s | 0.35° | 1.29° |

  If the 1 000 × 10 ms main lockout at `+0x06B6` (original `0x03E8`, patched `0x0000`) were still alive we would see a hard cutoff or monotonic degradation. We see neither.

- Disengagement was user-initiated (`pcmDisable` preceded any fault), not a timer.

**LKA does actuate.** Wheel-rate computed numerically from `SteeringPinion_Data.StePinComp_An_Est`:

- mean 3.1 °/s, p90 11 °/s, peak 51 °/s during `latActive` (rate fields `steeringTorqueEps` / `steeringRateDeg` are not populated by Ford carstate in openpilot, hence derived).

---

## What does not work — evidence for the firmware agent

### 1. PSCM torque-authority cap — **main limiter**

Per-command wheel response (route `074a9a28f2`, full 36 s engagement, 3 584 latActive samples):

| \|apply_angle\| (°, cmd−actual, clipped ±5.8) | n | \|wheel rate\| °/s | \|driver torque\| Nm |
|---|---:|---:|---:|
| 0.0 – 0.2 | 970 | 2.76 | 0.40 |
| 0.2 – 0.5 | 1 144 | 3.02 | 0.41 |
| 0.5 – 1.0 | 851 | 3.48 | 0.52 |
| 1.0 – 2.0 | 487 | 2.99 | 0.50 |
| 2.0 – 3.0 | 77 | **4.99** | 1.10 |
| 3.0 – 5.0 | 56 | **2.27** | 0.96 |

Rate **falls** at the 3–5° bin relative to the 2–3° bin even though the command is bigger. The PSCM is ramping the motor to some internal torque ceiling, then capping — classic LKA "nudge" authority.

We never hit the DBC ±102.3 mrad (≈±5.86°) ceiling on this drive (max `|apply_angle|` = 3.45°), so the openpilot-side clip is not the binding limit. The limit is inside the PSCM.

**Question for firmware**: where is the LKA motor-torque cap encoded? Candidates:
- A cal scalar (likely `float` or `u16`) near the known LKA timer table at `+0x06B0..06C2` — one of the adjacent entries may be an authority multiplier or Nm ceiling.
- Strategy-code constant (would need disassembly, not cal patch).
- A speed-scheduled authority curve (see §3).

A `0x23` (ReadMemoryByAddress) dump of the cal region around `+0x06C0..0700` across vehicles with strong LKA (F-150, Escape) vs Transit could reveal the delta.

### 2. Driver-override threshold too low

`1 097 steerOverride` events fired during a single-engagement 6-minute drive. Driver torque mean 0.47 Nm with peaks 2.7 Nm — consistent with a light hand on the wheel, not active override.

Example snapshot at `t=107 s` (route `074a9a28f2`):

```
t          cmd     actual   apply    rate     driver_tq
107.03    -0.00    -2.50    +2.50    -19.3    -2.00   ← driver holding wheel left
107.08    +0.25    -2.10    +2.35      0.0    -1.69
107.14    +0.23    -2.10    +2.33      0.0    -1.94
...
```

Wheel at 2° left, driver torque −2 Nm. Ford's stock LKA override threshold appears to be ≈ 0.7–1.5 Nm — the motor cuts out whenever the driver lightly rests on the wheel. openpilot's own steering-pressed threshold is `STEER_DRIVER_ALLOWANCE` but the PSCM has its own independent gate that we can't raise in software.

**Question for firmware**: the override-torque threshold is almost certainly a cal scalar. Locations worth probing:
- Any `float` near `+0x06B0..06C2` in the 0.5–2.0 range would match a Nm override threshold.
- Cross-reference with Escape cal (`LX6C`): does its LKA override threshold differ?

### 3. Speed-based authority floor below ~10 m/s

From route `259ad29d69`, the earlier drive with more low-speed content:

| vEgo (m/s) | mph | n | mean \|err\| | max \|err\| |
|---|---|---|---|---|
| 8–9 | 17.9 | 674 | **8.36°** | **22.05°** |
| 9–10 | 20.1 | 267 | 4.56° | 8.11° |
| 10–11 | 22.4 | 197 | 1.10° | 3.53° |
| 11–17 | 24–38 | 2 000+ | ≈ 1° | < 4° |
| 19–20 | 42.5 | 995 | 1.32° | 4.10° |

Below ~10 m/s the PSCM effectively refuses to actuate LKA regardless of command. Above 10 m/s the wheel tracks within ~1°. This is **not** the timer lockout (which is patched); it's a separate speed-schedule. APA's speed cap (`+0x02DC` / `+0x02E0`, already on your patch list) was for active-park; this low-end floor is the LKA-specific minimum-speed gate.

**Question for firmware**: is there an LKA minimum-speed scalar near the APA speed table at `+0x02C4..02E0`? Or in the block immediately after the zeroed timer table `+0x06C3..06C8`? A second `float` at ~10 m/s (36 kph) would be a strong candidate.

### 4. LKA angle cap ±5.86° (DBC)

`LaRefAng_No_Req` is ±102.3 mrad by DBC. Even if the PSCM would accept more (unknown), the signal encoding doesn't allow it. On this drive it wasn't binding, but it will be on tighter turns.

The only way past this is the LCA path (`LateralMotionControl` with `LatCtl_D_Rq=1`, curvature-based) — which is your `LCA_ENABLED.VBF` work-in-progress. LKA alone cannot execute turns beyond its clip.

---

## What was not a problem (for the agent to de-prioritise)

- **Timer-based lockout** — patched, confirmed inactive.
- **Direction-bit encoding** — `LkaActvStats_D2_Req` ∈ {0, 2, 4} accepted fine. Initial ghostdev branch had the direction logic inverted (used current-wheel sign, mims self-centering pattern); fixed in `opendbc@f4bfa254` to follow `sign(apply_angle)`.
- **openpilot-side cruise fault** — confirmed root cause was two-senders-of-ACCDATA (0x186) collision on the PT bus after disengagement (pandad 50 Hz + forwarded stock IPMA 50 Hz). CAN frame counts:

  | phase | 0x186 on bus 0 |
  |---|---|
  | engaged | 50 Hz (pandad only; fwd_hook blocked IPMA) |
  | post-disengage | 100 Hz (both senders) |

  Fixed at `ford_fwd_hook` to block ACCDATA/ACCDATA_3 unconditionally. **Not a PSCM issue** — noted here so the firmware agent doesn't chase it.

---

## Summary for the agent

The user has the **LKA timer lockout removed and it works**. Remaining limits on authority are all likely calibration-encoded:

1. **LKA motor-torque authority cap** — the highest-value target. PSCM ramps to a ceiling and stops.
2. **Driver-override torque threshold** — Ford's "hands-on detection" threshold is too sensitive; cutting motor at ~1 Nm.
3. **Minimum-speed floor** (~10 m/s) — separate from the zeroed timer, still active.
4. **LKA angle clip** — DBC-bound; not fixable in PSCM cal, need LCA path.

Suggested next action: `0x23` RAM/cal dump of a wider window around the known timer table (`+0x06A0..0700`), plus the same range on `LX6C` (Escape) for cross-diff. Any cal float in the range 0.5–5.0 Nm (override) or 8–12 m/s (speed floor) in that region is a smoking gun.

---

## Raw-log references

- Route `00000004--074a9a28f2` — 6.1 min drive, 1 engagement (100.6–136.4 s), cruise fault for the remaining 4 min.
- Route `00000003--259ad29d69` — 2.3 min drive, 2 engagements (20.4–30.3 s, 74.2–109.5 s), includes the low-speed authority-floor evidence.

Both rlogs are stored on-device at `/data/media/0/realdata/` on the comma device (dongle `ebf5c8dd5ae05d65`).
