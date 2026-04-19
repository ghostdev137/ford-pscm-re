---
title: 2025 Transit
parent: Vehicles
nav_order: 1
---

# 2025 Ford Transit — PSCM

**Primary target of this project.** This is the vehicle everything else is compared against.

## Identity

| Field | Value |
|---|---|
| Platform | Transit 2024+ (T-series 4G) |
| PSCM vendor | ThyssenKrupp Presta EPU |
| Platform ID (cal string) | `TKP_INFO:35.13.8.0_FIH` |
| MCU | Renesas **RH850** (V850-family, extended ops) |
| Ford base-part prefix (strategy) | `KK21` |
| Ford base-part prefix (cal) | `LK41` |
| IPMA (camera) prefix | `NK3T` |
| CAN ID (UDS request) | `0x730` |
| CAN ID (UDS response) | `0x738` |
| Bus | MS-CAN |
| Cal flash address | `0x00FD0000` (65,520 bytes, big-endian) |

## Stock feature state

| Feature | State | Why |
|---|---|---|
| LKA (Lane Keep Aid) | Enabled but with 10-s lockout | Timer at cal `+0x06B6 = 0x03E8` |
| LDW (Lane Departure Warning) | Enabled | |
| APA (Active Park Assist) | Enabled, capped ~3.2 kph | Float cap at cal `+0x02E0 = 8.0 kph` |
| LCA / TJA (Lane Centering) | **Disabled** | Missing cal regions + AS-built gated |
| ESA (Evasive Steering) | Unknown | |

## What we've done

- **Flashed `LKA_FULL_AUTHORITY.VBF`.** Cumulative: lockout zeroed + min-speed 3 m/s + torque curve at F-150 BlueCruise level. Drive-confirmed: torque median +184%, engages at 10.7 m/s.
- **Built `LKA_NO_LOCKOUT_APA_HIGH_SPEED.VBF` and `LKA_APA_STANDSTILL.VBF`.** APA caps raised; not yet driven.
- **Flashed `LCA_ENABLED.VBF`.** Cal data persists, AS-built enable bits revert on power cycle — strategy-level gate suspected.

## Related files in this repo

See [per-file-catalog](../per-file-catalog.html#2025-transit-firmwaretransit_2025) for full table. Summary:

- `firmware/Transit_2025/LK41-14D007-AH.VBF` — base cal, patches derived from this.
- `firmware/Transit_2025/KK21-14D003-AG..AM.VBF` — four strategy revisions we diffed.
- `firmware/Transit_2025/KK21-14D005-AB.vbf` — SBL (Secondary Bootloader).
- `firmware/patched/*.VBF` — our modified output.

## Strategy revision history (Transit 2025)

From older to newer, as shipped by Ford:

| Rev | What changed | Notes |
|---|---|---|
| AG | — | Our earliest file. |
| AH | Minor behavioral changes | Diff ~100 bytes. |
| AL | Removed ~40 instructions at `0x010E1000` | Not LCA handler. |
| AM | Removed another ~40 instructions at same site | Pure signal processing, no cal / CAN refs. Purpose unclear. |

## Cross-compatibility with other vehicles

| Source → Target | Compatible? |
|---|---|
| Escape 2022 cal → Transit 2025 cal | ✅ same 65,520 B layout (confirmed; this is why LCA donor works) |
| Escape 2022 strategy → Transit 2025 | ⚠ untested; different strategy PN prefix |
| Transit 2026 (`RK31`) → Transit 2025 | ❌ different platform |
| F-150 2022 → Transit 2025 | ❌ different platform |

## See also

- [LKA patch details](../lka.html)
- [LCA enable attempt](../lca.html)
- [APA speed unlock](../apa.html)
- [Flashing guide](../flashing.html)
