# Transit — 2x Active LKA Torque + Supervisor Settle Zero (+0x06AE)

**File:** `LKA_TORQUE25_06AE0.VBF` (66,915 bytes)
**Vehicle:** 2025 Ford Transit
**Base cal:** `LK41-14D007-AH`
**Flash address:** `0x00FD0000`
**Built on:** `LKA_APA_STANDSTILL.VBF` (lockout-zeroed + APA standstill)
**file_checksum:** `0xCF1A7818`

## Goal

This file now does two intentional LKA-side things on top of `LKA_APA_STANDSTILL`:

1. **Set the confirmed active LKA torque table to 2x stock** at `+0x03C4..+0x03E0`.
2. **Zero `+0x06AE`** (the 1500 supervisor settle/hysteresis constant adjacent to the lockout block).

The earlier accidental shifted `25.0` write is gone. The companion table and speed axis are back to stock.

## Changes from Stock

| Region | Cal offset | Stock | This file | Why |
|---|---|---|---|---|
| Active LKA torque table | `+0x03C4..+0x03E0` | `[0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 7.0]` | **`[0, 0.4, 0.8, 1.4, 2.0, 3.0, 4.0, 14.0]`** | Clean 2x test of the confirmed active LKA curve |
| Companion shaping table | `+0x03E4..+0x0400` | `[0.8, 0.8, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0]` | unchanged | Restored to stock |
| Speed axis | `+0x0404..+0x0420` | `[0, 10, 30, 50, 70, 90, 130, 250]` | unchanged | Restored to stock |
| Supervisor settle const | `+0x06AE` | `1500` | **`0`** | Remove adjacent settle / hysteresis term |
| LKA lockout table | `+0x06B0..+0x06C2` | `[0, 100, 0, 1000, 2000, 1000, 500, 400, 5, 255]` | all `0` | Remove known 10-second lockout supervisor |
| `FF01 FF02` boundary | `+0x06C4..+0x06C6` | `FF01 FF02` | unchanged | Left alone |
| Stray shifted write | `+0x06D6` | `FFFF` | unchanged (`FFFF`) | Restored to stock |

## Inherited APA Changes

| Region | Cal offset | Stock | This file |
|---|---|---|---|
| APA speed axis | `+0x02C4..+0x02E0` | `[0.0, 0.3, 1.1, 1.8, 2.5, 3.2, 4.6, 8.0]` | `[0.0, 0.0, 1.1, 1.8, 2.5, 3.2, 50.0, 200.0]` |
| APA output table | `+0x02E4..+0x02F0` | `[0.1, 0.25, 0.65, 0.9]` | `[1.0, 1.0, 1.0, 1.0]` |

## LKA Table Layout

```text
+0x03C4 .. +0x03E0   confirmed active LKA torque table
+0x03E4 .. +0x0400   companion shaping table
+0x0404 .. +0x0420   speed axis
```

Active LKA torque table:

```text
speed       0     10    30    50    70    90    130   250
stock       0.0   0.2   0.4   0.7   1.0   1.5   2.0   7.0
this file   0.0   0.4   0.8   1.4   2.0   3.0   4.0   14.0
```

Companion shaping table:

```text
speed       0     10    30    50    70    90    130   250
table       0.8   0.8   0.9   1.0   1.0   1.0   1.0   1.0
```

Speed axis:

```text
+0x0404..+0x0420 = [0.0, 10.0, 30.0, 50.0, 70.0, 90.0, 130.0, 250.0]
```

## Every Tweak In Plain Language

1. `+0x03C4..+0x03E0` doubles the real active LKA torque curve.
   This is the main steering-authority change.

2. `+0x06AE: 1500 -> 0`
   Removes a helper settle / hysteresis constant next to the lockout block.
   Best current guess: it changes how the PSCM decides the lockout state has fully started or fully cleared.

3. `+0x06B0..+0x06C2 -> all 0`
   Removes the known LKA lockout supervisor, including the proven 10-second entry at `+0x06B6`.

4. `+0x06C4..+0x06C6 = FF01 FF02`
   Unchanged. Those bytes are not part of the zeroed lockout block.

5. APA standstill/high-speed changes remain inherited from `LKA_APA_STANDSTILL.VBF`.

## Verification

Final artifact state:

```text
+0x03C4..+0x03E0 = [0.0, 0.4, 0.8, 1.4, 2.0, 3.0, 4.0, 14.0]
+0x03E4..+0x0400 = stock
+0x0404..+0x0420 = stock
+0x06AE = 0000
+0x06B0..+0x06C2 = 0000
+0x06C4..+0x06C6 = FF01 FF02
+0x06D6 = FFFF
```

## Risks

- This is still more aggressive than stock.
- EPS-core clips, driver override, and other downstream safety checks remain active.
- `+0x06AE = 0` is still not fully proven in firmware; it remains an informed experiment.

## Expected Outcomes

| Outcome | Interpretation |
|---|---|
| Wheel torque feels stronger | The active LKA torque table was a real limiter |
| Wheel torque feels about the same | Downstream clips / gains are still the main limiter |
| ~7s residual suppress changes | `+0x06AE` participates in the remaining supervisor behavior |
| ~7s residual suppress unchanged | The remaining suppress is elsewhere |
