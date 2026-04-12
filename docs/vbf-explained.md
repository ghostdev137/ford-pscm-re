---
title: VBF Files Explained (Friendly Walkthrough)
nav_order: 4
---

# VBF Files Explained

A **VBF** (Versatile Binary Format) is Ford's firmware file. When a dealer flashes your car, they upload VBFs to each ECU. When you use FORScan to flash patched firmware, you hand it VBFs too. This page walks through exactly what's inside one.

For the dry format spec, see [vbf-format](vbf-format.html). This page is the friendly version.

## Anatomy of a VBF

Every VBF has two parts:

```
┌─────────────────────────────────────────┐
│  1. ASCII HEADER                        │   ← human-readable text, key=value
│     vbf_version = "2.6";                │     tells FORScan *where* to flash
│     sw_part_number = "LK41-14D007-AH";  │     *what* the data is, *what CRC*
│     ecu_address = 0x730;                │     to expect, etc.
│     ...                                 │
│  };                                     │   ← header ends with };
├─────────────────────────────────────────┤
│  2. BINARY BLOCKS                       │   ← one or more chunks
│     ┌──────────────────────────────┐    │
│     │ u32 start_address (BE)       │    │   ← "flash me here"
│     │ u32 length       (BE)        │    │   ← "I'm this many bytes"
│     │ u8  data[length]             │    │   ← the actual bytes
│     │ u16 crc16         (BE)       │    │   ← integrity check
│     └──────────────────────────────┘    │
│     ┌──────────────────────────────┐    │
│     │ ... next block ...           │    │
│     └──────────────────────────────┘    │
├─────────────────────────────────────────┤
│  3. u32 file_checksum (BE)              │   ← CRC32 over all block data
└─────────────────────────────────────────┘
```

## A real example: `LK41-14D007-AH.VBF`

This is our base calibration VBF for the 2025 Transit. Let's look inside.

### Header (ASCII)

```
vbf_version = "2.6";
header {
    sw_part_number = "LK41-14D007-AH";     # the PN Ford tracks
    sw_part_type = DATA;                    # this file is calibration (not code)
    data_format_identifier = 0x00;          # 0x00 = raw, 0x10 = LZSS compressed
    ecu_address = 0x730;                    # which CAN ID the target ECU listens on
    frame_format = CAN_STANDARD;            # 11-bit CAN IDs
    network = CAN_MS;                       # medium-speed CAN (not HS-CAN!)
    file_checksum = 0xDEADBEEF;             # CRC32 we'll verify
    ecu_address_hr = "PSCM";                # human-readable, optional
    # ... more metadata ...
};
```

This tells FORScan: "hand this to the ECU at CAN ID `0x730`, using medium-speed CAN, it's calibration data, uncompressed."

### Block(s)

After the `};`, the binary starts. This particular VBF has **one** block:

```
start_address = 0x00FD0000   ← flash base for calibration
length        = 0x0000FFF0   ← 65,520 bytes
data          = 65,520 bytes of calibration tables
crc16         = 0xABCD       ← covers those 65,520 bytes
```

After the last block: a 4-byte CRC32 that must match `file_checksum` in the header.

## What's a "block"? What's block0/1/2?

A **block** is one `(address, length, data, crc16)` tuple inside a VBF. Big firmware ships in multiple blocks because different parts live at different flash addresses.

For the PSCM, flashing the complete application requires **three** VBFs, each containing one or more blocks. They correspond to three distinct firmware partitions:

| Nickname | VBF PN pattern | What it is | Flash address |
|---|---|---|---|
| **block0 / strategy** | `KK21-14D003-*` | Main application code — AUTOSAR BSW + Ford strategy | ~`0x00F00000` |
| **block1 / RAM init** | (usually bundled with block0) | Initialized data copied to RAM on boot | varies |
| **SBL** | `KK21-14D005-*` | Secondary Bootloader — uploaded to RAM during flashing, not persisted | RAM only |
| **calibration** | `LK41-14D007-*` | The 65,520-byte cal table | `0x00FD0000` |
| **supplementary** | `KK21-14D004-*` | MPU config / secondary data block | varies |

(Different vehicles use different PN prefixes — see [per-file-catalog](per-file-catalog.html).)

## Why four files for one module?

Because Ford split the firmware:
1. **Strategy (block0)** changes between model years, trims, and software revisions. Ford re-releases it often.
2. **Calibration** is tuned per vehicle variant (Transit passenger vs. cargo vs. LWB, etc.) without recompiling.
3. **SBL** (`-14D005-*`) is the uploader that runs in RAM during flashing; it rarely changes.
4. **Supplementary (`-14D004-*`)** carries MPU config or a secondary data block used by the strategy.

Splitting means when Ford tweaks a cal value they only ship a new `14D007` file, not the whole stack.

## The three things that matter for patching

1. **`data_format_identifier`** — `0x00` means raw bytes (easy to patch). `0x10` means LZSS-compressed (must decompress, patch, recompress OR decompress and re-ship uncompressed).
2. **`start_address` on each block** — tells you what flash range those bytes occupy. The PSCM cal we patch is always at `0x00FD0000`.
3. **The two CRCs** — both must be valid or the ECU rejects the flash. CRC16 is per-block over the decompressed data; CRC32 is over the concatenated block data.

Our patch tooling (see `tools/vbf_decompress.py`) handles all three automatically.

## The flashing sequence uses multiple VBFs in order

When you tell FORScan "program the PSCM," it's actually doing:

```
1. Unlock the PSCM (UDS security access).
2. Upload SBL to RAM.
3. Tell PSCM "run SBL."
4. SBL erases the application flash.
5. Upload block0 (strategy) VBF → flash.
6. Upload supplementary VBF (if any) → flash.
7. Upload cal VBF → flash.
8. Checksum verify.
9. Reset PSCM → it boots the new firmware.
```

You don't usually see this — FORScan handles it. But when you hand FORScan `LKA_NO_LOCKOUT.VBF`, you're replacing step 7 only. Steps 5 and 6 still use Ford's stock files, which is why our minimal patches are safe(r).

## Verifying a VBF before you flash

```bash
python tools/vbf_decompress.py firmware/patched/LKA_NO_LOCKOUT.VBF
```

This prints header fields, block addresses/lengths, and verifies CRC16 per block and CRC32 for the file. If anything says FAIL, do not flash.

## See also

- [Per-file VBF catalog](per-file-catalog.html) — every VBF in the repo, explained.
- [VBF format reference](vbf-format.html) — terse spec.
- [Flashing guide](flashing.html) — how to actually write a VBF to the car.
