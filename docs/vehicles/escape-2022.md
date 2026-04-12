---
title: 2022 Escape
parent: Vehicles
nav_order: 3
---

# 2022 Ford Escape — PSCM (our LCA donor)

**Same PSCM hardware and firmware platform as the 2025 Transit.** Ships with Lane Centering enabled. This is how we know Transit is hardware-capable.

## Identity

| Field | Value |
|---|---|
| PSCM vendor | ThyssenKrupp Presta EPU (same as Transit) |
| MCU | Renesas V850E2M / RH850 |
| Strategy prefix | `LX6C-14D003-*` |
| EPS core prefix | `LX6C-14D005-*` |
| Cal prefix | `LX6C-14D007-*` |
| Cal size | 65,520 bytes (same as Transit) |
| Cal flash address | `0x00FD0000` (same as Transit) |
| Donor VIN (files came from) | `1FMCU9J98NUA09141` |

## Stock feature state

| Feature | State |
|---|---|
| LKA | Enabled |
| LCA / TJA | **Enabled** — this is what we want to extract |
| APA | Enabled |
| Lane-change assist | Enabled (on some trims) |

## Files in this repo

`firmware/Escape_2022/`:

| File | Role |
|---|---|
| `LX6C-14D003-AL` | Strategy — block0. **Different** from Transit strategy; contains live LCA code paths. |
| `LX6C-14D005-AB` | EPS core — block2. Believed identical to Transit EPS core. |
| `LX6C-14D007-ABH` | **Calibration — our LCA data donor.** Regions copied into `LCA_ENABLED.VBF`. |

## Why this is the donor, not F-150

Early in the project I assumed F-150 was the right donor (bigger, more features). It's not — F-150 uses `ML34`/`ML3V`, a completely different PSCM platform with a different cal layout.

The Escape `LX6C` PSCM, however, is **identical hardware** to Transit PSCM. Same V850E2M. Same AUTOSAR build. Same 65,520-byte cal layout. Same flash address for cal. The only difference is some cal regions are populated on Escape (with LCA data) and blank on Transit.

## What we copied from Escape cal to Transit cal

Eleven contiguous regions totaling 4,460 bytes:

| Offset | Approx. purpose (inferred) |
|---|---|
| `+0x06C3` | Shared LKA/LCA authority |
| `+0x06C8` | Curvature gain lookup |
| `+0x0E79` | Heading error PID |
| `+0x0E82` | Lateral error PID |
| `+0x21BC` | Traffic-jam low-speed mode gains |
| `+0x2FCE` | Lane-change torque envelope |
| `+0x327C` | Centering hold torque |
| `+0x33DD` | Curvature rate limits |
| `+0x3AD1` | Hand-off detection thresholds |
| `+0x41AD` | Enable/disable hysteresis |
| `+0xFFDC` | End-of-cal footer / version tag |

On stock Transit cal these regions are `0xFF` fill. On Escape they're populated.

Result: the Transit PSCM's 12 GP-relative references into LCA tables all resolve to real numbers. Cal-level gate is satisfied. But the flash still doesn't enable LCA (AS-built reverts) — see [lca](../lca.html).

## Open question

Is there a way to use the **Escape strategy** (`LX6C-14D003-AL`) on a Transit? Risks:
- Different AUTOSAR config layout — BSW init values may not match Transit wiring.
- Vehicle-platform strings in strategy may cause it to refuse to run on a Transit VIN.
- EPS core interface may have subtle differences despite identical PN.

Untested. High-risk experiment.

## See also

- [LCA enable attempt](../lca.html)
- [2025 Transit](transit-2025.html)
- [2024 Escape](escape-2024.html) — newer Escape, unclear if still compatible
