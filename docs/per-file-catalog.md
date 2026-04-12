---
title: Per-File VBF Catalog
nav_order: 5
---

# Per-File VBF Catalog

Every VBF in this repo, what it is, which block/partition it delivers, and which vehicle it's for.

**Ford PN naming convention:**
```
KK21  -  14D003  -  AG
│         │         │
│         │         └── software revision (AA, AB, ... AG, AH, ... )
│         └──────────── part function code (see table below)
└────────────────────── Ford base-part number, tied to vehicle platform
```

## Part function codes

| Suffix | What it is | Block/partition |
|---|---|---|
| `-14D003-*` | PSCM strategy (application code) | block0 + block1 |
| `-14D004-*` | PSCM supplementary / MPU config | varies |
| `-14D005-*` | PSCM EPS core (low-level motor) | block2 |
| `-14D007-*` | PSCM calibration | cal partition at `0x00FD0000` |
| `-14F397-*` / `-14F398-*` / `-14F399-*` | IPMA camera firmware (not PSCM) | IPMA internal |
| `-14H102-*` / `-14H103-*` etc. | APIM / SYNC firmware (not PSCM) | — |

## 2025 Transit (`firmware/Transit_2025/`)

This is our primary target. PSCM split across three platforms for this model year: `KK21` strategy, `KK21` EPS core, `LK41` cal.

| File | Role | Block → flashes to | Revision notes |
|---|---|---|---|
| `KK21-14D003-AG.VBF` | Strategy | block0 → `~0x00F00000` | Earliest rev in our set. Code at `0x010E1000` intact. |
| `KK21-14D003-AH.VBF` | Strategy | block0 | Minor diff from AG. |
| `KK21-14D003-AL.VBF` | Strategy | block0 | Removed ~40 instructions at `0x010E1000`. |
| `KK21-14D003-AM.VBF` | Strategy | block0 | Removed another ~40 instructions. **Not** the LCA handler (verified). |
| `KK21-14D003-AM_LCA_ENABLED.VBF` | Strategy (my experiment) | block0 | AM strategy + speculative LCA code patches — did not work. |
| `KK21-14D005-AB.vbf` | EPS core | block2 (separate partition) | Motor control + safety. We do not modify. |
| `LK41-14D007-AD.VBF` | Calibration | cal → `0x00FD0000` (65,520 B) | Early cal. |
| `LK41-14D007-AF.VBF` | Calibration | cal | Intermediate cal. |
| `LK41-14D007-AH.VBF` | Calibration | cal | **Current production cal. Base for all our patches.** |
| `1FTBF8XG0SKA96907.ab` | Dealer manifest | (not flashed) | VIN-specific FDRS manifest — lists files dealer would flash. |

## 2026 Transit (`firmware/Transit_2026/`)

**Different platform** — new PN prefix `RK31`. Memory map not yet verified. Our patches do **not** work here without redoing the RE from scratch.

| File | Role | Block | Notes |
|---|---|---|---|
| `RK31-14D003-PB` | Strategy | block0 | New platform. |
| `RK31-14D004-PB` | Supplementary | varies | Purpose unconfirmed. |
| `RK31-14D005-PA` | EPS core | block2 | Likely redesigned motor driver. |
| `RK31-14D007-RAC` | Calibration | cal | Cal format may have changed. |

See [vehicles/transit-2026](vehicles/transit-2026.html).

## 2022 Escape (`firmware/Escape_2022/`)

**Same PSCM platform as 2025 Transit.** Same 65,520-byte cal layout. Ships with LCA enabled. Source of LCA data copied into our `LCA_ENABLED.VBF`. Donor VIN: `1FMCU9J98NUA09141`.

| File | Role | Block | Notes |
|---|---|---|---|
| `LX6C-14D003-AL` | Strategy | block0 | Escape strategy — **different** from Transit strategy. Contains LCA code paths. |
| `LX6C-14D005-AB` | EPS core | block2 | Likely same HW, same code as Transit. |
| `LX6C-14D007-ABH` | Calibration | cal | **LCA cal donor.** Regions `+0x06C3..0xFFDC` copied to our patched file. |

See [vehicles/escape-2022](vehicles/escape-2022.html).

## 2024 Escape (`firmware/Escape_2024/`)

Newer Escape revision. Prefix `PZ11`. Same family as LX6C but with updates.

| File | Role | Block | Notes |
|---|---|---|---|
| `PZ11-14D003-FB` | Strategy | block0 | Newer Escape strategy. |
| `PZ11-14D004-FAB` | Supplementary | varies | |
| `PZ11-14D005-AA` | EPS core | block2 | |
| `PZ11-14D005-AB` | EPS core | block2 | Later revision. |
| `PZ11-14D007-EBC` | Calibration | cal | Newer cal — may have revised layout vs LX6C. |

See [vehicles/escape-2024](vehicles/escape-2024.html).

## 2022 F-150 (`firmware/F150_2022/`)

**Different platform entirely.** PN prefixes `ML34` / `ML3V`. Cal layout does **not** match Transit. Included in the repo for architectural comparison only — do **not** try to cross-flash.

| File | Role | Block | Notes |
|---|---|---|---|
| `ML34-14D004-BP` | Supplementary | varies | |
| `ML34-14D005-AB` | EPS core | block2 | Different motor driver. |
| `ML34-14D007-BDL` | Calibration | cal | **Different layout** — offsets do not align with Transit. |
| `ML3T-14H106-EFE` | APIM (SYNC) | — | Not PSCM. Included by accident; ignore. |
| `ML3T-14H310-EDD` | APIM | — | Not PSCM. Ignore. |
| `ML3V-14D003-BD` | Strategy | block0 | F-150 strategy. |

See [vehicles/f150-2022](vehicles/f150-2022.html).

## Patched output (`firmware/patched/`)

What we produced from the stock VBFs above.

| File | Base | Changes | Status |
|---|---|---|---|
| `LKA_NO_LOCKOUT.VBF` | `LK41-14D007-AH` (Transit cal) | Zeroed timer table at `+0x06B0..06C2` (13 bytes) | **Flashed, works** |
| `APA_HIGH_SPEED.VBF` | `LK41-14D007-AH` | APA speed floats at `+0x02DC` / `+0x02E0` → 50 / 200 kph | Ready |
| `LCA_ENABLED.VBF` | `LK41-14D007-AH` | Timer zeroed + 4,460 B of LCA data copied from Escape `LX6C-14D007-ABH` | Flashed; AS-built reverts |
| `cal_APA_HIGH_SPEED.VBF` | — | Same as APA but cal-only intermediate | |
| `cal_*.bin` | — | Raw decompressed cal blobs for diffing | Reference only |

## Quick rules

- **Patching cal** (`-14D007-*`) → safe-ish, small changes, minimal brick risk.
- **Patching strategy** (`-14D003-*`) → higher risk; touches execution paths.
- **Never touch EPS core** (`-14D005-*`) → safety-critical motor control.
- **Cross-vehicle:** only Escape ↔ Transit PSCM has been confirmed as memory-layout-compatible (for cal). Everything else is unconfirmed; assume incompatible.
