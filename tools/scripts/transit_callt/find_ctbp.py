#!/usr/bin/env python3
"""Find CTBP init via ldsr rX, 20, 0 byte pattern in Transit firmware.

RH850 LDSR encoding (Format IX):
  HW1 bits 15-0: rrrrr(regID) 111111 RRRRR(reg2)
  HW2 bits 15-0: sssss(selID) 00000 100000
For CTBP: regID=20 (10100b), selID=0 (00000b)
  HW1 = 0xA7E0 | reg2   (reg2 in 0..31)
  HW2 = 0x0020
LE bytes on disk: [HW1&0xff, HW1>>8, 0x20, 0x00]
"""
import sys, struct, os

PATH = "/Users/rossfisher/Desktop/Transit_2025_PSCM_dump/transit_AM_blk0_0x01000000.bin"
BASE = 0x01000000

def u16le(b, o): return b[o] | (b[o+1]<<8)
def u32le(b, o): return b[o] | (b[o+1]<<8) | (b[o+2]<<16) | (b[o+3]<<24)

with open(PATH,"rb") as f: data = f.read()

hits = []
# Scan halfword aligned
for off in range(0, len(data)-4, 2):
    hw1 = u16le(data, off)
    hw2 = u16le(data, off+2)
    if (hw1 & 0xFFE0) == 0xA7E0 and hw2 == 0x0020:
        reg2 = hw1 & 0x1F
        hits.append((off, reg2))

print(f"Found {len(hits)} ldsr rX, 20, 0 (CTBP) sites")
# For each hit, try to reconstruct the constant loaded into rX via preceding movhi/movea.
# RH850 movea: Format VI: imm16 rrrrr 110001 RRRRR  -> movea imm16, reg1, reg2   reg2 <- reg1 + sign_ext(imm16)
# RH850 movhi: same form but opcode 110010 -> reg2 <- reg1 + (imm16<<16)
# LE halfword pattern: HW1 = rrrrr(reg1) 11001X RRRRR(reg2); followed by HW2 = imm16
# movhi HW1: (reg1<<11) | (0x32<<5) | reg2   = reg1<<11 | 0x0640 | reg2
# movea HW1: (reg1<<11) | (0x31<<5) | reg2   = reg1<<11 | 0x0620 | reg2

def decode_mov(hw1, hw2):
    op = (hw1 >> 5) & 0x3F
    reg1 = (hw1 >> 11) & 0x1F
    reg2 = hw1 & 0x1F
    if op == 0x32: return ("movhi", reg1, reg2, hw2)
    if op == 0x31: return ("movea", reg1, reg2, hw2)
    return None

for off, reg2 in hits:
    va = BASE + off
    # Look back up to 24 bytes for movhi/movea targeting reg2
    acc = {}  # register -> known value
    ctx = []
    start = max(0, off-32)
    # Walk forward from start through halfwords, executing movhi/movea
    p = start
    while p < off:
        if p+4 > len(data): break
        hw1 = u16le(data, p); hw2 = u16le(data, p+2)
        m = decode_mov(hw1, hw2)
        if m:
            mn, r1, r2, imm = m
            if mn == "movhi":
                base = acc.get(r1, 0 if r1==0 else None)
                if base is not None:
                    acc[r2] = (base + (imm<<16)) & 0xFFFFFFFF
                ctx.append(f"{p+BASE:08x} movhi 0x{imm:04x}, r{r1}, r{r2}")
            else:
                base = acc.get(r1, 0 if r1==0 else None)
                if base is not None:
                    se = imm if imm < 0x8000 else imm - 0x10000
                    acc[r2] = (base + se) & 0xFFFFFFFF
                ctx.append(f"{p+BASE:08x} movea 0x{imm:04x}, r{r1}, r{r2}")
            p += 4
        else:
            p += 2
    ctbp_val = acc.get(reg2)
    print(f"\n@ VA {va:08x}  ldsr r{reg2}, 20, 0   => CTBP = {('0x%08x'%ctbp_val) if ctbp_val is not None else '??'}")
    for line in ctx[-6:]:
        print("   " + line)
