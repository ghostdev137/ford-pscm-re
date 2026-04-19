# F-150 EPS DBC message trace from Ghidra

**Target:** `firmware/F150_2021_Lariat_BlueCruise/f150_pscm_full.elf`  
**DBC source:** local OpenPilot/OpenDBC `opendbc/dbc/ford_lincoln_base_pt.dbc`  
**Question:** which DBC messages belong to `LKA`, `LCA/BlueCruise`, and `APA`, and where do they land in the PSCM strategy?  
**Status:** this is now the canonical message-ownership note; command-path ownership is clear; `0x3D7` now has a best-current periodic shared-supervisor consumer path; `0x3CC` still lacks an exact packer despite stronger TX-descriptor-list proof

## Summary

For the F-150 PSCM, the message split is:

- `LKA`: `0x3CA Lane_Assist_Data1`
- `LCA / BlueCruise`: `0x3D3 LateralMotionControl`, `0x3D6 LateralMotionControl2`, `0x3D7 Steer_Assist_Data`
- `APA`: `0x3A8 ParkAid_Data`
- shared PSCM feedback: `0x082 EPAS_INFO`, `0x07E SteeringPinion_Data`, `0x3CC Lane_Assist_Data3_FD1`
- related UI / camera-side status: `0x3D8 IPMA_Data`

The current firmware ownership model stays consistent with
[eps_mode_separation_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_mode_separation_ghidra_trace.md):

- `LKA` local workspace: `fef21a**`, `fef263**`, `fef264**`
- `LCA / BlueCruise` local workspace: `fef238**`, `fef23b**`, `fef23c**`
- `APA` local workspace: `fef211**`, `fef212**`, `fef213**`
- shared feedback / signal-ingest layer: `10096xxx` / `10097xxx`

For the full end-to-end `LKA` walkthrough from mailbox family through local controller and
override logic, see
[lka_path_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lka_path_findings.md).

For the full end-to-end `LCA / BlueCruise` walkthrough from mailbox family through local
controller, shared sideband ingress, and calibration ownership, see
[lca_path_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lca_path_findings.md).

For the full end-to-end `APA` walkthrough from mailbox family through local controller and speed
gate ownership, see
[apa_path_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/apa_path_findings.md).

## Important platform note

The Ford base PT DBC exposes **both**:

- `0x3D3 LateralMotionControl`
- `0x3D6 LateralMotionControl2`

This matters because:

- OpenPilot’s Ford stack treats `0x3D6` as the newer CAN-FD lane-centering command.
- Older repo notes often refer to `0x3D3` as “the” LCA message.
- The F-150 PSCM strategy proof today is strongest at the **shared LCA controller chain** (`FUN_101aa05e`, `FUN_101ab934`, `FUN_101ad86c`), not yet at a clean per-mailbox split between `0x3D3` and `0x3D6`.
- Raw binary ID evidence in `f150_pscm_full.elf` currently leans heavily toward `0x3D3` in this exact image:
  - `0x3D3`: `101` big-endian hits
  - `0x3D6`: `1` big-endian hit
  - `0x3D7`: `0` direct big-endian hits in the same search

So the best current image-specific wording is:

- the firmware clearly has an `LCA / BlueCruise` command path
- the DBC exposes both legacy and newer lateral-control PDUs
- current function-level proof is still on the shared lane-centering controller path
- current raw binary evidence favors `0x3D3` as the primary active lateral-command PDU in this F-150 image, with `0x3D6` present but not yet shown as the dominant receive path

Exact `0x3D3` vs `0x3D6` mailbox ownership is still not fully proven at the dispatcher boundary, so this remains a strong `best current fit`, not final proof.

## Message map

| CAN ID | DBC message | DBC direction vs PSCM | Plain-English role | Firmware landing zone | Ownership |
|---|---|---|---|---|---|
| `0x3CA` | `Lane_Assist_Data1` | `IPMA_ADAS -> PSCM` | direct LKA steering request | `FUN_10065b7c` best-fit unpack helper, then `FUN_101a4d56 -> FUN_101a3b84 -> FUN_101a4e4a` | `LKA` |
| `0x3CC` | `Lane_Assist_Data3_FD1` | `PSCM -> IPMA_ADAS/GWM` | LKA / lateral availability and hands-off status | low-flash TX descriptor slot at `0x100416ea` inside a contiguous `0x082 -> 0x3CC -> 0x417` list; exact packer still not isolated | shared feedback |
| `0x3D3` | `LateralMotionControl` | DBC says `IPMA_ADAS -> GWM`; strategy use is lane-centering input | primary best-fit lateral path / curvature request in this image | shared LCA chain `FUN_101aa05e -> FUN_101ab934 -> FUN_101ad86c`; raw binary evidence strongly favors this PDU in `f150_pscm_full.elf` | `LCA / BlueCruise` |
| `0x3D6` | `LateralMotionControl2` | `IPMA_ADAS -> PSCM` | newer CAN-FD replacement lateral path request | same shared LCA controller family; present in the DBC and image, but exact mailbox split still open and image evidence is much thinner than `0x3D3` | `LCA / BlueCruise` |
| `0x3D7` | `Steer_Assist_Data` | `IPMA_ADAS -> PSCM` | ESA / object-aware steering-assist sideband input | RX descriptor slot at `0x10041144`; best current downstream consumer is `FUN_100586d0 -> FUN_1005ea9c -> FUN_1005e5fc` into shared supervisor state | `LCA / ESA` |
| `0x3A8` | `ParkAid_Data` | `IPMA_ADAS -> PSCM/GWM` in DBC | APA steering-angle request and APA state handshake | `FUN_10183a8a` best-known handler, then `FUN_10180044 -> FUN_1018466e -> FUN_101848ac` | `APA` |
| `0x082` | `EPAS_INFO` | `PSCM -> IPMA_ADAS/GWM/ABS_ESC` | torque, failure, and APA handshake feedback | common getter layer reads this into local state used by `LKA`, `LCA`, and `APA` | shared feedback |
| `0x07E` | `SteeringPinion_Data` | `PSCM -> many consumers` | pinion-angle / wheel-angle feedback | common getter layer and the shared angle path used by all steering modes | shared feedback |
| `0x3D8` | `IPMA_Data` | `IPMA_ADAS -> GWM` | lane-assist / hands-off / display-side status | used as camera/UI state in the broader Ford stack; not yet shown as a direct PSCM command path | secondary / UI |

## LKA message trace

The full continuous `LKA` path narrative now lives in
[lka_path_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lka_path_findings.md).

## `0x3CA` — `Lane_Assist_Data1`

DBC signals:

- `LkaActvStats_D2_Req`
- `LaRefAng_No_Req`
- `LaRampType_B_Req`
- `LaCurvature_No_Calc`
- `LdwActvStats_D_Req`
- `LdwActvIntns_D_Req`

Plain-English role:

- this is the **direct LKA steering request**
- it carries the requested lane-assist state, requested steering angle, and a small amount of ramp / curvature sideband

Best current firmware trace:

- [docs/lka.md](/Users/rossfisher/ford-pscm-re/docs/lka.md) already ties `LaRefAng_No_Req` to the stock DBC-level ±5.86° clip
- `FUN_10065b7c` is the best current unpack-helper match because it decodes:
  - one field as `(raw * 5e-06) - 0.01024` which matches `LaCurvature_No_Calc`
  - one field as `(raw * 0.05) - 102.4` which matches `LaRefAng_No_Req`
- the normalized/requested values then land in the proven `LKA` controller chain:
  - `FUN_101a4d56` loads current processed inputs into `fef21a**`
  - `FUN_101a3b84` applies the local LKA clamp / ramp / override logic
  - `FUN_101a4e4a` writes the final LKA-local output `_DAT_fef21a78`

Local ownership:

- `fef21a6c`, `fef21a68`, `fef21a6e`, `fef21a70`, `fef21a72`, `fef21a74`, `fef21a75`, `fef21a77`, `fef21a78`
- `fef263**`, `fef264**`

Confidence:

- **High** that `0x3CA` is the F-150 `LKA` command path
- **Medium** that `FUN_10065b7c` is the exact unpack helper for the same mailbox, rather than a shared decode helper adjacent to it

## `0x3CC` — `Lane_Assist_Data3_FD1`

DBC signals:

- `LatCtlLim_D_Stat`
- `LatCtlCpblty_D_Stat`
- `TjaHandsOnCnfdnc_B_Est`
- `LaHandsOff_B_Actl`
- `LaActDeny_B_Actl`
- `LaActAvail_D_Actl`

Plain-English role:

- this is the **PSCM-to-camera / gateway availability and capability status**
- it reports whether lane assist is available, denied, limited, or hands-off

Current trace status:

- the exact PSCM packer function is not pinned yet
- headless Ghidra now proves that `0x3CC` occupies one concrete low-flash TX descriptor slot at `0x100416ea`
  - bytes near `0x100416e8`: `82 00 01 00 01 03 08 00 00 00 cc 03 01 00 02 03 08 00 00 00 17 04 01 00`
  - the neighboring TX IDs are `0x082` at `0x100416e0` and `0x417` at `0x100416f4`
  - those addresses are spaced as one contiguous 10-byte TX descriptor list
- that strengthens the “real PSCM feedback PDU” claim, but the imported ELF still does **not** produce direct code xrefs from those raw descriptor bytes to one pack function
- but the semantic role is strong because:
  - OpenPilot reads `LaActAvail_D_Actl` from this message as PSCM LKA availability
  - the repo’s existing lockout / availability work is centered on these same capability semantics

Confidence:

- **High** at the message-role level
- **High** for the concrete low-flash TX slot ownership
- **Low** for the exact packer function in the F-150 strategy

## LCA / BlueCruise message trace

This note remains the canonical message-ownership map. The full continuous `LCA` path narrative
now lives in
[lca_path_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lca_path_findings.md).

## `0x3D3` — `LateralMotionControl`

DBC signals:

- `HandsOffCnfm_B_Rq`
- `LatCtl_D_Rq`
- `LatCtlRampType_D_Rq`
- `LatCtlPrecision_D_Rq`
- `LatCtlPathOffst_L_Actl`
- `LatCtlPath_An_Actl`
- `LatCtlCurv_NoRate_Actl`
- `LatCtlCurv_No_Actl`

Plain-English role:

- legacy lane-centering / TJA path request
- carries a path-offset, path-angle, curvature-rate, and curvature command plus enable / ramp bits

Best current firmware trace:

- `FUN_101aa05e` is the strongest normalization stage for this family because it lifts shared getter values into:
  - `fef23b7c` path offset-like float
  - `fef23b70` path angle-like float
  - `fef23b74` curvature-like float
  - `fef23b78` curvature-rate-like float
- `FUN_101ab934` is the large `LCA / BlueCruise` local controller over `fef238**`, `fef23b**`, and `fef23c**`
- `FUN_101ad86c` collects normalized output-side quantities into `fef238**`

Local ownership:

- `fef23b68..fef23c04`
- `fef23800..fef2384c`
- broader `fef23b** / fef23c**` state

Confidence:

- **High** that this DBC message family maps to the proven `LCA / BlueCruise` controller chain
- **Medium** on whether this exact on-wire PDU is the active one for this F-150 image versus `0x3D6`

## `0x3D6` — `LateralMotionControl2`

DBC signals:

- `LatCtlPath_No_Cnt`
- `LatCtlPath_No_Cs`
- `LatCtl_D2_Rq`
- `HandsOffCnfm_B_Rq`
- `LatCtlRampType_D_Rq`
- `LatCtlPrecision_D_Rq`
- `LatCtlPathOffst_L_Actl`
- `LatCtlPath_An_Actl`
- `LatCtlCurv_No_Actl`

Plain-English role:

- newer CAN-FD lane-centering path request
- same general control family as `0x3D3`, but with counter / checksum and a slightly different mode field

Current firmware trace:

- the downstream controller family is the same `LCA / BlueCruise` chain:
  - `FUN_101aa05e`
  - `FUN_101ab934`
  - `FUN_101ad86c`
- exact mailbox-level ownership is still open in this repo: the F-150 strategy proof is presently stronger at the normalized controller stage than at the raw receive-dispatch boundary

Confidence:

- **High** that `0x3D6` belongs to the F-150 lane-centering family in the DBC
- **Medium / Low** for exact F-150 PSCM mailbox routing proof in the current notes

## `0x3D7` — `Steer_Assist_Data`

DBC signals:

- `CmbbObjRelLat_V_Actl`
- `CmbbObjDistLong_L_Actl`
- `CmbbObjDistLat_L_Actl`
- `CmbbObjConfdnc_D_Stat`
- `CmbbObjColl_T_Actl`
- `CmbbObjClass_D_Stat`
- `EsaEnbl_D2_Rq`

Plain-English role:

- sideband obstacle / ESA steering-assist input to the rack
- not the main lane-centering path request, but a sibling steering-assist message family

Current trace:

- headless Ghidra now proves a dedicated F-150 receive descriptor entry at `0x10041144`
  - descriptor bytes: `d7 03 ff 47 1e 08 03 00`
  - adjacent entries are `0x3D6` at `0x1004114c`, `0x3CA` at `0x10041154`, and `0x3A8` at `0x1004116c`
- that places `0x3D7` inside the same 8-byte receive-descriptor run as the rack-facing lateral-command families
- the strongest downstream consumer is now:
  - periodic dispatcher `FUN_100586d0`
  - `FUN_1005ea9c`
  - which pulls four raw channels via `FUN_1005666e`, `FUN_10077308(0x6f)`, `FUN_10077308(0x70)`, and `FUN_10077308(0x79)`
  - then calls `FUN_1005e5fc(local_3c, uStack_3a, uStack_36, uStack_38)`
- `FUN_100586d0` also calls sibling supervisor branch `FUN_1005dbc8`, which reinforces that this is a periodic shared-supervisor consumer path rather than a mode-local mailbox wrapper
- `FUN_1005e5fc` normalizes those four raw inputs into:
  - `(raw * 0.035) - 17.9`
  - `(raw * 0.035) - 17.9`
  - `(raw * 0.03663) - 75.0`
  - `raw * 0.01`
- `FUN_1005ea9c` then clamps and stores the normalized outputs into shared supervisor globals:
  - `gp-0xe1dc`, `gp-0xe1d8`, `gp-0xe1d0`, `gp-0xe1d4`
  - mirrored live copies at `gp-0x154ec..gp-0x154e0`
  - plus associated status bytes at `gp-0xc397`, `gp-0xc395`, `gp-0xc390`, `gp-0xc392`
- one step tighter than the older note: the same `FUN_1005ea9c` body also writes the
  gp-backed halfwords at:
  - `gp-0x151a2`
  - `gp-0x1519e`
  - `gp-0x1519c`
- those are exactly the getter shims used by the lane-centering locals:
  - `FUN_10096f70()` -> `gp-0x151a2`
  - `FUN_10096f78()` -> `gp-0x1519e`
  - `FUN_10096f80()` -> `gp-0x1519c`
- and those getters land directly in the proven `LCA / BlueCruise` path:
  - `FUN_101ad86c` reads all three
  - `FUN_101ab934` reads `FUN_10096f70()` and `FUN_10096f80()`
- so the shared-supervisor branch is no longer just “near” the lane-centering path:
  three concrete `LCA` ingress channels are now pinned to the `FUN_100586d0 -> FUN_1005ea9c`
  sideband-normalization family
- those physical-value shapes are a strong match for the `0x3D7` object-sideband DBC family.
  This last step is still an inference from the code-backed scales plus descriptor-list placement, not a mailbox-local proof from the receive dispatcher boundary.
- importantly, this branch does **not** land in `fef21a**` (`LKA`) or `fef211**` (`APA`) local namespaces.
  It behaves like shared lateral-supervisor / ESA state.

Confidence:

- **High** that the F-150 strategy has a dedicated periodic shared-supervisor consumer for an ESA / object-sideband message family
- **Medium / High** that this exact branch is `0x3D7 Steer_Assist_Data` rather than another sibling PSCM-facing sideband PDU, because part of its normalized output is now pinned into concrete `LCA / BlueCruise` getter shims

## APA message trace

The full continuous `APA` path narrative now lives in
[apa_path_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/apa_path_findings.md).

## `0x3A8` — `ParkAid_Data`

DBC signals most relevant to steering:

- `ApaSys_D_Stat`
- `EPASExtAngleStatReq`
- `ExtSteeringAngleReq2`
- plus several park-assist state / request fields such as `ApaSteWhl_D_RqDrv`, `ApaScan_D_Stat`, `ApaLongCtl_D_RqDrv`

Plain-English role:

- this is the **APA steering-angle request and handshake**
- it carries the requested external steering angle plus the active APA state

Best current firmware trace:

- `FUN_10183a8a` is the best-known F-150 `0x3A8` handler anchor in the repo
- the now-proven `APA` task wrapper is:
  - `FUN_1017fd92`
  - which calls `FUN_1018466e()`, then `FUN_10183a8a()`, then `FUN_101848ac()`
- the proven `APA` local controller path remains:
  - `FUN_10180044`
  - `FUN_1018466e`
  - `FUN_101848ac`
- that path owns:
  - `fef211**`
  - `fef212**`
  - `fef213**`

Why this is strong:

- `FUN_1017fd92` is a small APA-only wrapper that sequences the receive / normalize / apply stages directly
- `FUN_1018466e` and `FUN_101848ac` manipulate APA-local state and output bytes only
- the local RAM families are distinct from both the `LKA` and `LCA` namespaces
- [docs/apa.md](/Users/rossfisher/ford-pscm-re/docs/apa.md) already ties this family to the APA speed-gate work

Confidence:

- **High** at subsystem role and ownership
- **Medium** for exact message-edge unpack detail beyond the handler anchor

## Shared PSCM feedback messages

## `0x082` — `EPAS_INFO`

DBC signals most relevant here:

- `SteeringColumnTorque`
- `EPAS_Failure`
- `SteMdule_I_Est`
- `DrvSte_Tq_Actl`
- `SAPPAngleControlStat1..6`

Plain-English role:

- common PSCM feedback frame for:
  - driver torque / interaction
  - EPS fault state
  - module current / state
  - APA handshake status

Current strategy tie-in:

- `LKA` and `LCA / BlueCruise` consume processed local RAM channels derived from this common feedback layer
- [torque_sensor_source_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/torque_sensor_source_trace.md) proves that the controllers read processed local channels, not a private CAN torque message
- OpenPilot uses `EPAS_INFO` exactly this way in `carstate.py`

Message role:

- `LKA`, `LCA`, and `APA` all depend on it
- it is the main **shared rack feedback** frame

## `0x07E` — `SteeringPinion_Data`

DBC signals:

- `StePinComp_An_Est`
- `StePinCompAnEst_D_Qf`
- `StePinRelInit_An_Sns`
- `StePinAn_No_Cs`
- `StePinAn_No_Cnt`

Plain-English role:

- common pinion-angle / compensated-wheel-angle feedback frame

Current strategy tie-in:

- [angle_scale_patch.md](/Users/rossfisher/ford-pscm-re/analysis/f150/angle_scale_patch.md) and the broader shared getter work both support this as the common steering-angle feedback family
- OpenPilot reads it as the authoritative steering-angle signal

Message role:

- shared by all three steering-command families

## Secondary / UI-side messages

## `0x3D8` — `IPMA_Data`

DBC signals most relevant to steering:

- `LaActvStats_D_Dsply`
- `LaHandsOff_D_Dsply`
- `LaDenyStats_B_Dsply`
- `DasStats_D_Dsply`
- `DasWarn_D_Dsply`

Plain-English role:

- camera / UI-side lane-assist status frame
- useful for cluster / gateway behavior, but not yet proven as a direct PSCM steering-command ingress path

Current strategy tie-in:

- OpenPilot retains and forwards this message for stock LKAS UI behavior
- the repo’s current F-150 firmware work does not yet show it as a direct owner of the `LKA`, `LCA`, or `APA` local namespaces

## Practical ownership summary

If the goal is to modify steering behavior at the PSCM:

- touch `0x3CA` for direct `LKA` behavior
- touch `0x3D3` / `0x3D6` / `0x3D7` for `LCA / BlueCruise / ESA` behavior
- touch `0x3A8` for `APA`
- read `0x082` and `0x07E` as the common rack feedback layer
- treat `0x3CC` as the PSCM’s availability / capability feedback back to the camera / gateway

## Open questions

1. Exact F-150 mailbox split between `0x3D3` and `0x3D6`
   - the DBC exposes both
   - the current F-150 strategy proof is stronger at the shared `LCA` controller chain than at the raw receive dispatcher

2. Exact PSCM packer for `0x3CC Lane_Assist_Data3_FD1`
   - low-flash TX slot ownership is now clear
   - exact TX function is still not pinned

3. Exact mailbox-local wrapper for `0x3D7 Steer_Assist_Data`
   - periodic shared-supervisor consumer path is now clear
   - the receive-dispatch boundary is still not isolated in the current notes

## Cross-links

- [lka_path_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lka_path_findings.md)
- [lca_path_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lca_path_findings.md)
- [apa_path_findings.md](/Users/rossfisher/ford-pscm-re/analysis/f150/apa_path_findings.md)
- [eps_mode_separation_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_mode_separation_ghidra_trace.md)
- [torque_sensor_source_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/torque_sensor_source_trace.md)
- [angle_scale_patch.md](/Users/rossfisher/ford-pscm-re/analysis/f150/angle_scale_patch.md)
