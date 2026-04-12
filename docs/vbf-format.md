---
title: VBF Format Spec
nav_order: 22
---

# VBF (Versatile Binary Format) — Ford/Volvo ECU Programming Container

## File structure

```
ASCII header:
  vbf_version = "2.X";
  header {
      sw_part_number = "LK41-14D007-AH";
      sw_part_type   = SWL | EXE | DATA | SBL ;
      data_format_identifier = 0x00 ;    # 0x00 raw, 0x10 LZSS
      ecu_address = 0x730 ;
      frame_format = CAN_STANDARD ;
      network = CAN_HS | CAN_MS ;
      file_checksum = 0xXXXXXXXX ;       # CRC32 over all block bytes
      ...
  };
BINARY blocks (repeated):
  u32 be    start_address
  u32 be    length
  u8[len]   data                          # raw or LZSS-compressed
  u16 be    crc16                         # CRC16-CCITT on DECOMPRESSED data
u32 be     file_checksum                  # matches header value
```

## CRCs

- **Block CRC16** = CRC16-CCITT (poly `0x1021`, init `0xFFFF`) over the **decompressed** payload. For `data_format=0x00` the raw and decompressed data are identical.
- **File CRC32** = standard CRC32 over the concatenation of all block data sections.

## Compression (data_format 0x10)

LZSS variant: 8-flag byte, each bit = literal (1) or back-reference (0). Back-reference = 2 bytes with 12-bit offset + 4-bit length (min length usually 3). Window size 4096.

## Modification workflow

1. Parse header (ASCII until `};`).
2. Decompress each block if `data_format=0x10`.
3. Patch bytes.
4. Recompute CRC16 per block on decompressed data.
5. Re-compress (or keep uncompressed — safer, changes `data_format` to `0x00`).
6. Concatenate all block data, compute CRC32, update `file_checksum` in header.
7. Write out.

## PSCM-specific

- 3 blocks: strategy (`~0x00F00000`), RAM init (`~0x40000000`), EPS core.
- Cal is part of strategy block at `0x00FD0000` (65,520 bytes).
- SBL is a separate VBF uploaded first by FORScan during flashing.
