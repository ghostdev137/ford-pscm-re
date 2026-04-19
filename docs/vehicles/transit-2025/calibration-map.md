---
title: Calibration Map
nav_order: 21
parent: 2025 Transit
grand_parent: Vehicles
---

# PSCM Calibration Map — Transit 2025

All offsets relative to cal base `0x00FD0000`. **Big-endian** throughout. Total cal size: 65,520 bytes.

This page covers Transit/Escape PSCM only. F-150 cal is at `0x101D0000`, little-endian, different layout — see `analysis/f150/cal_findings.md`.

---

## LKA torque authority curve — `+0x03C4` (8 × float32 BE)

**Confirmed active LKA curve.** Cross-vehicle analysis: Transit `+0x03C4` matches Escape `+0x06BC` byte-for-byte on stock firmware. No other Transit torque table matches any Escape table — this is the one shared LKA parameter.

Speed breakpoints axis at `+0x0304`: `[0, 10, 30, 50, 70, 90, 130, 250]` kph

| Cal offset | Stock values (Nm) | LKA_FULL_AUTHORITY (Nm) | Notes |
|---|---|---|---|
| `+0x03C4..+0x03E3` | `[0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 7.0]` | **`[0, 0.7, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]`** | **Flashed and drive-confirmed** |

Stock at 70 kph: 1.0 Nm → matches observed torque ceiling in drive data. Patched at 70 kph: 3.5 Nm. Peak 6.5 Nm is below F-150 BlueCruise production peak (6.25 Nm on `ML34`). Column torque median: 0.44 Nm → 1.25 Nm (+184%).

Other torque curves in the `+0x0280..+0x04A0` region (identified but not yet confirmed as active):

| Offset | Values (Nm) | Label |
|---|---|---|
| `+0x0288` | `[0, 0.05, 0.1, 0.2, 0.4, 0.7, 1.0]` | fine-grain |
| `+0x0344` | `[0, 0.25, 0.5, 1, 1.5, 2.5, 3, 7]` | mild |
| `+0x0384` | `[0, 0.3, 0.6, 1, 2, 7, 10, 20]` | aggressive |

---

## LKA minimum-speed floor — `+0x0690` (float32 BE)

| Offset | Stock | Patched (MIN_3) | Notes |
|---|---|---|---|
| `+0x0690` | `41 20 00 00` (10.0 m/s ≈ 36 kph) | `40 40 00 00` (3.0 m/s ≈ 11 kph) | Flashed, drive-confirmed: LKA engages at 10.7 m/s with this patch |

Stock: LKA refuses to actuate below ~10 m/s regardless of command. Separate from the timer lockout.

---

## LKA lockout timer table — `+0x06B0..+0x06C2` (10 × u16 BE, × 10 ms)

| Offset | Stock (BE) | Decoded | Patched (LKA_NO_LOCKOUT) |
|---|---|---|---|
| `+0x06B0` | `00 00` | `0` | `00 00` |
| `+0x06B2` | `00 64` | `1.0 s` | `00 00` |
| `+0x06B4` | `00 00` | `0` | `00 00` |
| **`+0x06B6`** | **`03 E8`** | **`10.0 s (main lockout)`** | **`00 00`** |
| `+0x06B8` | `07 D0` | `20.0 s` | `00 00` |
| `+0x06BA` | `03 E8` | `10.0 s` | `00 00` |
| `+0x06BC` | `01 F4` | `5.0 s` | `00 00` |
| `+0x06BE` | `01 90` | `4.0 s` | `00 00` |
| `+0x06C0` | `00 05` | `5` | `00 00` |
| `+0x06C2` | `00 FF` | `255` | `00 00` |

Exact stock series: `[0, 100, 0, 1000, 2000, 1000, 500, 400, 5, 255]`

Best current interpretation: this is an older packed LKA lockout supervisor. `+0x06B6` is the only entry firmly closed as the main 10-second lockout. The surrounding values are best understood as the short qualify, extended watchdog, re-arm, recovery, and small state-count pieces of that same state machine. This matches the newer F-150 cal structurally, where Ford exposes separate `arm timer`, `re-arm timer`, and adjacent debounce-style constants instead of one packed Transit-style cluster.

Immediately before that cluster, Transit has a mixed-type preamble:

- `+0x06A0 = 6.0f`
- `+0x06A4 = 200000`
- `+0x06A8 = 300000`
- `+0x06AE = 1500`

Best current read of `+0x06AE`: related hysteresis / settle constant for the same supervisor, not another hidden member of the `10 ms` timer table. If it used the same `10 ms` scale as `+0x06B6`, it would imply `15.0 s`, which does not fit observed Transit behavior. It also mirrors the newer F-150 LKA timer neighborhood, where a `1500` value sits right beside the named `arm` / `re-arm` timers as a likely debounce-style parameter.

**Flashed and confirmed.** Zeroing the whole cluster removes the 10-second steering lockout after each LKA intervention and also removes the surrounding qualify / recovery / watchdog terms.

---

## Speed breakpoints axis — `+0x0304` (8 × float32 BE)

`[0, 10, 30, 50, 70, 90, 130, 250]` kph — axis for torque curves at `+0x03C4`, `+0x0344`, `+0x0384`. Copied at `+0x0404` and `+0x0484`.

---

## APA speed table — `+0x02C4..+0x02E0` (float32 BE, kph)

| Offset | Stock | Patched | Notes |
|---|---|---|---|
| `+0x02C8` | 0.3 kph | 0.0 kph | APA X[0] first breakpoint (standstill patch) |
| `+0x02DC` | 4.6 kph | 50.0 kph | APA low-speed reference |
| `+0x02E0` | 8.0 kph | 200.0 kph | APA high-speed cap |

Full APA speed table axis: `[0, 0.3, 1.1, 1.8, 2.5, 3.2, 4.6, 8.0]` kph (stock).

---

## LCA GP-relative regions (Escape → Transit)

LCA cal data is present in Escape (`LX6C`) but absent (0xFF fill) in Transit. Copying these 11 regions from Escape into Transit cal fills all LCA code path references.

| Region start | Bytes | Purpose (inferred) |
|---|---|---|
| `+0x06C3` | small | Shared LKA/LCA authority |
| `+0x06C8` | | Curvature gain lookup |
| `+0x0E79` | | Heading error PID |
| `+0x0E82` | | Lateral error PID |
| `+0x21BC` | | Traffic-jam low-speed gains |
| `+0x2FCE` | | Lane-change torque envelope |
| `+0x327C` | | Centering hold torque |
| `+0x33DD` | | Curvature rate limits |
| `+0x3AD1` | | Hand-off detection thresholds |
| `+0x41AD` | | Enable/disable hysteresis |
| `+0xFFDC` | | End-of-cal footer |
| **Total** | **~4,460 B** | |

> Filling this data is not sufficient to enable LCA — AS-built enable bits revert on power cycle. A strategy-level gate (suspected VIN/vehicle-code check in block0) also needs bypassing.

---

## Reading cal via UDS

```
# Read 20 bytes at cal+0x06B0 (lockout timer table)
req  0x730  10 0A 23 44 00 FD 06 B0 00 14
resp 0x738  63 <20 bytes>
# All zeros = patch is live

# Read LKA torque curve (32 bytes at cal+0x03C4)
req  0x730  10 12 23 44 00 FD 03 C4 00 20
resp 0x738  63 <32 bytes>
# Decode as 8 × BE float32
```

```python
import struct
data = bytes.fromhex("...")  # 32 bytes from UDS response
for i in range(8):
    print(f"+0x{0x03C4+i*4:04X}: {struct.unpack_from('>f', data, i*4)[0]:.2f} Nm")
```

---

## LKA actuator scaler — firmware-side, not cal

Not every LKA authority knob lives in cal. The Transit-side angle scaler that converts commanded `LaRefAng_No_Req` into the internal wheel-angle request is a code-path constant inside `FUN_010babf2`:

- Instruction: `mulhi 0x67c2` at `0x010babf8` (Q15 multiplier, 2-byte patch site)
- Functional equivalent of the F-150's `movhi 0x4480` (float `1024.0`) at file offset `0x569d0`
- Raising this multiplier is the path for expanding LKA angle beyond the `LaRefAng_No_Req` DBC ceiling (12-bit signed, 0.05 mrad/bit, ±5.86° wheel) — cal patches alone cannot move that ceiling.

See [Transit torque arbitration map](arbitration-map.html) for the full arbitration chain this multiplier feeds into.

---

## Open: cal addressing mode

No `movhi 0x00FD` instruction pair appears in Transit strategy — the cal base is not embedded as a literal. Cal is probably accessed via a data-space mirror address initialized by the SBL or startup code. Finding this mirror address is the highest-value static-RE task: it would allow tracing exactly which functions read each cal offset.
