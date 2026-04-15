#!/usr/bin/env python3
"""Combine static + dynamic audit decisions -> final cleaned seed list."""
import json, os

OUT = "/tmp/ghidra_phase5"
with open(f"{OUT}/entries_cleaned.json") as f:
    static_accept = set(json.load(f))
print(f"static_accepted = {len(static_accept)}")

dyn_reject = set()
dyn_keep = set()
reasons = {}
with open(f"{OUT}/dynamic_audit.tsv") as f:
    next(f)
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3: continue
        addr = int(parts[0], 16)
        decision = parts[1]
        reason = parts[2]
        # Only use hard-data-signal reasons for rejection; "halt_baddata" and
        # "too_short" are too circular / aggressive.
        hard_reject = {"bad_bm", "rare_opcodes"}
        if decision == "REJECT" and reason in hard_reject:
            dyn_reject.add(addr)
            reasons[reason] = reasons.get(reason, 0) + 1
        else:
            dyn_keep.add(addr)

print(f"dyn_rejects by reason: {reasons}")
print(f"dyn_keep = {len(dyn_keep)} dyn_reject = {len(dyn_reject)}")

final = sorted(a for a in static_accept if a not in dyn_reject)
# NB: funcs present in static_accept but NOT in dyn set means Ghidra
# never successfully created a function at that addr - we still drop them.
never_created = static_accept - dyn_keep - dyn_reject
print(f"never_created_in_phase4 = {len(never_created)} (dropped)")

# Final = static-accepted AND not hard-rejected by dynamic heuristics.
# Include ones phase4 never created (maybe clean analysis will succeed).
final = sorted(a for a in static_accept if a not in dyn_reject)
print(f"FINAL cleaned seed count = {len(final)}")

with open(f"{OUT}/entries_cleaned.json","w") as f:
    json.dump(final, f)
print(f"wrote {OUT}/entries_cleaned.json")
