#!/usr/bin/env python3
"""
Recursive-descent disassembler for RH850 Transit PSCM firmware.

Follows control flow from seed addresses through every branch/call/jump
target. Anything reached is code; anything not reached is data. Skips
Ghidra's bogus data-as-code seeds.

Output:
  ~/ford-pscm-re/analysis/transit_disasm/rd_functions/FUN_<VA>.asm
  ~/ford-pscm-re/analysis/transit_disasm/rd_index.tsv
  ~/ford-pscm-re/analysis/transit_disasm/rd_coverage.json
"""
import os, sys, struct, json
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "vendor", "rh850-tools"))
from binja_v850.opcode_table import decode
from binja_v850.enums import Subarch, MNEM

BIN_PATH = os.path.expanduser("~/Desktop/Transit_2025_PSCM_dump/transit_AM_blk0_0x01000000.bin")
BASE_VA  = 0x01000000
BIN_END_VA = 0x01100000       # 1 MB strategy block
OUT_DIR  = os.path.expanduser("~/ford-pscm-re/analysis/transit_disasm")
GHIDRA_TSV = "/tmp/ghidra_function_list.tsv"

# Mnemonics that terminate straight-line execution.
STOP_MNEMS = {MNEM.JMP, MNEM.JR}     # JMP=register-indirect (return), JR=long unconditional
COND_BRANCH = {MNEM.B}               # conditional branch (cond is first operand)
CALL_MNEMS = {MNEM.JARL, MNEM.CALLT} # call and link / call-table

def load_seeds():
    """Load Ghidra-seeded addresses that pass a bogus-prune filter."""
    seeds = []
    try:
        with open(GHIDRA_TSV) as f:
            next(f)
            for line in f:
                va_hex, _, body, first = line.rstrip().split("\t")
                if first == "ffffffff" or int(body) < 4:
                    continue
                seeds.append(int(va_hex, 16))
    except FileNotFoundError:
        pass
    return seeds

def extract_target(operands, pc_va, insn_size):
    """Pull a concrete VA from a branch/call operand if we can."""
    for op in operands:
        s = str(op)
        # JumpAddress operands render as "PC±N" or "0xVA"
        if s.startswith("PC+") or s.startswith("PC-"):
            try:
                off = int(s[2:])
                return pc_va + off
            except ValueError:
                pass
        # Some renderers produce raw VA
        if s.startswith("0x") or s.startswith("0X"):
            try:
                return int(s, 16)
            except ValueError:
                pass
        # Plain hex digits
        try:
            v = int(s, 16)
            if BASE_VA <= v < BIN_END_VA:
                return v
        except ValueError:
            pass
    return None

def walk(data, seeds, max_steps=10_000_000):
    """Recursive descent. Returns dict: va -> (mnem_name, size_bytes, operands_str)."""
    visited = {}
    function_entries = set(seeds)
    worklist = list(seeds)
    steps = 0
    while worklist and steps < max_steps:
        pc_va = worklist.pop()
        while True:
            steps += 1
            if pc_va in visited: break
            if not (BASE_VA <= pc_va < BIN_END_VA): break
            foff = pc_va - BASE_VA
            bs = data[foff:foff+8]
            if len(bs) < 2: break
            try:
                mnem, ops, hw = decode(bs, subarch=Subarch.RH850)
            except Exception:
                break
            size_b = hw * 2
            if "INVALID" in mnem.name: break
            ops_str = ", ".join(str(o) for o in ops)
            visited[pc_va] = (mnem.name.lower().replace("_", "."),
                              size_b, ops_str, bs[:size_b].hex())
            # Branch/call targets
            tgt = extract_target(ops, pc_va, size_b)
            if mnem in CALL_MNEMS and tgt is not None:
                function_entries.add(tgt)
                worklist.append(tgt)
                pc_va += size_b    # continue after call
                continue
            if mnem in COND_BRANCH and tgt is not None:
                worklist.append(tgt)
                pc_va += size_b
                continue
            if mnem in STOP_MNEMS:
                # Unconditional — if we can resolve target, follow it; else stop
                if tgt is not None:
                    worklist.append(tgt)
                break
            pc_va += size_b
    return visited, function_entries, steps

def build_functions(visited, entries):
    """Split visited addresses into per-function listings using entry set."""
    sorted_entries = sorted(e for e in entries if e in visited)
    funcs = {}
    for i, ep in enumerate(sorted_entries):
        next_ep = sorted_entries[i+1] if i+1 < len(sorted_entries) else BIN_END_VA
        addrs = sorted(a for a in visited if ep <= a < next_ep)
        if not addrs: continue
        funcs[ep] = addrs
    return funcs

def main():
    os.makedirs(os.path.join(OUT_DIR, "rd_functions"), exist_ok=True)
    data = open(BIN_PATH, "rb").read()
    seeds = load_seeds()
    print(f"[i] {len(seeds)} seeds (Ghidra-pruned)")
    visited, entries, steps = walk(data, seeds)
    print(f"[i] walked {steps} steps, visited {len(visited)} instruction addresses")
    print(f"[i] reachable function entries: {len(entries)}")
    funcs = build_functions(visited, entries)
    print(f"[i] built {len(funcs)} functions")

    with open(os.path.join(OUT_DIR, "rd_index.tsv"), "w") as f:
        f.write("va\tinsns\tfirst_insn\n")
        for ep, addrs in sorted(funcs.items()):
            first = visited[addrs[0]]
            f.write(f"{ep:08X}\t{len(addrs)}\t{first[0]} {first[2]}\n")

    for ep, addrs in funcs.items():
        path = os.path.join(OUT_DIR, "rd_functions", f"FUN_{ep:08X}.asm")
        with open(path, "w") as f:
            f.write(f"; FUN_{ep:08X}  ({len(addrs)} insns, recursive-descent)\n")
            for a in addrs:
                mn, sz, ops, raw = visited[a]
                f.write(f"{a:08X}: {raw:<12} {mn:<10} {ops}\n")

    total_bytes = sum(visited[a][1] for a in visited)
    coverage = {
        "seeds": len(seeds),
        "visited_insns": len(visited),
        "functions": len(funcs),
        "code_bytes": total_bytes,
        "strategy_bytes": BIN_END_VA - BASE_VA,
        "coverage_pct": round(100 * total_bytes / (BIN_END_VA - BASE_VA), 2),
    }
    with open(os.path.join(OUT_DIR, "rd_coverage.json"), "w") as f:
        json.dump(coverage, f, indent=2)
    print(f"[✓] coverage: {coverage['coverage_pct']}% of strategy "
          f"({total_bytes}/{BIN_END_VA-BASE_VA} bytes)")
    print(f"[✓] wrote to {OUT_DIR}/rd_functions/")

if __name__ == "__main__":
    main()
