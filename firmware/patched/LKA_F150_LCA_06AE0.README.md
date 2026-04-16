# Transit — F-150 LCA / BlueCruise LKA Reference Curve (+0x06AE = 0)

**File:** `LKA_F150_LCA_06AE0.VBF` (66,913 bytes)  
**Vehicle:** 2025 Ford Transit  
**Base cal:** `LK41-14D007-AH`  
**Flash address:** `0x00FD0000`  
**Built on:** `LKA_TORQUE2X_06AE0.VBF` (cleaned active-table patch, no shifted writes)  
**file_checksum:** `0x3DA76C9F`
**block CRC16:** `0x42E7`

## Goal

Keep the same cleaned Transit patch stack:

1. `+0x0690 = 3.0 m/s`
2. `+0x06AE = 0`
3. `+0x06B0..+0x06C2 = 0`
4. inherited APA standstill / high-speed changes

But replace the active LKA torque curve with the F-150 LCA / BlueCruise-style envelope already documented in this repo:

`[0.0, 0.7, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]`

This is the same curve described in [LKA_FULL_AUTHORITY.README.md](/Users/rossfisher/ford-pscm-re/firmware/patched/LKA_FULL_AUTHORITY.README.md) as the Transit patch intended to match the F-150 production lane-centering envelope.

This file now also includes the `MIN_3` speed-floor change, so the engage floor is reduced from stock `10.0 m/s` to `3.0 m/s`.

## Changes from Stock

| Region | Cal offset | Stock | This file | Why |
|---|---|---|---|---|
| Active LKA torque table | `+0x03C4..+0x03E0` | `[0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 7.0]` | **`[0, 0.7, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]`** | Match the repo's F-150 LCA / BlueCruise reference envelope |
| Companion shaping table | `+0x03E4..+0x0400` | `[0.8, 0.8, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0]` | unchanged | Clean table layout preserved |
| Speed axis | `+0x0404..+0x0420` | `[0, 10, 30, 50, 70, 90, 130, 250]` | unchanged | Clean table layout preserved |
| LKA min-speed float | `+0x0690` | `10.0 m/s` | **`3.0 m/s`** | Include the `MIN_3` engage-floor tweak |
| Supervisor settle const | `+0x06AE` | `1500` | **`0`** | Keep the adjacent settle / hysteresis term removed |
| LKA lockout table | `+0x06B0..+0x06C2` | `[0, 100, 0, 1000, 2000, 1000, 500, 400, 5, 255]` | all `0` | Keep the known 10-second lockout supervisor removed |
| Boundary word | `+0x06C4..+0x06C7` | `FF 01 FF 02` | unchanged | Left alone |
| Former stray write | `+0x06D6` | `FFFF` | unchanged (`FFFF`) | Restored to stock in the cleaned base |

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
this file   0.0   0.7   1.5   2.5   3.5   4.5   5.5   6.5
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

## What This Means

- Compared to stock Transit, this gives much more mid-speed authority where the van actually drives.
- Compared to the `2x` patch, this is stronger through the 10-130 kph bins but avoids the silly `14.0 Nm` top bin.
- It is meant to approximate the F-150 BlueCruise / LCA feel, not blindly multiply every Transit stock value.

Real bins:

```text
10 kph   0.7 Nm
30 kph   1.5 Nm
50 kph   2.5 Nm
70 kph   3.5 Nm
90 kph   4.5 Nm
130 kph  5.5 Nm
```

## Every Tweak In Plain Language

1. `+0x03C4..+0x03E0`
   Changes the real active LKA torque curve to the repo's F-150 reference envelope.

2. `+0x0690: 10.0 m/s -> 3.0 m/s`
   Lowers the stock LKA minimum-speed floor so the system can engage much earlier.

3. `+0x06AE: 1500 -> 0`
   Keeps the adjacent settle / hysteresis constant removed.
   Best current guess: this changes how the PSCM decides the supervisor state has fully started or fully cleared.

4. `+0x06B0..+0x06C2 -> all 0`
   Keeps the known LKA lockout supervisor removed, including the proven 10-second entry at `+0x06B6`.

5. `+0x06C4..+0x06C7 = FF 01 FF 02`
   Unchanged boundary / sentinel word after the timer cluster.

6. APA standstill / high-speed changes remain inherited from `LKA_APA_STANDSTILL.VBF`.

## Verification

Final artifact state:

```text
+0x03C4..+0x03E0 = [0.0, 0.7, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
+0x03E4..+0x0400 = stock
+0x0404..+0x0420 = stock
+0x0690 = 3.0 m/s
+0x06AE = 0000
+0x06B0..+0x06C2 = 0000
+0x06C4..+0x06C7 = FF01FF02
+0x06D6 = FFFF
```

## Expected Behavior

- Stronger lane-centering than the `2x` patch in the real driving bins.
- Closer to the F-150 production lane-centering envelope already used as the repo's best Transit cross-platform reference.
- Still bounded by downstream EPS core clips, driver override logic, and other untouched strategy limits.
