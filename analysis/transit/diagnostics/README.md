# Transit 2025 PSCM Diagnostic Spec

Ford CANdelaStudio diagnostic database for the 2025 Transit Custom 320 LWB
PSCM, extracted from a FDRS VIN-session dump (VIN redacted).

## Source

- **File:** `firmware/Transit_2025/diagnostics/730_PSCM.xml`
- **Vehicle:** 2025 Transit Custom 320 LWB (per FDRS folder name)
- **ECU name:** Power Steering Control Module
- **SHORTNAME:** PSCM
- **UID:** `G2373842`
- **Generated:** 2023-08-23 by Ford ETIS "Colinizer" tool (MDX Generator v6.25, schema `GMRDB_20190121_160058.gdx`)
- **XML schema:** `RuntimeMDX.xsd`, `MDX VERSION=4.0`

## Memory map (confirmed)

| Region | Start | Confirms |
|---|---|---|
| Bootloader | `0x00F9C000` | **NEW** — previously unknown Transit SBL base |
| Calibration | `0x00FD0000` | matches repo RE |
| Strategy | `0x01000000` | matches repo RE |

## UDS services supported

Same set as F-150: `0x10, 0x11, 0x14, 0x19, 0x22, 0x27, 0x2E, 0x31, 0x34, 0x36, 0x37, 0x3E, 0x85`.
**No `0x23 ReadMemoryByAddress`** — same limitation as F-150.

## Sessions (5)

| ID | Name |
|---|---|
| `session_01` | defaultSession |
| `session_02` | programmingSession |
| `session_03` | extendedDiagnosticSession |
| **`session_60`** | **TKPSession** (rack-vendor supplier session) |
| **`session_70`** | **ToolboxLoaderSession** (dev/bringup) |

## Security levels (4)

| ID | Name | Role |
|---|---|---|
| `security_01` | Send Key Level 0x01 | Standard (activate SBL, flash erase) |
| `security_03` | Send Key Level 0x03 | Ford writable DIDs + most routines |
| **`security_61`** | **Send Key Level 0x60** | **TKP Presta (rack vendor) supplier access** |
| `security_71` | Send Key Level 0x70 | Toolbox/dev access |

**Every writable DID accepts either `security_03` OR `security_61`.** Owning the TKP supplier seed/key is an alternate path to write access that bypasses the Ford-standard SA algorithm.

## DIDs — all F-150 key DIDs present with identical numbers

Complete cross-platform validation: every live-readable DID we identified from the F-150 MDX exists on Transit with the same number, same byte size, same units/scaling.

### LKA-relevant DIDs (19 identified in Transit)

| DID | Size | R/W | Units | Role |
|---|---|---|---|---|
| `0x330C` | 1 B | R | **Nm, res 1/10, offset −12.7** | **Steering Shaft Torque Sensor #2** (driver-input torque) |
| `0x3020` | 2 B | R | Deg, offset −780 | Steering Pinion Angle |
| `0x301F` | 1 B | R | Deg/s | Steering Pinion Rotation Speed |
| `0x301A` | 2 B | R | **Nm** | Pull Drift Compensation Value |
| `0x3B4B` | 2 B | R | Deg | Steering wheel angle alignment offset |
| `0xD118` | 2 B | R | Amp | Motor Current |
| `0xEE02` | 1 B | R/W(sec) | enum | Assist On/Off (3-stage: InputTorqRaw / FilteredBCAssist / ReqFinalMotor) |
| `0xEE05` | 2 B | R | **Nm** | **Final Motor Torque** |
| `0xEE07` | 1 B | R | enum | **EPS System State** |
| `0xEE09` | 4 B | R | — | Total EPS Operation Time |
| `0xEE24` | 64 B | R | — | Connected Vehicle: Steering Turn Counters |
| `0xEE25` | 32 B | R | — | **Connected Vehicle: Lock End & High Input Torque Counters** |
| `0xEE26` | 99 B | R | — | Connected Vehicle: Max Pinion Velocity Level Counters |
| `0xEE42` | — | R | — | **Active Features (LKA state byte in SF5)** |
| `0xEE43` | 1 B | R | enum | SDM Steering Mode |
| `0x205A` | 2 B | R/W(sec) | Count | Torque Steer Compensation Activation Counter |
| `0x205B` | 2 B | R/W(sec) | Count | Brake Pull Reduction Activation Counter |
| `0xDE04` | 2 B | R/W(sec) | **Nm** | **Pull Drift Compensation Reset Value** |
| `0xFDB4` | 2 B | R | — | Motor ID |

## Writable configuration DIDs (security_03 or security_61)

| DID | Role |
|---|---|
| `0xDE00` | Vehicle Data |
| `0xDE01` | **Ford In House Software Feature Configuration** (LKA/LDW/TJA/LCA enable bits) |
| `0xDE02` | **Feature Configuration** (APA, Active Return, Soft End Stops) |
| `0xDE03` | Enable/Disable DTCs |
| `0xDE04` | Pull Drift Compensation Reset Value (Nm) |
| `0xEE00` | **Developmental Message Configuration** (broadcast EPS pages 1-n on `0x61C`/`0x61D`) |
| `0xEE01` | **XCP Enable** — runtime measurement/cal protocol |
| `0xEE02` | Assist On/Off |
| `0xC01C` | Freshness Value Message Authentication Failure Threshold |
| `0xC021/23/28` | Security message auth parameters |
| `0x205A/205B` | Compensation activation counters |
| `0x409F` | Unlock Request |
| `0xFD11` | ASW Production Mode Switch (security_61 only) |

## Routines (10 total)

| ID | Name | Security |
|---|---|---|
| `0x020A` | Report All Inhale/Exhale ECU Configuration DIDs | — |
| `0x020B` | Restore Initial ECU Configuration to Not Complete State | 03 + 61 |
| `0x0301` | Activate Secondary Boot-loader | 01 + 61 |
| `0x0304` | Check Valid Application | — |
| `0x200F` | Clear Steering Angle Centre Position Calibration | 03 + 61 |
| **`0x3054`** | **Clear Power Steering Lockout Counter** | **03 + 61** |
| `0xDC01` | Clear Mechanical End Stop Positions | 61 (TKP only) |
| **`0xFEB0`** | **SHE Key Update** — HSM key rotation | 61 (TKP only) |
| `0xFF00` | Flash Erase | 01 + 61 |
| `0xFF01` | Check Programming Dependencies | — |

**`0x3054 Clear Power Steering Lockout Counter` is the standout.** If this routine resets the 10-second LKA lockout timer at runtime without flashing, it's an alternative to the `LKA_NO_LOCKOUT` cal patch — but requires security access.

## DTCs

50 total. Steering-specific DTCs use identical numbers to F-150:
- `0x502D` High Friction Inside Power Steering
- `0x5110` Power steering Calibration Data
- `0x5B00` Steering Angle Sensor
- `0x600B` Steering Shaft Torque Sensor 1
- `0x600C` Steering Shaft Torque Sensor 2
- `0x600D` Motor Rotation Angle Sensor
- Communication-loss DTCs (`0xC126`, `0xC212`, `0xC428`, `0xC45A`)

Rack-vendor prefix: TKP Presta Nexteer-equivalent trouble codes (confirmed by `session_60 TKPSession` + `security_61` convention).

## Implications for Transit LKA RE work

**This completes the on-car measurement plan.** With Transit confirmed to expose every key LKA DID at the same number as F-150, the Panda UDS poller outlined in `analysis/f150/diagnostics/lka_validation_plan.md` works directly on Transit without modification.

Critical validation path:
1. Poll `0x330C` at 10 Hz during a failing turn on Transit
2. At the moment `0xEE07` transitions `0x02 Full → 0x01 Limited`, read the `0x330C` Nm value
3. If that value is ~0.8 Nm → confirms the `cal+0x29D4 ±0.8 Nm` override threshold hypothesis
4. If different → we have the real number, patch accordingly

**Supplier access alternative:** writable DIDs accept `security_61` (TKP) OR `security_03` (Ford). If the TKP supplier key is extractable or already published by third parties, it's an alternate SA path for enabling XCP, writing feature configs, or invoking `0x3054` to clear the lockout counter live.

## Additional modules available in the FDRS dump

Same folder contains MDX for 22 other ECUs on the Transit Custom 320 LWB:

| CAN ID | Module | Possibly useful because... |
|---|---|---|
| `0x706` | IPMA | Sends `0x3CA Lane_Assist_Data1` to PSCM; its side of the LKA handshake |
| `0x716` | GWM | Gateway — bus topology and inter-network routing |
| `0x720` | IPC | Cluster — displays LKA/BlueCruise status messages |
| `0x724` | SCCM | Steering Column Control Module — torque-sensor-adjacent |
| `0x726` | BCM | Body Control — feature config at vehicle level |
| `0x737` | RCM | Restraint Control — seatbelt/hands-on-wheel signals |
| `0x760` | ABS | Vehicle speed + lateral-accel feeds |
| `0x7E0` | PCM | Engine — vehicle state for speed-gated features |
| `0x7E4` | BECM | Battery Electronics — power supply context |

IPMA (`0x706`) is the most relevant for LKA command path analysis — it's the sender of `0x3CA Lane_Assist_Data1`.

## Files

- `firmware/Transit_2025/diagnostics/730_PSCM.xml` — source MDX
- `analysis/transit/diagnostics/transit_pscm_dids.json` — 106 DIDs extracted
- `firmware/F150_2021_Lariat_BlueCruise/diagnostics/` — F-150 counterpart
