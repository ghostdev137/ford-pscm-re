# Transit 2025 `AH` Strategy — LCA RX Probe

**File:** `KK21-14D003-AH_LCA_RX_PROBE.VBF`  
**Base:** stock `KK21-14D003-AH.VBF`  
**Purpose:** first Transit-native strategy experiment for the Escape-style LCA RX path.

This is **not** a full Escape strategy transplant.

It keeps Transit `AH` strategy and only patches the known Transit RX-routing data in
block0 so the strategy now advertises:

- `0x3D7`
- `0x3D3`

where stock Transit `AH` advertised:

- `0x416`
- `0x415`

## What changed

### 1. RX PDU descriptor table

Block0 offsets:

- `+0x2C70`: `0416011401080000` -> `03D7011401080000`
- `+0x2C78`: `0415011501080000` -> `03D3011501080000`

Plain language:

- Transit slot `0x14` now routes `0x3D7` instead of `0x416`
- Transit slot `0x15` now routes `0x3D3` instead of `0x415`

Stock Transit `AH` neighborhood:

```text
0x01002C70  0416011401080000
0x01002C78  0415011501080000
0x01002C80  040A011601080000
0x01002C88  03CA011701080000
0x01002C90  03B3011801080000
0x01002C98  03A8011901080000
```

Patched neighborhood:

```text
0x01002C70  03D7011401080000
0x01002C78  03D3011501080000
0x01002C80  040A011601080000
0x01002C88  03CA011701080000
0x01002C90  03B3011801080000
0x01002C98  03A8011901080000
```

### 2. Compact CAN-ID list

Block0 offsets:

- `+0x2D4E`: `0416` -> `03D7`
- `+0x2D50`: `0415` -> `03D3`

Stock Transit `AH` compact list region:

```text
0x01002D38  07DF0730063C060C060B060A04B00431
0x01002D48  0430042C041E04160415040A03CA03B3
0x01002D58  03A80263021702160213020201670083
0x01002D68  007D007700760000
```

Patched region:

```text
0x01002D38  07DF0730063C060C060B060A04B00431
0x01002D48  0430042C041E03D703D3040A03CA03B3
0x01002D58  03A80263021702160213020201670083
0x01002D68  007D007700760000
```

## What this means

This is a **routing probe**, not a proven complete LCA enable.

It answers one narrow question:

> If Transit `AH` starts advertising `0x3D7` / `0x3D3` in the known RX routing
> structures, does anything new happen at runtime?

What it does **not** prove:

- that Transit already has the correct downstream `0x3D3` handler
- that slot `0x14/0x15` are the correct donor-equivalent slots
- that `0x3D7` and `0x3D3` alone are sufficient for full LCA
- that no other backend table needs donor bytes too

## Important limitation

This experiment **repurposes** two existing Transit RX entries:

- `0x416`
- `0x415`

So this is intentionally not production-safe or feature-complete. It is a
binary probe to test whether Transit strategy reacts differently once those two
LCA-related IDs are present in the Transit RX tables.

## Verification

Verified after rebuilding the VBF:

- block0 patched bytes match expected values
- block0 CRC16 = `0x8980`
- block1 CRC16 unchanged = `0x2D93`
- block2 CRC16 unchanged = `0xFFCD`
- header `file_checksum = 0x417B7509`

Local post-build parse confirms:

- stock Transit `AH`: `{0x416 -> 0x14, 0x415 -> 0x15, 0x3CA -> 0x17}`
- patched probe: `{0x3D7 -> 0x14, 0x3D3 -> 0x15, 0x3CA -> 0x17}`

## Build tool

Built with:

- `tools/vbf_patch_multiblock.py`

That tool preserves untouched blocks and rebuilds only the patched block with
fresh per-block CRC16 and updated VBF header checksum.
