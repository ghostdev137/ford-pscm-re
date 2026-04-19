# F-150 LKA driver-override logic — strategy findings

**Date:** 2026-04-16  
**Target:** 2021 F-150 Lariat 502A BlueCruise PSCM, strategy `ML34-14D003-*`

## TL;DR

The F-150 LKA override path is **not** a single obvious "driver torque Nm" calibration scalar in the LKA function itself.

The actual drop/yield decision lives in:

- `FUN_101a4d56` — input wrapper
- `FUN_101a3b84` — main LKA controller / override state machine

That controller does **not** compare a raw wheel-torque float directly against one threshold. Instead, it consumes:

- two processed internal driver-interaction channels
- one status byte
- several threshold / hysteresis cal mirrors

So the best current model is: **Ford classifies driver interaction upstream, then LKA uses that classified result to decide whether to keep or drop assist.**

## Function chain

The LKA execution chain remains:

- `FUN_1017fbe0`
- `FUN_101a4d56`
- `FUN_101a3b84`
- `FUN_101a4e4a`

For override behavior, the first two important blocks are:

### 1. `FUN_101a4d56` — snapshot the LKA inputs

Decompile:
- `tmp/pscm/f150_lka/101a4d56.c`

Key lines:

- `101a4d56.c:17` — `DAT_fef21a77 = FUN_100978bc();`
- `101a4d56.c:19` — `_DAT_fef21a6e = FUN_100968ea()` result, clamped to `±0x2800`
- `101a4d56.c:23` — `_DAT_fef21a72` comes from `FUN_10096f40()`
- `101a4d56.c:26` — `_DAT_fef21a70` comes from `FUN_10096f38()`

The two override-related channels are scaled before LKA uses them:

```c
uVar2 = (uVar2 * (uVar2 < 0x7fbd) * 0x20) / 0x19;
_DAT_fef21a72 = ... clamp ... 0x6400;

uVar2 = (uVar2 * (uVar2 < 0x7fbd) * 0x20) / 0x19;
_DAT_fef21a70 = ... clamp ... 0x6400;
```

That matters: these are already normalized internal channels, not cleanly exposed raw Nm.

### 2. `FUN_101a3b84` — actual override / yield logic

Decompile:
- `tmp/pscm/f150_lka/101a3b84.c`

Assembly:
- `tmp/pscm/f150_lka/asm_101a3b84.txt`

This is the function that decides whether LKA stays active, soft-yields, or drops into lower-assist / no-assist states.

## The three main override inputs

### A. `0xFEF2197A` -> `_DAT_fef21a70`

Read path:
- `FUN_10096f38()` -> `_DAT_fef21a70`

Writer xref:
- `0x101A20F8`

Instruction trace:
- `ld.bu 0x133[r29], r10`
- `st.b r10, 0x197a[r12]`

Then the same function conditionally substitutes another byte before writing it back to the struct:

- `0x101A2100` reads cal byte `0x622d`
- `0x101A210C` reads cal byte `0x622e`
- `0x101A211E` may reload `0x197a`
- `0x101A2122` writes the chosen value back to `0x133[r29]`

Relevant dump:
- `tmp/f150around.out`

Best current interpretation:
- **processed driver-interaction byte**
- likely not raw driver torque
- may be a filtered / qualified override-confidence or hands-on-related channel

### B. `0xFEF2197C` -> `_DAT_fef21a72`

Read path:
- `FUN_10096f40()` -> `_DAT_fef21a72`

Writer xref:
- `0x1018A062`

Instruction trace:

- `ld.bu 0x135[r29], r10`
- `st.b r10, 0x197c[r11]`

Then downstream code immediately uses it in further math:

- `0x1018A164` reloads `0x197c`

Best current interpretation:
- another **processed driver-interaction byte**
- likely sibling to `0x197a`
- again, not proven raw Nm

### C. `0xFEF21A77` -> `DAT_fef21a77`

Read path:
- `FUN_100978bc()` -> `DAT_fef21a77`

This is the status byte used by the end-state machine in `FUN_101a3b84`.

Confirmed compares:

- `== 3`
- `== 5`

Instruction-level proof:
- `0x101A4CBA` compares against `5`
- `0x101A4CCC`, `0x101A4CE2`, `0x101A4D00` compare against `3`

Best current interpretation:
- **mode / availability status byte**
- not torque
- but directly gates whether the controller can stay in stronger assist states

## What `FUN_101a3b84` actually does

### 1. Early "quiet / okay" gate

At function entry, the controller checks:

- absolute requested angle `_DAT_fef21a6e`
- processed channel `_DAT_fef21a72`
- processed channel `_DAT_fef21a70`

Pseudo-C:
- `101a3b84.c:45`

Assembly is clearer:
- `asm_101a3b84.txt:16`

Logic:

1. `abs(_DAT_fef21a6e)` vs `_DAT_fef26382`
2. `_DAT_fef21a72` vs `_DAT_fef263de`
3. `_DAT_fef21a70` vs `_DAT_fef263de`

Plain language:
- if requested angle is small and both interaction channels are under a threshold, mark the system "quiet / okay"
- otherwise move into the stronger monitoring path

### 2. Delta / activity checks on both channels

The function compares current and previous values of both processed channels:

- previous values are in the local controller struct at `r29+0x5e` and `r29+0x60`
- current values are `_DAT_fef21a70` and `_DAT_fef21a72`

It takes absolute-ish deltas, right-shifts them, and compares against `DAT_fef26406`.

Key range:
- `asm_101a3b84.txt:31`

Plain language:
- this is a rate / recent-activity detector
- likely suppresses false override from tiny changes and helps decide whether the driver is actively loading the wheel

### 3. Banding the combined interaction metric

Later, the controller bands an internal combined value using:

- `_DAT_fef263d0`
- `_DAT_fef263d2`

Pseudo-C:
- `101a3b84.c:192`

Plain language:
- these look like low/high boundaries for a small state bucket
- not raw Nm labels, but they clearly partition the override metric

### 4. Hysteresis / persistence counter

The controller then runs another stage against:

- `_DAT_fef263da`
- `_DAT_fef263dc`

Pseudo-C:
- `101a3b84.c:242`

Plain language:
- this looks like hold-time / persistence logic
- not a torque limit itself
- likely controls how long override evidence must persist before assist state changes

### 5. Final assist-state machine

The final drop / keep decision uses:

- `DAT_fef21a74`
- `DAT_fef21a75`
- `DAT_fef21a77`
- current internal substate
- thresholds `0x7EB9` and `0x0148`

Pseudo-C:
- `101a3b84.c:780`

Instruction view:
- `f150around.out`, around `0x101A4CBA`

Observed behavior:

- `DAT_fef21a77 == 3` is the permissive path into stronger assist substates
- `DAT_fef21a77 == 5` is a block / deny path
- `0x7EB9` and `0x0148` act like large/small hysteresis boundaries for state transitions

## Best current candidate thresholds

These are the most relevant cal mirrors if the goal is to relax nuisance override:

- `_DAT_fef263de`  
  earliest threshold applied to **both** processed interaction channels

- `_DAT_fef263d0`
- `_DAT_fef263d2`  
  bucket boundaries for the combined interaction metric

- `_DAT_fef263da`
- `_DAT_fef263dc`  
  persistence / hysteresis thresholds

- `DAT_fef26406`
- `DAT_fef26405`  
  small-change / rate-quiet logic

## What this means for Transit work

This F-150 trace strongly argues against the earlier simple model:

> "there must be one scalar in cal that directly equals the driver override torque threshold in Nm"

Instead, Ford appears to do:

1. derive or qualify driver-interaction channels upstream
2. feed those channels into the LKA controller
3. apply thresholding, banding, and hysteresis
4. gate final assist state with a status byte

So the real "override threshold" may be the result of **multiple thresholds plus state logic**, not one clean Nm number.

That still gives useful patch targets:

- the earliest shared threshold `_DAT_fef263de`
- the band edges `_DAT_fef263d0/_d2`
- the persistence thresholds `_DAT_fef263da/_dc`

## What is proven vs. inferred

### Proven

- Override/yield behavior is inside `FUN_101a3b84`
- `FUN_101a4d56` feeds it two processed channels and one status byte
- those channels come from RAM `0xFEF2197A` and `0xFEF2197C`
- the status byte comes from RAM `0xFEF21A77`
- the controller compares them against `_DAT_fef263de`, `_DAT_fef263d0/_d2`, `_DAT_fef263da/_dc`, and `DAT_fef26405/6`

### Not yet proven

- exact Ford signal names for `0xFEF2197A` and `0xFEF2197C`
- whether one of those bytes is a direct wheel-torque magnitude, hands-on confidence, or a higher-level override-confidence channel
- physical engineering units for those intermediate channels

## Practical takeaway

If Transit is giving up in curves because "driver override feels too sensitive," the F-150 strategy says the fix probably is **not** just "find one torque Nm scalar."

The better framing is:

- find the upstream interaction-channel writer(s)
- identify the earliest shared threshold
- then patch threshold / hysteresis logic together, not the torque curve alone

## Files used

- `tmp/pscm/f150_lka/101a4d56.c`
- `tmp/pscm/f150_lka/101a3b84.c`
- `tmp/pscm/f150_lka/asm_101a3b84.txt`
- `tmp/f150_probe/10197376.c`
- `tmp/f150around.out`
