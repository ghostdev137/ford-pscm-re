---
title: Transit LKA authority patches from drive-findings
nav_order: 81
---

# Transit LKA authority patches — derived from real drive data

Responding to [`docs/openpilot-drive-findings.md`](../../docs/openpilot-drive-findings.md). Two drive sessions identified three remaining LKA limits after the 10-sec timer patch was confirmed working:

1. Motor-torque authority cap (PSCM ramps to a ceiling, then stops)
2. Driver-override torque threshold (~0.5–1.5 Nm — cuts on light hand-on-wheel)
3. Low-speed authority floor (~10 m/s / 22 mph hard cut)

## The LKA config block — found

Scanning cal around the known timer table (`+0x06B0..06C3` already zeroed) turned up a structured scalar block **directly preceding the timer table**. Structure matches the F-150 LKA config block (where we already identified `cal+0x0114 = 10.0 m/s` as LKA min-speed):

```
Transit cal+0x0670..0x06B0:
  +0x0670:   0.600     (misc threshold)
  +0x0674:   5.000     (misc)
  +0x0680:   3.000     (misc threshold — possibly angle rate)
  +0x0684:   3.78e-5   (very small rate/gain coefficient)
  +0x0688:   0.500     ← DRIVER OVERRIDE TORQUE (Nm)
  +0x0690:  10.000     ← LKA MIN-ENGAGE SPEED (m/s ≈ 22 mph)   MATCHES drive-floor evidence exactly
  +0x0694: 270.000     (angle limit — likely mrad, ~15°)
  +0x0698:  90.000     (angle limit — likely mrad, ~5.15°, matches DBC ±5.86°)
  +0x069C:   2.000     ← authority multiplier candidate
  +0x06A0:   6.000     ← MOTOR TORQUE CEILING (Nm) candidate
  +0x06A4..06AC: u32 timer constants (200000, 300000, 1500)
  +0x06B0..06C3: zeroed (LKA post-intervention lockout table — already patched)
```

Structural evidence for each assignment:
- `0x0688 = 0.5` is a clean half-Nm scalar adjacent to a very small coefficient (typical gain/threshold pairing). Matches drive-observed override of 0.5-1.5 Nm.
- `0x0690 = 10.0` — exact match with drive finding of cutoff at 10 m/s (4-sample-bin histogram showed 8.36° error at 8-9 m/s collapsing to 1.10° above 10 m/s, a discontinuity not a gradient).
- `0x06A0 = 6.0` — in a region adjacent to ceiling-sounding values (90, 270). 6 Nm is believable as a Ford "nudge" torque maximum; raising this should let the PSCM apply stronger torque before capping.
- `0x069C = 2.0` — possibly an authority scaler.

Angle limits at `0x0694 = 270` and `0x0698 = 90` are likely mrad (15.5° and 5.16° — 90 mrad matches the DBC ±102.3 mrad clip). Patching these doesn't help because the DBC signal encoding caps at 102.3 mrad upstream — must move to LCA path.

## Three patch variants, layered on `LKA_APA_STANDSTILL.VBF`

All three inherit the existing LKA timer zeros + APA curve flattening. Each adds drive-findings fixes on top.

### Variant A — `LKA_SPEED_FLOOR_FIX.VBF` (single change, safest test)

```
cal+0x0690:  41 20 00 00  (10.0 m/s)  →  00 00 00 00  (0.0 m/s)
```

Kills the LKA minimum-speed gate only. If the drive-findings diagnosis is right, LKA should now apply torque at any speed instead of discontinuously cutting below ~10 m/s.

Header CRCs: CRC16 `0x685B`, file_checksum `0x054F57A7`.

### Variant B — `LKA_NO_LOW_GATES.VBF` (two changes)

```
cal+0x0690:  41 20 00 00  (10.0)  →  00 00 00 00  (0.0)      # speed floor
cal+0x0688:  3F 00 00 00  (0.5)   →  40 40 00 00  (3.0)      # override threshold
```

Speed floor + raise override threshold 0.5 → 3.0 Nm (6x). Driver can rest a hand on the wheel without cutting the motor. An actual resistive grab still overrides (drive data showed 2.7 Nm peak driver torque, so 3.0 Nm threshold keeps that responsive).

Header CRCs: CRC16 `0x8362`, file_checksum `0x8A09A8C8`.

### Variant C — `LKA_FULL_AUTHORITY.VBF` (aggressive)

```
cal+0x0690:  41 20 00 00  (10.0)  →  00 00 00 00  (0.0)      # speed floor
cal+0x0688:  3F 00 00 00  (0.5)   →  40 40 00 00  (3.0)      # override threshold
cal+0x06A0:  40 C0 00 00  (6.0)   →  41 F0 00 00  (30.0)     # torque ceiling 5x
cal+0x069C:  40 00 00 00  (2.0)   →  41 20 00 00  (10.0)     # authority multiplier 5x
```

Everything from Variant B, plus raising two candidates suspected to be torque-authority scalars. The 5x raise is aggressive — directly tackles the drive-finding that wheel rate *falls* at larger commands (evidence of internal torque saturation).

Header CRCs: CRC16 `0x5412`, file_checksum `0x3AAE37AD`.

## Suggested flash order

1. **Variant A** first. Narrowest change — confirms that `cal+0x0690` is really the speed floor before touching more scalars. A quick drive with engagements below 20 mph answers it.
2. **Variant B** next. Adds the override-threshold raise. Drive test: casually rest a hand on the wheel during LKA — does it keep holding vs. stock-firmware's immediate cutout?
3. **Variant C** last if Variants A/B behave sanely. This is where things get uncertain — `cal+0x06A0=6.0` and `cal+0x069C=2.0` might not be Nm/multiplier. If the wheel starts yanking, revert.

## What's NOT addressed

- **Angle clip (DBC ±5.86°)** — encoding-bound; cannot be lifted from PSCM cal. Only the LCA path (`LatCtl_D_Rq=1`, curvature-based) gets past this.
- **Strategy-level safety interlocks** — we did not RE the strategy for secondary gates. If Variant A / B don't produce the expected behavior, there may be a strategy check beyond the cal scalars.

## All files

- `firmware/patched/LKA_SPEED_FLOOR_FIX.VBF` — Variant A (flashable, 66,915 B, CRC-valid)
- `firmware/patched/LKA_NO_LOW_GATES.VBF` — Variant B
- `firmware/patched/LKA_FULL_AUTHORITY.VBF` — Variant C

All three base on `LKA_APA_STANDSTILL.VBF` so they also include the previous timer-lockout removal and APA curve flattening.
