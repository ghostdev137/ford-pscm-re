# Transit `AG + AD` vs `AH + AD` against Escape 2022 LCA donor strategy

**Date:** 2026-04-16

Compared:

- Transit `KK21-14D003-AG` strategy + `LK41-14D007-AD` cal
- Transit `KK21-14D003-AH` strategy + `LK41-14D007-AD` cal
- Escape 2022 donor strategy `LX6C-14D003-AL`

Purpose:

- determine whether one of the stock Transit strategy revisions looks like it
  still has active LCA / lane-centering support while another does not

## TL;DR

I do **not** see evidence that one of `AG` or `AH` has active LCA while the
other does not.

The strongest result is at the CAN routing layer:

- Escape 2022 has a real `0x3D3` PDU descriptor entry in strategy
- Transit `AG` and `AH` do **not**
- Transit `AG` and `AH` are identical in the relevant PDU table neighborhood

So the safest current answer is:

- neither `AG` nor `AH` appears to retain the Escape-style active LCA receive
  path
- `AH` is slightly closer to Escape overall in some late block0/block2
  neighborhoods, but not in a way that proves active LCA

## 1. Escape has the active `0x3D3` PDU entry

In Escape 2022 strategy block0, the PDU descriptor neighborhood around
`0x0100CE98` contains:

```text
0x0100CE90  03d7011701080000
0x0100CE98  03d3011801080000   <- 0x3D3 present
0x0100CEA0  03ca011901080000
0x0100CEA8  03b3011a01080000
0x0100CEB0  03a8011b01080000
```

This is the direct routing-layer evidence that the donor strategy actually
registers LCA traffic.

## 2. Transit `AG` and `AH` are identical at the same routing layer

In both Transit `AG` and `AH`, the known PDU descriptor neighborhood around
`0x01002B50` is the same:

```text
... 0082012503080000
... 0085012603080000
... 03cc012703080000
... 0417012803080000
... 05b5012903080000
... 060e012a03080000
... 060f012b03080000
... 063a012c03080000
... 063b012d03080000
... 063d012e03080000
```

And in the nearby RX table region both Transit revisions contain:

- `0x3CA`
- `0x3B3`

but **not**:

- `0x3D3`
- `0x3D6`

For this exact question, this is the most important result:

- `AG` and `AH` do not differ at the obvious LCA message registration layer

## 3. What Transit actually has in the PDU neighborhood

Using the same table parser on Transit `AG` and `AH`:

- `0x3CA` present
- `0x3B3` present
- `0x3D3` absent
- `0x3D6` absent

And the result is the same in both revisions.

So if one stock Transit revision had active LCA while the other did not, the
most obvious place to show it would be this table. It does not.

## 4. Raw `0x3D3` / `0x3D6` constants still exist in both Transit revisions

Both Transit strategies still contain raw `0x3D3` / `0x3D6` byte patterns in
other code/data regions.

Examples:

### Transit `AG`

- `0x3D3` hits: `15`
- `0x3D6` hits: `10`

### Transit `AH`

- `0x3D3` hits: `9`
- `0x3D6` hits: `10`

Interpretation:

- both revisions still carry some dormant/shared code or data motifs related to
  these IDs
- but because neither one registers `0x3D3` in the PDU table, these hits are
  not enough to claim active LCA

This matches the earlier Transit conclusion:

- LCA-related fragments may still exist
- active routing/enable is still missing

## 5. Which Transit revision is closer to Escape overall?

### Whole-block diff against Escape

#### Block0

- Escape vs `AG`: `927,518` differing bytes
- Escape vs `AH`: `921,622` differing bytes

#### Block2

- Escape vs `AG`: `244,571` differing bytes
- Escape vs `AH`: `244,464` differing bytes

So:

- `AH` is slightly closer to Escape overall

But the margin is small, and by itself it does **not** imply active LCA.

## 6. Late block0 bank: `AH` trends a bit closer to Escape

Comparing page-by-page in the late `0x010Exxxx` bank:

Pages where `AH` is closer to Escape:

- `0x010E0000`
- `0x010E1000`
- `0x010E2000`
- `0x010E4000`
- `0x010E5000`
- `0x010E7000`
- `0x010EA000`
- `0x010EB000`
- `0x010EC000`

Pages where `AG` is closer:

- `0x010E3000`
- `0x010E6000`
- `0x010E8000`
- `0x010E9000`

Interpretation:

- `AH` is somewhat closer to the donor in more of the late-bank pages
- but not uniformly
- and not at the routing-layer feature gate that matters most

## 7. Late block2 donor neighborhood: `AH` also trends closer

In the highly changed block2 donor neighborhood `0x21018000..0x21024000`,
`AH` is closer to Escape in more pages than `AG`.

Examples where `AH` is closer:

- `0x21018000`
- `0x2101A000`
- `0x2101B000`
- `0x2101C000`
- `0x2101D000`
- `0x2101E000`
- `0x21020000`
- `0x21023000`
- `0x21024000`

Pages where `AG` wins:

- `0x21019000`
- `0x2101F000`
- `0x21021000`
- `0x21022000`

Again:

- this makes `AH` the slightly more donor-like strategy of the two
- but still not enough to call it "the one with LCA"

## Best current conclusion

If the question is:

> "Does one of the stock Transit strategies appear to have active LCA while the
> other does not?"

Best current answer:

- **no**

Why:

- Escape has an actual `0x3D3` PDU entry
- Transit `AG` does not
- Transit `AH` does not
- Transit `AG` and `AH` are identical in that routing neighborhood

If the question is:

> "Which stock Transit revision is a little closer to the Escape donor
> strategy?"

Best current answer:

- **`AH`**

But only slightly, and not in the one place that would let us say LCA is
actually present.

## Practical read

The cleanest interpretation right now is:

- `AG`: no active LCA routing
- `AH`: no active LCA routing
- `AH` is a somewhat more donor-like later build
- the real gating problem is still strategy-level routing/enable, not just the
  presence of LCA-ish constants elsewhere in the binary
