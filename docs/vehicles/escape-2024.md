---
title: 2024 Escape
parent: Vehicles
nav_order: 4
---

# 2024 Ford Escape — PSCM

Newer Escape revision. Ford switched prefix from `LX6C` (2022) to `PZ11` (2024).

## Identity

| Field | Value |
|---|---|
| Strategy prefix | `PZ11-14D003-*` |
| Supplementary prefix | `PZ11-14D004-*` |
| EPS core prefix | `PZ11-14D005-*` |
| Cal prefix | `PZ11-14D007-*` |
| Compatibility with 2022 Escape (`LX6C`) | **Unconfirmed** |
| Compatibility with 2025 Transit | **Unconfirmed** |

## Files in this repo

`firmware/Escape_2024/`:

| File | Role |
|---|---|
| `PZ11-14D003-FB` | Strategy — block0 |
| `PZ11-14D004-FAB` | Supplementary — purpose unknown |
| `PZ11-14D005-AA` | EPS core (earlier rev) |
| `PZ11-14D005-AB` | EPS core (later rev) |
| `PZ11-14D007-EBC` | Calibration |

## Why this vehicle matters

- **Fallback LCA donor** if `LX6C` ever turns out to be incompatible with a future Transit revision.
- **Newer cal layout** — Ford may have added fields or shifted offsets. Diffing `LX6C-14D007-ABH` vs `PZ11-14D007-EBC` tells us how stable the cal format is across model years.
- **Presence of `-14D004-*`** — the 2022 Escape set didn't ship this supplementary file. New addition. What is it? Open question.

## Starting analysis

```bash
# Size/address comparison
python tools/vbf_decompress.py firmware/Escape_2022/LX6C-14D007-ABH
python tools/vbf_decompress.py firmware/Escape_2024/PZ11-14D007-EBC

# Byte-level diff of the two Escape cals
python tools/compare_fw.py \
  firmware/Escape_2022/LX6C-14D007-ABH \
  firmware/Escape_2024/PZ11-14D007-EBC
```

If the cal length matches and most bytes match, the layout is stable and LCA offsets we identified on `LX6C` probably still apply on `PZ11`. If length differs, Ford reorganized — requires fresh RE.

## Open questions

1. Is `PZ11-14D004-FAB` an extra flash block (new partition), or an MPU config descriptor, or an SBL variant?
2. Are the LCA cal regions at the same offsets as 2022 Escape?
3. Would the `PZ11` strategy run on a 2025 Transit PSCM?

## Status

**Not yet analyzed in depth.** Files archived in repo for future work.

## See also

- [2022 Escape](escape-2022.html) — our actual LCA donor.
- [Per-file catalog](../per-file-catalog.html#2024-escape-firmwareescape_2024)
