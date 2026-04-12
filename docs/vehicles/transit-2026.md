---
title: 2026 Transit
parent: Vehicles
nav_order: 2
---

# 2026 Ford Transit — PSCM

**New platform.** Ford switched PSCM part-number family from `KK21`/`LK41` (2025) to `RK31` (2026). Memory layout, cal format, and strategy are **not confirmed** to match 2025. Our 2025 patches do not apply here without redoing the reverse engineering.

## Identity (what we know)

| Field | Value |
|---|---|
| PSCM prefix (strategy) | `RK31-14D003-*` |
| PSCM prefix (supplementary) | `RK31-14D004-*` |
| PSCM prefix (EPS core) | `RK31-14D005-*` |
| PSCM prefix (cal) | `RK31-14D007-*` |
| MCU | Likely V850E2M or successor — not confirmed |
| Cal flash address | Unconfirmed |

## Files in this repo

`firmware/Transit_2026/`:

| File | Role (inferred) |
|---|---|
| `RK31-14D003-PB` | Strategy — block0 |
| `RK31-14D004-PB` | Supplementary — purpose unknown, possibly MPU config or bootloader config |
| `RK31-14D005-PA` | EPS core — block2 |
| `RK31-14D007-RAC` | Calibration |

## Open questions (would love help on these)

1. **Is the MCU still V850E2M?** Disassemble `RK31-14D003-PB` and see if V850E2M opcodes decode sanely. If they do, our reversing tools carry over.
2. **Does the cal still live at `0x00FD0000`?** Parse the `RK31-14D007-RAC` VBF header and look at `start_address`.
3. **Is the cal still 65,520 bytes?** Check `length` in the cal VBF.
4. **Are LKA / APA / LCA field offsets the same?** Grep the 2026 cal for the Transit 2025 LKA timer values (`00 64 00 C8 01 F4 03 E8`) — if present, layout is conserved and our patches port trivially.
5. **Does it ship with LCA enabled?** Would let a 2026 owner compare to our `LCA_ENABLED.VBF` attempt.

## Starting a port

```bash
# Disassemble the strategy to confirm MCU
python tools/decompile_block0.py firmware/Transit_2026/RK31-14D003-PB

# Inspect cal VBF header
python tools/vbf_decompress.py firmware/Transit_2026/RK31-14D007-RAC

# Compare cal bytes at LKA timer offsets
python tools/compare_fw.py \
  firmware/Transit_2025/LK41-14D007-AH.VBF \
  firmware/Transit_2026/RK31-14D007-RAC
```

## Status

**Untouched.** Nobody has flashed a patched 2026 VBF. If you have a 2026 Transit and want to help, reach out on the repo issues.

## See also

- [2025 Transit](transit-2025.html) — base for comparison.
- [Per-file catalog](../per-file-catalog.html#2026-transit-firmwaretransit_2026)
