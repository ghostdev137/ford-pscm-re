---
title: Calibration Map
nav_order: 21
---

# PSCM Calibration Map

All offsets relative to cal base `0x00FD0000`. **Big-endian.** Total size 65,520 bytes.

## APA (Active Park Assist) speed table — `+0x02C4 .. +0x02E0`

IEEE-754 BE floats, kph.

| Offset | Field | Transit (stock) | Escape | Patched |
|---|---|---|---|---|
| `+0x02C4` | APA min speed | — | — | — |
| `+0x02DC` | APA low-speed thresh | `40 93 33 33` (4.6) | — | `42 48 00 00` (50.0) |
| `+0x02E0` | APA high-speed cap | `41 00 00 00` (8.0) | — | `43 48 00 00` (200.0) |

## LKA lockout timer table — `+0x06B0 .. +0x06C2`

13 bytes of `u16` BE values, units of 10 ms.

| Offset | Stock (BE) | Value | Patched |
|---|---|---|---|
| `+0x06B0` | `00 64` | 1.0 s | `00 00` |
| `+0x06B2` | `00 C8` | 2.0 s | `00 00` |
| `+0x06B4` | `01 F4` | 5.0 s | `00 00` |
| **`+0x06B6`** | **`03 E8`** | **10.0 s (main lockout)** | **`00 00`** |
| `+0x06B8..0x06C2` | various | various | all zero |

## Lane Centering Assist (LCA) GP-relative regions

Data missing from Transit but present in Escape (`LX6C` PSCM, same platform). Copying these from Escape cal into Transit cal fills all 12 GP-relative references in LCA code paths:

| Region | Bytes |
|---|---|
| `+0x06C3` | small |
| `+0x06C8` | |
| `+0x0E79` | |
| `+0x0E82` | |
| `+0x21BC` | |
| `+0x2FCE` | |
| `+0x327C` | |
| `+0x33DD` | |
| `+0x3AD1` | |
| `+0x41AD` | |
| `+0xFFDC` | |
| **Total** | **~4,460 bytes across 11 regions** |

> **Note:** Filling the cal was not sufficient to enable LCA — AS-built config reverts on power cycle. Strategy-level gate suspected (separate from cal).

## Read via UDS

```
request:  0x730  03 22 F1 88             # ReadDID strategy PN
response: 0x738  10 xx 62 F1 88 <ascii>  # first frame
```

```
request:  0x730  10 0A 23 44 00 FD 06 B0 00 14   # ReadMemByAddr 20 bytes at cal+0x06B0
response: 0x738  63 <20 bytes>
```
