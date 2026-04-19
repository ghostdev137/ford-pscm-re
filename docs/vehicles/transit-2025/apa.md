---
title: APA — Active Park Assist
nav_order: 12
parent: 2025 Transit
grand_parent: Vehicles
---

# APA (Active Park Assist) Speed Unlock

## Ford's limit

APA is enabled on the Transit but will only steer the vehicle during parking at very low speeds — the PSCM accepts APA torque commands only below ~3.2 kph. This is enforced by a speed comparison against float values in the cal.

## Cal table location

```
cal base    = 0x00FD0000
APA table   = cal + 0x02C4 .. cal + 0x02E0
encoding    = IEEE-754 big-endian float32
units       = kph
```

Observed values:

| Offset | Stock (BE hex) | Decoded | Patched |
|---|---|---|---|
| +0x02DC | `40 93 33 33` | 4.6 kph | `42 48 00 00` (50.0 kph) |
| +0x02E0 | `41 00 00 00` | 8.0 kph | `43 48 00 00` (200.0 kph) |

The 4.6 appears to be the low-speed reference, 8.0 the high-speed cutoff. Both are checked; both must be raised.

## Patch

`firmware/patched/APA_HIGH_SPEED.VBF` — APA speed floats replaced with 50 / 200. Timer table left alone. **Ready to flash, not yet driven.**

## CAN messages involved

| CAN ID | Name | Direction | Purpose |
|---|---|---|---|
| `0x3A8` | APA | PAM → PSCM | Desired steering angle during parking maneuver |
| `0x415` | BrkSpeed | ABS → PSCM | Wheel speed reference used in the comparator |
| `0x082` | EPAS_INFO | PSCM → bus | Returns APA active / not-active status |

Confirming the patch: while APA is engaged, compare `0x415` wheel-speed to `0x082`-reported APA state. Above 3.2 kph stock, APA should drop out. Post-patch, APA should stay engaged up to whatever cap you set.

## Caveats

- APA geometry math is tuned for parking-lot maneuvers. At high speed, large commanded steering angles from the PAM could be dangerous. Start with a modest cap (e.g. 15 kph) if you are not sure what the PAM will request.
- The Transit PAM is `L1BT` / `H1BT`. It is unlikely to command large steering at highway speeds (it can't see lanes), but the cap is still worth testing with a human hand on the wheel.
- APA is **not** the same as openpilot lateral control. If your goal is highway lateral control, see [lca.html](lca.html) — drive `0x213 DesTorq` directly.

## Verification via UDS

```
# Dump 32 bytes of APA table
req  0x730  10 0E 23 44 00 FD 02 C4 00 20
resp 0x738  63 <32 bytes float BE>
```

Decode:

```python
import struct
data = bytes.fromhex("...")  # 32 bytes
for i in range(0, 32, 4):
    print(f"+0x{0x02C4+i:04X}: {struct.unpack_from('>f', data, i)[0]:.2f} kph")
```

See `tools/pscm_test32.py` for the full UDS harness (32-bit Python + TOPDON RLink FDRS DLL).
