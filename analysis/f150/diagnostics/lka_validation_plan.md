# F-150 LKA patch validation via UDS DIDs

The ML34 MDX exposes live-readable DIDs that directly measure the three
things our LKA patches change. Every claim we've made about the patches
can now be verified on-car via standard UDS `0x22 ReadDataByIdentifier`
— no security access, default session.

## Patch-to-DID mapping

| Patch | Claim | Validation DID | Units | Expected stock | Expected patched |
|---|---|---|---|---|---|
| `LKA_NO_LOCKOUT` (zero lockout timers at `cal+0x07ADC/0x07ADE`) | LKA stays in ACTIVE state past 10 s | `0xEE42` SF5 "LKA Feature State" | enum | `0x03 ACTIVE` → `0x05 LOCKED` after ~10 s | stays at `0x03 ACTIVE` indefinitely |
| `LKA_FULL_AUTHORITY` (torque curve at `cal+0x03C4..+0x03E3`) | Motor torque cap raised ~3× at highway speed | `0xEE05` Final Motor Torque | Nm | caps at ~1.0 Nm at 70 kph | caps at ~3.5 Nm at 70 kph |
| `LKA_MIN_SPEED=0` (zero `cal+0x0690`) | LKA engages below 22 mph | `0xEE42` SF5 + `0xEE07` EPS State | enum + enum | stock: LKA `PASSIVE` below ~10 m/s | patched: LKA `ACTIVE` from standstill |
| `OVERRIDE_2X` (±0.8 → ±1.6 Nm at Transit `cal+0x29D4/0x29E0`) | Driver torque threshold doubled | `0x330C` Steering Shaft Torque | Nm | yield fires ~0.8 Nm (per stock hypothesis) | yield fires ~1.6 Nm on Transit; F-150 not yet patched for override |

## Supporting DIDs for context

| DID | Purpose |
|---|---|
| `0x3020` Steering Pinion Angle | Deg, resolution 1/10, offset=-780. Correlate angle command vs state transitions. |
| `0x301F` Steering Pinion Rotation Speed | Deg/s, resolution 4/1. Angular velocity. |
| `0xDD09` Vehicle Speed | Frame of reference for speed-gated behaviors. |
| `0xEE20` LoA Fault Reporting | 8 newest Limitation-of-Availability DTCs. Read after any drop to see what the rack flagged. |
| `0xFD01` Ford System State Fault Counter | Per-ECU persistence + limp-home counters. Reveals dual-ECU fault state. |

## On-car polling plan (via Panda or J2534)

Extended session isn't required for most of these — default session
`session_01` covers the reads. Request format: `0x22 HH LL` where
`HHLL` is the DID number.

At 10 Hz, log:

```
0x22 33 0C    # Steering Shaft Torque Sensor #2 (1 B, Nm)
0x22 30 20    # Steering Pinion Angle (2 B, 0.1 deg)
0x22 EE 05    # Final Motor Torque (2 B, Nm)
0x22 EE 07    # EPS System State (1 B, enum)
0x22 EE 42    # Active Features (10 B, enum × 10)
0x22 DD 09    # Vehicle Speed (1 B)
```

That's 6 DIDs ~= 25 bytes of response per poll. Easy 10 Hz over ISOTP.

Poll, drive a known-failing scenario, correlate timestamps of:

- `0xEE07` transitions (e.g. `0x02 Full Assist` → `0x01 Limited Assist`)
- `0xEE42` SF5 (LKA Feature State: `0x03 ACTIVE` → `0x05 LOCKED`)
- `0xEE05` trajectory (motor torque hitting ceiling?)
- `0x330C` reading at moment of yield (driver input torque)

## Validation scenarios

### Scenario A: Validate `LKA_NO_LOCKOUT`
Engage LKA, hold for 15+ seconds, watch `0xEE42` SF5.

- Stock: transitions `0x03 ACTIVE` → `0x05 LOCKED` at ~10 s.
- Patched: stays `0x03 ACTIVE` indefinitely.

### Scenario B: Validate `LKA_FULL_AUTHORITY`
Engage LKA at 70 kph in a curve, log `0xEE05` Final Motor Torque.

- Stock: ceiling clips at ~1.0 Nm.
- Patched: ceiling clips at ~3.5 Nm (curve value at 70 kph).

### Scenario C: Validate `LKA_MIN_SPEED=0`
Try to engage LKA at 10 mph.

- Stock: `0xEE42` LKA stays `PASSIVE`.
- Patched: `0xEE42` LKA transitions to `ACTIVE`.

### Scenario D: Measure override threshold (prerequisite for cal+0x29D4 validation)
F-150 driver-override RAM threshold (`_DAT_fef263de`) couldn't be
directly cal-sourced from emulation. The on-car reading of `0x330C`
when `0xEE07` transitions Full→Limited Assist **is** the stock
threshold value in Nm. Log this during a turn where LKA yields. If the
reading at yield is ~0.8 Nm, that confirms the Transit `cal+0x29D4 =
+0.8 Nm` hypothesis is correct in units AND magnitude.

## Confidence update after on-car measurement

The whole Transit `cal+0x29D4` patch is currently labeled "Medium
confidence" in `analysis/transit/driver_override_patch_candidates.md`
pending direct emulation proof. A measurement of **F-150 `0x330C` at
the moment of `0xEE07` state transition on a failing turn** would move
that to HIGH confidence — it's the same Ford override architecture, so
a measured F-150 threshold validates the Transit cal value inference.

## Writable DIDs — alternative to flashing

Several DIDs are writable at `security_level_2` and may toggle LKA
behavior without a flash:

| DID | Bit | Purpose |
|---|---|---|
| `0xDE01` SF7 | 1 B | LKA Enabled (`0x00`/`0xFF`) |
| `0xDE01` SF6 | 1 B | LDW Enabled |
| `0xDE01` SF8 | 1 B | TJA (Traffic Jam Assist) Enabled |
| `0xDE01` SF9 | 1 B | LCA Enabled |
| `0xDE01` SF11 | 1 B | ESA (Evasive Steering Assist) Enabled |
| `0xDE01` SF12 | 1 B | HAD Enabled |
| `0xDE02` SF2 | 1 B | SAPP/APA Enable/Disable |
| `0xEE02` | 1 B | Assist ON / OFF (`0xFF` = on, `0x00`/`0x01`/`0x02` = off at 3 different pipeline stages) |
| `0xEE01` | 1 B | **XCP Enable** — enables runtime cal read/write via XCP-on-CAN |
| `0xEE41` | 1 B | Research Feature Switch |
| `0xEE40` | 3 B | Ford In-House HSCAN passthrough signals (dev instrumentation) |
| `0xEED0` | 1 B | Supplier Factory Mode |

**`0xEE01` XCP Enable is the standout.** XCP is the standard
measurement/calibration protocol Ford uses internally. If enabled, it
exposes read/write of cal variables at runtime via CAN, without a
flash cycle. Requires `security_level_2`.

**`0xEE00` Dev Msg Config** enables broadcast of internal EPS state on
CAN messages `0x61C` and `0x61D` — 9 different data pages selectable
per channel, covering Base EPS / ANC / PDC / STDR. Another
never-explored observability surface.

## What we didn't know before the MDX

1. **`LOCKED` is a named LKA state** (`0xEE42` SF5 = `0x05`) — almost
   certainly the end-state of the 10 s lockout timer.
2. **Three distinct "assist off" points** in the PSCM pipeline (`0xEE02`
   enum: `InputTorquRaw`, `FilteredBCAssistTorque`, `RequestedFinalMotorTorque`)
   — reveals the internal signal chain.
3. **Two ECUs inside the PSCM** (`0xFD01` has ECU1 + ECU2 counters;
   `0x502D` DTC description mentions "High Friction ... ECU2").
4. **Nexteer steering vendor on F-150** (confirmed via DTC NTC
   prefixes); Transit uses TKP Presta.
5. **XCP capability** at `0xEE01` — a whole runtime cal protocol we
   hadn't touched.
6. **HSCAN dev pass-through** at `0xEE40` — internal dev instrumentation.
7. **Research DIDs** (`0xEE41`, `0xEE40`, `0xEED0`) — likely unlock
   additional dev DIDs or relax limits.
8. **SDM 10 Steering Modes** (`0xEE43`) — Sport/Comfort/LowMu/MudRuts/Sand etc.
   affect steering feel, therefore effective override behavior.
9. **`0x205A` Torque Steer Compensation counter** — a writable feature
   with an activation counter. Separate feedback loop for torque-steer
   cancellation, likely operating alongside LKA.
10. **`0x301A` Pull Drift Compensation Value** — auto pull-drift
    compensator, Nm units, res 1/128. Can't override your LKA command
    directly but affects baseline torque the driver feels.
11. **DTC freeze-frame snapshots** capture a standard 19-DID set on
    every steering fault. Reveals Ford's own "what matters when
    something breaks" list.

## Files

- `firmware/F150_2021_Lariat_BlueCruise/diagnostics/DSML34-3F964-AE.mdx` — source
- `analysis/f150/diagnostics/ml34_dids.json` — extracted DID metadata (74 entries)
- `firmware/_other_platforms/diagnostics/DSSZ1C-3F964-AB.MDX` — related but different platform
- `firmware/_other_platforms/diagnostics/sz1c_dids.json` — extracted SZ1C DIDs (106 entries)
