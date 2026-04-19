# Transit PSCM LKA angle-scaling — overnight findings

Run on 2026-04-14 overnight. User asleep. Exit criterion: a concrete
patchable solution. **Met.** Loop terminated.

## TL;DR

**Two patched strategy blobs ready for you to test in the morning:**

1. `transit_blk0_Q15x1.23.bin` — conservative, single-gain patch (2 bytes changed)
2. `transit_blk0_Q15_both_fwd_gains.bin` — both forward gains maxed out (4 bytes changed)

Files live in `/Users/rossfisher/ford-pscm-re/firmware/patched/`. Builder script: `transit_q15_multiplier_patch.py` (same dir).

**Expected effect:** ~1.23× to ~1.54× more commanded-angle authority through the APA hack path. Not the 3× you wanted, but genuinely the ceiling of what a single-word (or two-word) patch can achieve on this firmware given the Q15 fixed-point limits. See "Why not ×3" below.

**Before flashing:** both files are the DECOMPRESSED strategy blob (flash base 0x01000000). You still need to:

1. Wrap them back into a VBF via the LZSS encoder at `~/ford-pscm-re/tools/vbf_lzss_encode.py` (or a qvbf equivalent).
2. Recompute the strategy CRC32 that your SBL enforces.
3. Flash via ForScan / UDS RequestDownload. Prior-session notes say Transit PSCM accepts RequestDownload without 0x27 seed/key, so this should go through without bootloader-auth.

I did not wrap to VBF or compute CRC — those steps are firmware-specific and I didn't want to ship something that looks flashable but isn't.

## Why not ×3 by simple multiplier patch

Transit uses **integer Q15 fixed-point** in the torque angle reader, NOT F150's IEEE-754 float. Key difference:

- F150: `mulf.s r11, r17, r12` after `movhi 0x4480, r0, r11` (= 1024.0f). Changing to 3072.0f gives ×3 cleanly because floats have no bounded range.
- Transit: `mulhi 0x67C3, r6, r6` → `r6 = (r6 × 0x67C3) >> 16` where imm16 is **signed Q15** (range −1.0 .. +0.99997). Current coefficient is ≈+0.81. Max achievable is +1.0 = ×1.234 of original gain.

Going above 0x7FFF flips the imm to a negative value via V850's sign-extension and would reverse the steering direction — catastrophic. The builder refuses to produce that unless you pass `--force`.

To get higher than ×1.23 you'd need either:
- A compound patch affecting multiple stages (the "both forward gains" variant tries this but the actual gain depends on whether stage 0x67C3 and stage 0x66C1 are in series or in alternative paths — MEDIUM confidence they're in series, MED-LOW they compound cleanly)
- A **shift** patch: find a `>> N` downstream and reduce N by 1 (halves the post-mul shift = doubles output). Didn't locate one tonight — would need another dedicated pass.
- **Remove a saturation clamp** further downstream — biggest potential gain but highest risk.

## Exact patch coordinates (for reference)

Primary target:
- **Function:** `torque_angle_reader_Q15` (vaddr `0x010BABF2`)
- **Instruction:** `mulhi 0x67C3, r6, r6` at vaddr `0x010BABF8`
- **File offset of the 16-bit imm:** `0xBABFA..0xBABFB` (2 bytes, LE)
- **Original:** `c3 67` (imm = 0x67C3 = Q15 +0.8106)
- **Patched:** `ff 7f` (imm = 0x7FFF = Q15 +0.99997)

Secondary target (compound variant also patches this):
- **Function:** same `torque_angle_reader_Q15`
- **Instruction:** `mulhi 0x66C1, r8, r5` at vaddr `0x010BAC08`
- **File offset:** `0xBAC0A..0xBAC0B`
- **Original:** `c1 66` (imm = 0x66C1 = Q15 +0.8028)
- **Patched:** `ff 7f` (imm = 0x7FFF)

Tertiary candidates (NOT patched — noted for further exploration):

| vaddr | file | imm | Q15 | guess |
|---|---|---|---|---|
| `0x010BAC88` | 0xBAC8A | 0xBE50 | −0.513 | compensator (negative, don't naively raise) |
| `0x010BACD8` | 0xBACD8 | 0x1E51 | +0.237 | minor / damper |
| `0x010BACE2` | 0xBACE4 | 0x3D51 | +0.479 | intermediate gain |
| `0x010BAD28` | 0xBAD2A | 0x9E50 | −0.763 | negative compensator |
| `0x010BAD7A` | 0xBAD7C | 0xBE53 | −0.513 | negative compensator |
| `0x010BADA4` | 0xBADA6 | 0x0950 | +0.073 | small, maybe a rate limiter |
| `0x010BADC8` | 0xBADCA | 0xBE53 | −0.513 | negative compensator |

## How I verified the patch bytes

The agent report said `mulhi 0x67c2` but I went to the raw binary:

```
$ xxd -s 0xbabe0 -l 32 transit_AM_blk0_0x01000000.bin
000babe0: e615 50fe 0084 c207 195e 8084 2200 017d
000babf0: e21f 501e 008c 2a00 e636 c367 3087 0014
                                  ^^^^^^^^^^^
                                  e6 36 c3 67 at 0xBABF8
```

Decoding: halfword1 = `0x36E6` = (reg2=6, opcode=0x37 MULHI, reg1=6). Halfword2 = `0x67C3` (NOT 0x67C2 as the agent reported — 1-bit typo on its part).

Patch applied at `0xBABFA..0xBABFB` = `c3 67 → ff 7f`. Verified 2-byte diff via hexcompare.

## Test plan for morning

1. **Confirm openpilot can send wider angle commands.** In `~/openpilot/opendbc_repo/opendbc/car/ford/carcontroller.py`, verify what the APA path is currently clamping `apply_angle` to. If OP itself has a soft limit of ~5°, raise it to e.g. 15°. The CAN signal `ExtSteeringAngleReq2` carries up to ±2276° so there's no DBC limit.

2. **Flash `transit_blk0_Q15x1.23.bin` first** (least intrusive). Test at low speed in an empty parking lot. Observe:
   - Does the car now steer past ~5°? If yes by any amount (e.g. ~6°), the gain patch worked.
   - Any DTCs? If the CRC gate catches the patch, you'll get a flash or run-time fault.
   - Any unusual lag / oscillation? If the single-gain patch destabilizes a filter, the response will oscillate rather than settle.

3. **If ×1.23 is noticeable but not enough:** try `transit_blk0_Q15_both_fwd_gains.bin`. That should land around ×1.5 effective if the gains compound.

4. **If you need more than that:** we escalate. Two paths — each a separate session:
   - Find a downstream `>> N` shift and reduce N.
   - Remove or widen a saturation clamp in `motor_output_saturate_and_commit` (agent A4 identified this name but I didn't verify the clamp bounds).

## What I did NOT do

- Did NOT push anything to git (no PRs, no commits to forks).
- Did NOT apply any patch to the openpilot fork — left that as a morning decision for you.
- Did NOT wrap the patched blob into a flashable VBF — needs your LZSS + CRC tooling.
- Did NOT run the killed agents' partial work — A1 (LKA float reader) and A3 (APA clamp) last-result fragments showed:
  - A3 had a useful anchor: "case 0x1900 in dispatcher = CAN index 0x19 for 0x3A8" — suggests the 0x3A8 RX path lands at a case-0x1900 dispatch handler somewhere. Worth chasing next session.

## Confidence levels

- **Patch byte location (0xBABFA..0xBABFB):** HIGH. Verified bytes match expected V850 mulhi encoding, matches BN's disasm identification of `mulhi 0x67C3`.
- **Effect of ×1.23 patch on wheel authority:** MEDIUM-HIGH. arg1 of `torque_angle_reader_Q15` is provably in the APA command path (chain verified via BN). Whether 0x67C3 is the gain-dominating stage vs a filter is MED confidence — there are other multipliers and I can't know without live trace.
- **Compound-patch actually gives ×1.5:** MEDIUM. Depends on whether 0x67C3 and 0x66C1 are in series or in alternative paths.
- **No downstream clamp will mask the gain increase:** LOW-MED. Saturation clamps exist in the arbiter; I didn't verify their thresholds are loose enough to accommodate the new gain.

## Concrete answer to your original question

**Q:** "Find some way to scale the LKA angle, eg 2 deg → 6 deg or whatever."

**A:** Single-word patch achieves ~×1.23 (2° → 2.5°). Double-word compound achieves up to ~×1.5 (2° → 3°) if forward gains are in series. The ×3 target isn't reachable with a simple byte-level multiplier patch on Transit's Q15 firmware — would need either a downstream shift patch or a saturation-clamp removal, both more invasive and riskier.

Files ready: `/Users/rossfisher/ford-pscm-re/firmware/patched/`
