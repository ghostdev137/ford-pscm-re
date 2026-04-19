# Transit 2025 compare — `AG strategy + AD cal` vs `AH strategy + AD cal`

**Date:** 2026-04-16

Compared flash sets:

- `KK21-14D003-AG` strategy + `LK41-14D007-AD` cal
- `KK21-14D003-AH` strategy + `LK41-14D007-AD` cal

This is the cleanest stock Transit compare for isolating strategy changes,
because the cal is held constant.

Related notes:

- [transit_2025_cal_diff_findings.md](./transit_2025_cal_diff_findings.md)
- [transit_2025_strategy_compare.md](./transit_2025_strategy_compare.md)

## TL;DR

Holding `AD` cal constant, `AG` and `AH` are **not** small strategy tweaks.

What changes:

- `block0_strategy` is heavily rewritten:
  - `822,609` differing bytes
- `block2_ext` is also materially rewritten:
  - `52,883` differing bytes
- the biggest block0 churn is in the late `0x010Exxxx` bank
- the biggest block2 churn is concentrated in:
  - `0x21018000..0x21024000`

What does **not** change:

- the `AD` cal itself
- so any behavior difference between these two flash sets is a **strategy**
  difference, not a torque-table/timer-table difference in cal

Best current practical read:

- `AH + AD` is not "longer" than `AG + AD`
- it is a denser, reorganized strategy build with a reworked late-bank logic
  neighborhood and a heavily changed late block2 table/data neighborhood

## 1. The cal is identical in both sets

Both sets use:

- `LK41-14D007-AD`

So these known stock values are the same in both:

- `+0x03C4..+0x03E0` main LKA torque table
- `+0x0404..+0x0420` speed axis
- `+0x0690` minimum speed
- `+0x06AE`
- `+0x06B0..+0x06C2` visible timer block
- the AD-only populated tail at `+0x327C..+0x335B`

This matters because it means:

- if `AG + AD` and `AH + AD` behave differently on the vehicle, the cause is
  in strategy, not in cal

## 2. Size compare

### Compressed VBF size

- `AG` strategy VBF: `825,049` bytes
- `AH` strategy VBF: `827,724` bytes

Difference:

- `AH` is `2,675` bytes larger

### Decompressed block size

`block0_strategy.bin`:

- `AG`: `1,048,560`
- `AH`: `1,048,560`

So the real strategy block is not longer in `AH`. It just compresses worse.

### Actual used end

Both `AG` and `AH` carry meaningful non-`00`/non-`FF` data through the same
last offset:

- `used_through = 0x0FFFE3`

Both also have the same trailing tail shape:

- last `12` bytes are only `0x00/0xFF`

So `AH` is not "more code at the end." It is different inside the same fixed
address space.

## 3. Strategy block0: large rewrite

Pairwise diff:

- `AG -> AH block0_strategy`: `822,609` differing bytes

This is not one small patch. It is a broad rebuild.

### Same-seed recursive-descent coverage

Using the same pruned Ghidra seed set for both:

- `AG`
  - visited instructions: `69,801`
  - code bytes covered: `224,474`
  - functions built: `1,666`
- `AH`
  - visited instructions: `64,200`
  - code bytes covered: `212,098`
  - functions built: `1,671`

This should be treated as a **compare aid**, not an absolute truth source.
But it does support the idea that `AH` is reorganized enough that the same seed
set walks a meaningfully different code graph.

## 4. The highest-signal block0 change is the late `0x010Exxxx` bank

This is where the strategy difference really stands out.

### `0x010E1000`

The old repo note about "removed code" is only partly relevant here.

In this exact pair:

- `AG`: live code/data page
- `AH`: also live, but heavily changed

Window diff over `0x200` bytes:

- `AG -> AH`: `498 / 512`

So for `AG vs AH`, the story is not removal yet. It is heavy rewrite.

### `0x010E3000`

This window is almost entirely different:

- diff over `0x400` bytes:
  - `979 / 1024`

This is a stronger signal than `0x010E1000`, because it points to a real logic
neighborhood that was rebuilt, not just a page later zeroed in `AL/AM`.

### Late-bank page density shift

#### `AG`

Notable nontrivial-byte density:

- `0x010E8000`: `1473`
- `0x010E9000`: `378`
- `0x010EA000`: `357`
- `0x010EC000`: `102`
- `0x010ED000`: `4096`

#### `AH`

Notable nontrivial-byte density:

- `0x010E8000`: `3489`
- `0x010E9000`: `1752`
- `0x010EA000`: `375`
- `0x010EB000`: `389`
- `0x010EC000`: `101`
- `0x010ED000`: `4096`

Interpretation:

- `AH` carries much more live-looking content than `AG` in:
  - `0x010E8000`
  - `0x010E9000`
- `AH` also has a live `0x010EB000` page where `AG` is effectively not
  participating in the same way

That is consistent with a late-bank logic/data reorganization, not a simple
feature deletion.

## 5. Concrete changed function neighborhoods in block0

Using the same recursive-descent compare, the following entry points in the
late bank changed materially between `AG` and `AH`.

### Shared starts with very different reachable size

- `0x010E190E`
  - `AG = 182`
  - `AH = 51`
- `0x010E1FF6`
  - `AG = 83`
  - `AH = 41`
- `0x010E23F8`
  - `AG = 13`
  - `AH = 89`
- `0x010E2EB8`
  - `AG = 196`
  - `AH = 37`
- `0x010E3218`
  - `AG = 22`
  - `AH = 13`
- `0x010E6116`
  - `AG = 24`
  - `AH = 52`
- `0x010E679C`
  - `AG = 195`
  - `AH = 34`
- `0x010E69EC`
  - `AG = 184`
  - `AH = 36`
- `0x010E70E8`
  - `AG = 51`
  - `AH = 176`
- `0x010E7A12`
  - `AG = 158`
  - `AH = 59`
- `0x010E7FE6`
  - `AG = 23`
  - `AH = 2368`
- `0x010EF0D6`
  - `AG = 677`
  - `AH = 1979`

### AG-only late entry points

- `0x010EC012` (`576`)
- `0x010EC898` (`1207`)
- `0x010ED5BA` (`902`)
- `0x010EDCC6` (`1361`)
- `0x010EEED0` (`130`)
- `0x010EF620` (`6456`)
- `0x010F2890` (`4910`)
- `0x010F4EEC` (`1864`)
- `0x010F5D7C` (`303`)
- `0x010F5FDA` (`1021`)
- `0x010F67D4` (`309`)
- `0x010F6A3E` (`14776`)
- `0x010FDDAE` (`4377`)

### AH-only late entry points

- `0x010F004C` (`136`)
- `0x010F015C` (`63`)
- `0x010F01DA` (`71`)
- `0x010F0268` (`233`)
- `0x010F043A` (`112`)
- `0x010F051A` (`46`)
- `0x010F0576` (`10`)
- `0x010F058A` (`265`)
- `0x010F079C` (`8521`)
- `0x010F4A2E` (`14958`)
- `0x010FBF0A` (`3842`)
- `0x010FDD0E` (`191`)
- `0x010FDE8C` (`4265`)

Important caveat:

- the recursive-descent tool is best used here as a **shape detector**
- some of these very large late entries sit in sparse/`0xFF`-heavy regions and
  should not be treated as fully trusted function boundaries

The safe conclusion is still:

- `AG` and `AH` do not share the same late-bank control-flow layout

## 6. Block2 is also materially different, and the change is localized

Pairwise diff:

- `AG -> AH block2_ext`: `52,883` differing bytes

Unlike block0, this change is not spread uniformly.

### Diff concentration by 4 KB page

Earlier pages are lightly touched.

Examples:

- `0x20FF0000`: `47` diff bytes
- `0x20FFC000`: `185`
- `0x21001000`: `270`

The real concentration is later:

- `0x21018000`: `2015`
- `0x21019000`: `3961`
- `0x2101A000`: `3921`
- `0x2101B000`: `3964`
- `0x2101C000`: `4023`
- `0x2101D000`: `4009`
- `0x2101E000`: `4009`
- `0x2101F000`: `3996`
- `0x21020000`: `4026`
- `0x21021000`: `4036`
- `0x21022000`: `3964`
- `0x21023000`: `3947`
- `0x21024000`: `3826`

That is essentially a contiguous rewritten neighborhood from:

- `0x21018000` through `0x21024000`

### Largest contiguous changed runs in block2

Top runs:

- `0x21021755`, len `727`
- `0x2101E987`, len `476`
- `0x2101913E`, len `437`
- `0x2101FDA5`, len `409`
- `0x210243F7`, len `387`

Interpretation:

- `AG` vs `AH` block2 difference is real and concentrated
- this looks more like a rewritten late ext/data neighborhood than a few
  version/footer updates

## 7. Best practical interpretation

Comparing:

- `AG strategy + AD cal`
- `AH strategy + AD cal`

lets you isolate **strategy-only** behavior change.

That is the most important take-away.

If the vehicle behaves differently between these two:

- it is not because of:
  - LKA torque table
  - LKA visible timer table
  - `+0x06AE`
  - the AD-only `+0x327C` cal tail changing

It is because:

- `AG` and `AH` strategy are genuinely different builds
- the biggest strategy delta is in late block0 `0x010Exxxx`
- and there is a second major rewritten neighborhood in block2
  `0x21018000..0x21024000`

## Best current conclusion

For the exact pair:

- `AG + AD`
- `AH + AD`

the correct summary is:

- **same cal**
- **different strategy**
- **same nominal block length**
- **same used end**
- **large internal rewrite**

And the deepest useful conclusion from static compare is:

- `AH` is not simply `AG` with a few patches
- it is a reworked strategy family member with substantial late-bank changes in
  both block0 and block2

That makes this pair the right stock-vs-stock test if the goal is:

- hold cal constant
- vary only strategy
- observe whether vehicle behavior changes
