# F-150 torque-sensor source trace from Ghidra

**Target:** `firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf`  
**Question:** are the driver-interaction / torque-like channels coming from a bus message, or from a local sensor path inside the PSCM?  
**Status:** strong enough to rule out a simple private-CAN source in the application-layer control path; exact electrical interface (`PWM` vs `SENT` vs ADC-style analog front end) is still not proven

## Short answer

For interceptor planning, treat the driver-torque path as a **local rack sensor path**, not a private CAN input.

What the current reverse engineering supports:

- the LKA and LCA controllers read **processed local RAM channels**
- those channels are returned by tiny getter shims, not by CAN-frame decode functions
- one upstream writer lives in a large local state/conditioning function, not in the known steering-command CAN RX path

What is still **not** proven:

- whether the physical sensor wiring is `PWM`, `SENT`, differential analog into an ADC, or some other direct electrical interface

So the practical engineering answer is:

- **not a private CAN message path at the application level**
- **very likely a direct local sensor interface into the PSCM**

## What the mode controllers actually read

The two driver-interaction channels used by the on-road lateral controllers are:

- `FUN_10096f38()` -> `*(gp - 0x15188)` -> `0xFEF2197A`
- `FUN_10096f40()` -> `*(gp - 0x15186)` -> `0xFEF2197C`

The getter bodies are just direct RAM returns:

```c
undefined2 FUN_10096f38(void) { return *(undefined2 *)(unaff_gp + -0x15188); }
undefined2 FUN_10096f40(void) { return *(undefined2 *)(unaff_gp + -0x15186); }
```

These are consumed by:

- `FUN_101a4d56` (`LKA`)
- `FUN_101ab934` (`LCA / BlueCruise`)

So the on-road lateral controllers are **not** decoding a bus frame themselves for driver torque.  
They are consuming already-normalized local channels from RAM.

## Why this does not look like a CAN-fed torque source

## 1. The getter pattern is local-buffer style, not frame-decode style

The steering-mode wrappers call short getters like:

- `FUN_100968ea`
- `FUN_10096f38`
- `FUN_10096f40`
- `FUN_10096b1e`
- `FUN_10096e72`

These are tiny accessors over `gp`-relative RAM, for example:

```c
FUN_100968ea -> *(short *)(gp - 0x151a6)
FUN_10096f38 -> *(short *)(gp - 0x15188)
FUN_10096f40 -> *(short *)(gp - 0x15186)
```

That is the pattern of an AUTOSAR-style local signal layer or runtime data cache, not direct CAN parsing in the controller itself.

## 2. The known steering-command CAN path is a different, shared input path

We already proved in
[angle_scale_patch.md](/Users/rossfisher/ford-pscm-re/analysis/f150/angle_scale_patch.md)
that the external steering-command messages for:

- `0x3CA` (`LKA`)
- `0x3D3` (`LCA/TJA/LateralMotionControl`)
- `0x3A8` (`APA`)

go through a **shared steering-angle ingest path**.

That shared path is about commanded steering requests coming into the rack from other modules.  
It is separate from the local driver-interaction channels at `0xFEF2197A` / `0xFEF2197C`.

## 3. The upstream writer is a large local conditioning/state function

One of the traced upstream writer sites for the `0x197a` channel lands inside:

- `FUN_10197376`

That function is a large internal state/conditioning block using many nearby `fef219**` and `fef20e**` locals, not a small CAN dispatch shim.

That is a much better fit for:

- local signal conditioning
- sensor plausibility / state handling
- local subsystem arbitration

than for “copy a torque byte from a private CAN frame and return it unchanged.”

## What this means for an interceptor

If you want to intercept or emulate driver torque for this PSCM, the safest current assumption is:

- **tap the local torque-sensor path**
- **do not assume a private CAN message exists that you can spoof to replace the torque sensor**

The firmware evidence today points to:

- local processed torque / driver-interaction channels
- stored into PSCM RAM
- then consumed by LKA/LCA logic

not to:

- a distinct PSCM-internal CAN mailbox carrying “driver torque” as a networked signal for the controller

## What I can and cannot say about PWM

I cannot yet prove `PWM`.

What I can say:

- the application-layer controllers are **not** handling raw PWM capture directly
- they are reading already-processed RAM values
- that preprocessing almost certainly happens below this layer in MCAL / I/O / signal-conditioning code

Possible physical implementations still consistent with the current evidence:

- dual analog torque channels into ADC hardware
- PWM or SENT-like digital sensor interface into a lower driver layer
- another local serial sensor interface

Possible implementation that is **not** supported by the current evidence:

- a private CAN bus message being used as the primary torque-sensor feed to the LKA/LCA controller logic

## Practical recommendation

For hardware planning:

- assume **local sensor interception**, not CAN spoofing
- assume there may be **two correlated channels** or a plausibility pair, not one single torque wire
- expect the PSCM to be checking a processed interaction metric, not just one raw torque amplitude

That matches the earlier result in
[driver_override_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/driver_override_findings.md):

- the rack does not use one naked “driver torque Nm” scalar
- it uses multiple processed channels plus threshold / hysteresis logic

## Next proof target

If we want to pin the physical layer more tightly, the next pass should trace:

- who writes `gp - 0x15188` and `gp - 0x15186` completely
- what lower-level drivers feed that writer
- whether those lower-level drivers touch timer capture, ADC, or a serial sensor peripheral

That is the step that would distinguish `PWM` from another direct local sensor interface.
