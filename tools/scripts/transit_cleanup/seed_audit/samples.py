#!/usr/bin/env python3
"""Sample-check: which halt_baddata seeds in baseline were (a) rejected in clean,
(b) still present as halt_baddata in clean, and (c) previously halt_baddata but
now clean."""
import csv

def load(path):
    rows=[]
    with open(path) as f:
        r=csv.DictReader(f, delimiter='\t')
        for row in r: rows.append(row)
    return rows

# baseline = phase4 dynamic audit (contains addr, decision, reason, halt, ...)
base={}
with open("/tmp/ghidra_phase5/dynamic_audit.tsv") as f:
    r=csv.DictReader(f, delimiter='\t')
    for row in r:
        base[row['addr']] = (row['halt_baddata']=='true', row['reason'])

# clean = MeasureQuality tsv: addr size has_halt_baddata has_bad_bm trailing_byte
clean={}
with open("/tmp/ghidra_phase5/clean_measure.tsv") as f:
    r=csv.DictReader(f, delimiter='\t')
    for row in r:
        clean[row['addr']] = (row['has_halt_baddata']=='true', row['has_bad_bm']=='true', int(row['size']))

base_halt = {a for a,(h,_) in base.items() if h}
print(f"baseline halt count = {len(base_halt)}")
clean_halt = {a for a,(h,_,_) in clean.items() if h}
print(f"clean halt count = {len(clean_halt)}")
clean_all = set(clean.keys())

# (A) rejected: in baseline halt, not in clean at all
rejected_halt = sorted(base_halt - clean_all)
print(f"\n== (A) halt_baddata seeds REJECTED (absent in clean): {len(rejected_halt)} ==")
for a in rejected_halt[:5]: print("  ", a)

# (B) still halt_baddata in clean
still_halt = sorted(base_halt & clean_halt)
print(f"\n== (B) halt_baddata STILL present in clean: {len(still_halt)} ==")
for a in still_halt[:5]: print("  ", a, "size=", clean[a][2])

# (C) previously halt, now clean
fixed = sorted(base_halt & (clean_all - clean_halt))
print(f"\n== (C) previously halt_baddata, now CLEAN: {len(fixed)} ==")
for a in fixed[:5]: print("  ", a, "size=", clean[a][2])

# new halt (appeared in clean but not in baseline halt set)
new_halt = sorted(clean_halt - base_halt)
print(f"\nnew halt in clean (not halt in baseline): {len(new_halt)}")
