# Transit 2025 stock calibration diffs — what actually changed

**Date:** 2026-04-16

Files compared:

- `LK41-14D007-AD.VBF`
- `LK41-14D007-AF.VBF`
- `LK41-14D007-AH`

Related strategy compare:

- [transit_2025_strategy_compare.md](./transit_2025_strategy_compare.md)

## TL;DR

There are only **two real stock cal families** in the 2025 Transit set:

- `AD`
- `AF ≈ AH`

`AF` and `AH` are functionally the same. The real cal change is `AD -> AF`.

Just as important:

- the known stock **LKA torque table**, **speed axis**, **min-speed**, and
  **timer/lockout** settings do **not** change across `AD / AF / AH`
- the meaningful change is a **single mid-cal block** starting around
  `+0x2868`

## Pairwise byte diffs

- `AD -> AF`: `2264` differing bytes
- `AF -> AH`: `5` differing bytes
- `AD -> AH`: `2264` differing bytes

So:

- `AH` is effectively `AF` plus metadata/footer changes
- `AD` is the odd one

## 1. AF vs AH: only metadata/footer

The only `AF -> AH` differences are:

- `+0x0025`
  - part-number string byte (`...-AF` vs `...-AH`)
- `+0xFFEC..+0xFFEF`
  - footer/checksum/version bytes

Everything meaningful in the known LKA areas is unchanged between `AF` and
`AH`, including:

- `+0x03C4..+0x03E0` LKA torque table
- `+0x0404..+0x0420` speed axis
- `+0x0690` LKA minimum speed
- `+0x06AE`
- `+0x06B0..+0x06C2` timer block

## 2. AD vs AF/AH: one real changed cal block

The meaningful `AD -> AF/AH` change is:

- small metadata changes at `+0x0008..+0x0017`
- part-name byte at `+0x0025`
- big changed region at about:
  - `+0x2868..+0x335B`
- footer bytes at `+0xFFEC..+0xFFEF`

The known stock LKA tuning outside this region is unchanged.

## 3. What did NOT change

These values are identical in `AD`, `AF`, and `AH`:

### Main LKA torque table

`+0x03C4..+0x03E0`

```text
[0.0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 7.0]
```

### Speed axis

`+0x0404..+0x0420`

```text
[0.0, 10.0, 30.0, 50.0, 70.0, 90.0, 130.0, 250.0]
```

### LKA minimum speed

`+0x0690 = 10.0 m/s`

### Adjacent supervisor constant

`+0x06AE = 1500`

### Visible timer block

`+0x06B0..+0x06C2`

```text
[0, 100, 0, 1000, 2000, 1000, 500, 400, 5, 255]
```

So the visible stock LKA authority and lockout knobs are **not** what changed
between stock Transit cal revisions.

## 4. What actually changed inside `+0x2868..+0x335B`

This region is not one clean table. It contains multiple different structures.

Two kinds of changes stand out:

### A. Populated in both, but materially different format/content

Examples:

- `+0x28CF..+0x292C`
- `+0x292E..+0x2995`
- `+0x2E16..+0x2E28`
- `+0x309F..+0x30E1`
- `+0x3113..+0x3131`
- `+0x3163..+0x317B`

These are not simple scalar tweaks. They look like swapped lookup/config
sub-blocks.

### B. Present in `AD`, blanked in `AF/AH`

One especially clear case:

- `+0x327C..+0x335B`

`AF` and `AH` are all `0xFF` here, while `AD` contains real data.

That is the cleanest example of Ford removing or blanking a structured region
between stock cal revisions.

## 5. LCA-relevant overlaps

The changed `AD -> AF/AH` region overlaps offsets already documented as
LCA-related in Escape donor work:

- `+0x2FCE` — lane-change torque envelope
- `+0x327C` — centering hold torque
- `+0x33DD` — curvature rate limits

Those names come from:

- [docs/lca.md](../../docs/lca.md)
- [docs/calibration-map.md](../../docs/calibration-map.md)

### `+0x2FCE`

This offset is populated in both `AD` and `AF/AH`, but the bytes differ
materially. This looks like a real format/content change, not a checksum.

Example first 16 bytes:

```text
AD: cccd3f8000003ecccccd3fa000003fa0
AF: ffff0101000501135a5a5a010a0a0a0a
```

So `AD` and `AF/AH` are not merely toggling one value here. They are using
different structured content in the same region.

### `+0x327C`

This is the clearest change.

Example:

```text
AD: 0000003f007300a001f3037d06f21146...
AF: ffffffffffffffffffffffffffffffff...
```

Interpretation:

- `AD` carries a populated block at `+0x327C`
- `AF/AH` blank that block completely

### `+0x33DD`

This one is `0xFF` in both `AD` and `AF/AH`, so it is **not** part of the
stock Transit revision difference here.

## 6. Comparison against Escape 2022

The changed region is **not** a clean Escape-style LCA donor block.

Examples:

- `+0x327C` in Escape is populated with clean BE float-looking content
- `+0x327C` in `AD` is populated, but not in the same form
- `+0x327C` in `AF/AH` is blank

So the best current read is:

- `AD` contains an older/different Transit-specific populated block
- `AF/AH` removed or blanked at least part of that block
- neither one is just “Escape donor data already hiding in Transit”

## Best current conclusion

What actually changed between Transit stock cals is **not**:

- the visible LKA torque table
- the visible LKA timer block
- the visible LKA min-speed gate

What changed is:

- a large mid-cal structured region at `+0x2868..+0x335B`
- including a clearly populated-in-`AD` but blank-in-`AF/AH` block at
  `+0x327C..+0x335B`
- and a differently encoded/populated block around `+0x2FCE`

Plain-language summary:

- `AD` carries extra or different mid-cal assist data
- `AF/AH` standardize on a newer family
- Ford appears to have removed or blanked at least one structured assist block
  in later Transit stock cals

## 7. Best current structural map of `+0x2868..+0x335B`

This region is **not one table**. Best current read is that it is a packed
assist-data neighborhood made of several sub-block families.

### `+0x2868..+0x29B7`

Mostly **u16 / fixed-point lookup content**, not clean human-readable floats.

Examples from `AF`:

```text
0x2868: [512, 3277, 3277, 2000, 65434, 102, 90, 102]
0x2878: [3277, 102, 154, 1280, 2880, 1920, 9600, 11520]
0x2888: [12800, 218, 256, 26214, 839, 278, 383, 1000]
```

Best current interpretation:

- breakpoint tables
- fixed-point gains
- packed curve inputs / thresholds

### `+0x29B8..+0x2A47`

Clean **scalar/gain cluster** with directly readable floats.

`AD` examples:

```text
10, 2500, -2500, 20, 3, 0.1, 0, 150,
0.8, 0.5, 30, -0.8, -0.5, 1000, 0.1, 0.1,
6, 5, -5, 2, 1, 0.1, 1, 0.5, 2.5, 0, -2, 0.2, 0, 0.8,
0.8, 20, 0.002, 0, 2, 0.6
```

`AF/AH` examples:

```text
2500, 10, 20, 3, 0.1, 0, 150, 0.8,
0.5, 30, -0.8, -0.5, 1000, 0.1, 0.1, 6,
5, -5, 2, 1, 0.1, 1, 0.5, 0.5, 2.5, 0, -2, 0.2, 0, 0.8,
1.8, 1.8, 1.8, 2.8, 0.8, 20
```

Best current interpretation:

- supervisor / hysteresis / gain constants
- likely part of centering / assist enable-yield behavior

### `+0x2A48..+0x2E13`

Mostly **float table family** with multiple obvious lookup sequences.

Examples from `AF`:

```text
1.0, 1.0, 1.0, 10.0
0.002, 0.0, 2.0, 0.6
0.7, 2.8, 0.3, 300.0
0.03, 0.3, 0.015, 30.0
1.0, 0.2, 0.05, 10.0
800.0, 50.0, 0.7, 15.0
5.0, 3.0, 1.72, 2.5
0.8, 0.05, 63.0, 5.0
```

Later in the same block:

```text
3.0, 15.0, 20.0, 100.0, 400.0, 1400.0, 3600.0
10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 100.0, 150.0
0.4, 0.2, 0.1333, 0.1, 0.08, 0.0667, 0.0571, 0.05, 0.04
7.0, 18.0, 30.0, 60.0, 100.0, 160.0, 200.0
```

Best current interpretation:

- multiple paired lookup curves
- axes plus gains / authority shaping

### `+0x2E14..+0x2FCD`

Mixed opaque structured block.

`AF` here no longer looks like clean float tables. It looks more like packed
fixed-point / flags / counts:

```text
0x2E14: [33536, 32, 64225, 64225, 13107, 13107, 13107, 13107]
0x2E24: [13107, 13107, 2048, 2048, 2048, 2048, 2048, 2048]
```

Best current interpretation:

- packed supervisor/config data
- mixed units, not one simple float table

### `+0x2FCE..+0x327B`

Structured assist-envelope block, and clearly one of the places Ford changed
families.

Examples:

```text
AD: cccd3f8000003ecccccd3fa000003fa0...
AF: ffff0101000501135a5a5a010a0a0a0a...
```

This overlaps the documented LCA region:

- `+0x2FCE` = lane-change torque envelope

Best current interpretation:

- same broad feature purpose
- different encoding/layout between `AD` and `AF/AH`

### `+0x327C..+0x335B`

This is the clearest sub-block in the whole diff.

- `AD`: populated
- `AF/AH`: all `0xFF`

And `AD` is **not random** here. Parsed as big-endian u16 rows, it becomes a
duplicated lookup family:

```text
0x327C: [0, 63, 115, 160, 499, 893, 1778, 4422]
0x328C: [0, 63, 115, 160, 499, 893, 1778, 4422]
0x329C: [0, 78, 140, 193, 619, 937, 1521, 3748]
0x32AC: [0, 75, 135, 186, 572, 847, 1249, 2583]
0x32BC: [0, 75, 135, 184, 554, 809, 1164, 2322]
0x32CC: [0, 76, 134, 183, 524, 776, 1126, 2218]
0x32DC: [0, 76, 134, 181, 495, 741, 1090, 2151]
0x32EC: [0, 76, 133, 179, 476, 706, 1046, 1978]
```

Then the family repeats at `+0x32FC..+0x335B`.

This overlaps the documented LCA region:

- `+0x327C` = centering hold torque

Best current interpretation:

- old lookup table family
- probably an assist/centering-hold envelope in packed integer form
- explicitly blanked by Ford in `AF/AH`

## 8. Best plain-language answer

So, what is `+0x2868..+0x335B`?

Best current answer:

- a **packed assist-data neighborhood**
- not one thing
- contains:
  - fixed-point breakpoint/gain tables
  - readable scalar gain/hysteresis constants
  - multiple float lookup families
  - a changed lane-change/assist envelope block
  - an **AD-only** old lookup-table tail at `+0x327C..+0x335B` that Ford later
    blanked

Most important practical takeaway:

- Ford did **not** revise the visible LKA torque/timer knobs here
- Ford revised a **deeper centering/LCA-related subregion** instead
