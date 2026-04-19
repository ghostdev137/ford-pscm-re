---
title: Transit Torque Arbitration Map
nav_order: 14
---

# Transit PSCM Torque Arbitration Map

**Session Date:** 2026-04-14 | **Binary:** `transit_AM_blk0_0x01000000.bin.bndb`

Canonical RE artifact: maps torque-arbitration entry points, Q15 scaling, and TAUB MMIO writes in the Transit PSCM strategy. Referenced from [LKA](lka.html).

---

## Executive Summary

The torque arbitration subsystem occupies a dense cluster of functions in the
`0x10ba900`–`0x10bb200` range. The arbiter is a multi-state machine that
merges manual driver torque and APA angle commands, applies Q15 scaling, and
commits the saturated result into an output struct that is subsequently written
to a TAUB MMIO timer register (`ST.H r0, 0x4040[r28]`). LCA command path
appears to be the same CAN cluster but no active LCA torque injection was
confirmed in this session.

---

## Key Addresses

### Torque Arbitration Entry Function

| Symbol (renamed) | Address | Notes |
|---|---|---|
| `torque_arbiter_entry` | **0x10BA92A** | Primary arbiter state machine entry. Contains `mulhi 0x5dc2, r6, r8` (Q15 multiply) and `satadd`/`satsubr` patterns. Called from `motor_ctrl_supervisor` (case 0x19). |
| `torque_arbiter_state_A` | 0x10BA9F6 | Arbiter sub-state; tail-calls `torque_angle_reader_Q15` via `sub_10babf2`. |
| `torque_arbiter_state_B` | 0x10BAA90 | Parallel state path; same Q15 `0x5dc2` and `set1 0, 0x5e19[r2]` output enable. |
| `torque_arbiter_state_C` | 0x10BABAA | Third state path; computes `r6 = arg1.w * *(arg1+0x700)` (torque-table lookup), calls `torque_angle_reader_Q15`. |
| `torque_arbiter_state_D` | 0x10BA98E | Fourth state path; mirrors state_A logic. |
| `torque_arbiter_state_E` | 0x10BAE2E | PID-like state that feeds `motor_output_saturate_and_commit`. |
| `torque_angle_reader_Q15` | **0x10BABF2** | **THE shared angle reader** (Transit equiv of F150 `FUN_1009ea6`). Contains `mulhi 0x67c2, r6, r6` (Q15 scale), `mulhi 0x66c0, r8, tp`, `set1 0, 0x5e19[r2]` (output enable bit), `satadd 0x14, r24`. |
| `torque_arbiter_mega_dispatch` | 0x10B97EA | Large dispatch hub — case 7 writes `*(arg12 - 0x4858) = 0` (motor_torque_command global clear). Dispatches to `motor_ctrl_state_machine` (case 3), `torque_angle_reader_Q15` path (cases 2/4/6/8/a/c), and many others. |

### Motor Output / PWM Stage

| Symbol (renamed) | Address | Notes |
|---|---|---|
| `motor_output_saturate_and_commit` | **0x10BAFCE** | Applies `*(arg12 - 0x4858) = 0` reset, reads output struct at `*(sp_7 + 0x50..0x6c)` (8× 16-bit words = 8 TAUB channels), forwards to `pwm_output_write`. |
| `torque_arbiter_exit_to_motor` | 0x10BAF50 | Bridge from arbiter to `motor_output_saturate_and_commit`. Loads torque table via `ld.h 0x7dd2[r12]`. |
| `pwm_output_write` | **0x10BB0F2** | Reads 8 consecutive halfwords from a struct at `sp_1 + 0x50..0x6c` and disposes back to caller. Contains `st.h r0, 0x4040[r28]` — the actual TAUB register write. If `r28` = TAUB base (0xFFE30000), register target = **0xFFE34040** (TAUB0 channel TDR/TPR). |
| `motor_ctrl_reset_and_relay` | 0x10BB072 | Resets `*(arg6 - 0x4858) = 0`, initializes motor struct fields (`+0x82`, `+0x48`, `+0x86`), tail-calls `pwm_output_write`. |

### State Machine Callers

| Symbol (renamed) | Address | Notes |
|---|---|---|
| `motor_ctrl_supervisor` | **0x10C5788** | Large state machine, case 0x19 calls `torque_arbiter_entry`. Also calls `motor_ctrl_reset_and_relay` via `sub_10c6a9c`. Called from `motor_ctrl_dispatch` (case 0x2a). |
| `motor_ctrl_state_machine` | 0x10BB33A | Contains `*(r16_1 - 0x4858) = 0` pattern. Case 3 jumps to `torque_arbiter_mega_dispatch + 0x12a`. Case 8 writes `*(r17_1 + 0x2444)` (TAUB-like). Called from `motor_ctrl_dispatch` (case 0x2a). |
| `motor_ctrl_dispatch` | 0x10CB2CC | Top-level motor dispatch table (~0x44 cases). Case 0x2a calls `motor_ctrl_state_machine`, case 0x32 calls `sub_10bc1dc`. No BN xref callers detected (entered via jump table). |
| `rte_motor_task_dispatcher` | **0x108033C** | RTE task function; **case 0x10** is the motor control path. Calls `sub_10ba506` (RTE-registered), then `sub_10b9526`, `sub_10b8546`, `sub_10b82e0`, applies `r16_5 * 0x626a` (Q15 current/torque scale), saturating subtract, and writes to `*(sx.d(*(arg13+0x3c8)) + 0x6a19)`. |
| `sub_10ba506` | 0x10BA506 | RTE task entry — registered in task table at **0x1076220**, called by `rte_motor_task_dispatcher`. This is the outermost motor task entry point. |

---

## Globals: Where Torque Commands Are Read

### Manual Torque (driver input)

Not yet resolved to a concrete global address. The pattern `ld.b 0x700[r6], r7` appears
repeatedly in the arbiter cluster (0x10ba950, 0x10babfb, 0x10bac04, etc.) — `r6` likely
holds a pointer to the torque sensor data block, and `+0x700` is the torque sensor
offset. The computed value feeds into `mulhi 0x67c2, r6, r6` (Q15 scale to motor current).

The table lookup `r6 = arg1.w * *(arg1 + 0x700)` in `torque_arbiter_state_C` (0x10babaa)
is the torque assist curve: sensor reading × LUT entry = assist force.

### APA Commanded Angle

The `set1 0, 0x5e19[r2]` instruction at `0x10bac22` (in `torque_angle_reader_Q15`)
sets bit 0 of `*(r2 + 0x5e19)` — this is the APA active/latch flag write. `r2` at this
point holds a pointer derived from `*(r6 + 0x700)` traversal (likely the APA message
struct base). The angle value is read via the `*(r0 + 0x71)` → linked-list walk pattern
(AUTOSAR RTE signal chain: `*(*(ptr + 0x71) + 0x1d55)` is a double-pointer dereference
common in RTE signal buffers).

CAN message 0x3A8 (`ExtSteeringAngleReq2`) bytes match at addresses 0x101a4e9 and
0x101a546 — these are in the RTE receive path. The resolved signal feeds into the
torque_angle_reader_Q15 via `arg1` (the first argument, which is the scaled CAN-derived
angle word).

### LCA Commanded Path

No distinct LCA torque injection confirmed. CAN 0x3D6 bytes appear at 0x103d3e0
(`sub_103d36e`) which is far from the arbiter cluster — likely the LCA path is gated
off on this Transit variant (consistent with prior session hypothesis).

### Motor Torque Command Output Global

The pattern `*(ctrl_blk - 0x4858) = 0` identifies the committed motor torque output
slot. It appears at:
- `torque_arbiter_mega_dispatch` 0x10B97EA, case 7: `*(arg12 - 0x4858) = 0`
- `motor_ctrl_reset_and_relay` 0x10BB072: `*(arg6 - 0x4858) = 0`
- `motor_output_saturate_and_commit` 0x10BAFCE: `*(arg12 - 0x4858) = 0`
- `motor_ctrl_state_machine` 0x10BB33A: `*(r16_1 - 0x4858) = 0`

This is a **16-bit signed saturated integer** in a motor control block (the "ctrl_blk").
The actual runtime base of ctrl_blk was not resolved in this session (it is passed as a
pointer argument through the call chain, allocated during RTE init).

---

## TAUB PWM MMIO Write

The actual hardware write is at address **0x10BB14E** and **0x10BB1D4** (two instances
within `pwm_output_write`):

```
0x10bb14e: st.h r0, 0x4040[r28]   ; write 16-bit duty to TAUB reg at r28+0x4040
0x10bb1d4: st.h r0, 0x4040[r28]   ; second write (likely second channel or retry)
```

`r28` is loaded from `sp_1 - 0x53fb7784` or similar saturation expression — the runtime
value will be the TAUB peripheral base, expected to be in the 0xFFE30000 range. Offset
`0x4040` from the TAUB0 base places this at **0xFFE34040** if TAUB0, or a shifted address
for other TAUB units.

The struct feeding these writes spans offsets `+0x50` through `+0x6c` (8 halfwords = 8
channels), consistent with TAUB having 16 channels where 8 are used for 3-phase bridge PWM.

---

## Call Graph

```
[RTE Task Table 0x1076220]
        │
        ▼
sub_10ba506 (RTE-registered motor task, 0x10BA506)
        │  called by
        ▼
rte_motor_task_dispatcher (0x108033C)
  case 0x10:
    ├── sub_10ba506          (0x10BA506)   step 1
    ├── sub_10b9526          (0x10B9526)   step 2: updates ctrl block
    ├── sub_10b8546          (0x10B8546)   step 3: APA gate check
    ├── sub_10b82e0          (0x10B82E0)   step 4: signal write
    └── [Q15 multiply 0x626a + satsub → TAUB write at 0x10762a8]

[Parallel path via motor_ctrl_dispatch]
        │
        ▼
motor_ctrl_dispatch (0x10CB2CC)
  case 0x2a:
        │
        ▼
motor_ctrl_state_machine (0x10BB33A)
  [*(r16-0x4858)=0 pattern; satadd/satsubr galore]
  case 0xf: → motor_ctrl_supervisor (0x10C5788)
                case 0x19: → torque_arbiter_entry (0x10BA92A)
                                  │
                          ┌───────┴────────────────────────────────────┐
                          │                                            │
               torque_arbiter_state_D (0x10BA98E)         torque_arbiter_state_A (0x10BA9F6)
                          │                                            │
                          └──────────────────┬─────────────────────────┘
                                             │
                                             ▼
                               torque_angle_reader_Q15 (0x10BABF2)
                               [mulhi 0x67c2 = Q15 angle scale]
                               [mulhi 0x66c0 = secondary scale]
                               [set1 0, 0x5e19[r2] = APA active flag]
                               [satadd 0x14, r24 = saturation +20]
                                             │
                                             ▼
                           torque_arbiter_exit_to_motor (0x10BAF50)
                                             │
                                             ▼
                         motor_output_saturate_and_commit (0x10BAFCE)
                         [*(arg12 - 0x4858) = 0  → motor_torque_cmd slot]
                         [reads output struct +0x50..+0x6c]
                                             │
                                             ▼
                                 pwm_output_write (0x10BB0F2)
                                 [reads *(sp_1+0x50..0x6c) = 8 TAUB channels]
                                 [st.h r0, 0x4040[r28] @ 0x10BB14E]  ← TAUB MMIO write
                                 [st.h r0, 0x4040[r28] @ 0x10BB1D4]  ← TAUB MMIO write

[Reset path via motor_ctrl_reset_and_relay]
motor_ctrl_reset_and_relay (0x10BB072)
  [*(arg6 - 0x4858) = 0]
  └──→ pwm_output_write (0x10BB0F2)
```

---

## Summary Table

| What | Address | Confidence |
|---|---|---|
| Torque arbitration entry | `torque_arbiter_entry` 0x10BA92A | HIGH |
| Shared angle reader (Transit equiv of F150 0x1009ea6) | `torque_angle_reader_Q15` 0x10BABF2 | HIGH — contains `mulhi 0x67c2`, `set1 0, 0x5e19`, `satadd` |
| Motor torque command global (ctrl_blk - 0x4858) | runtime pointer, slot at `ctrl_blk - 0x4858` | HIGH — 4 independent write sites confirm |
| APA active/latch flag | `*(r2 + 0x5e19)` bit 0 | MEDIUM — set at 0x10BAC22 |
| Saturated output commit | `motor_output_saturate_and_commit` 0x10BAFCE | HIGH |
| PWM MMIO write | 0x10BB14E: `st.h r0, 0x4040[r28]` | HIGH — hardware store instruction |
| TAUB register (absolute) | ~0xFFE34040 (if TAUB0 base = 0xFFE30000) | MEDIUM — r28 base not traced to literal |
| RTE task entry | `sub_10ba506` 0x10BA506 | HIGH — referenced from 0x1076220 task table |

---

## Next Steps

1. **Resolve ctrl_blk base address**: Trace argument to `rte_motor_task_dispatcher` case
   0x10 back to where `arg17` (the ctrl block) is allocated/initialized. This will give
   the absolute address of the `motor_torque_cmd` global at `ctrl_blk - 0x4858`.

2. **Confirm TAUB base in r28**: In `pwm_output_write`, trace how `sp_1` is constructed
   from `arg8 + 0x887c` — if arg8 is the TAUB peripheral base pointer, the full TAUB
   channel map falls out.

3. **Trace APA signal chain from CAN 0x3A8 to `torque_angle_reader_Q15` arg1**: The
   angle value enters via `arg1` in the arbiter. Follow CAN RX at 0x101a546 through the
   RTE signal chain to confirm it reaches `torque_angle_reader_Q15`.

4. **LCA confirmation**: Check `sub_103d36e` (0x3D6 handler) for any writes into the
   motor ctrl block — if none, LCA path is confirmed gated off on Transit variant.

5. **Patch vector for APA authority**: The `satadd 0x14, r24` at 0x10BAC7F is a +20
   saturation add on the angle accumulator. The `mulhi 0x67c2` scale (= 0.406 in Q15)
   is the angle-to-current gain. This is the parameter to modify for increased APA
   steering authority (analogous to F150's `80 44 → 40 45` patch).
