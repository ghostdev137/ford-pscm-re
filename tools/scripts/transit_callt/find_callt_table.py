#!/usr/bin/env python3
"""Find callt table by structural self-consistency since CTBP is not set in
any of the available Transit flash dumps.

Strategy:
- The callt table is a contiguous run of 16-bit LE offsets.
- Each offset, when added to CTBP, must point to valid code.
- CTBP must be halfword-aligned.
- If table is at VA T, we'd typically have CTBP == T itself (common compiler
  convention), so offsets are relative to table start.
- Heuristic: slide a candidate-CTBP window over 0x01000000..0x010FF000 at
  halfword stride. For each candidate, read the next 64 halfwords as offsets,
  compute candidate+offset targets, check what fraction land on plausible
  code starts (address inside image and inside executable-looking region).

This is expensive but tractable.
"""
import sys
PATH="/Users/rossfisher/Desktop/Transit_2025_PSCM_dump/transit_AM_blk0_0x01000000.bin"
BASE=0x01000000
d=open(PATH,"rb").read()
SIZE=len(d)

def u16(off): return d[off]|(d[off+1]<<8)

# Precompute: "looks like code start" — halfword-aligned, not 0xFFFF, not 0x0000
def looks_code(va):
    off = va - BASE
    if off < 0 or off+2 > SIZE: return False
    hw = u16(off)
    if hw in (0x0000, 0xFFFF): return False
    # Common function prologue on RH850: prepare or mov sp... or addi -N, sp, sp
    # Conservative: just require non-trivial halfword + halfword-aligned
    return True

best=[]
# Scan CTBP candidates every 2 bytes; entries must all be non-zero, and at least
# 32 of 64 must point to plausible code starts.
for ctbp_off in range(0, SIZE-128, 2):
    good=0; total=0; nonzero=0
    for i in range(64):
        hw = u16(ctbp_off + i*2)
        if hw == 0: continue
        if hw == 0xFFFF: break
        nonzero += 1
        target_off = ctbp_off + hw  # offset from CTBP
        if 0 <= target_off < SIZE-2:
            thw = u16(target_off)
            if thw not in (0x0000, 0xFFFF):
                good += 1
        total += 1
    if nonzero >= 16 and good >= max(12, int(nonzero*0.75)):
        best.append((good, nonzero, ctbp_off))

best.sort(reverse=True)
print(f"Top 20 callt-table candidates (score=good_targets, nonzero_entries, CTBP_VA):")
for g, nz, off in best[:20]:
    print(f"  CTBP=0x{BASE+off:08x}  good={g}/{nz}")
