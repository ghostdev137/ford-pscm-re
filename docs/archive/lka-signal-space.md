---
layout: default
title: LKA signal space + open A/Bs
nav_order: 81
---

# LKA signal space & open A/B tests

Handoff notes for the firmware agent. Covers the full `Lane_Assist_Data1` (0x3CA) + `Lane_Assist_Data3_FD1` (0x3CC) signal map, which bits openpilot currently sends, which are unused/rejected, adjacent cal regions worth probing, and the A/B ideas still parked.

Pairs with `openpilot-drive-findings.md` (drive-level evidence) and `lka.md` (the zeroed-timer patch).

---

## Current state summary (2026-04-12)

- `LKA_NO_LOCKOUT.VBF` **flashed and working** — `cal + 0x06B0..0x06C2` zeroed.
- One of the secondary timers at `+0x06B8..0x06C2` was raised back from 0 to a 3 m/s equivalent (a later tweak — zero there destabilised the PSCM; 3 m/s was stable). *Exact offset and value should be recorded here once confirmed.*
- Low-speed engagement now works down to ~10 m/s (driver reports stable LKA at 24 mph).
- Residual limits: weak authority 10–11 m/s (7° mean tracking error), ±5.8° LKA signal clip at the DBC level, and PSCM motor torque cap (unknown offset, likely near `+0x06C3..0x06C8`).

---

## `Lane_Assist_Data1` (0x3CA / 970) — what openpilot sends to PSCM

Frame is 8 bytes, 33 Hz, sender IPMA_ADAS. openpilot (ghostdev137/opendbc@ford-lka) replaces the stock camera's frame with its own.

| Signal | Bit@order | Scale / offset | Range | Values | **What we send today** |
|---|---|---|---|---|---|
| `LkaActvStats_D2_Req` | 7\|3@0+ | 1,0 | 0–7 | 0=NoInterv, 1=**IncrIntervLeft**, 2=StandIntervLeft, 3=SupprLeft, 4=StandIntervRight, 5=SupprRight, 6=**IncrIntervRight**, 7=NotUsed | **0 / 2 / 4** only (panda `ford_tx_hook` rejects all others) |
| `LdwActvIntns_D_Req` | 1\|2@0+ | 1,0 | 0–3 | 0=None, 1=Low, 2=Medium, 3=High | **3=High** when active, 0 otherwise |
| `LdwActvStats_D_Req` | 4\|3@0+ | 1,0 | 0–7 | 0=LDW_Idle … 7=Suppress_Right_Left | **0** (LDW idle) |
| `LaCurvature_No_Calc` | 15\|12@0+ | 5e-6, -0.01024 | ±0.01023 1/m | 4095=Fault | **0** (not populated) |
| `LaRefAng_No_Req` | 19\|12@0+ | 0.05, -102.4 | **±102.3 mrad ≈ ±5.86°** | 4095=Fault | `apply_angle` in mrad, clipped ±5.8° |
| `LkaDrvOvrrd_D_Rq` | 38\|2@0+ | 1,0 | 0–3 | 0=Level_0 … 3=Level_3 | **0** (Level_0, no override request) |
| `LaRampType_B_Req` | 39\|1@0+ | 1,0 | 0–1 | 0=Smooth, 1=Quick | **1=Quick** (unconditional, from commit `c96b9e36`) |

---

## `Lane_Assist_Data3_FD1` (0x3CC / 972) — what PSCM tells IPMA

Frame is 8 bytes, sender PSCM. openpilot currently reads only `LaActAvail_D_Actl` into `CS.lkas_available`. The rest is a diagnostic gold mine that we ignore.

| Signal | Values | Why it matters |
|---|---|---|
| `LaActAvail_D_Actl` | 0=LCA/LKA/LDW_Suppress, 1=LDW_only, 2=LCA/LKA_Avail, **3=all_avail** | Our current gate; we require =3 to send LKA |
| **`LatCtlCpblty_D_Stat`** | 0=NoMode, **1=LimitedMode**, **2=ExtendedMode**, 3=Faulty | **Transit stock = 1 Limited; LCA-enabled vehicles = 2 Extended.** Target signal for `LCA_ENABLED.VBF` success verification |
| **`LatCtlLim_D_Stat`** | 0=NotReached, 1=Close, **2=LimitReached**, 3=LimitWithDriverActive | **PSCM's "I'm capping you" flag.** If we see value 2 during our engagement it proves the authority cap is firmware-enforced |
| `LatCtlSte_D_Stat` | 0=Unavailable, 1=Available, 2=ContLatControlInProgress, 3=RampOut, 4=Denied | PSCM state machine |
| `LaHandsOff_B_Actl` | 0=Hands_On, 1=Hands_Off | PSCM's own hands-off verdict (separate from `TjaHandsOnCnfdnc_B_Est`) |
| `TjaHandsOnCnfdnc_B_Est` | 0=Low, 1=High | TJA-path hands-on confidence |
| `LaActDeny_B_Actl` | 0=Not_Denied, 1=LA_Denied | PSCM outright denial |
| **`LsmcBrk_Tq_Rq`** | 0..32764 Nm | **ABS asymmetric brake request.** PSCM can recruit ABS to brake one wheel for yaw assist, augmenting EPS motor. Has never been observed active in our drive data |
| `LsmcBrkDecelEnbl_D_Rq` | 0=Off, 1=On | Brake-assist enable flag |

### Diagnostic action requested
Would be valuable to add these to openpilot's `CS` read-out + a short A/B drive that commands a large sustained angle and logs `LatCtlLim_D_Stat` / `LsmcBrk_Tq_Rq`. Needed to localize the authority cap.

---

## LCA path for reference — `LateralMotionControl` (0x3D3 / 979)

Not the LKA channel, but the target of your `LCA_ENABLED.VBF` work. openpilot currently uses this only as **passthrough** (replay stock camera values with `LatCtl_D_Rq=0` to keep heartbeat alive).

| Signal | Values | Notes |
|---|---|---|
| `LatCtl_D_Rq` | 0=NoLatCtl, 1=**ContinuousPathFollowing**, 2=InterventionLeft, 3=InterventionRight | Our planner target would be =1 once LCA is unlocked |
| `LatCtlRampType_D_Rq` | 0=Slow, 1=Medium, **2=Fast**, **3=Immediately** | **4 values** — note this is NOT the same as LKA's 1-bit `LaRampType_B_Req` |
| `LatCtlPrecision_D_Rq` | 0=Comfortable, 1=Precise | Upstream uses Precise |
| `LatCtlPathOffst_L_Actl` | −5.12..5.11 m | Lateral offset command |
| `LatCtlPath_An_Actl` | −0.5..0.5235 rad | Path angle |
| `LatCtlCurv_No_Actl` | −0.02..0.02094 1/m | Curvature — the primary actuation signal |
| `LatCtlCurv_NoRate_Actl` | ±0.00102 1/m² | Curvature rate |

---

## Adjacent cal regions

From `docs/lka.md`:

| Offset | Contents | Status |
|---|---|---|
| +0x06B0..0x06C2 | Lockout timer table (13 bytes) | **Zeroed (main patch)** — one secondary counter later raised to 3 m/s equiv |
| **+0x06C3..0x06C8** | **LKA gain / authority** | **Untouched. Primary candidate for raising motor-torque cap.** Shared with LCA — must be scaled, not zeroed |
| +0x0E79..0x0E82 | Heading / curvature scale | Shared with LCA |

The user's complaint "tuning is terrible, but it works" implies PSCM's motor is under-commanded for the openpilot target curvature. `+0x06C3..0x06C8` is the top-priority region to ReadMemoryByAddress dump and compare vs Escape (`LX6C`) to isolate authority scalars.

---

## Open A/B tests (parked)

### 1. `LkaActvStats_D2_Req` = 1 / 6 (Incr) instead of 2 / 4 (Stand)
**Hypothesis**: `LkaIncrIntervLeft/Right` requests stronger motor torque than `LkaStandIntervLeft/Right`. Stock IPMA may escalate from Stand→Incr when lane departure is severe; we never see it because we always pick Stand.

**Required work**:
- `opendbc/safety/modes/ford.h` → extend LKA allow-list from `{0,2,4}` to `{0,1,2,4,6}`.
- `opendbc/car/ford/carcontroller.py` → choose Incr when |apply_angle| > some threshold.

**Risk**: unknown PSCM response to unsolicited Incr. May reject, may work, may be logged as fault. Reversible.

### 2. `LkaDrvOvrrd_D_Rq` = 2 or 3 instead of 0
**Hypothesis**: raising the override-level request tells PSCM that driver is confirmed engaged / assist-requested, possibly relaxing hands-off detection or raising override-torque threshold.

**Required work**: 1-line change in carcontroller; no panda change needed.

**Risk**: low. Could reduce nuisance override-cut events at 0.7–1.0 Nm driver torque.

### 3. Populate `LaCurvature_No_Calc` with modeld curvature
**Hypothesis**: stock IPMA sends camera-computed road curvature here as feed-forward. PSCM may use it to pre-ramp motor, reducing lag on turns.

**Required work**: carcontroller wires `sm['modelV2'].action.desiredCurvature` (or similar) into the packed field.

**Risk**: very low; signal is advisory.

### 4. Additional cal A/B ideas
- **`+0x06C3..0x06C8` gain scaling**: multiply by 1.25x–2x, flash, drive, measure tracking error in the 10–11 m/s bucket. If mean error drops from 7° toward 1°, we've found the authority cap. If PSCM faults, revert.
- **Dump Escape `LX6C` cal at same offset**: direct diff to see if Escape's gain values are higher, explaining why Escape has usable LCA out of the box.

---

## Drive evidence pointers

| Route | Purpose |
|---|---|
| `ebf5c8dd5ae05d65/00000003--259ad29d69` | Low-speed tracking before any PSCM patches — 22° errors at 8–9 m/s |
| `ebf5c8dd5ae05d65/00000004--074a9a28f2` | Proof of two-sender ACCDATA collision (post-fix) |
| `ebf5c8dd5ae05d65/00000014--10a5949cf7` | After `LKA_NO_LOCKOUT.VBF` + 3 m/s floor patch — 11 engagements, 0 cruise faults, engages at 10.7 m/s, still 7° mean err at 10–11 m/s |

All three rlogs are on-device at `/data/media/0/realdata/` and mirrored to `/Users/rossfisher/comma-segments/` on the dev workstation.

---

## Questions for the firmware agent

1. **Where is the PSCM's LKA motor torque authority encoded?** Best guess: cal floats in the `+0x06C3..0x06C8` window, or inline scalars in the strategy block that load from cal base. A `0x23` dump of `+0x06A0..0x0700` (120 bytes) across Transit (KK21) vs Escape (LX6C) would be the fastest path to identify.
2. **Is `LatCtlCpblty_D_Stat` reported by the unpatched 2025 Transit as 1 (Limited) or 2 (Extended)?** We could read it at runtime to confirm LCA is stuck in Limited. Need carstate telemetry.
3. **Does `LkaDrvOvrrd_D_Rq` affect the override-torque threshold, or is it purely a mode request the PSCM may ignore?** Code-level question — likely findable in a disassembly search for the signal decoder.
4. **What was the exact offset + value of the secondary timer we bumped to 3 m/s equivalent?** Should be recorded here once the user confirms (currently undocumented in the repo).
