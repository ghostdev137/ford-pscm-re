# Transit / Escape / F-150 calibration comparison — first pass

**Date:** 2026-04-16

This is a calibration-only comparison across the stock PSCM cal files currently in the repo, focused on LKA-related tables and supervisor-looking timer / hysteresis neighborhoods.

Files compared:

- Transit 2025: `LK41-14D007-AD`, `-AF`, `-AH`
- Escape 2022: `LX6C-14D007-ABH`
- Escape 2024: `PZ11-14D007-EBC`
- F-150 2022: `ML34-14D007-BDL`
- F-150 2021: `ML34-14D007-EDL`

## TL;DR

Three things stand out immediately:

1. **Transit stock revisions AD/AF/AH are identical in the known LKA regions.**
2. **Escape 2022 shares the same main LKA torque curve and speed axis as Transit, but uses a stronger companion table.**
3. **Escape 2022 has a second mixed timer/hysteresis-looking cluster that Transit does not, and it partially resembles the F-150 timer-neighbor motif.**

The most actionable result is item 2: **Transit’s weak feel is probably not just the main torque curve.** The companion/shaping table differs too.

## Extraction summary

Raw cal payloads extracted from the VBFs:

- Transit AD/AF/AH: `65520` bytes each
- Escape 2022 ABH: `65520` bytes
- Escape 2024 EBC: `63744` bytes per bank, dual-bank layout
- F-150 BDL/EDL: `195584` bytes each

Immediate consequence:

- Transit 2025 and Escape 2022 are directly comparable as same-size big-endian cal families
- Escape 2024 is a different layout
- F-150 is a different platform and little-endian; use it only for motif comparison, not direct offset transplanting

## 1. Transit stock LKA regions are unchanged across AD / AF / AH

The following Transit regions are byte-stable across all three stock cal revisions:

### Main LKA torque curve

Offset:
- `+0x03C4..+0x03E3`

All Transit AD / AF / AH:

```text
[0.0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 7.0]
```

### Companion / shaping table

Offset:
- `+0x03E4..+0x0403`

All Transit AD / AF / AH:

```text
[0.8, 0.8, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0]
```

### Speed axis

Offset:
- `+0x0404..+0x0423`

All Transit AD / AF / AH:

```text
[0.0, 10.0, 30.0, 50.0, 70.0, 90.0, 130.0, 250.0]
```

### LKA minimum speed

Offset:
- `+0x0690`

All Transit AD / AF / AH:

```text
10.0 m/s
```

### Transit supervisor / timer block

Offset:
- `+0x06A0..+0x06C3`

All Transit AD / AF / AH are byte-identical here, including:

- `+0x06AE = 1500`
- `+0x06B0..+0x06C2 = [0, 100, 0, 1000, 2000, 1000, 500, 400, 5, 255]`

So there is no stock-revision clue inside Transit itself. Whatever makes Transit weak is not a late AD/AF/AH regression in these known regions.

## 2. Escape 2022 shares the main LKA curve, but not the companion table

The strongest same-platform match is:

- Transit main LKA curve at `+0x03C4`
- Escape 2022 main LKA curve at `+0x06BC`

### Main curve

Transit `+0x03C4..+0x03E3`:

```text
[0.0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 7.0]
```

Escape 2022 `+0x06BC..+0x06DB`:

```text
[0.0, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 7.0]
```

### Speed axis

Transit `+0x0404..+0x0423`:

```text
[0.0, 10.0, 30.0, 50.0, 70.0, 90.0, 130.0, 250.0]
```

Escape 2022 `+0x06FC..+0x071B`:

```text
[0.0, 10.0, 30.0, 50.0, 70.0, 90.0, 130.0, 250.0]
```

### Companion table

Transit `+0x03E4..+0x0403`:

```text
[0.8, 0.8, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0]
```

Escape 2022 `+0x06DC..+0x06FB`:

```text
[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
```

## Practical meaning

This is the cleanest cross-vehicle clue so far.

Transit and Escape use:

- the **same headline LKA torque curve**
- the **same speed axis**

but Escape does **not** attenuate the first three bins with `0.8 / 0.8 / 0.9`.

That means a stronger Escape feel can come from the companion table alone, even before changing the headline torque table.

Plain-language read:

- Transit: low/mid bins are slightly derated before full authority
- Escape 2022: full weight from the start

If the goal is to raise Transit authority while staying closer to a Ford-stock envelope, this companion-table difference is a better clue than blindly pushing the torque curve higher.

## 3. Escape 2022 has a second mixed LKA/LCA-looking supervisor block

Escape 2022 has another structured region that stands out:

### Region A: `+0x09A0..+0x09E3`

Decoded as big-endian float32 where sensible, the sequence is:

```text
0x09A0: [3.0, 0.0, 0.0, 1.0]
0x09B0: [0.0, 0.5, 2.0, 10.0]
0x09C0: [2.0, 21.0, 270.0, 90.0]
0x09D0: [2.0, 6.0, <u16/u8 cluster begins>]
0x09E0: [100, 5, 255, 1, ...]
```

This is not byte-identical to Transit, but it reuses several numbers that also appear in Transit’s known LKA neighborhood:

- `3.0`
- `0.5`
- `10.0`
- `270.0`
- `90.0`
- `2.0`
- `6.0`

Transit has a mixed region nearby at `+0x0680..+0x06C3`, but not in the same order and not with the same extra fields.

Best current interpretation:

- same broad feature family
- different struct layout or different revision packing
- worth treating as a candidate **gate / supervisor config block**, not just random floats

### Region B: `+0x2E14..+0x2E3B`

Escape 2022 also has a much more explicit timer/hysteresis-looking cluster:

```text
0x2E14: 10000, 5000
0x2E1C: 10000, 5000
0x2E20: 1500, 300, 257, 768
0x2E28: 0.75, 0.064
0x2E30: 3.25, 10000, 300, 1500
0x2E3C: 0.349066
0x2E40: 0.4, 0.1, 0.02, 0.8
```

This exact motif does **not** appear anywhere in Transit AD / AF / AH.

## Why this matters

Earlier Transit work focused heavily on the visible `+0x06B0..+0x06C2` timer table because it was obvious and easy to patch.

Escape 2022 suggests Ford may have a **second layer** of LKA/LCA supervisor tuning elsewhere:

- timers
- debounce / hysteresis
- small state bytes
- angle / confidence / override-related floats

That is a better place to look for:

- driver-override sensitivity
- re-arm behavior
- hands-on / hands-off hysteresis

than assuming everything lives in the Transit `+0x06B0` table.

## 4. Escape 2022 partially resembles the F-150 timer-neighbor motif

F-150 BDL / EDL both contain the known timer neighborhood:

```text
0x07ADC..0x07AEF:
10000, 10000, 1500, 300, 257, 3, 256, 257, 0, 1
```

Escape 2022 does **not** match this exactly, but it has a partial analogue:

```text
10000, 5000, 10000, 5000, 1500, 300, ...
```

That matters because the F-150 strategy work already showed that Ford likes to keep:

- the obvious timer entries
- the 1500 / 300 / 257 / small-state neighbors

in one mixed supervisor struct.

Transit’s visible `+0x06B0` cluster does **not** look like that. Escape’s `+0x2E14` region does.

So the F-150 comparison supports this hypothesis:

> Escape’s `+0x2E14..+0x2E4F` region is likely a real supervisor / hysteresis / timer block relevant to LKA/LCA behavior.

## 5. Escape 2024 is a different layout

Escape 2024 `PZ11-14D007-EBC`:

- extracts as `63744` bytes per bank
- appears as a dual-bank image
- does **not** contain the Transit 2025 LKA curve bytes
- does **not** contain the Transit timer-cluster bytes

Conclusion:

- do not use Escape 2024 as a first-pass donor for Transit 2025 cal diffing
- Escape 2022 is the better comparison target

## Best current calibration candidates from cross-vehicle diffing

If the goal is to make Transit LKA stronger without wandering blindly, the best current candidates are:

### 1. Transit companion table at `+0x03E4..+0x0403`

Reason:

- Escape 2022 uses the same main torque curve
- but its companion table is flat `1.0`
- Transit attenuates low/mid bins

This is the cleanest stock-to-stock explanation for some of the authority gap.

### 2. Escape 2022 mixed block at `+0x09A0..+0x09E3`

Reason:

- reuses several Transit gate-like constants
- looks like a packed feature supervisor block
- may contain min-speed / engage / authority / timing terms in a more advanced layout

### 3. Escape 2022 timer/hysteresis-looking block at `+0x2E14..+0x2E4F`

Reason:

- contains obvious timer-like values
- contains the same 1500 / 300 style neighbors seen in F-150
- absent from Transit
- plausible location for stronger override / hysteresis behavior

## Bottom line

Cross-vehicle cal comparison already gives one strong answer:

> **Transit is not weaker only because of the main LKA torque table.**

Transit and Escape 2022 share the same main torque curve, but Escape uses a stronger companion table and appears to carry richer supervisor/hysteresis data elsewhere in cal.

That shifts the next patch targets from:

- only `+0x03C4`

to:

- `+0x03E4..+0x0403` on Transit
- and Escape-only supervisor-looking regions as donor clues

## Raw extracted files used

- `/tmp/calcmp_extract/transit_ad.bin`
- `/tmp/calcmp_extract/transit_af.bin`
- `/tmp/calcmp_extract/transit_ah.bin`
- `/tmp/calcmp_extract/escape_2022_abh.bin`
- `/tmp/calcmp_extract/escape_2024_ebc.bin`
- `/tmp/calcmp_extract/f150_2022_bdl.bin`
- `/tmp/calcmp_extract/f150_2021_edl.bin`
