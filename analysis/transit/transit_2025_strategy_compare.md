# Transit 2025 strategy compare — AG/AH/AL/AM vs the AD-only cal tail

**Date:** 2026-04-16

Compared strategy files:

- `KK21-14D003-AG.VBF`
- `KK21-14D003-AH.VBF`
- `KK21-14D003-AL.VBF`
- `KK21-14D003-AM.VBF`

Related cal note:

- [transit_2025_cal_diff_findings.md](./transit_2025_cal_diff_findings.md)

## TL;DR

The Transit strategy changes are real, but they do **not** reduce to one old
"removed code" site at `0x010E1000`.

What the compare actually shows:

- `0x010E1000` was progressively gutted, but that is only one visible symptom
- the broader late `0x010Exxxx` strategy neighborhood changes heavily across
  revisions
- the function slot at `0x010E3218` is **different in all four revisions**
- there are **no direct absolute references** in strategy to:
  - `0x00FD2FCE`
  - `0x00FD327C`
  - `0x00FD33DD`
- so the AD-only cal tail at `+0x327C..+0x335B` still looks
  centering/LCA-related, but this compare does **not** yet prove a specific
  strategy site that stopped reading it

Best current read:

- the strategy evidence supports a real LCA/centering logic-family churn in the
  late `0x010Exxxx` bank
- but it does **not** yet close the "AG used the AD-only `+0x327C` tail, later
  builds stopped" hypothesis

## 1. Direct absolute cal references: none found

Searched each decompressed strategy block for little-endian absolute addresses:

- `0x00FD2FCE`
- `0x00FD327C`
- `0x00FD33DD`

Result:

- `AG`: none
- `AH`: none
- `AL`: none
- `AM`: none

Interpretation:

- if these cal regions are used from strategy, they are not referenced as clean
  embedded absolute addresses in block0
- that matches the older repo conclusion that Transit cal reads are likely
  GP-relative / indirect / runtime-derived rather than obvious literals

## 2. `0x010E1000`: yes, it was removed

This is the old "removed code" site already mentioned elsewhere in the repo.

The compare confirms:

- `AG`: real code bytes present
- `AH`: different nonzero bytes still present
- `AL`: page is mostly zeroed / placeholder
- `AM`: page is fully zeroed in the sampled window

Window diff at `0x010E1000` over `0x200` bytes:

- `AG -> AH`: `498 / 512`
- `AG -> AL`: `444 / 512`
- `AG -> AM`: `446 / 512`
- `AH -> AL`: `431 / 512`
- `AH -> AM`: `433 / 512`
- `AL -> AM`: `26 / 512`

So the earlier repo summary was directionally right:

- `AG` had code there
- `AH` already changed it heavily
- `AL/AM` mostly removed it

But that is **not** the whole strategy story.

## 3. `0x010E3218`: the same slot is different in all four revisions

This is the more important compare result.

The window starting at `0x010E3218` is not stable:

- `AG`: one code body
- `AH`: a different code body
- `AL`: different again
- `AM`: different again

Window diff at `0x010E3000` over `0x400` bytes:

- `AG -> AH`: `979 / 1024`
- `AG -> AL`: `981 / 1024`
- `AG -> AM`: `979 / 1024`
- `AH -> AL`: `970 / 1024`
- `AH -> AM`: `974 / 1024`
- `AL -> AM`: `982 / 1024`

That means:

- this is not one stable function with a few patch bytes
- this entire code neighborhood was rebuilt/reorganized across revisions

This matters more than the `0x010E1000` note because it points to a real logic
cluster that kept changing, not just dead code getting zeroed.

## 4. Late `0x010Exxxx` bank: real family split

The strongest grouped change is in the late `0x010Exxxx` region.

Window diff at `0x010EB000` over `0x1800` bytes:

- `AG -> AH`: `1028 / 6144`
- `AG -> AL`: `6050 / 6144`
- `AG -> AM`: `6080 / 6144`
- `AH -> AL`: `5486 / 6144`
- `AH -> AM`: `5517 / 6144`
- `AL -> AM`: `1264 / 6144`

Interpretation:

- `AG` and `AH` are relatively close here
- `AL` and `AM` are relatively close here
- but the `AG/AH` family is very far from the `AL/AM` family

So there is a real late-revision strategy split in this neighborhood.

## 5. 4 KB page grouping in the late bank

Looking at `0x010E0000..0x010EFFFF` page-by-page:

- `0x010E0000`:
  - `AG`
  - `AH`
  - `AL = AM`
- `0x010E1000`:
  - `AG`
  - `AH`
  - `AL`
  - `AM`
- `0x010E2000` through `0x010EC000`:
  - all four are distinct page images
- `0x010ED000`:
  - `AG`
  - `AH`
  - `AL = AM`
- `0x010EE000`:
  - `AG = AH`
  - `AL`
  - `AM`
- `0x010EF000`:
  - `AG = AH`
  - `AL`
  - `AM`

This is a cleaner way to say what changed:

- there is broad logic churn across the late `0x010Exxxx` bank
- some of that churn groups as `AG/AH` vs `AL/AM`
- some pages are unique in every revision

So the strategy evolution is not just a one-off patch site.

## 6. Largest contiguous changed runs

Top runs between revisions:

### `AG -> AH`

- `0x010EA92F`, len `1315`
- `0x01064466`, len `992`
- `0x010EA40B`, len `939`

### `AH -> AL`

- `0x010ED000`, len `4097`
- `0x010EF000`, len `4096`
- `0x010EB40D`, len `2137`
- `0x010EC303`, len `1085`
- `0x010EBC67`, len `926`

### `AH -> AM`

- `0x010ED000`, len `4097`
- `0x010EF000`, len `4096`
- `0x010EB40D`, len `2377`
- `0x010EC3F3`, len `1085`
- `0x010EC0B0`, len `834`

This again points to the late `0x010EBxxx..0x010EFFFF` area as the most
interesting strategy neighborhood, not just `0x010E1000`.

## 7. What this says about the AD-only `+0x327C` cal block

From the cal diff note:

- `AD` alone has populated data at `+0x327C..+0x335B`
- `AF/AH` blank it with `0xFF`
- that block overlaps the documented Transit/Escape donor region:
  - `+0x327C` = centering hold torque

What the strategy compare adds:

- there **is** real logic churn in a likely assist-related late strategy bank
- but there is **not** yet a clean "this exact function disappeared when the
  `+0x327C` tail was blanked" proof
- the earlier `0x010E1000` removal is too narrow and likely not the main
  explanation
- the better candidate region is the wider late bank:
  - `0x010E3000..0x010ECFFF`
  - especially `0x010EBxxx..0x010EFFFF`

So the safest current wording is:

- the AD-only tail still looks like old centering/LCA-related data
- the strategy side also changed in a compatible late-bank logic neighborhood
- but the cal/strategy link is not yet closed function-by-function

## 8. What did NOT show up

These checks came back negative:

- no direct embedded absolute refs to Transit cal offsets
- no copy of the AD-only `+0x327C` row bytes inside strategy
- no copy of those row bytes inside block2

So we should **not** claim:

- that block0 literally embeds the AD tail
- that block2 took over those tables
- that `0x010E1000` alone was the LCA handler

## Best current conclusion

If the question is:

> "Does the Transit strategy compare support the idea that `AD` had extra
> centering/LCA-related logic/data that later revisions lost?"

The answer is:

- **yes, weak-to-moderate support**

Why:

- the cal side shows a real AD-only structured tail at `+0x327C..+0x335B`
- the strategy side shows real late-bank logic churn, especially around
  `0x010E3218` and `0x010EBxxx..0x010EFFFF`

But if the question is:

> "Did we prove which exact strategy function reads `+0x327C`?"

The answer is:

- **no**

That is still open.

## Best next step

The next useful pass is not more raw byte diffing. It is:

1. build comparable recursive-disasm outputs for `AG`, `AH`, `AL`, and `AM`
2. isolate the late-bank functions present in `AG/AH` but removed/reworked in
   `AL/AM`
3. trace those functions for indirect cal-read motifs rather than literal cal
   addresses

That is the shortest path to closing whether the AD-only `+0x327C` tail was
actually live in early Transit strategy.
