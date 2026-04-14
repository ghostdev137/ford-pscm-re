#!/usr/bin/env python3
"""
Function-wise disassemble of Transit PSCM strategy block.

Reads the function pointer table at file offset 0xE2B0 (seeded by
SeedEntries.java), walks each function entry, and writes per-function
asm listings plus a combined index.

Output:
  <outdir>/functions/FUN_<VA>.asm   — one file per function
  <outdir>/index.txt                — VA → file map with first insn
  <outdir>/all.asm                  — concatenated listing
"""
import sys, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "vendor", "rh850-tools"))
from binja_v850.opcode_table import decode
from binja_v850.enums import Subarch, MNEM

BIN_PATH  = os.path.expanduser("~/Desktop/Transit_2025_PSCM_dump/transit_AM_blk0_0x01000000.bin")
BASE_VA   = 0x01000000
TBL_OFF   = 0x0E008          # file offset of function pointer table (full range)
OUT_DIR   = os.path.expanduser("~/ford-pscm-re/analysis/transit_disasm")
MAX_FUNCS = 3000

RETURN_MNEMS = {MNEM.JMP}     # `jmp [lp]` = return. Heuristic.
MAX_INSNS_PER_FUNC = 2000     # safety cap

def read_function_table(data):
    """Parse 8-byte entries: (size:4BE, funcaddr:4BE). Table in big-endian."""
    addrs = set()
    off = TBL_OFF
    while off + 8 <= len(data):
        size, va = struct.unpack(">II", data[off:off+8])
        if size not in (0x01000000, 0x02000000) or not (BASE_VA <= va < BASE_VA + 0x100000):
            break
        addrs.add(va & ~1)
        off += 8
    return sorted(addrs)

def disassemble_fn(data, start_va, end_va):
    pc = start_va - BASE_VA
    stop = min(end_va - BASE_VA, len(data))
    lines = []
    insns = 0
    while pc < stop and insns < MAX_INSNS_PER_FUNC:
        bs = data[pc:pc+8]
        if len(bs) < 2:
            break
        try:
            mnem, operands, hw = decode(bs, subarch=Subarch.RH850)
            n = hw * 2
        except Exception as e:
            lines.append(f"{BASE_VA+pc:08X}: {data[pc:pc+2].hex():<12} ???        <exception: {e}>")
            pc += 2; insns += 1
            continue
        name = mnem.name.lower().replace("_", ".")
        raw = data[pc:pc+n].hex()
        ops = ", ".join(str(o) for o in operands)
        lines.append(f"{BASE_VA+pc:08X}: {raw:<12} {name:<10} {ops}")
        pc += n
        insns += 1
        # Stop at `jmp [lp]` — RH850 return
        if mnem in RETURN_MNEMS and len(operands) == 1 and str(operands[0]) == "[LP]":
            break
    return lines

def main():
    os.makedirs(os.path.join(OUT_DIR, "functions"), exist_ok=True)
    data = open(BIN_PATH, "rb").read()
    addrs = read_function_table(data)
    if MAX_FUNCS:
        addrs = addrs[:MAX_FUNCS]
    print(f"[i] {len(addrs)} functions to disassemble")

    index_lines = []
    all_lines = []
    for i, va in enumerate(addrs):
        next_va = addrs[i+1] if i+1 < len(addrs) else va + 0x1000
        lines = disassemble_fn(data, va, next_va)
        fname = f"FUN_{va:08X}.asm"
        path = os.path.join(OUT_DIR, "functions", fname)
        with open(path, "w") as f:
            f.write(f"; FUN_{va:08X}  ({len(lines)} insns)\n")
            f.write("\n".join(lines) + "\n")
        first = lines[0] if lines else "<empty>"
        index_lines.append(f"{va:08X}\t{fname}\t{first}")
        all_lines.append(f"\n; ==== FUN_{va:08X} ====")
        all_lines.extend(lines)
        if (i+1) % 200 == 0:
            print(f"  {i+1}/{len(addrs)}")

    with open(os.path.join(OUT_DIR, "index.txt"), "w") as f:
        f.write("VA\tfile\tfirst_insn\n")
        f.write("\n".join(index_lines) + "\n")
    with open(os.path.join(OUT_DIR, "all.asm"), "w") as f:
        f.write("\n".join(all_lines) + "\n")

    print(f"[✓] wrote {len(addrs)} functions to {OUT_DIR}/functions/")
    print(f"[✓] index: {OUT_DIR}/index.txt")
    print(f"[✓] combined: {OUT_DIR}/all.asm")

if __name__ == "__main__":
    main()
