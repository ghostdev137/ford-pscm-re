# F-150 LKA System Map

End-to-end map of the Lane Keeping Assist subsystem on the 2021 F-150 PSCM,
integrating firmware RE findings with the diagnostic spec from
`DS-ML34-3F964-AE.mdx` and the newer F-150-family spec `G2354864.mdx`
(106 DIDs, 12 routines, dual-ECU architecture).

Paired reads:
- `analysis/f150/lka_path_findings.md` — strategy-side LKA controller chain
- `analysis/f150/driver_override_findings.md` — override state machine RE
- `analysis/f150/cal_findings.md` — cal parameter classification
- `analysis/f150/emu/README.md` — Unicorn emulation proof of threshold
- `firmware/F150_2021_Lariat_BlueCruise/diagnostics/README.md` — MDX summary

## Architecture at a glance

```
                    HS-CAN (0x730 / 0x738)
                            │
                            ▼
┌───────────────────────────────────────────────────┐
│  PSCM ECU (dual-CPU: SelfSide + RemoteSide)      │
│                                                   │
│  ┌─ CAN RX ──────┐      ┌─ CAN TX ─────┐         │
│  │ 0x3CA LKA cmd │      │ 0x3CC LKA    │         │
│  │ 0x3A8 APA cmd │      │  status fb   │         │
│  │ 0x213 Des trq │      │ 0x61C/0x61D  │         │
│  └──────┬───────┘      │  Dev Data    │         │
│         │              │  Pages 1-15  │         │
│         ▼              └──────────────┘         │
│  FUN_10065b7c                                     │
│  (CAN unpack helper: LaRefAng × 0.05 - 102.4)    │
│         │                                         │
│         ▼                                         │
│  FUN_1017fbe0 (upstream LKA wrapper)              │
│         │                                         │
│         ▼                                         │
│  FUN_101a4d56 (input snapshot → fef21a** ws)     │
│    reads:  fef2197A/7C (proc'd interaction chan)  │
│            fef21a77 (status byte)                 │
│    writes: fef21a6e (angle, clamp ±0x2800)        │
│            fef21a70/72 (chan scaled, clamp 0x6400)│
│         │                                         │
│         ▼                                         │
│  FUN_101a3b84 — OVERRIDE STATE MACHINE ◄─── cal ─┐│
│  Stage 1: quiet gate    (fef263de, fef26382)    ││
│  Stage 2: rate detector (fef26406)              ││
│  Stage 3: banding       (fef263d0/d2)           ││
│  Stage 4: persistence   (fef263da/dc)           ││
│  Stage 5: final state   (fef21a77 == 3 or == 5) ││
│         │                                         ││
│         ▼                                         ││
│  FUN_101a4e4a (writes final fef21a78)            ││
│         │                                         ││
│         ▼                                         ││
│  Motor torque command → rack hardware            ││
│                                                   ││
│  Supporting loops (separate from LKA):            ││
│   - 0x205A Torque Steer Compensation ─────────────┤│
│   - 0x301A Pull Drift Compensation ────────────── ││
└───────────────────────────────────────────────────┘
```

## 1. Signals in

### CAN RX messages (strategy-side)

| CAN ID | DBC name | Direction | Handler | Notes |
|---|---|---|---|---|
| `0x3CA` | `Lane_Assist_Data1` | IPMA → PSCM | `FUN_10065b7c` decode (conf: high), `FUN_1017fbe0` dispatch | Direct LKA steering command. `LaRefAng_No_Req` 12-bit signed × 0.05 mrad/bit - 102.4 → **±5.86° hardware max at wheel**. `LaCurvature_No_Calc` × 5e-6 - 0.01024. |
| `0x3A8` | APA / ParkAid | IPMA → PSCM | archived at `0x0108E02E` | Not in LKA path, shares cal regions |
| `0x213` | `DesiredTorqBrk` | IPMA → PSCM | archived at `0x0108F094` | Desired target torque sideband |

### Local sensor inputs (internal to PSCM)

- Steering shaft torque sensor (driver-input torque) — conditioned upstream, stored at `0xFEF2197A/7C`
- Steering pinion angle sensor
- Motor rotation angle sensor

### Live-readable via UDS `0x22` (default session, no SA)

| DID | Units | Resolution | What it measures | Role in LKA |
|---|---|---|---|---|
| **`0x330C`** | Nm | 1/10 | Steering Shaft Torque Sensor #2 | **Driver input torque** — what the override state machine compares against |
| `0x3020` | Deg | 1/10 (offset −780) | Steering Pinion Angle | Actual wheel position |
| `0x301F` | Deg/s | 4/1 | Steering Pinion Rotation Speed | Angular velocity |
| `0x3B4B` | Deg | 1/10 | Steering Wheel Angle Alignment Offset | Zero-point cal value |
| `0xD118` | Amp | 1/10 | Motor Current | Rack motor draw |
| `0xD117` | — | — | ECU Internal Temperature | Thermal state |
| `0xD111` | — | — | ECU Power Supply Voltage | Supply health |
| `0xDD09` | — | — | Vehicle Speed | Frame of reference for speed gates |
| `0xEE08` | — | — | Compensated SPA Quality Factor (G2354864-only) | Sensor/pinion angle confidence |
| `0xFDB5` | — | — | TSU torque (G2354864-only) | Torque Sensor Unit raw torque |

## 2. Internal processing

### Controller chain (from RE)

| PC | Function | Role | Writes |
|---|---|---|---|
| `0x10065B7C` | LKA CAN unpack | Decodes `0x3CA` into angle + curvature (conf: best-fit) | — |
| `0x1017FBE0` | Upstream LKA wrapper | Task entry before local normalization | — |
| `0x101A4D56` | Input snapshot | Load current angle/chan/status into workspace | `fef21a6e/70/72/77` |
| `0x101A3B84` | **Override state machine** | 5-stage gating (quiet→rate→band→persist→final) | Internal state flags |
| `0x101A4E4A` | Output writer | Commit final assist decision | `fef21a78` |

### RAM workspace (LKA-local, cluster `fef21a**`)

| Address | Role | Writer |
|---|---|---|
| `fef21a6e` | Requested angle (Q10 fixed-pt, ±0x2800 clamp) | `FUN_101a4d56` |
| `fef21a70` | Processed driver-interaction channel A | `FUN_101a4d56` |
| `fef21a72` | Processed driver-interaction channel B | `FUN_101a4d56` |
| `fef21a74/75` | Auxiliary state bytes | `FUN_101a3b84` |
| `fef21a77` | Mode/availability status byte (3=permit, 5=deny) | `FUN_101a4d56` |
| `fef21a78` | Final LKA output | `FUN_101a4e4a` |
| `fef21a64` | **Quiet-gate exit flag (emulator-observable)** | `FUN_101a3b84` |

### RAM threshold family (cluster `fef263**`, cal-mirrored)

| Address | Stock value | Role (proven by Unicorn emulation) |
|---|---|---|
| **`fef263de`** | **0x40** | **Earliest shared channel threshold — quiet gate** |
| `fef263d0` | — | Band low edge |
| `fef263d2` | — | Band high edge |
| `fef263da` | — | Persistence counter 1 |
| `fef263dc` | — | Persistence counter 2 |
| `fef26382` | `0x400` | Angle quiet-gate threshold |
| `fef26405` | — | Rate-detector quiet threshold |
| `fef26406` | — | Rate-detector small-change threshold |

Emulation proof (see `analysis/f150/emu/`): raising `fef263de` from `0x10` → `0x200` linearly shifts the quiet-gate boundary 1:1. This is the primary patch target for "LKA yields on big turns" symptoms.

## 3. Cal parameters (in `ML34-14D007-EDL`, flash base `0x101D0000`)

| Offset | Stock value | Role | Patched variant |
|---|---|---|---|
| `+0x0114` | `10.0 f32` | LKA min-engage speed (m/s) | patch to `0.5` or `0.0` |
| `+0x00C4` | `10.0 f32` | LDW / shared envelope gate (m/s) | match 0x0114 |
| `+0x0120` | `10.0 f32` | LCA min (LEAVE ALONE) | — |
| `+0x0140` | `0.5 f32` | APA min-engage speed | (separate feature) |
| `+0x0144` | `8.0 f32` | APA max-engage speed | `APA_HIGH_SPEED.VBF` raises to 80 |
| `+0x07ADC` | u16 10000 | **LKA arm timer (10 s)** | zero for `LKA_NO_LOCKOUT` |
| `+0x07ADE` | u16 10000 | **LKA re-arm timer (10 s)** | zero |
| `+0x07E64` | u16 10000 | ESA/TJA sibling timer | zero if aggressive |
| `+0x1660` | bell curve [10,19,23,29,31,32,...] | **LKA torque authority profile** | raise peak for more authority |
| `+0x0DA8`/others | monotonic u16 family (4-5 copies) | Authority/rate scheduling | — |
| `+0x080C..+0x0878` | step-threshold family | Low-level gain steps | — |

Strategy-side (in `ML3V-14D003-BD`, flash base `0x10040000`):

| File offset | Role | 
|---|---|
| `0x569D0..0x569D1` | Shared angle scaler (`movhi 0x4480` = 1024.0f). Patch to `0x45C0` = 3072.0f for 3× all-modes angle authority |

## 4. Signals out

### CAN TX

| CAN ID | DBC name | Destination | Contents |
|---|---|---|---|
| `0x3CC` | `Lane_Assist_Data3_FD1` | PSCM → IPMA | Lane-assist availability, deny, `LatCtlLim_D_Stat` (cap-reached flag). Descriptor slot at `0x100416ea`, packer body not yet isolated. Broadcasts every 30 ms. |
| `0x61C` | Dev Data Page A | Configurable diagnostic channel | Enable via DID `0xEE00`. **Page 10 = LKS content** in G2354864 (newer spec). |
| `0x61D` | Dev Data Page B | Configurable diagnostic channel | Second parallel page |

### Live-readable state via UDS

| DID | Meaning | Enum values | Use |
|---|---|---|---|
| **`0xEE07`** | **EPS System State** | 0x00 Init / 0x01 Limited Assist / 0x02 Full Assist / 0x03 Limp Home / 0x04 Limp Aside / 0x05 Ramp Out / 0x06 Assist Off / 0x07 Shutdown / 0x08 Power Down | **Watch for 0x02→0x01 transition = LKA yielded** |
| **`0xEE42`** (10 B) | **Active Features** | each byte: 0x00 PASSIVE / 0x03 ACTIVE / 0x05 LOCKED / 0x99 DONT CARE | SF5 = **LKA Feature State**. 0x05 LOCKED means 10-s timer fired |
| `0xEE42` SF4 | LDW Feature State | same enum | |
| `0xEE42` SF6 | LATCTL (lane centering) State | same enum | |
| `0xEE42` SF7 | TBA (Trailer Backup Assist) | | |
| `0xEE42` SF8 | ESA (Evasive Steering) | | |
| `0xEE42` SF9 | APA | | |
| `0xEE42` SF10 | DSR | | |
| `0xEE02` | Assist ON/OFF | 0x00 off @InputTorq / 0x01 off @FilteredBCAssist / 0x02 off @RequestedFinalMotor / 0xFF on | Reveals 3-stage pipeline |
| `0xEE05` | Final Motor Torque | Nm, res 1/1 | **What LKA is actually commanding** — validates torque-curve patch |
| `0xEE43` | SDM Steering Mode | 10 modes (Normal/Sport/Comfort/LowMu/MudRuts/Sand/...) | Affects steering feel / effective override threshold |
| `0xEE09` | Total EPS Operation Time (G2354864-only) | — | Lifetime hours |
| `0xEE25` | Connected Vehicle: Lock End + High Input Torque Counters (G2354864) | — | **Counts override-like events** |

## 5. Writable configuration (all at `security_level_2`)

### Feature toggles

| DID | Size | Bit-position (SF) | Role |
|---|---|---|---|
| `0xDE01` | 24 B | SF6 | LDW Enabled (0x00 / 0xFF) |
| `0xDE01` | | SF7 | **LKA Enabled** |
| `0xDE01` | | SF8 | TJA Enabled |
| `0xDE01` | | SF9 | LCA Enabled |
| `0xDE01` | | SF11 | ESA Enabled |
| `0xDE01` | | SF12 | HAD Enabled |
| `0xDE02` | 24 B | SF2 | SAPP/APA Enable/Disable |
| `0xDE02` | | SF3 | Active Return |
| `0xDE02` | | SF4 | Software End Stops |
| `0xDE02` | | SF6 | DSR |

**Implication:** features can be toggled without flashing via `0x27 01` seed/key → `0x10 03` extended session → `0x2E DE 01 ...` write.

### Observability unlocks

| DID | Role |
|---|---|
| `0xEE00` | Dev Msg Config — enable EPS Data Pages 1-15 on CAN `0x61C`/`0x61D` (G2354864 adds pages 10-15: **LKS, TBA, ESA, + 3 free**) |
| `0xEE01` | **XCP Enable** — runtime measurement/calibration protocol. 0x00 disabled / 0x01-0x09 enabled with different page selections |
| `0xEE40` | Research Msg Config — HSCAN_In_1..4 + HSCAN_Out_1..4 pass-through signals |
| `0xEE41` | Research Feature Switch (0xFF Enabled) |
| `0xEED0` | Supplier Factory Mode |

### Pipeline control

| DID | Role |
|---|---|
| `0xEE02` | Assist ON/OFF — turn LKA completely off via single UDS write |

## 6. UDS routines (relevant to LKA)

From `DS-ML34-3F964-AE` (2021):

| Routine | Purpose | Session | Security |
|---|---|---|---|
| `0x200F` | Clear Steering Angle Centre Position Calibration | extended | SL2 |
| `0x0301` | Activate Secondary Boot-loader | programming | |
| `0x0304` | Check Valid Application | | |
| `0xFF00` | Flash Erase | programming | SL2 |
| `0xFF01` | Check Programming Dependencies | | |

From `G2354864` (newer F-150 spec, 12 routines):

- `0x200E` Calibrate Steering Angle Centre Position (complement to 0x200F)
- **`0x3054` Clear Power Steering Lockout Counter** — may reset LKA lockout state live without flash!
- `0xDC01` Clear Mechanical Endstop Positions
- `0xF000` Activate ToolBoxLoader
- `0xF001` Reset MinIdleTime
- `0xF002` MDC Clear
- `0x0202` On-Demand Self-Test

## 7. DTCs (steering/LKA-relevant)

| DTC | Description | Nexteer NTC | ECU Action |
|---|---|---|---|
| `0x502D` | High Friction Inside Power Steering | 0x0A2 | Reduced performance |
| `0x5110` | Power Steering Calibration Data | 0x004 (CRC memory fault) | Reduced performance |
| `0x5B00` | Steering Angle Sensor | 0x097 | Remains in normal op; ignores SA value |
| `0x600B` | Steering Shaft Torque Sensor 1 | 0x074 | Reduced performance |
| `0x600C` | Steering Shaft Torque Sensor 2 | 0x078 | Reduced performance |
| `0x600D` | Motor Rotation Angle Sensor | 0x0AD | Reduced performance |
| `0xC126` | Lost Comms With Steering Angle Sensor Module | | |
| `0xC159` | Lost Comms With Parking Assist Module "A" | | |
| `0xC212` | Lost Comms With Steering Column Control Module | | |
| `0xC428` | Invalid Data From Steering Angle Sensor Module | | |
| `0xC45A` | Invalid Data From Parking Assist Module "A" | | |

### Freeze-frame snapshot set

Every steering DTC captures the **same 19 DIDs** at fault time:

```
did_301F did_3020 did_330C did_3B4B did_D111 did_D117 did_D118
did_DD00 did_DD01 did_DD05 did_DD09 did_EE02 did_EE03 did_EE04
did_EE05 did_EE07 did_EE42 did_EE43 did_FD01
```

That's Ford's own "what matters when LKA breaks" list. Use as your on-car measurement baseline.

### Suppressible DTCs (via `0xDE03`, 63 flags)

`0xDE03` is a writable 64-byte field with per-DTC enable/disable bits. If a patched cal trips a specific check, disable just that DTC:
- `U023A-00`, `U023B-00`, `U0252-00` — comms DTCs
- `C200B/C/D-49/62` — steering rack DTCs
- `C102D-00`, `C1B00-49/62`, `C1110-56` — sensor DTCs

## 8. Sessions + security

5 sessions (Ford-standard):
- `session_01` default — most reads allowed
- `session_03` extended — writes + routines
- `session_02` programming
- two more (supplier/dev)

4 security levels:
- `security_level_2` — gates most writable DIDs, most routines
- `security_level_3`, `security_level_4` — programming / supplier-only

**Seed/key algorithm not in the MDX.** F-150 SA not yet extracted (see repo memory `ford_kk21_sa_level_01_algo`). Without it, writable DIDs + most routines are locked. Reads don't require it.

## 9. Dual-ECU architecture

G2354864 reveals Ford's dual-CPU safety architecture via these DID groupings:

- `0xEE1F` CPU idle time A + CPU idle time B (dual subfields)
- `0xFDA0..0xFDA5` SelfSide / RemoteSide Bootloader/SW/TBL versions
- `0xFDAB/0xFDAC` SelfSide/RemoteSide Boot Manager
- `0xFDD0/0xFDD1` SelfSide/RemoteSide MCU ID
- `0xFD01` ECU1 + ECU2 persistence + limp-home counters
- DTC `0x502D` explicitly references "ECU2"

The PSCM runs two independent MCUs (self-side + remote-side) with cross-checking. Override yield / state transitions can originate from either ECU; both must agree for certain actions.

## 10. Connected-vehicle telemetry (G2354864 adds)

These counters run continuously on the vehicle and are retrieved via UDS:

- `0xEE24` Steering Turn Counters
- `0xEE25` **Lock End and High Input Torque Counters** — counts times the driver hit rack endstops or applied high torque (tracks override-like events!)
- `0xEE26` Max Pinion Speed
- `0xEE27` Power Level Counters

Ford uses these for fleet analytics + warranty. For us: `0xEE25` is a **running counter of override events** — comparing stock vs patched readings over a drive quantifies the behavioral change.

## 11. End-to-end validation flow

1. **Read baseline state.** Poll DIDs `0x330C`, `0xEE05`, `0xEE07`, `0xEE42`, `0x3020`, `0xDD09`, `0xEE25` at 10 Hz.
2. **Engage LKA stock.** Drive the known-failing turn.
3. **Observe transitions:**
   - `0xEE07` flips `0x02 → 0x01` (Full → Limited) at override-yield
   - `0xEE42` SF5 flips `0x03 → 0x05` (ACTIVE → LOCKED) at 10-s timer
   - `0x330C` reading at the moment of transition = stock override threshold in Nm
   - `0xEE05` at saturation = stock torque authority ceiling
   - `0xEE25` counter increments on yield
4. **Flash patched VBF** (`LKA_NO_LOCKOUT` + `FULL_AUTHORITY` + `OVERRIDE_2X`).
5. **Re-run the same poll + drive.** Verify:
   - `0xEE42` SF5 stays ACTIVE past 10 s (NO_LOCKOUT working)
   - `0xEE05` now saturates higher (FULL_AUTHORITY working)
   - `0xEE07` stays at `0x02` through the failing turn (OVERRIDE_2X working)
   - `0xEE25` counter grows slower (less override events)

## 12. Still unknown

1. **Which cal byte initializes `fef263de`** at PSCM boot. The F-150 and Transit override thresholds are documented in RAM; the cal source location is inferred only for Transit (`cal+0x29D4 = +0.8 Nm` via pattern match). F-150 cal source not yet pinned.
2. **`0x3CC` TX packer body** — descriptor slot known (`0x100416ea`), code that fills the message not yet isolated.
3. **Engineering units for `_DAT_fef21a70/72`** — processed interaction channels. Relation to raw torque-sensor Nm not fully modeled.
4. **`FUN_10065b7c` mailbox-wrapper proof** — best-fit for `0x3CA` unpack but not the final dispatch-table entry proven.
5. **Security-access seed/key algorithm** — needed to write configurable DIDs (`0xDE01 LKA toggle`, `0xEE01 XCP enable`, etc.) and invoke routines (`0x3054 Clear Lockout Counter`).

## References

- Firmware: `firmware/F150_2021_Lariat_BlueCruise/ML3V-14D003-BD.VBF` (strategy), `ML34-14D007-EDL.VBF` (cal)
- MDX source of truth: `firmware/F150_2021_Lariat_BlueCruise/diagnostics/DSML34-3F964-AE.mdx`
- Newer F-150 PSCM spec: `/tmp/fdrs_extract/strings/G2354864.mdx.txt` (not yet in repo; add if needed)
- Emulation proof: `analysis/f150/emu/f150_threshold_test.py`
- Patched VBFs (tested): `firmware/patched/F150_Lariat_BlueCruise/LKA_LOCKOUT_ONLY.VBF`, `LKA_FULL_UNLOCK.VBF`, `APA_HIGH_SPEED.VBF`
