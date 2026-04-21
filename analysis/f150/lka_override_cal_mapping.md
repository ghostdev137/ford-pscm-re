# F-150 LKA Quiet-Gate — Cal Threshold Mapping (2026-04-21)

## Summary

The LKA driver-override quiet-gate function `FUN_101a3b84` compares driver
torque against two RAM-resident thresholds (`_DAT_fef26382` and
`_DAT_fef263de`). Those RAM cells are populated at boot from cal flash
by the C-runtime `.data` init routine `FUN_100913ee`.

**Cal flash sources of the LKA thresholds are now located.**

| Runtime RAM | Cal flash VA | Cal offset | Current u16 LE value | Role |
|---|---|---|---|---|
| `_DAT_fef26382` | `0x101D70AE` | cal+0x70AE | `0x2800` = 10240 | abs torque threshold |
| `_DAT_fef263de` | `0x101D710A` | cal+0x710A | `0x6400` = 25600 | state / hysteresis threshold |
| `_DAT_fef263fa` (ep anchor) | `0x101D7126` | cal+0x7126 | `0x6380` | ep-base for adjacent shorts |

**Patch these bytes in cal to change LKA override threshold behavior.**

## How the mapping was found

1. The quiet-gate reads `_DAT_fef26382` and `_DAT_fef263de` in `FUN_101a3b84` at
   `/tmp/pscm/cmpf_f150/101a3b84_FUN_101a3b84.c:41`. No writer visible in
   Ghidra's xref graph — the writers use a mechanism const-prop can't
   resolve.

2. Found the C-runtime init: `FUN_100913ee` (called from `entry` @ `0x10040098`).
   It walks a copy-descriptor table at address `0x000D1490`, which on
   RH850 is a "local-ref" alias for code-flash address `0x100D1490`
   (local refs `0x000XXXXX` map to code-flash `0x100XXXXX`).

3. The descriptor table has 227 entries × 12 bytes each
   `{src:u32, dst:u32, len:u16, rsv:u16}`, only 13 non-zero-length:

   | idx | src (local-ref) | src (real VA) | dst (RAM) | len | region |
   |---|---|---|---|---|---|
   | 2 | `0x000538D4` | `0x100538D4` | `0xFEBF8700` | 1 | strategy → RAM |
   | 10 | `0x000538E0` | `0x100538E0` | `0xFEBEC000` | 0xE60 | strategy → RAM |
   | 18 | `0x00054740` | `0x10054740` | `0xFEBF8020` | 0x74 | strategy → RAM |
   | 26 | `0x000547B4` | `0x100547B4` | `0xFEBF86B8` | 0x37 | strategy → RAM |
   | 190 | `0x00054B00` | `0x10054B00` | `0xFEBF9854` | 2 | strategy → RAM |
   | 202 | `0x000D1F34` | `0x100D1F34` | `0xFEBF9984` | 0xC | strategy → RAM |
   | 214 | `0x000D5490` | `0x100D5490` | `0xFEBFE000` | 0x6F0 | strategy → RAM |
   | 215 | `0x001A9608` | `0x101A9608` | `0xFEF20800` | 0x99A | strategy → RAM |
   | 219 | `0x001B0E40` | `0x101B0E40` | `0xFEF23800` | 0x367 | strategy → RAM |
   | **223** | **`0x001D652C`** | **`0x101D652C`** | **`0xFEF25800`** | **0xF8C** | **CAL → RAM** |
   | 224 | `0x001D74B8` | `0x101D74B8` | `0xFEF2678C` | 0xC18 | CAL → RAM |
   | 225 | `0x0004F7E0` | `0x1004F7E0` | `0xFEBEBE60` | 0x172 | strategy → RAM |
   | 226 | `0x0004F954` | `0x1004F954` | `0xFEBEBFD4` | 0x1E | strategy → RAM |

4. Descriptor [223] covers the quiet-gate RAM region:
   - `_DAT_fef26382` is at RAM offset `0xfef26382 - 0xfef25800 = 0xB82` within the copy
   - Cal source: `0x101D652C + 0xB82 = 0x101D70AE` (= cal+0x70AE)
   - `_DAT_fef263de` at RAM offset `0xBDE` → cal source `0x101D710A` (cal+0x710A)

## Cal bytes at thresholds

```
cal+0x70A0  00180018002000187806a864401f0028
cal+0x70B0  af13e1fa005800980050000000580058
                           ^^^^ cal+0x70AE = 0x2800 LE (threshold A)

cal+0x7100  cd0c0083800200ec7d00006400000000
                           ^^^^ cal+0x710A = 0x6400 LE (threshold B)
```

The adjacent `8000, 10240, 5039` sequence at cal+0x70AC..0x70B0 looks like
a monotonically-increasing torque threshold table (the previous entries
at 0x70A0 are lower: `6144, 6144, 8192, 6144, 1656, 25768`). The
threshold at cal+0x70AE is the one consumed by the LKA quiet-gate.

## Endianness note

Ford F-150 PSCM uses little-endian data (standard V850 native). The
`ld.hu` instruction in the quiet-gate does a LE halfword load, returning
`0x2800 = 10240` for cal+0x70AE. Scaling to physical units (N·m) requires
the torque-sensor calibration constant which we don't have — but for
empirical patching, bit-flip + drive-test is sufficient to characterize.

## Patching guidance

**Do not** run write patches blindly against cal+0x70AE / cal+0x710A
without first confirming the full struct layout by bisecting nearby
fields. The quiet-gate also reads `_DAT_fef263f2`, `_DAT_fef263f4`,
`_DAT_fef263f6`, `_DAT_fef263f8`, `_DAT_fef263fa`, `_DAT_fef263fc`,
`_DAT_fef263fe` — a 16-byte struct. Their cal sources are all in the
range cal+0x711E..cal+0x712A. Treat the whole block as a struct and
document each field before patching.

## Why Ghidra couldn't resolve the writer

The writer is `FUN_100bfee0` (a memcpy-like leaf called from FUN_100913ee),
invoked in a loop `for (i=0; i<227; i++)` with arguments loaded from the
descriptor table. Const-prop can't follow the loop-variant pointer, so
no xref from `FUN_100bfee0` back to any specific cal byte ever gets
stored.

## Reusable tool

None of the byte-crunching here needs Ghidra; it was done with a pure
Python script parsing the ELF + descriptor table. The same technique
applies to any of the 13 non-zero descriptors for mapping any other
RAM cell back to its cal source.
