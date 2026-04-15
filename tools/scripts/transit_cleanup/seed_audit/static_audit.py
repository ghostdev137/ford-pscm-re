#!/usr/bin/env python3
"""Phase 5 static seed audit.

Reads /tmp/pscm/entries.json, loads raw bytes from the transit ELF main
strategy segment, applies heuristics 1-3, emits:
 - /tmp/ghidra_phase5/static_audit.tsv  (addr, decision, reason, bytes16)
 - /tmp/ghidra_phase5/entries_cleaned.json (accepted seeds as JSON int array)
"""
import json, os, struct, sys

SEEDS = "/tmp/pscm/entries.json"
# Main strategy code blob (vaddr 0x01000000, file offset 0, 1 MiB)
BIN   = "/Users/rossfisher/Desktop/Transit_2025_PSCM_dump/transit_AM_blk0_0x01000000.bin"
BASE  = 0x01000000

OUT_DIR = "/tmp/ghidra_phase5"
os.makedirs(OUT_DIR, exist_ok=True)

with open(BIN, "rb") as f:
    blob = f.read()
SIZE = len(blob)
print(f"[+] blob {SIZE:#x} bytes, base {BASE:#x}")

with open(SEEDS) as f:
    seeds = json.load(f)
print(f"[+] seeds total = {len(seeds)}")

# segment histogram
buckets = {"strategy_0x01":0, "ram_0x10":0, "cal_0x20":0, "other":0}
for a in seeds:
    if 0x01000000 <= a <= 0x010FFFFF:   buckets["strategy_0x01"] += 1
    elif 0x10000400 <= a <= 0x100013FF: buckets["ram_0x10"] += 1
    elif 0x20FF0000 <= a <= 0x21040000: buckets["cal_0x20"] += 1
    else: buckets["other"] += 1
print("[+] segment distribution:", buckets)

def readbytes(addr, n=16):
    off = addr - BASE
    if off < 0 or off + n > SIZE: return None
    return blob[off:off+n]

counts = {k:0 for k in ["oob","unaligned","zero_pad","ff_fill","ascii","ok"]}
rows = []
accepted = []

for a in seeds:
    # H1: out of strategy segment
    if not (0x01000000 <= a <= 0x010FFFFF):
        counts["oob"] += 1
        rows.append((a,"REJECT","oob",""))
        continue
    # H2: alignment
    if a & 1:
        counts["unaligned"] += 1
        rows.append((a,"REJECT","unaligned",""))
        continue
    b = readbytes(a, 16)
    if b is None:
        counts["oob"] += 1
        rows.append((a,"REJECT","oob",""))
        continue
    hx = b.hex()
    # H3a: leading 0x0000 + 6 more zero bytes = padding
    if b[0]==0 and b[1]==0 and b[2]==0 and b[3]==0 and b[4]==0 and b[5]==0 and b[6]==0 and b[7]==0:
        counts["zero_pad"] += 1
        rows.append((a,"REJECT","zero_pad",hx))
        continue
    # H3b: 0xFFFF fill
    if b[0]==0xFF and b[1]==0xFF:
        counts["ff_fill"] += 1
        rows.append((a,"REJECT","ff_fill",hx))
        continue
    # H3c: first 4 bytes all printable ASCII
    if all(0x20 <= x <= 0x7E for x in b[:4]):
        counts["ascii"] += 1
        rows.append((a,"REJECT","ascii",hx))
        continue
    counts["ok"] += 1
    rows.append((a,"KEEP","static_ok",hx))
    accepted.append(a)

print("[+] static counts:", counts)
print(f"[+] accepted after static pass: {len(accepted)}")

with open(f"{OUT_DIR}/static_audit.tsv","w") as f:
    f.write("addr\tdecision\treason\tbytes16\n")
    for a,d,r,h in rows:
        f.write(f"{a:08x}\t{d}\t{r}\t{h}\n")

with open(f"{OUT_DIR}/entries_cleaned.json","w") as f:
    json.dump(accepted, f)
print(f"[+] wrote {OUT_DIR}/entries_cleaned.json")
