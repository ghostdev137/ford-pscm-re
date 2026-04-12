# Transit — LKA Unlock + APA Standstill-Capable

**File:** `LKA_APA_STANDSTILL.VBF` (66,915 bytes)
**Vehicle:** 2025 Ford Transit
**Base cal:** `LK41-14D007-AH`
**Flash address:** `0x00FD0000`

## Goal

Let APA move the steering wheel from **0 kph** (true standstill), not just from the stock `0.3` kph creep-speed lower end.

## Changes from stock cal

| Region | Cal offset | Stock | Patched | Why |
|---|---|---|---|---|
| LKA timer table | `+0x06B0..0x06C3` | various | all `00` | Kill the 10-s lockout (inherited from LKA_NO_LOCKOUT) |
| **APA X[0] (first speed breakpoint)** | `+0x02C8` | 0.3 kph | **0.0 kph** | Extend lookup to true zero speed |
| **APA Y[0] (authority at X[0])** | `+0x02E4` | 0.10 | **1.00** | Full authority at zero speed |
| **APA Y[1..3]** | `+0x02E8..0x02F0` | 0.25, 0.65, 0.90 | **1.00** | Flatten the ramp — full authority across the range |
| APA X[5] (was 4.6) | `+0x02DC` | 4.6 kph | 50.0 kph | Raise upper breakpoint (from HIGH_SPEED variant) |
| APA X[6] (was 8.0, last) | `+0x02E0` | 8.0 kph | 200.0 kph | Effectively uncap top end |

## Final APA curve

```
speed (kph)    authority
    0.00         1.000
    1.10         1.000
    1.80         1.000
    2.50         1.000
    3.20         1.000
   50.00         1.000
  200.00         1.000
```

Flat 100% authority from 0 through 200 kph. In plain English: whenever APA is commanded (by PAM or via diagnostic activation), the PSCM applies full commanded torque regardless of vehicle speed — including standstill.

## Header

- `file_checksum` = **0xBA9CD48C** (zlib CRC32, recomputed & verified)
- `data_format_identifier` = `0x00` (uncompressed)
- 66,915 bytes — same wrapper as all previous patched files

## What will happen at zero speed

Honest uncertainty: we've patched the cal side of the APA gate. The strategy code **may** have an additional check — something like `if (vehicle_speed < epsilon) return;` — that's hard-coded and not driven by cal values. If that check exists, the wheel still won't move at pure 0 kph despite our cal changes.

Testing at zero speed will answer this in one data point:
- Trigger APA while stopped
- If wheel moves → success, cal was the only gate
- If wheel doesn't move → strategy has an additional hard-coded speed check; we'd need to RE the strategy (block0 `KK21-14D003-AM`) to find and patch it

Either way this patch does NOT brick anything; worst case it behaves like `LKA_NO_LOCKOUT_APA_HIGH_SPEED.VBF` without the standstill capability.

## Safety caveats

- **EPS motor thermal stress at stall.** Moving the rack with zero forward speed means static friction is high and the motor can heat up quickly if you hold full command for long periods. Don't leave APA engaged at standstill for more than a few seconds at a time during testing.
- **Static tire scrubbing** is hard on tires and suspension components. Parking-lot testing only.
- APA at highway speed (now technically permitted by the cal) would be unsafe — but the PAM module won't command large angles without a parking scenario, so it's unlikely to actually engage at road speed.

## Flash procedure

Same as the others — FORScan → PSCM → Module Programming → Load from file → `LKA_APA_STANDSTILL.VBF`. Battery maintainer at 13.5-14.0 V. Clear DTCs after.

## Revert

Flash `firmware/Transit_2025/LK41-14D007-AH.VBF` (stock) to return to original behavior.
