# Transit-native LCA transplant plan

**Date:** 2026-04-16

Goal:

- keep Transit executable/runtime shape
- do **not** flash donor Escape or F-150 EXE
- transplant only the minimum routing/enable pieces needed for Transit to
  accept the Escape-style LCA command path

Related notes:

- [ag_ah_vs_escape_2022_lca_strategy.md](./ag_ah_vs_escape_2022_lca_strategy.md)
- [ag_vs_ah_strategy_with_ad_cal.md](./ag_vs_ah_strategy_with_ad_cal.md)
- [transit_2025_strategy_compare.md](./transit_2025_strategy_compare.md)
- [transit_2025_cal_diff_findings.md](./transit_2025_cal_diff_findings.md)
- [../../transit_lca_hunt.md](../../transit_lca_hunt.md)

## TL;DR

Direct donor strategy flashing is dead:

- Escape EXE bricks Transit until recovery
- F-150 EXE bricks Transit until recovery

So the only credible path left is:

1. keep Transit EXE
2. keep Transit boot/runtime shape
3. patch Transit block0/block2 just enough to:
   - register the LCA CAN message
   - route it into the existing application plumbing
   - keep the rest of Transit untouched

The first concrete target is still `0x3D3`, not a full-strategy transplant.

## 1. What we know for sure

### Escape 2022 has active LCA routing

In Escape 2022 strategy block0, the RX PDU descriptor neighborhood contains:

```text
0x0100CE90  03d7011701080000
0x0100CE98  03d3011801080000   <- LCA/TJA command present
0x0100CEA0  03ca011901080000
0x0100CEA8  03b3011a01080000
0x0100CEB0  03a8011b01080000
```

This is the strongest static proof that Escape has live LCA routing.

### Transit `AG` and `AH` do not

In both Transit `AG` and `AH`, the corresponding RX region is:

```text
0x01002C80  040a011601080000
0x01002C88  03ca011701080000
0x01002C90  03b3011801080000
0x01002C98  03a8011901080000
0x01002CA0  0263011a01080000
```

Missing:

- `0x3D7`
- `0x3D3`

So neither stock Transit strategy has the donor-style LCA receive entry.

### `AG` and `AH` are identical at this routing layer

This matters because it rules out the easy theory that one stock Transit
strategy kept LCA while the other lost it.

At the relevant descriptor table, `AG` and `AH` are byte-identical.

## 2. The exact structural delta we need to account for

Escape RX sequence:

```text
0x3D7 -> slot 0x17
0x3D3 -> slot 0x18
0x3CA -> slot 0x19
0x3B3 -> slot 0x1A
0x3A8 -> slot 0x1B
0x242 -> slot 0x1C
0x217 -> slot 0x1D
0x216 -> slot 0x1E
0x213 -> slot 0x1F
...
```

Transit RX sequence:

```text
0x3CA -> slot 0x17
0x3B3 -> slot 0x18
0x3A8 -> slot 0x19
0x263 -> slot 0x1A
0x217 -> slot 0x1B
0x216 -> slot 0x1C
0x213 -> slot 0x1D
...
```

Implication:

- Escape does not just have one extra `0x3D3` entry
- it has a **different slot numbering layout** from that point downward

So the minimal patch is **not** obviously:

```text
replace 03ca with 03d3
```

because that would steal the `0x3CA` slot and almost certainly break stock LKA.

## 3. Why the patch is still feasible without a perfect decompile

Because the highest-value parts are structured data, not only code.

### Stage A: descriptor table

The RX descriptor table is raw block0 data.

We can:

- compare Escape and Transit entries directly
- identify which bytes define:
  - CAN ID
  - network
  - slot / PDU index
  - direction
  - DLC

This does not require clean C-like lift.

### Stage B: slot consumers / callback metadata

We already see a second structured region immediately after the descriptor
table, for example in Transit:

```text
0x01002D50  0415040a03ca03b3
0x01002D58  03a8026302170216
0x01002D60  0213020201670083
```

and in Escape:

```text
... 0414011501080000
0x0100CE90  03d7011701080000
0x0100CE98  03d3011801080000
0x0100CEA0  03ca011901080000
...
```

This is exactly the kind of thing we can diff/transplant directly:

- message ordering
- slot numbering
- nearby compact lookup arrays

Again, no full clean decompile required.

## 4. What is still unknown

These are the open questions that still block a reliable binary patch:

### Unknown 1: Is `0x3D7` required along with `0x3D3`?

Escape inserts both:

- `0x3D7`
- `0x3D3`

Transit has neither.

We do not yet know whether:

- `0x3D3` alone is sufficient
- `0x3D7` is a companion/heartbeat/gate message
- the application expects both to be routed

### Unknown 2: Where is the slot-to-handler mapping?

The raw descriptors are easy to see.

What is not fully closed yet is:

- how slot `0x18`, `0x19`, `0x1A`, etc. map into:
  - AUTOSAR Com callbacks
  - internal signal unpackers
  - application tasks

We have strong candidates, but not a full proven map.

### Unknown 3: How much of the compact post-table metadata must move with it?

It is unlikely that only the 8-byte descriptor entry is enough.

More likely, the patch needs:

- descriptor entry/entries
- associated compact lookup rows nearby
- maybe one or more callback/dispatch tables elsewhere in block0 or block2

## 5. Concrete next-step plan

This is the actual work sequence that makes sense now.

### Step 1. Lock down the Transit RX table patch target

Target region in Transit block0:

- descriptor neighborhood around:
  - `0x01002C88`
  - `0x01002C90`
  - `0x01002C98`
  - `0x01002CA0`

Need to decide patch strategy:

#### Option A: insert Escape-style pair and shift the rest

Pros:

- most donor-faithful
- preserves `0x3CA`, `0x3B3`, `0x3A8` ordering like Escape

Cons:

- requires editing downstream slot references

#### Option B: repurpose one Transit slot temporarily for `0x3D3`

Pros:

- easier first experiment

Cons:

- likely breaks the displaced message
- poor long-term solution

Recommended:

- use **Option B only as a fast bench experiment**
- use **Option A** for a real patch

### Step 2. Diff and transplant the compact post-table metadata

Priority neighborhoods:

- Transit:
  - `0x01002D50..0x01002D68`
- Escape:
  - corresponding rows after `0x0100CE90..0x0100CEA8`

Why:

- these compact arrays likely encode ordering/slot-group assumptions
- patching descriptors without these may silently fail

### Step 3. Close the slot-to-handler mapping

Short-term target:

- identify which handler path Transit uses for:
  - slot `0x17`
  - slot `0x18`
  - slot `0x19`

and compare with Escape’s:

- slot `0x17`
  - `0x3D7`
- slot `0x18`
  - `0x3D3`
- slot `0x19`
  - `0x3CA`

This is where we need:

- targeted disassembly
- callback-table tracing
- not a full firmware understanding

### Step 4. Build a minimal Transit experiment patch

First realistic patch candidates:

#### Patch A: descriptor-only experiment

- add/replace Transit RX entry to route `0x3D3`
- leave cal and everything else alone

Purpose:

- see if the CAN stack starts accepting the message at all

Expected result:

- probably not enough, but useful as a routing-only probe

#### Patch B: descriptor + compact metadata transplant

- patch `0x3D3` routing entry
- patch nearby post-table metadata rows to match donor layout as closely as
  possible without moving the whole strategy

Purpose:

- first serious Transit-native LCA routing experiment

### Step 5. Runtime validation

Once a patched Transit strategy exists, validate by:

- injecting `0x3D3`
- logging whether:
  - mailboxes are populated
  - slot/handler activity changes
  - `0x3CC` behavior changes
  - any new LCA-related state appears

## 6. What is already ruled out

These are dead ends now:

- whole Escape EXE transplant
- whole F-150 EXE transplant
- hoping one stock Transit strategy secretly has active `0x3D3`

The facts now are:

- donor EXE bricks Transit
- donor cal can be borrowed
- stock Transit `AG` and `AH` both lack the donor routing entry

## 7. Best current implementation target

If I had to pick one concrete next binary-edit target today, it is:

- Transit `AH` block0
- RX PDU neighborhood around `0x01002C88`
- plus the compact table region around `0x01002D50`

Why `AH`:

- slightly more donor-like than `AG`
- later stock revision
- still Transit-native and bootable

## Best current conclusion

The practical path forward is not:

- "decompile everything first"

It is:

- patch the known routing structures
- trace the slot/callback plumbing just enough
- iterate with runtime validation on a Transit-native binary

That is realistic even with imperfect decompilation, because the first hard
problem is structured routing data, not pretty pseudocode.
