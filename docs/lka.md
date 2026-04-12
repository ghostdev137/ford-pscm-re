---
title: LKA — Lane Keep Aid
nav_order: 10
---

# LKA (Lane Keeping Aid) on the Transit PSCM

## What Ford ships

LKA is enabled on the 2025 Transit but has a **10-second active steering lockout**. After each LKA intervention, the PSCM refuses to apply assist torque for 10 s. The camera (IPMA, `NK3T`) keeps detecting lanes and commanding, but the PSCM ignores it during the lockout window.

Behavior: you feel one tug, then nothing for 10 s, then another tug. This makes LKA effectively useless at highway speeds.

## Root cause — calibration table

The lockout is not a hard-coded constant. It lives in a small `u16` timer table in the calibration partition:

```
cal base      = 0x00FD0000
timer table   = cal + 0x06B0 .. cal + 0x06C2   (13 bytes, big-endian u16 array)
units         = 10 ms ticks
```

| Offset | Stock value | Decoded | Meaning (inferred) |
|---|---|---|---|
| +0x06B0 | `00 64` | 1.0 s | Minimum re-arm window |
| +0x06B2 | `00 C8` | 2.0 s | Secondary hold |
| +0x06B4 | `01 F4` | 5.0 s | Debounce |
| **+0x06B6** | **`03 E8`** | **10.0 s** | **Main post-intervention lockout** |
| +0x06B8..06C2 | various | — | Secondary counters |

Strategy code at multiple GP-relative sites loads these values, decrements each 10 ms tick, and gates `LKA_apply_torque` until the counter reaches zero.

## The patch

Zero all 13 bytes. Lockout counter starts at 0, gate opens immediately. File:

- `firmware/patched/LKA_NO_LOCKOUT.VBF` — **flashed and running** on a 2025 Transit since 2026-04-12.

Minimal diff (only the cal bytes changed). CRC16 and CRC32 recomputed. Exact VBF header:

```
vbf_version = "2.6";
sw_part_number = "LK41-14D007-AH";
sw_part_type = DATA;
ecu_address = 0x730;
data_format_identifier = 0x00;
```

## Reproduction steps

1. Start from `firmware/Transit_2025/LK41-14D007-AH.VBF` (uncompressed cal VBF).
2. Locate the data block (skip ASCII header until `};`, then read `u32 addr` + `u32 len`).
3. At `addr=0x00FD0000`, overwrite bytes `0x06B0..0x06C2` with zeros.
4. Recompute CRC16-CCITT over the block data → patch in trailing u16.
5. Recompute CRC32 over full block data section → patch `file_checksum` in header.
6. Flash with FORScan → Module Programming → PSCM.

`tools/vbf_decompress.py` has the VBF parser. See also `docs/vbf-format.html`.

## Verification via UDS

```
# ReadMemoryByAddress 20 bytes at cal+0x06B0
req  0x730  10 0A 23 44 00 FD 06 B0 00 14
resp 0x738  63 00 00 00 00 00 00 00 00 00 00 00 00 00 ...
```

If you see zeros, patch is live.

## What LKA uses from the cal (partial map)

Working list of adjacent fields, derived by GP-displacement cross-reference and runtime logging:

| Offset | Field | Notes |
|---|---|---|
| +0x06B0..06C2 | Lockout timers | Patched |
| +0x06C3..06C8 | LKA gain / authority | Region also used by LCA — do not zero |
| +0x0E79..0E82 | Heading / curvature scale | Shared with LCA |

## Risks

- Without the lockout, repeated LKA tugs can fight steady-state cornering. The camera still limits torque magnitude via the `0x213 DesTorq` CAN message, so you will not experience a sudden hard steering input.
- Some Ford TSBs reference the 10-s lockout as "operator alertness strategy." Removing it is out-of-spec. It is not a functional-safety lockout (that is enforced separately in the EPS core block).
- Disengages remain: hands-off detection, driver torque override, and speed floor (~40 kph) are enforced elsewhere and are **not** affected by zeroing this table.

## Status

**Flashed and awaiting road test.** Next step is a highway drive to confirm continuous LKA authority.
