"""Scan Transit functions in the override-candidate range (0x010B4000-0x010B8000)
and classify each by whether Unicorn RH850 can cleanly execute them. Output:
CSV of address → outcome + block count, for picking override-function candidates
that avoid V850E2M extension opcodes.
"""
import os, sys, signal
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools"))

from unicorn_transit_override_harness import (
    setup_machine, call_function,
)

# Pull candidate function starts from the transit_disasm index
INDEX = REPO / "analysis" / "transit_disasm" / "index.tsv"
candidates = []
with open(INDEX) as f:
    next(f)  # header
    for line in f:
        cols = line.strip().split("\t")
        if not cols: continue
        va = int(cols[0], 16)
        if 0x010B4000 <= va < 0x010B8000:
            candidates.append(va)

print(f"# Found {len(candidates)} candidate function entries in 0x010B4000-0x010B8000")
print(f"addr,blocks,last_pc,reason")

out_path = REPO / "analysis" / "transit" / "emu" / "emulatable.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)
out = open(out_path, "w")
out.write("addr,blocks,last_pc,reason\n")

for i, va in enumerate(candidates):
    try:
        uc = setup_machine()
        r = call_function(uc, va, max_blocks=50)
        line = f"0x{va:08x},{r['blocks']},0x{r['last_pc']:08x},\"{r['reason'] or 'clean'}\""
    except Exception as e:
        line = f"0x{va:08x},-1,0x0,\"exception: {e}\""
    print(line, flush=True)
    out.write(line + "\n")
    out.flush()

out.close()
print(f"\n# Saved {out_path}")
