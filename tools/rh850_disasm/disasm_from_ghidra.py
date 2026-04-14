#!/usr/bin/env python3
"""
Disassemble every function Ghidra flagged as valid, using the tizmd RH850
decoder. Skips bogus entries (all-FF bytes, tiny body, invalid first insn).

Input:  /tmp/ghidra_function_list.tsv  (from DumpFunctionList.java)
Output: ~/ford-pscm-re/analysis/transit_disasm/functions/FUN_<VA>.asm
        ~/ford-pscm-re/analysis/transit_disasm/all.asm
        ~/ford-pscm-re/analysis/transit_disasm/index.tsv
"""
import os, sys, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "vendor", "rh850-tools"))
from binja_v850.opcode_table import decode
from binja_v850.enums import Subarch, MNEM

BIN_PATH = os.path.expanduser("~/Desktop/Transit_2025_PSCM_dump/transit_AM_blk0_0x01000000.bin")
BASE_VA  = 0x01000000
FUNC_TSV = "/tmp/ghidra_function_list.tsv"
OUT_DIR  = os.path.expanduser("~/ford-pscm-re/analysis/transit_disasm")
MAX_INSNS = 4000  # per function safety cap

def load_functions(path):
    """Return list of (va, name, body_size), pruning obvious bogus entries."""
    out = []
    with open(path) as f:
        next(f)  # header
        for line in f:
            va_hex, name, body, first = line.rstrip().split("\t")
            va = int(va_hex, 16)
            body = int(body)
            if first == "ffffffff": continue          # erased flash
            if body < 4: continue                      # too tiny
            out.append((va, name, body))
    return sorted(out)

def disasm_function(data, va, max_bytes):
    pc = va - BASE_VA
    end = min(pc + max_bytes, len(data))
    lines = []
    for _ in range(MAX_INSNS):
        if pc >= end: break
        bs = data[pc:pc+8]
        if len(bs) < 2: break
        try:
            mnem, ops, hw = decode(bs, subarch=Subarch.RH850)
            n = hw * 2
            name = mnem.name.lower().replace("_", ".")
            ops_s = ", ".join(str(o) for o in ops)
            raw = data[pc:pc+n].hex()
            lines.append(f"{BASE_VA+pc:08X}: {raw:<12} {name:<10} {ops_s}")
            pc += n
            # Stop at `jmp [lp]` — RH850 return convention
            if mnem == MNEM.JMP and ops_s.strip() == "[LP]":
                break
        except Exception as e:
            lines.append(f"{BASE_VA+pc:08X}: {data[pc:pc+2].hex():<12} ???        <{e}>")
            pc += 2
    return lines

def main():
    os.makedirs(os.path.join(OUT_DIR, "functions"), exist_ok=True)
    data = open(BIN_PATH, "rb").read()
    funcs = load_functions(FUNC_TSV)
    print(f"[i] {len(funcs)} candidate functions (after bogus-prune)")

    all_lines = []
    index_lines = ["va\tname\tbody\tasm_file\tinsns"]
    written = 0
    for va, name, body in funcs:
        lines = disasm_function(data, va, body)
        fname = f"FUN_{va:08X}.asm"
        with open(os.path.join(OUT_DIR, "functions", fname), "w") as f:
            f.write(f"; {name}  va=0x{va:08X}  body={body}B  insns={len(lines)}\n")
            f.write("\n".join(lines) + "\n")
        all_lines.append(f"\n; ==== {name} (va=0x{va:08X}, {len(lines)} insns) ====")
        all_lines.extend(lines)
        index_lines.append(f"{va:08X}\t{name}\t{body}\t{fname}\t{len(lines)}")
        written += 1
        if written % 500 == 0:
            print(f"  {written}/{len(funcs)}")

    with open(os.path.join(OUT_DIR, "all.asm"), "w") as f:
        f.write("\n".join(all_lines) + "\n")
    with open(os.path.join(OUT_DIR, "index.tsv"), "w") as f:
        f.write("\n".join(index_lines) + "\n")
    print(f"[✓] {written} functions written to {OUT_DIR}/functions/")
    sz_mb = sum(os.path.getsize(os.path.join(OUT_DIR, "functions", fn))
                for fn in os.listdir(os.path.join(OUT_DIR, "functions"))) / 1024 / 1024
    print(f"[✓] total size: {sz_mb:.1f} MB")
    print(f"[✓] combined:   {OUT_DIR}/all.asm")
    print(f"[✓] index:      {OUT_DIR}/index.tsv")

if __name__ == "__main__":
    main()
