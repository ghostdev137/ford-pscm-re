---
title: Firmware Inventory
nav_order: 23
---

# Firmware Inventory

Everything in `firmware/` organized by vehicle. All files are Ford VBF programming containers. See [vbf-format.html](vbf-format.html).

## 2025 Ford Transit (our target)

Location: `firmware/Transit_2025/`

| File | Type | PN | Notes |
|---|---|---|---|
| `KK21-14D003-AG.VBF` | Strategy | AG | Earliest revision in our set — code at `0x010E1000` intact |
| `KK21-14D003-AH.VBF` | Strategy | AH | Minor diff from AG |
| `KK21-14D003-AL.VBF` | Strategy | AL | Removed ~40 instructions at `0x010E1000` |
| `KK21-14D003-AM.VBF` | Strategy | AM | Removed another ~40 instructions — not LCA handler (see [lca.html](vehicles/transit-2025/lca.html)) |
| `KK21-14D003-AM_LCA_ENABLED.VBF` | Strategy | AM | Our LCA experiment on the AM strategy |
| `KK21-14D005-AB.vbf` | EPS core | AB | Low-level motor control |
| `LK41-14D007-AD.VBF` | Cal | AD | Earlier cal revision |
| `LK41-14D007-AF.VBF` | Cal | AF | |
| `LK41-14D007-AH.VBF` | Cal | AH | **Current production cal** — base for our patches |
| `1FTBF8XG0SKA96907.ab` | VIN-specific | — | Dealer-delivered manifest |

## 2026 Ford Transit (new platform — RK31)

Location: `firmware/Transit_2026/`

| File | Type |
|---|---|
| `RK31-14D003-PB` | Strategy |
| `RK31-14D004-PB` | ? |
| `RK31-14D005-PA` | EPS core |
| `RK31-14D007-RAC` | Cal |

Different prefix (`RK31` vs `KK21`). Memory map not yet verified against Transit 2025 — treat as separate RE effort.

## 2022 Ford Escape (LCA donor)

Location: `firmware/Escape_2022/`

| File | Type | PN |
|---|---|---|
| `LX6C-14D003-AL` | Strategy | AL |
| `LX6C-14D005-AB` | EPS core | AB |
| `LX6C-14D007-ABH` | Cal | ABH |

**Same PSCM platform as Transit.** Same 65,520-byte cal layout. Source of the LCA data copied into `LCA_ENABLED.VBF`. VIN: `1FMCU9J98NUA09141`.

## 2024 Ford Escape (newer revision)

Location: `firmware/Escape_2024/`

| File | Type |
|---|---|
| `PZ11-14D003-FB` | Strategy |
| `PZ11-14D004-FAB` | ? |
| `PZ11-14D005-AA` / `-AB` | EPS core |
| `PZ11-14D007-EBC` | Cal |

## 2022 Ford F-150 (different platform, reference only)

Location: `firmware/F150_2022/`

| File | Type | Notes |
|---|---|---|
| `ML34-14D004-BP` | ? | |
| `ML34-14D005-AB` | EPS core | |
| `ML34-14D007-BDL` | Cal | |
| `ML3T-14H106-EFE` | — | |
| `ML3T-14H310-EDD` | — | |
| `ML3V-14D003-BD` | Strategy | |

**Not cross-compatible with Transit.** Different platform, different cal layout. Included for architectural comparison only.

Excluded from repo: `PJ6T-*`, `RJ6T-*`, `RJ8T-*`, `SL3T-*`, `PL3T-*`, `H1BT-*`, `NK3T-*` — these are IPMA / APIM / PAM firmware, not PSCM, and some are >60 MB. They live in the separate research archive.

## 2021 Ford F-150 Lariat 502A — BlueCruise (`firmware/F150_2021_Lariat_BlueCruise/`)

Donor set from a 2021 F-150 Lariat 502A with BlueCruise. Same `ML34`/`ML3V` PSCM platform as the 2022 F-150 files, newer revisions.

| File | `sw_part_type` | Role | Size |
|---|---|---|---|
| `ML34-14D004-EP.VBF` | `DATA` | Supplementary | 66,332 B |
| `ML34-14D005-AB.VBF` | `SBL` | Secondary Bootloader | 10,583 B |
| `ML34-14D007-EDL.VBF` | `DATA` | Calibration | 197,409 B |
| `ML3V-14D003-BD.VBF` | `EXE` | Strategy | 1,573,660 B |

Cal is little-endian (unlike Transit/Escape big-endian). Full RE complete — see `analysis/f150/`.

## Patched output

Location: `firmware/patched/`

| File | Base | Changes | Status |
|---|---|---|---|
| `LKA_NO_LOCKOUT.VBF` | `LK41-14D007-AH` cal | Timer table `+0x06B0..06C2` → zero | Flashed |
| `LKA_FULL_AUTHORITY.VBF` | `LK41-14D007-AH` cal | Timer + min-speed (3 m/s) + torque curve raised | **Flashed, drive-confirmed** |
| `LKA_NO_LOCKOUT_APA_HIGH_SPEED.VBF` | `LK41-14D007-AH` cal | Timer + APA 50/200 kph | Ready |
| `LKA_APA_STANDSTILL.VBF` | `LK41-14D007-AH` cal | Timer + APA standstill-capable | Ready |
| `LCA_ENABLED.VBF` | `LK41-14D007-AH` cal | Timer + 4,460 B Escape LCA data | Flashed; AS-built reverts |
| `cal_*.bin` | — | Decompressed calibration blobs for diffing | Reference only |
| `F150_Lariat_BlueCruise/*.VBF` | `ML34-14D007-EDL` | 6 variants — LKA lockout, min-speed, APA cap | Built, not yet test-flashed |

## Cross-platform compatibility matrix

| Donor → Target | Strategy | Cal | EPS core |
|---|---|---|---|
| Escape 2022 `LX6C` → Transit 2025 `LK41` | ⚠ untested (different PN prefix on strategy) | ✅ tested — LCA_ENABLED.VBF | ⚠ untested |
| Escape 2024 `PZ11` → Transit 2025 | ⚠ untested | ⚠ newer cal layout suspected | — |
| F-150 `ML34` → Transit | ❌ different platform | ❌ incompatible | ❌ |
| Transit 2026 `RK31` → Transit 2025 | ❌ different platform | ❌ | ❌ |
