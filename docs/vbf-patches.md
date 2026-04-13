---
title: VBF Patches
nav_order: 13
---

# VBF Patches — What Changed, Why, How to Flash

All patched VBFs target the Transit 2025 PSCM cal at `0x00FD0000` (base cal `LK41-14D007-AH`). Verify your cal PN via UDS before flashing (`DID F10A`). Do not flash files built against `AH` to a different revision without rederiving the patch.

Flash via FORScan → Service → Module Programming → PSCM → Load from file. Battery maintainer at 13.5–14.0 V. Clear DTCs after.

## Transit patched files (`firmware/patched/`)

### `LKA_FULL_AUTHORITY.VBF` — **current recommended patch**

Cumulative patch including everything below plus the torque authority raise.

| Cal offset | Stock | Patched | Effect |
|---|---|---|---|
| `+0x0690` | `41 20 00 00` (10.0 m/s) | `40 40 00 00` (3.0 m/s) | LKA min-speed floor from 36 kph → 11 kph |
| `+0x06B0..+0x06C3` | timer table | all `00` | Lockout timer zeroed |
| **`+0x03C4..+0x03E3`** | `[0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 7.0]` Nm | **`[0, 0.7, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]`** Nm | Torque authority raised to F-150 BlueCruise envelope |

**Status: flashed and drive-confirmed.** Column torque median 0.44 Nm → 1.25 Nm (+184%).

Rationale for torque values: `+0x03C4` is confirmed as the active LKA authority curve by cross-vehicle byte comparison (Transit `+0x03C4` = Escape `+0x06BC` stock values, byte-for-byte; no other Transit table matches any Escape table). Peak 6.5 Nm is below F-150 BlueCruise production peak (6.25 Nm) — within Ford's own validated envelope.

Verify after flash:
```
req  0x730  10 12 23 44 00 FD 03 C4 00 20
resp 0x738  63 <32 bytes — decode as 8 BE float32>
# Expect: [0, 0.7, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
```

---

### `LKA_NO_LOCKOUT.VBF` — minimal lockout removal only

| Cal offset | Stock | Patched |
|---|---|---|
| `+0x06B0..+0x06C2` | lockout timers | all `00` |

Status: flashed, working. Removes the 10-second steering dropout after each LKA intervention. No torque raise, no min-speed change. Lowest-risk patch; good starting point.

---

### `LKA_NO_LOCKOUT_APA_HIGH_SPEED.VBF` — lockout + APA speed raise

| Cal offset | Stock | Patched |
|---|---|---|
| `+0x06B0..+0x06C2` | lockout timers | all `00` |
| `+0x02DC` | 4.6 kph | 50.0 kph |
| `+0x02E0` | 8.0 kph | 200.0 kph |

Status: ready. APA will engage above stock ~3 kph cap. Test first at 10–15 mph in an empty lot. The PAM won't command large steering angles at highway speeds.

---

### `LKA_APA_STANDSTILL.VBF` — lockout + APA from true standstill

| Cal offset | Stock | Patched |
|---|---|---|
| `+0x06B0..+0x06C3` | lockout timers | all `00` |
| `+0x02C8` | 0.3 kph | 0.0 kph (APA X[0]) |
| `+0x02E4..+0x02F0` | ramp authority | 1.0 (flat) |
| `+0x02DC` | 4.6 kph | 50.0 kph |
| `+0x02E0` | 8.0 kph | 200.0 kph |

Status: ready. Honest caveat: strategy code may have a separate hard-coded zero-speed check that the cal patch can't reach. If the wheel still doesn't move at standstill after this patch, static strategy RE is needed.

---

### `LCA_ENABLED.VBF` — LCA cal data from Escape

Copies ~4,460 bytes of LCA-specific cal from Escape `LX6C-14D007-ABH` into the 11 Transit cal regions that are otherwise 0xFF fill, plus zeros the LKA lockout timer table.

Status: flashed, cal data persists across ignition cycles, but AS-built enable bits revert on power cycle. A strategy-level gate (likely a VIN or vehicle-code check in block0) vetoes the enable. Not harmful to leave flashed — just doesn't enable LCA yet.

---

## Safety notes

- **Driver override remains active** — pushing against the wheel still disengages motor assist regardless of patch.
- **Min-speed floor is NOT zero** — stock floor ~36 kph; the MIN_3 patch lowers to ~11 kph. LKA does not engage at parking speeds.
- **EPS core safety limits independent** — motor overcurrent, rate, and thermal protections in block0's inner loop are not touched by any cal patch.
- **F-150 BlueCruise peak is the ceiling** — 6.5 Nm peak (Transit LKA_FULL_AUTHORITY) is below 6.25 Nm (F-150 BlueCruise). Escape LCA uses 11.9 Nm peak for its smaller vehicle; we do not go that high.

## Reverting to stock

Flash `firmware/Transit_2025/LK41-14D007-AH.VBF` via FORScan. Keep this file on your laptop before starting.

## F-150 patches (`firmware/patched/F150_Lariat_BlueCruise/`)

Six VBFs for the 2021 F-150 Lariat BlueCruise (`ML34-14D007-EDL`). Cal is little-endian, lives at `0x101D0000`.

| File | Changes |
|---|---|
| `LKA_LOCKOUT_ONLY.VBF` | `cal+0x07ADC/ADE` → 0 (LKA arm + re-arm timers) |
| `LKA_FULL_UNLOCK.VBF` | + `cal+0x0114` 10.0→0.0 m/s (LKA min-speed) |
| `LKA_AGGRESSIVE.VBF` | + `cal+0x07E64` → 0 (third related timer) |
| `APA_HIGH_SPEED.VBF` | `cal+0x0144` 8.0→80.0 (APA max) |
| `APA_UNLOCK.VBF` | `cal+0x0140` 0.5→0.0 (APA min) + max→200.0 |
| `LKA_AND_APA_UNLOCK.VBF` | LKA lockout (2 timers) + LKA min-speed + APA max |

**Status: not yet flashed.** SBL RE confirmed no crypto verification of cal (see `analysis/f150/verdict.md`). Unknown risk: mask ROM boot behavior. Test on a donor/bench module first. Try `LKA_LOCKOUT_ONLY.VBF` first — narrowest change.

Use `tools/vbf_patch_f150.py` to produce custom F-150 patches.
