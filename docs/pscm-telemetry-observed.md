---
layout: default
title: PSCM telemetry — what Transit actually reports
nav_order: 82
---

# PSCM telemetry — what the 2025 Transit actually reports over CAN

Handoff to the firmware agent. Companion to `lka-signal-space.md` (which covers command-side signals). This doc is about **readback signals** — what we can observe the PSCM doing, and where the instrumentation appears to be dead on Transit.

Short version: some PSCM signals that should tell us whether the motor is torque-capped are either **not populated** on Transit or populated trivially. If confirmed in firmware, these are candidates for either (a) enabling the telemetry so we can diagnose, or (b) cross-referencing what *is* populated to find the real torque cap.

---

## CAN IDs referenced in this doc

| Msg | ID (hex/dec) | Direction | Purpose |
|---|---|---|---|
| `EPAS_INFO` | `0x082 / 130` | PSCM → bus | Motor current, column torque, EPS failure |
| `SteeringPinion_Data` | `0x07E / 126` | PSCM → bus | Pinion angle |
| `Yaw_Data_FD1` | `0x091 / 145` | ABS → bus | Yaw rate |
| `Steering_Data_FD1` | `0x083 / 131` | SCCM → bus | Button presses |
| `Lane_Assist_Data1` | `0x3CA / 970` | IPMA_ADAS → PSCM | LKA commands (openpilot TX) |
| `Lane_Assist_Data3_FD1` | `0x3CC / 972` | PSCM → IPMA_ADAS | LKA status (read-only) |
| `LateralMotionControl` | `0x3D3 / 979` | IPMA_ADAS → PSCM | LCA/TJA commands |
| `LateralMotionControl2` | `0x3CE / 974` | IPMA_ADAS → PSCM | LCA on CANFD |
| `ACCDATA` | `0x186 / 390` | IPMA_ADAS → PCM | ACC request |
| `ACCDATA_3` | `0x17D / 381` | IPMA_ADAS → PCM | ACC UI |
| `IPMA_Data` | `0x3D8 / 984` | IPMA_ADAS → bus | Camera status, LDW UI |
| `EngBrakeData` | `0x167 / 359` | PCM → bus | Cruise state (`CcStat_D_Actl`) |
| `PSCM_Diag_Req` | `0x730 / 1840` | tester → PSCM | UDS request |
| `PSCM_Diag_Resp` | `0x738 / 1848` | PSCM → tester | UDS response |

---

## `EPAS_INFO` (0x82) — signal-by-signal observation

Route `ebf5c8dd5ae05d65/00000015--818b269270` (4.5 min drive with `LKA_NO_LOCKOUT.VBF` + 3 m/s floor patch + fast-ramp). 4 471 EPAS_INFO frames captured during `latActive`.

### Signal layout from DBC

```
BO_ 130 EPAS_INFO: 8 PSCM
 SG_ SteeringColumnTorque : 7|8@0+ (0.0625,-8) [-8|7.8125] "Nm"
 SG_ EPAS_Failure          : 9|2@0+ (1,0) [0|3] "SED"
 SG_ DrvSteActv_B_Stat     : 10|1@0+ (1,0) [0|1] "SED"
 SG_ SteMdule_I_Est        : 21|12@0+ (0.05,-64) [-64|140.7] "Amps"
 SG_ SteMdule_U_Meas       : 39|8@0+ (0.05,6) [6|18.7] "Volts"
 SG_ DrvSte_Tq_Actl        : 47|8@0+ (0.0625,-8) [-8|7.8125] "Nm"
 SG_ SteMdule_D_Stat       : 55|3@0+ (1,0) [0|7] "SED"
 SG_ Veh_V_RqMxTrlrAid     : 63|8@0+ (0.1,0) [0|25.5] "km/h"
```

### What we observed

| Signal | Observed range during latActive | Apparent status |
|---|---|---|
| `SteeringColumnTorque` | −2.7 Nm to +1.0 Nm, meanabs ≈ 0.4 Nm | **Live** (driver column input) |
| `DrvSte_Tq_Actl` | Stuck at `-8.00` in my decoder | **Either dead or decoded wrong** |
| `SteMdule_I_Est` | `−0.15` to `+0.35` A across entire drive; meanabs 0.04 A; even with 13° of commanded apply_angle the max seen was 0.35 A | **Either dead or decoded wrong** (DBC range is ±140 A; if live, we'd expect A-level current during steering) |
| `EPAS_Failure` | `0` (healthy) | Live |

### Why this matters

We can't **directly** verify whether the PSCM's motor is hitting its torque cap, because the signal that would tell us (`SteMdule_I_Est`) reads as near-zero across every demand bucket — even when the planner is saturating the ±5.8° LKA clip and the wheel isn't catching up. The **indirect** evidence remains:

- Commanded wheel angle 11.4° at 9–10 m/s, actual at 1.5°, driver torque 0.16 Nm (hands off).
- ±5.8° clip saturated for 754 samples at low speed.

Something is limiting, but we can't yet point at a specific motor current / torque ceiling from the bus.

### Open questions for the firmware agent

1. **Does the 2025 Transit PSCM strategy populate `SteMdule_I_Est` and `DrvSte_Tq_Actl`?**  
   Worth checking the `EPAS_INFO` packer in strategy — search for writes to the corresponding frame bytes. If the fields are left at default on Transit but populated on e.g. F-150, that's a platform-specific telemetry gap.

2. **If the signal is alive but my decode is wrong**, it'd be useful to document the exact bit-packing the Transit PSCM uses. (Cabana will resolve this in 30 s on the user's side — noted in docs/openpilot.md.)

3. **If telemetry is genuinely off on Transit**, is there a cal bit that enables it, or is it strategy-level? Enabling would give us a direct motor-current trace to pair with our drive logs.

---

## `Lane_Assist_Data3_FD1` (0x3CC) — PSCM → IPMA

We don't currently read most of this. Candidates for diagnostic logging (see `lka-signal-space.md` for full table):

- `LatCtlCpblty_D_Stat` — is Transit stock stuck at `1=LimitedMode`? If yes, that's the gate `LCA_ENABLED.VBF` must flip to `2=ExtendedMode`.
- `LatCtlLim_D_Stat` — does PSCM announce `2=LimitReached` when we hit the authority cap?
- `LsmcBrk_Tq_Rq` — does PSCM ever recruit asymmetric ABS braking for lane-keep? Never seen on any of our drives yet.

---

## Drive evidence locations

| Route | Note |
|---|---|
| `ebf5c8dd5ae05d65/00000003--259ad29d69` | Pre-patch, low-speed 22° errors |
| `ebf5c8dd5ae05d65/00000004--074a9a28f2` | Post-ACCDATA-fix, single engagement |
| `ebf5c8dd5ae05d65/00000014--10a5949cf7` | `LKA_NO_LOCKOUT.VBF` + 3 m/s floor, 11 engagements |
| `ebf5c8dd5ae05d65/00000015--818b269270` | + fast-ramp A/B, 4 engagements, EPAS_INFO decoded |

rlogs mirrored to `/Users/rossfisher/comma-segments/<route>/*/rlog.zst` on the workstation.

---

## Tools note for future sessions

openpilot ships `tools/cabana/cabana` which ingests route rlogs and visualizes every DBC signal live with overlays. Preferred over manual bit-decoding for sanity checks — would have resolved the `SteMdule_I_Est` question in seconds by showing whether the signal is flat or alive.

```
cd ~/openpilot && tools/cabana/cabana --stream /path/to/rlog.zst
```
