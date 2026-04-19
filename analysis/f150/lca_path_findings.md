# F-150 LCA / BlueCruise path findings

**Target:** `firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf`  
**Question:** what is the detailed `LCA / BlueCruise` path in the 2021 F-150 PSCM, from mailbox family through local controller state, shared sideband ingress, and calibration ownership?  
**Status:** this is the canonical F-150 `LCA / BlueCruise` path note; the controller family, local namespaces, and one shared sideband ingress branch are now clear; exact mailbox-local boundaries for `0x3D3` vs `0x3D6`, the precise `0x3D7` receive wrapper, and the exact `0x3CC` packer remain open

## Summary

The current best model for the 2021 F-150 BlueCruise PSCM is:

- `0x3D3` is the best current fit for the primary active lateral-command PDU in this image
- `0x3D6` belongs to the same lane-centering message family, but its exact mailbox split is not yet pinned at the dispatcher edge
- `0x3D7` is the best current fit for an ESA / object-sideband message family that feeds shared lateral-supervisor state and concrete `LCA` ingress shims
- `0x3CC` is a real PSCM transmit feedback frame in the same low-flash TX descriptor list as `0x082` and `0x417`, but its exact packer is still not isolated

What is directly pinned in code:

- the `LCA / BlueCruise`-local controller family is `FUN_10186afa`, `FUN_101aa05e`, `FUN_101ab934`, and `FUN_101ad86c`
- the local runtime namespaces cluster into `fef238**`, `fef23b**`, and `fef23c**`
- `cal+0x0120 = 10.0` is the strongest current `LCA` engage-min gate
- `FUN_1005ea9c` writes the gp-backed halfword shims at `gp-0x151a2`, `gp-0x1519e`, and `gp-0x1519c`, which are then read through `FUN_10096f70()`, `FUN_10096f78()`, and `FUN_10096f80()` by the proven `LCA` locals

The result is that the F-150 rack does not look like one flat lane-centering loop. It looks like:

- a shared input/getter layer
- a shared lateral-supervisor layer
- an `LCA / BlueCruise`-local controller and state-machine family

## Message family and confidence

The mailbox family that matters to `LCA / BlueCruise` in this image is:

| CAN ID | Role in the current model | Confidence |
|---|---|---|
| `0x3D3 LateralMotionControl` | best current fit for the primary active lane-centering command PDU in this image | strong best current fit |
| `0x3D6 LateralMotionControl2` | same lane-centering family, newer CAN-FD variant in the DBC, exact mailbox split still open | present but not dispatcher-pinned |
| `0x3D7 Steer_Assist_Data` | best current fit for the ESA / object-sideband message feeding shared supervisor state and concrete `LCA` ingress shims | strong best current fit |
| `0x3CC Lane_Assist_Data3_FD1` | PSCM transmit feedback for lateral availability / hands-off state | descriptor-slot proof only for the exact TX path |

Why `0x3D3` is the best current primary-command fit in this exact image:

- the DBC exposes both `0x3D3` and `0x3D6`
- the downstream controller proof is strongest on the shared `LCA` controller chain, not yet at a clean per-mailbox split
- raw binary ID evidence in `f150_pscm_full.elf` still leans heavily toward `0x3D3`
  - `0x3D3`: `101` big-endian hits
  - `0x3D6`: `1` big-endian hit
  - `0x3D7`: `0` direct big-endian hits in the same search

So the safe wording is:

- `0x3D3` is the best current fit for the active lane-centering command PDU in this image
- `0x3D6` belongs to the same family but is not yet proven as the dominant receive path
- the code-backed proof is strongest at the normalized controller family, not the mailbox dispatcher boundary

## Top-level execution chain

The current `LCA / BlueCruise` path is best read as one continuous chain:

1. shared getters and mailbox-adjacent decode feed a lane-centering command family
2. `FUN_101a392a` calls `FUN_10186afa` as an upstream `LCA`-side setup / scheduler stage
3. `FUN_101aa05e` lifts shared getter values into the `fef23b**` / `fef23c**` local workspace
4. `FUN_101ab934` runs the large local controller over `fef238**`, `fef23b**`, `fef23c**`, and sibling working state
5. `FUN_101ad86c` collects output-side normalized quantities into `fef238**`
6. a separate shared-supervisor sideband branch `FUN_100586d0 -> FUN_1005ea9c -> FUN_1005e5fc` feeds concrete object / ESA-like ingress channels back into the same `LCA` locals through gp-backed getter shims

That last branch matters because it tightens the old “shared supervisor nearby” claim into something stronger:

- the sideband branch is not merely adjacent to `LCA`
- part of its output is now pinned into concrete `LCA / BlueCruise` ingress channels

## Function roles

### `FUN_101a392a` -> `FUN_10186afa`

This pair is the upstream `LCA / BlueCruise` wrapper and pipeline entry.

What is safe to say:

- `FUN_101a392a` is an upstream wrapper that hands control into `FUN_10186afa`
- `FUN_10186afa` belongs to the confirmed `LCA / BlueCruise`-local controller family
- the broader `FUN_10186afa` pipeline is heavily interpolation-oriented, which fits the repeated limiter / authority / schedule records now treated as `LCA`-side or shared-lateral best fits

Plain-English role:

- upstream lane-centering scheduler / conditioning stage before the big local controller consumes its normalized inputs

### `FUN_101aa05e`

`FUN_101aa05e` is the strongest normalization stage in the current `LCA` proof.

It lifts shared getter values into the local `LCA / BlueCruise` workspace, including:

- `fef23b7c` as a path-offset-like float
- `fef23b70` as a path-angle-like float
- `fef23b74` as a curvature-like float
- `fef23b78` as a curvature-rate-like float

It also populates the broader staging area across:

- `fef23b68..fef23c04`

Plain-English role:

- convert shared decoded inputs into the `LCA`-local continuous-value and mode/state workspace

### `FUN_101ab934`

`FUN_101ab934` is the large local `LCA / BlueCruise` controller.

What is directly shown in the current traces:

- it operates across `fef238**`, `fef239**`, `fef23b**`, and `fef23c**`
- it consumes at least two of the shared sideband getter shims
  - `FUN_10096f70()` -> `gp-0x151a2`
  - `FUN_10096f80()` -> `gp-0x1519c`

Plain-English role:

- main `LCA / BlueCruise` local authority, shaping, and state-machine body
- where lane-centering command values are combined with shared sideband state and internal mode logic

### `FUN_101ad86c`

`FUN_101ad86c` is the output-side collector for the local `LCA` family.

What is directly shown in the current traces:

- it populates `fef23800..fef2384c`
- it reads all three gp-backed sideband getter shims
  - `FUN_10096f70()` -> `gp-0x151a2`
  - `FUN_10096f78()` -> `gp-0x1519e`
  - `FUN_10096f80()` -> `gp-0x1519c`

Plain-English role:

- gather output-side normalized quantities and sideband-conditioned values into the `fef238**` working/output space

### `FUN_101ad5a4`, `FUN_101aef34`, `FUN_101aaf16`

These deeper helpers sit below the same local controller family.

What is safe to say:

- they are part of the `LCA / BlueCruise`-local control tree
- they reinforce that this is a distinct on-road lane-centering controller family, not just a few shared getters with light gating

Plain-English role:

- deeper limit, state-transition, and shaping helpers beneath the primary `LCA` wrappers

### Shared sideband ingress: `FUN_100586d0 -> FUN_1005ea9c -> FUN_1005e5fc`

This is the most important newer refinement for the `LCA` path.

The branch works like this:

- periodic dispatcher `FUN_100586d0` calls `FUN_1005ea9c`
- `FUN_1005ea9c` pulls four raw channels through shared readers:
  - `FUN_1005666e`
  - `FUN_10077308(0x6f)`
  - `FUN_10077308(0x70)`
  - `FUN_10077308(0x79)`
- `FUN_1005ea9c` passes those values into `FUN_1005e5fc(local_3c, uStack_3a, uStack_36, uStack_38)`
- `FUN_1005e5fc` normalizes them into physical-value shapes:
  - `(raw * 0.035) - 17.9`
  - `(raw * 0.035) - 17.9`
  - `(raw * 0.03663) - 75.0`
  - `raw * 0.01`
- `FUN_1005ea9c` then clamps and stores them into shared supervisor globals:
  - `gp-0xe1dc`, `gp-0xe1d8`, `gp-0xe1d0`, `gp-0xe1d4`
  - mirrored live copies at `gp-0x154ec..gp-0x154e0`
  - associated status bytes at `gp-0xc397`, `gp-0xc395`, `gp-0xc390`, `gp-0xc392`

The concrete new proof is that `FUN_1005ea9c` also writes:

- `gp-0x151a2`
- `gp-0x1519e`
- `gp-0x1519c`

Those are exactly:

- `FUN_10096f70()`
- `FUN_10096f78()`
- `FUN_10096f80()`

And those getters land directly in the proven `LCA / BlueCruise` locals:

- `FUN_101ad86c` reads all three
- `FUN_101ab934` reads `FUN_10096f70()` and `FUN_10096f80()`

Plain-English meaning:

- this branch is the rack’s object / ESA sideband normalization path
- it is shared-supervisor code, not an `LKA`-local or `APA`-local workspace
- part of its output is now proven to feed the `LCA / BlueCruise` local controller family directly

This is why `0x3D7` is now a stronger best current fit than before:

- the descriptor placement matches the lateral command neighborhood
- the physical-value scales match the object / ESA-style DBC fields
- the normalized outputs now land in concrete `LCA` ingress getters

The last step is still an inference from descriptor placement, scales, and consumers, not a mailbox-local receive-wrapper proof.

## Runtime namespace ownership

The `LCA / BlueCruise` local runtime state is split into three main namespaces:

- `fef23b**` — input prep and feature conditioning
- `fef23c**` — mode, status, and intermediate controller state
- `fef238**` — normalized continuous quantities and output-side working floats

The current concrete mapping is:

| Namespace | Current role | Main proven writer / consumer |
|---|---|---|
| `fef23b68..fef23c04` | local input normalization and staging | `FUN_101aa05e` |
| `fef23800..fef2384c` | output-side normalized quantities | `FUN_101ad86c` |
| broader `fef238**`, `fef239**`, `fef23b**`, `fef23c**` | main local controller state | `FUN_101ab934` |

This is the key ownership separation:

- `LKA` owns `fef21a**`
- `APA` owns `fef211**`, `fef212**`, `fef213**`
- `LCA / BlueCruise` owns `fef238**`, `fef23b**`, `fef23c**`

So the lane-centering path in this image is not just “shared lateral” in the abstract. It has a distinct local namespace and controller tree.

## Calibration ownership

### Confirmed `LCA` gate

The strongest current `LCA`-specific calibration ownership is:

- `cal+0x0120 = 10.0` — `LCA` engage minimum speed

This should be treated as confirmed at the feature-envelope level, not as a generic lateral value.

### Shared-lateral / `LCA`-side best fits

The repeated limiter / schedule families are best treated as:

- shared on-road lateral supervisor data, or
- `LCA / BlueCruise`-side limiter and authority schedules

The main families in that bucket are:

- `ctx + 0x68`, `+0x6c`, `+0x74`, `+0x78`, `+0x7c`, `+0xa8`
- `cal+0x07D68..0x07E3F`
- `cal+0x07E64..0x07E68`

Why they fit here:

- they are seeded globally from `FUN_10055494`
- they feed timer, filter, limiter, interpolation, and state-selection logic above the individual mode-local outputs
- `FUN_10186afa` is heavily interpolation-oriented
- the deeper lane-centering controller family is exactly where those schedule and authority records would naturally land

Safe wording:

- these records are not proven `APA`-side
- they are better treated as shared-lateral or `LCA / BlueCruise`-side best fits, not final single-mode proof

### What is not yet field-pinned

The following items are still not fully field-pinned inside the local `LCA` pipeline:

- exact offset-to-field ownership for every repeated breakpoint / limiter curve
- exact split between shared-lateral supervisor curves and purely `LCA`-local limiter curves

So the calibration model should remain:

- `cal+0x0120` is confirmed `LCA`
- the broader repeated limiter / schedule families are best current fits on the shared-lateral or `LCA` side

## Transmit feedback and closure path

`0x3CC Lane_Assist_Data3_FD1` belongs in the same overall story because it is the visible PSCM transmit feedback for lane-assist availability and hands-off state.

What is directly pinned:

- `0x3CC` occupies one concrete low-flash TX descriptor slot at `0x100416ea`
- it sits inside a contiguous `0x082 -> 0x3CC -> 0x417` list

What remains open:

- the exact PSCM packer for `0x3CC`

Plain-English meaning:

- the F-150 rack clearly publishes a lateral-feedback/status frame back out
- the output descriptor is proven even though the exact function body that fills it is not yet pinned

## Remaining unresolved boundaries

### `0x3D3` vs `0x3D6`

Still unresolved:

- exact mailbox-local dispatcher ownership between `0x3D3` and `0x3D6`

Current safe claim:

- both belong to the lane-centering command family
- `0x3D3` is the best current fit for the primary active PDU in this image

### Exact `0x3D7` receive wrapper

Still unresolved:

- the mailbox-local receive wrapper for `0x3D7`

Current safe claim:

- the strongest downstream consumer is the shared-supervisor sideband branch
- that branch now feeds concrete `LCA` ingress shims
- `0x3D7` remains the strongest best current mailbox fit, not final dispatcher proof

### Exact `0x3CC` packer

Still unresolved:

- the exact TX-side packer for `0x3CC`

Current safe claim:

- descriptor-slot ownership is real
- pack-function ownership is not yet pinned

## Practical takeaway

If the goal is to change the F-150 lane-centering path without touching `LKA` or `APA`, the highest-value ownership targets are:

- the `LCA`-local runtime family `fef238**`, `fef23b**`, `fef23c**`
- the confirmed `LCA` gate at `cal+0x0120`
- the shared sideband ingress branch `FUN_100586d0 -> FUN_1005ea9c -> FUN_1005e5fc`
- the shared-lateral limiter / schedule records only when intentionally changing behavior across the broader on-road lateral stack

## Cross-links

- [eps_dbc_message_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_dbc_message_trace.md)
- [eps_mode_separation_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_mode_separation_ghidra_trace.md)
- [strategy_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/strategy_findings.md)
- [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md)
- [eps_curve_family_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_curve_family_ghidra_trace.md)
