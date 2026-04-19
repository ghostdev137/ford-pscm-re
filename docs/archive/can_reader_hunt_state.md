# CAN reader scaling hunt — iteration state

## Goal
Scale the incoming 0x3A8 ExtSteeringAngleReq2 at the RX unpack so raw commanded angle gets multiplied before propagating into Q15 arithmetic downstream. Target ×3 effective authority (2° → 6°).

## What I know
- **PDU table entry for 0x3A8** at file `0x1002c98`: `03 a8 01 19 01 08 00 00` (ID BE, handle=0x0119, flag=0x01 RX, DLC=8)
- **DBC signal**: `ExtSteeringAngleReq2 : 22|15@0+ (0.1,-1000)` — 15-bit at bit 22 big-endian. In the 8-byte payload this spans byte 2 bits [6:0] + byte 3 [7:0] = 15 bits total.
- **Signed 15-bit raw → physical**: raw × 0.1 − 1000 degrees. Raw 10000 (= 0x2710) = 0° physical.
- **Handler dispatch**: by PDU handle 0x0119 via unknown callback table; no direct xref found yet from PDU table entry.

## What I tried
- Searched `03 a8 01` → found the PDU entry + another CAN-ID table at 0x10b031e
- Xrefs to 0x1002c98 → none (computed lookup, not direct)
- Searched `10 27` (0x2710 offset, = 0° physical) → only 2 hits, neither in RX handler context
- Searched `c6 36 7f 00` and `c8 46 7f 00` (andi 0x7f, for 15-bit-lower-byte mask) → zero hits
- Prior agent (killed) fragment: "case 0x1900 = CAN index 0x19 for 0x3A8 maps to case 0x1900 in dispatcher" — MEDIUM confidence, worth chasing next

## Next iteration plan
1. Search for "case 0x1900" dispatcher with MCP — find function containing a `cmp 0x1900` or `switch` landing at 0x1900
2. Hunt 5° equivalent constants in raw scale: raw = 10050 (0x2742), bytes `42 27` LE; if found, that's the clamp
3. **Alternative pivot**: check if the 5° limit is in openpilot's APA handshake (carcontroller.py) not firmware — simple code fix if so
4. **Alternative pivot 2**: look for multiplier saturation / downstream shift. The shifts earlier identified (`shr 0xc`, `shr 0x14`) are downstream of mulhi — reducing one by 1 doubles output. This IS a single-byte patch possibility.

## Fallback: downstream shift patch (less invasive than expected, worth trying if RX hunt stalls)
From earlier raw-byte scan of torque_angle_reader_Q15:
- `shr 0xc, tp` at vaddr 0x10babf5 — if tp holds multiplier result, changing to `shr 0xb` doubles output
- `shr 0x14, tp` at vaddr 0x10bac43 — similar, changing to `shr 0x13` doubles
- `shr 0x4, gp` at vaddr 0x10bac27 — less likely to be the right one (small shift = less leverage)

For `shr imm5, reg2` V850 Format II:
- encoding: `iiiii 101011 rrrrr` (op=0x2B, 6 bits)
- Halfword LE bytes: `HH LL` where HH = (reg2<<3) | imm5[4:2], LL = (imm5[1:0]<<6) | opcode(6 bits) = ...

Actually Format II details for `shr imm5, reg2`:
- bits [15:11] = reg2
- bits [10:5]  = op (0x10 I think? need to verify)
- bits [4:0]   = imm5

Imm5 occupies the reg1 slot. So patching an imm5 is modifying the low 5 bits of the first instruction halfword.

## Immediate todo
When loop resumes: try the "case 0x1900" search and the openpilot carcontroller.py inspection in parallel. If both dead, pivot to the shift patch at 0x10babf5 (change `shr 0xc` to `shr 0xb`).
