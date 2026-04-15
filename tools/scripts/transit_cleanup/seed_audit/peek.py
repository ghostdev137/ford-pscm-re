#!/usr/bin/env python3
"""Dump raw bytes around a few sample still-halt addrs plus the 5 'rejected halt'
addrs (confirming they look like data), plus check the r1115 pattern frequency."""
BIN="/Users/rossfisher/Desktop/Transit_2025_PSCM_dump/transit_AM_blk0_0x01000000.bin"
BASE=0x01000000
with open(BIN,"rb") as f: blob=f.read()

def dump(a,n=24):
    o=a-BASE; return blob[o:o+n].hex()

print("== still-halt (B) samples ==")
for a in [0x01002000,0x01002068,0x0100310c,0x01003126,0x01003a40]:
    print(f" {a:08x}: {dump(a)}")

print("\n== rejected halt (A) samples (should look like data/pad/ascii) ==")
for a in [0x01002028,0x010052a4,0x010070a0,0x01009158,0x0100916c]:
    print(f" {a:08x}: {dump(a)}")
