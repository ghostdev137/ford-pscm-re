---
title: LKA — Lane Keep Aid
nav_order: 10
parent: 2025 Transit
grand_parent: Vehicles
---

# LKA (Lane Keeping Aid) on the Transit PSCM

## What Ford ships

LKA is enabled on the 2025 Transit but has two artificial limits baked into the calibration:

1. **10-second lockout** — after each LKA intervention, PSCM refuses to apply torque for 10 s.
2. **Weak torque authority** — max ~1.0 Nm at 70 kph, which produces a "one tug then done" feel.
3. **~36 kph minimum-speed floor** — LKA does not actuate below ~10 m/s.

All three live in the cal partition and are patchable without touching strategy code.

## Patches available (see `docs/vbf-patches.md` for details)

| Patch | File | Status |
|---|---|---|
| Lockout removal only | `LKA_NO_LOCKOUT.VBF` | Flashed, confirmed |
| Lockout + min-speed 3 m/s | `LKA_NO_LOCKOUT_MIN_3.VBF` | Flashed, confirmed (engages at 10.7 m/s) |
| Lockout + min-speed + full authority | `LKA_FULL_AUTHORITY.VBF` | **Flashed, drive-confirmed** |

**`LKA_FULL_AUTHORITY.VBF` is the recommended patch.** It is cumulative (includes lockout removal and min-speed fix) plus the torque raise. Column torque median: 0.44 Nm → 1.25 Nm (+184%).

## Calibration fields changed

| Cal offset | Field | Stock | Best current patch |
|---|---|---|---|
| `+0x03C4..+0x03E3` | LKA torque curve (8 BE float32 Nm) | `[0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 7.0]` | `[0, 0.7, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]` |
| `+0x0690` | LKA min-speed (BE float32 m/s) | 10.0 m/s | 3.0 m/s |
| `+0x06B0..+0x06C2` | Lockout timer cluster (10 × u16 BE × 10 ms) | `[0, 100, 0, 1000, 2000, 1000, 500, 400, 5, 255]` | all zero |

The torque curve at `+0x03C4` is confirmed as the active LKA authority lookup by cross-vehicle analysis: Transit `+0x03C4` = Escape `+0x06BC` byte-for-byte on stock firmware. No other Transit torque table matches any Escape table.

The plain-language read of that cluster is: short qualify terms + main 10-second lockout at `+0x06B6` + re-arm / recovery / watchdog terms around it. Zeroing the whole cluster removes the full Transit lockout supervisor, not just the one 10-second entry.

## Verify the patch via UDS

```
# Read LKA torque curve (32 bytes at cal+0x03C4)
req  0x730  10 12 23 44 00 FD 03 C4 00 20
resp 0x738  63 <32 bytes>
# Decode as 8 × BE float32: should show [0, 0.7, 1.5, 2.5, ...]

# Read lockout timer table (20 bytes at cal+0x06B0)
req  0x730  10 0A 23 44 00 FD 06 B0 00 14
resp 0x738  63 <20 bytes = all zeros if patch is live>

# Read min-speed (4 bytes at cal+0x0690)
req  0x730  05 23 44 00 FD 06 90 00 04
resp 0x738  63 40 40 00 00  (= 3.0 m/s in BE float32)
```

## Remaining limits after LKA_FULL_AUTHORITY

- **Driver-override threshold (~0.7–1.5 Nm)** — PSCM cuts out when driver applies light torque. This is enforced in strategy, not cal, and has not been located.
- **Angle clip ±5.86°** — `LaRefAng_No_Req` in the `0x3CA` CAN message is a 12-bit signed field with scale 0.05°/LSB. This is a DBC-level constraint, not a PSCM firmware clamp. Going beyond it requires the LCA path (`0x3D3 LateralMotionControl`, `LatCtl_D_Rq=1`).
- **LCA itself still blocked** — see [LCA](lca.html) and the [Transit LCA hunt](lca-hunt.html).

## Firmware-side reference

The torque arbitration chain (manual driver torque + APA angle → Q15 scaling → TAUB MMIO output) is mapped in [Transit torque arbitration map](arbitration-map.html). The Transit-side angle scaler lives at `FUN_010babf2` — `mulhi 0x67c2` @ `0x010babf8` is a 2-byte patch site for amplifying commanded LKA angle beyond the `LaRefAng_No_Req` DBC ceiling.

## Risks

- Without the lockout, repeated LKA tugs can fight cornering. The camera still limits commanded torque via `0x213 DesTorq`, so sudden hard inputs are not expected.
- Ford TSBs describe the 10-s lockout as "operator alertness strategy." Removing it is out-of-spec.
- EPS core (inner motor loop) safety limits are independent and remain active regardless of any cal patch.
