---
title: LCA — Lane Centering
nav_order: 11
---

# LCA / TJA (Lane Centering Assist, Traffic Jam Assist)

Ford ships LCA on the Escape, Bronco Sport, F-150 and others, but disables it on the Transit despite the PSCM being **the same hardware and same firmware platform** as the Escape. This is the hardest feature to unlock.

## Key discovery

`LX6C` PSCM firmware (2022 Escape, VIN `1FMCU9J98NUA09141`) uses the same 65,520-byte calibration layout and same strategy base as the 2025 Transit `LK41-14D007-AH`. Not F-150 — F-150 uses `ML34` / `ML3V`, a different platform. Use the **Escape** as the donor.

## Three things block LCA on Transit

### 1. Missing cal data (fixed)

The Escape cal contains ~4.5 KB of data in 11 regions that the Transit cal leaves as `0xFF` fill. These are pointed to by 12 GP-relative references in LCA code paths. Regions copied from Escape:

| Offset | Purpose (inferred) |
|---|---|
| +0x06C3 | Shared LKA/LCA authority |
| +0x06C8 | Curvature gain lookup |
| +0x0E79 | Heading error PID |
| +0x0E82 | Lateral error PID |
| +0x21BC | Traffic-jam low-speed mode gains |
| +0x2FCE | Lane-change torque envelope |
| +0x327C | Centering hold torque |
| +0x33DD | Curvature rate limits |
| +0x3AD1 | Hand-off detection thresholds |
| +0x41AD | Enable/disable hysteresis |
| +0xFFDC | End-of-cal footer / version |

`firmware/patched/LCA_ENABLED.VBF` contains Transit strategy + timer-zeroed cal + Escape-sourced LCA data. CRC16/CRC32 pass. **Flashed successfully.**

### 2. AS-built configuration reverts

After flashing LCA-capable cal, setting the AS-built bits that enable LCA in the IPMA (`NK3T`) and PSCM modules via FORScan **sticks through ignition-on → ignition-off**, but is **reverted at next power cycle**. This is the current blocker.

Two hypotheses:

- **Strategy-level gate** — code in block0 reads a VIN-tied or vehicle-code-tied identifier and writes AS-built back to default if the vehicle isn't whitelisted.
- **IPMA side check** — `NK3T` firmware might be vetoing.

### 3. Code diffs across Transit revisions

Between revisions `AG → AH → AL → AM` of `KK21-14D003`, code at `0x010E1000` was progressively removed (~80 instructions). We hypothesized this was the LCA handler.

After full disassembly and EP-relative access analysis, **this is not the LCA handler**:
- 80 EP-relative accesses (reads steering sensor & torque state)
- No calibration reads
- No CAN references
- Pure signal processing function, likely a filter or observer

So LCA is not disabled by code removal. It is disabled by cal + AS-built state.

## What to try next

1. **Dump PSCM RAM at boot** (via UDS `0x23 ReadMemoryByAddress`) to catch the moment AS-built is rewritten.
2. **Diff live RAM vs. expected** — find where the "vehicle = Transit" identifier is latched.
3. **Search strategy for VIN-character comparisons** — `LK41` vs `LX6C` substring checks are likely somewhere in block0.
4. **Alternative path:** run openpilot-style external steering controller that sends `0x213 DesTorq` continuously and bypass the PSCM's internal LCA gate entirely. The PSCM still applies torque requested via `0x213` as long as LKA authority is granted (which the LKA patch above does).

## Openpilot angle

For folks coming from openpilot: the PSCM accepts a continuous steering-torque command on CAN ID `0x213` regardless of whether Ford's internal LCA state machine is "on." With the LKA lockout removed (`LKA_NO_LOCKOUT.VBF`), the authority window stays open indefinitely, so an external controller can drive lane-centering without needing Ford's LCA state machine at all. This is the path of least resistance — forget enabling Ford LCA, just drive `0x213` from your own stack.

Relevant openpilot DBC tokens: `DesTorq`, `EPAS_INFO`, `Steering_Pinion_Data`.

## Files

- `firmware/patched/LCA_ENABLED.VBF` — Transit + Escape LCA cal + LKA patch
- `firmware/Escape_2022/LX6C-14D007-ABH` — donor Escape calibration
- `firmware/Transit_2025/LK41-14D007-AH.VBF` — base Transit cal
