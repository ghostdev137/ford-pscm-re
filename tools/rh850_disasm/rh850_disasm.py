#!/usr/bin/env python3
"""
Standalone RH850 disassembler for the Ford Transit PSCM firmware.
Wraps the tizmd/binja-v850 decoder (no Binary Ninja required).

Usage:
  rh850_disasm.py <bin> <base_va> <start_va> [<end_va>|+N]
  rh850_disasm.py transit_pscm.elf 0x01000000 0x01050000 +400

Produces:
  01050000: 7528         sld.hu   5[ep], tp
  01050002: 2844         sld.b    40[ep], r8
  ...
"""
import sys, struct, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "vendor", "rh850-tools"))
from binja_v850.opcode_table import decode
from binja_v850.enums import Subarch

def load_range(path, base_va, start_va, length):
    with open(path, "rb") as f:
        data = f.read()
    # If it's an ELF, pull the main program segment(s) rather than the whole file
    if data[:4] == b"\x7fELF":
        import struct as st
        # parse ELF32 LE program headers, find segment covering start_va
        e_phoff = st.unpack_from("<I", data, 0x1C)[0]
        e_phentsize = st.unpack_from("<H", data, 0x2A)[0]
        e_phnum = st.unpack_from("<H", data, 0x2C)[0]
        for i in range(e_phnum):
            o = e_phoff + i * e_phentsize
            p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = \
                st.unpack_from("<IIIIIIII", data, o)
            if p_type == 1 and p_vaddr <= start_va < p_vaddr + p_filesz:
                file_off = p_offset + (start_va - p_vaddr)
                return data[file_off : file_off + length]
        raise ValueError(f"no ELF LOAD segment covers va=0x{start_va:08X}")
    else:
        file_off = start_va - base_va
        return data[file_off : file_off + length]

def fmt_operand(op):
    return str(op)

def disassemble(path, base_va, start_va, end_va, subarch=Subarch.RH850):
    length = end_va - start_va
    payload = load_range(path, base_va, start_va, length)
    pc = 0
    out = []
    invalid_count = 0
    total = 0
    while pc < len(payload) - 1:
        bs = payload[pc : pc + 8]
        try:
            mnem, operands, hw_size = decode(bs, subarch=subarch)
            byte_size = hw_size * 2  # decoder returns size in halfwords
            name = mnem.name.lower().replace("_", ".")
            ops = ", ".join(fmt_operand(o) for o in operands)
            raw = payload[pc : pc + byte_size].hex()
            valid = "INVALID" not in mnem.name
        except Exception as e:
            byte_size = 2
            name = "???"
            ops = f"<decode error: {e}>"
            raw = payload[pc : pc + 2].hex()
            valid = False
        out.append(f"{base_va_of(start_va, pc):08X}: {raw:<12} {name:<10} {ops}")
        if not valid:
            invalid_count += 1
        total += 1
        pc += byte_size
    return out, total, invalid_count

def base_va_of(start_va, offset):
    return start_va + offset

def parse_arg(arg, default=0):
    if arg is None: return default
    arg = arg.strip()
    if arg.startswith("+"): return int(arg[1:], 0)
    return int(arg, 0)

def main():
    if len(sys.argv) < 4:
        print(__doc__, file=sys.stderr); sys.exit(1)
    path = sys.argv[1]
    base_va = parse_arg(sys.argv[2])
    start_va = parse_arg(sys.argv[3])
    end_arg = sys.argv[4] if len(sys.argv) > 4 else "+0x80"
    if end_arg.startswith("+"):
        end_va = start_va + parse_arg(end_arg)
    else:
        end_va = parse_arg(end_arg)
    lines, total, invalid = disassemble(path, base_va, start_va, end_va)
    for L in lines:
        print(L)
    print(f"; -- {total} insns, {invalid} invalid, coverage {100*(total-invalid)/max(total,1):.1f}%",
          file=sys.stderr)

if __name__ == "__main__":
    main()
