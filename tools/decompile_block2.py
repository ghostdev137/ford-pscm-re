#!/usr/bin/env python3
"""
Decompile transit_block2_ext.bin (EPS firmware block2) into searchable C pseudocode.

Pipeline:
  1. Load block2 + block0 binaries
  2. Set up DataBlocks for cross-block data resolution
  3. Find code end (first long 0xFFFF run)
  4. Linear sweep to collect entry points (PREPARE, JARL targets, post-return)
  5. Recursive descent disassembly from those entry points
  6. Decompile each function (structured C or annotated asm fallback)
  7. Write output/block2_full.c and output/block2_index.txt
"""

import os
import sys
import struct
import time
import re

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_DIR)

from tools.v850.decoder import V850Decoder
from tools.v850.models import Instruction, REG_NAMES, sign_extend
from tools.v850.cfg import ControlFlowGraph, _is_conditional_branch
from tools.v850.analyzer import FirmwareAnalyzer
from tools.v850.structurer import Decompiler
from tools.v850.propagate import (
    DataBlocks, set_data_blocks, CAN_IDS, annotate_address, annotate_can_id,
)

# ── Configuration ──────────────────────────────────────────────────────────
BLOCK2_PATH = os.path.join(PROJECT_DIR, "bins", "transit_block2_ext.bin")
BLOCK0_PATH = os.path.join(PROJECT_DIR, "bins", "transit_strategy_AM.bin")
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "output")
BLOCK2_BASE = 0x20FF0000
BLOCK0_BASE = 0x01000000
MAX_DECOMPILE_INSNS = 3000
FALLBACK_LARGE = True


def load_binary(path):
    with open(path, "rb") as f:
        return f.read()


def find_code_end(data, base):
    """Scan for the first run of >32 consecutive 0xFFFF halfwords."""
    run = 0
    for off in range(0, len(data) - 1, 2):
        hw = struct.unpack_from('<H', data, off)[0]
        if hw == 0xFFFF:
            run += 1
            if run > 32:
                end_off = off - (run - 1) * 2
                return base + end_off
        else:
            run = 0
    return base + len(data)


def collect_entry_points(data, base, code_end_addr):
    """Linear sweep to find all plausible entry points."""
    decoder = V850Decoder()
    code_len = code_end_addr - base
    entries = set()
    jarl_targets = set()
    offset = 0
    prev_was_return = False

    while offset < code_len:
        insn = decoder.decode(data, offset, base)
        if insn is None:
            offset += 2
            prev_was_return = False
            continue

        if insn.mnemonic == '.fill':
            offset += insn.size
            prev_was_return = False
            continue

        addr = base + offset
        hw0 = struct.unpack_from('<H', data, offset)[0]

        # PREPARE detection
        if (hw0 & 0xFFE0) == 0x0780:
            entries.add(addr)

        # Post-return entry point
        if prev_was_return:
            entries.add(addr)

        # JARL branch targets
        if insn.mnemonic == 'jarl' and insn.branch_target is not None:
            t = insn.branch_target
            if base <= t < code_end_addr:
                jarl_targets.add(t)
                entries.add(t)

        # Track if other branch instructions point somewhere
        if insn.is_call and insn.branch_target is not None:
            t = insn.branch_target
            if base <= t < code_end_addr:
                entries.add(t)

        # Post-return: DISPOSE with return, or JMP [lp]
        prev_was_return = False
        if insn.is_return:
            prev_was_return = True
        elif insn.mnemonic == 'dispose' and insn.is_branch:
            prev_was_return = True

        offset += insn.size

    return sorted(entries), jarl_targets


def annotated_asm_fallback(func_addr, instructions):
    """Produce annotated disassembly with register tracking for large/failed functions."""
    lines = []
    lines.append(f"void func_0x{func_addr:08X}() {{")
    lines.append(f"    // Annotated disassembly ({len(instructions)} instructions)")
    lines.append(f"    // Decompiler fallback: function too large or decompilation failed")
    lines.append("")

    # Simple register tracker
    regs = {0: 0}  # r0 = 0

    for insn in instructions:
        comment_parts = []
        m = insn.mnemonic
        parts = insn.op_str.split(", ")

        # Track registers
        try:
            if m == "movhi" and len(parts) == 3:
                imm = int(parts[0], 0)
                r1_name = parts[1].strip()
                r2_name = parts[2].strip()
                r1 = REG_NAMES.index(r1_name) if r1_name in REG_NAMES else None
                r2 = REG_NAMES.index(r2_name) if r2_name in REG_NAMES else None
                if r1 is not None and r2 is not None:
                    base_val = regs.get(r1, 0)
                    result = ((imm << 16) + base_val) & 0xFFFFFFFF
                    regs[r2] = result
                    comment_parts.append(f"{r2_name} = 0x{result:08X}")

            elif m == "movea" and len(parts) == 3:
                imm = int(parts[0], 0)
                r1_name = parts[1].strip()
                r2_name = parts[2].strip()
                r1 = REG_NAMES.index(r1_name) if r1_name in REG_NAMES else None
                r2 = REG_NAMES.index(r2_name) if r2_name in REG_NAMES else None
                if r1 is not None and r2 is not None and r1 in regs:
                    result = (regs[r1] + sign_extend(imm & 0xFFFF, 16)) & 0xFFFFFFFF
                    regs[r2] = result
                    ann = annotate_address(result)
                    if ann:
                        comment_parts.append(f"{r2_name} = 0x{result:08X} ({ann})")
                    else:
                        comment_parts.append(f"{r2_name} = 0x{result:08X}")

            elif m == "mov" and len(parts) == 2:
                src, dst = parts[0].strip(), parts[1].strip()
                dst_idx = REG_NAMES.index(dst) if dst in REG_NAMES else None
                if dst_idx is not None:
                    if src in REG_NAMES:
                        s_idx = REG_NAMES.index(src)
                        if s_idx in regs:
                            regs[dst_idx] = regs[s_idx]
                    else:
                        try:
                            val = int(src, 0)
                            regs[dst_idx] = val & 0xFFFFFFFF
                        except ValueError:
                            pass

            elif m == "addi" and len(parts) == 3:
                imm = int(parts[0], 0)
                r1_name = parts[1].strip()
                r2_name = parts[2].strip()
                r1 = REG_NAMES.index(r1_name) if r1_name in REG_NAMES else None
                r2 = REG_NAMES.index(r2_name) if r2_name in REG_NAMES else None
                if r1 is not None and r2 is not None and r1 in regs:
                    result = (regs[r1] + sign_extend(imm & 0xFFFF, 16)) & 0xFFFFFFFF
                    regs[r2] = result

            # Annotate LD/ST with resolved addresses
            if m.startswith("ld.") or m.startswith("st."):
                op = insn.op_str
                bracket_s = op.find('[')
                bracket_e = op.find(']')
                if bracket_s >= 0 and bracket_e >= 0:
                    base_reg = op[bracket_s+1:bracket_e].strip()
                    if base_reg in REG_NAMES:
                        reg_idx = REG_NAMES.index(base_reg)
                        if reg_idx in regs:
                            # Extract displacement
                            if m.startswith("ld."):
                                disp_str = op[:bracket_s].rstrip().rstrip(',').strip()
                            else:
                                sub = op.split(',')
                                if len(sub) >= 2:
                                    disp_str = sub[1].strip().split('[')[0].strip()
                                else:
                                    disp_str = "0"
                            try:
                                disp = int(disp_str, 0)
                            except ValueError:
                                disp = 0
                            data_addr = (regs[reg_idx] + disp) & 0xFFFFFFFF
                            ann = annotate_address(data_addr)
                            rw = "read" if m.startswith("ld.") else "write"
                            if ann:
                                comment_parts.append(f"{rw} {ann}@0x{data_addr:08X}")
                            else:
                                comment_parts.append(f"{rw} 0x{data_addr:08X}")

            # CMP annotations
            if m == "cmp" and len(parts) == 2:
                try:
                    imm = int(parts[0], 0)
                    can = annotate_can_id(imm)
                    if can:
                        comment_parts.append(f"CAN:{can}")
                except ValueError:
                    pass

            # BSW annotation
            if m == "bsw":
                comment_parts.append("byte-swap (BE->LE)")

            # JARL annotation
            if insn.is_call and insn.branch_target is not None:
                comment_parts.append(f"call func_0x{insn.branch_target:08X}")

        except (ValueError, IndexError):
            pass

        # Format output line
        comment = ""
        if comment_parts:
            comment = "  // " + "; ".join(comment_parts)
        lines.append(f"    /* 0x{insn.addr:08X} */  {insn.mnemonic:<10s} {insn.op_str}{comment}")

    lines.append("}")
    return "\n".join(lines)


def build_can_index(functions_code):
    """Build CAN ID cross-reference from the decompiled output."""
    index = {}
    for can_id, name in CAN_IDS.items():
        refs = []
        for func_addr, code in functions_code.items():
            if name in code or f"0x{can_id:X}" in code.upper() or f"0x{can_id:03X}" in code:
                refs.append(func_addr)
        if refs:
            index[can_id] = (name, refs)
    return index


def main():
    t0 = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── 1. Load binaries ───────────────────────────────────────────────────
    print("[1/8] Loading binaries...")
    block2_data = load_binary(BLOCK2_PATH)
    block0_data = load_binary(BLOCK0_PATH)
    print(f"  block2: {len(block2_data):,} bytes (base 0x{BLOCK2_BASE:08X})")
    print(f"  block0: {len(block0_data):,} bytes (base 0x{BLOCK0_BASE:08X})")

    # ── 2. Set up DataBlocks ───────────────────────────────────────────────
    print("[2/8] Setting up cross-block data resolution...")
    db = DataBlocks()
    db.add_block(BLOCK2_BASE, block2_data)
    db.add_block(BLOCK0_BASE, block0_data)
    set_data_blocks(db)

    # ── 3. Find code end ──────────────────────────────────────────────────
    print("[3/8] Finding code region end...")
    code_end = find_code_end(block2_data, BLOCK2_BASE)
    code_size = code_end - BLOCK2_BASE
    print(f"  Code region: 0x{BLOCK2_BASE:08X} - 0x{code_end:08X} ({code_size:,} bytes)")

    # ── 4. Collect entry points ───────────────────────────────────────────
    print("[4/8] Linear sweep for entry points...")
    entry_points, jarl_targets = collect_entry_points(block2_data, BLOCK2_BASE, code_end)
    print(f"  Found {len(entry_points)} entry points ({len(jarl_targets)} JARL targets)")

    # ── 5. Recursive descent disassembly ──────────────────────────────────
    print("[5/8] Recursive descent disassembly...")
    analyzer = FirmwareAnalyzer(block2_data, BLOCK2_BASE, "transit_block2_ext")
    functions = analyzer.disassemble_recursive(entry_points)
    print(f"  Discovered {len(functions)} functions")

    total_insns = sum(len(v) for v in functions.values())
    print(f"  Total instructions: {total_insns:,}")

    # Filter out functions that are beyond the code end or entirely .fill padding
    filtered = {}
    for func_addr, insns in functions.items():
        # Skip functions starting in padding region
        if func_addr >= code_end:
            continue
        # Skip functions that are entirely .fill
        real_insns = [i for i in insns if i.mnemonic != '.fill']
        if not real_insns:
            continue
        filtered[func_addr] = insns
    skipped = len(functions) - len(filtered)
    if skipped:
        print(f"  Filtered out {skipped} padding/empty functions")
    functions = filtered

    total_insns = sum(len(v) for v in functions.values())

    # Sort functions by address
    sorted_funcs = sorted(functions.items(), key=lambda x: x[0])

    # ── 6. Decompile each function ────────────────────────────────────────
    print("[6/8] Decompiling functions...")
    decompiler = Decompiler(block2_data, BLOCK2_BASE)
    functions_code = {}
    stats = {
        'decompiled': 0, 'fallback': 0, 'failed': 0,
        'total_insns': total_insns,
        'if_else': 0, 'while_loops': 0, 'func_calls': 0, 'bswap_ops': 0,
    }

    for i, (func_addr, insns) in enumerate(sorted_funcs):
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            print(f"  ... {i+1}/{len(sorted_funcs)} functions ({elapsed:.1f}s)")

        n_insns = len(insns)

        if n_insns > MAX_DECOMPILE_INSNS:
            # Too large -- fallback
            code = annotated_asm_fallback(func_addr, insns)
            functions_code[func_addr] = code
            stats['fallback'] += 1
            continue

        try:
            code = decompiler.decompile_instructions(func_addr, insns)
            functions_code[func_addr] = code
            stats['decompiled'] += 1
        except Exception:
            # Fallback to annotated asm
            code = annotated_asm_fallback(func_addr, insns)
            functions_code[func_addr] = code
            stats['fallback'] += 1

    print(f"  Decompiled: {stats['decompiled']}, Fallback: {stats['fallback']}, Failed: {stats['failed']}")

    # ── 7. Build output ──────────────────────────────────────────────────
    print("[7/8] Writing output files...")

    # Count structural elements
    for code in functions_code.values():
        stats['if_else'] += code.count('if (')
        stats['while_loops'] += code.count('while (')
        stats['func_calls'] += code.count('func_0x')
        stats['bswap_ops'] += code.count('bswap(')

    # Build CAN index
    can_index = build_can_index(functions_code)

    # Write block2_full.c
    c_path = os.path.join(OUTPUT_DIR, "block2_full.c")
    with open(c_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("/*\n")
        f.write(" * Ford Transit 2025 EPS Firmware - Block 2 Decompilation\n")
        f.write(f" * Binary: transit_block2_ext.bin ({len(block2_data):,} bytes)\n")
        f.write(f" * Base address: 0x{BLOCK2_BASE:08X}\n")
        f.write(f" * Code region: 0x{BLOCK2_BASE:08X} - 0x{code_end:08X} ({code_size:,} bytes)\n")
        f.write(f" * Functions: {len(functions_code)}\n")
        f.write(f" * Total instructions: {total_insns:,}\n")
        f.write(f" * Architecture: V850E2 (RH850), LE instructions, BE data\n")
        f.write(f" * Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(" */\n\n")

        # CAN ID cross-reference index
        f.write("/* ============================================================\n")
        f.write(" * CAN ID Cross-Reference Index\n")
        f.write(" * ============================================================ */\n")
        for can_id in sorted(can_index.keys()):
            name, refs = can_index[can_id]
            ref_str = ", ".join(f"func_0x{r:08X}" for r in refs)
            f.write(f"// CAN 0x{can_id:03X} {name:<30s} -> {ref_str}\n")
        f.write("\n\n")

        # Statistics summary
        f.write("/* ============================================================\n")
        f.write(" * Decompilation Statistics\n")
        f.write(" * ============================================================\n")
        f.write(f" * Structured decompilation: {stats['decompiled']} functions\n")
        f.write(f" * Annotated asm fallback:   {stats['fallback']} functions\n")
        f.write(f" * if/else blocks:           {stats['if_else']}\n")
        f.write(f" * while loops:              {stats['while_loops']}\n")
        f.write(f" * Function calls:           {stats['func_calls']}\n")
        f.write(f" * Byte swap operations:     {stats['bswap_ops']}\n")
        f.write(" * ============================================================ */\n\n")

        # Each function
        for func_addr, code in sorted(functions_code.items()):
            n = len(functions.get(func_addr, []))
            f.write(f"/* ---- func_0x{func_addr:08X} ({n} insns) ---- */\n")
            f.write(code)
            f.write("\n\n")

    c_size = os.path.getsize(c_path)
    print(f"  {c_path}: {c_size:,} bytes")

    # Write block2_index.txt
    idx_path = os.path.join(OUTPUT_DIR, "block2_index.txt")
    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write(f"Block2 Function Index\n")
        f.write(f"Binary: transit_block2_ext.bin ({len(block2_data):,} bytes)\n")
        f.write(f"Base: 0x{BLOCK2_BASE:08X}, Code end: 0x{code_end:08X}\n")
        f.write(f"Total functions: {len(functions_code)}\n")
        f.write(f"Total instructions: {total_insns:,}\n\n")
        f.write(f"{'Address':<14s} {'Insns':>6s} {'Type':<12s} {'Calls':>6s} {'Branches':>9s} {'Notes'}\n")
        f.write("-" * 80 + "\n")

        for func_addr in sorted(functions_code.keys()):
            insns = functions.get(func_addr, [])
            n = len(insns)
            code = functions_code[func_addr]
            is_decomp = "decomp" if "Annotated disassembly" not in code else "asm"
            n_calls = sum(1 for i in insns if i.is_call)
            n_branches = sum(1 for i in insns if i.is_branch and not i.is_call)

            # Check for notable features
            notes = []
            if any(i.mnemonic == 'bsw' for i in insns):
                notes.append("bsw")
            if any(i.mnemonic == 'callt' for i in insns):
                notes.append("callt")
            # Check for CAN ID refs in code
            for can_id_val, name in CAN_IDS.items():
                if name in code:
                    notes.append(f"CAN:{name}")
                    break

            notes_str = ", ".join(notes) if notes else ""
            f.write(f"0x{func_addr:08X}  {n:6d}  {is_decomp:<12s} {n_calls:6d}  {n_branches:9d}  {notes_str}\n")

    idx_size = os.path.getsize(idx_path)
    print(f"  {idx_path}: {idx_size:,} bytes")

    # ── 8. Search output ─────────────────────────────────────────────────
    print("\n[8/8] Searching decompiled output...")
    all_code = "\n".join(functions_code[a] for a in sorted(functions_code.keys()))

    print(f"\n{'='*60}")
    print("DECOMPILATION RESULTS")
    print(f"{'='*60}")
    print(f"Functions:         {len(functions_code)}")
    print(f"Decompiled (C):    {stats['decompiled']}")
    print(f"Fallback (asm):    {stats['fallback']}")
    print(f"Total insns:       {total_insns:,}")
    print(f"if/else blocks:    {stats['if_else']}")
    print(f"while loops:       {stats['while_loops']}")
    print(f"Function calls:    {stats['func_calls']}")
    print(f"bswap operations:  {stats['bswap_ops']}")

    # CMP against small values (LaActAvail states)
    print(f"\n--- CMP against small constants (state machine patterns) ---")
    for val in [0, 1, 2, 3]:
        count_eq = all_code.count(f"== {val})")
        count_ne = all_code.count(f"!= {val})")
        count_lt = all_code.count(f"< {val})")
        count_cmp = all_code.count(f"cmp {val},") + all_code.count(f"cmp 0x{val},")
        print(f"  CMP {val}: == {count_eq}, != {count_ne}, < {count_lt}, cmp_asm {count_cmp}")

    # Timer patterns (increment + compare)
    print(f"\n--- Timer/counter patterns ---")
    add1_count = all_code.count("+ 1)")
    add1_count2 = all_code.count("+ 0x1)")
    print(f"  ADD 1 patterns:  {add1_count + add1_count2}")

    # Block0 cross-references
    print(f"\n--- Block0 (strategy) cross-references ---")
    block0_refs = 0
    block0_addrs = set()
    for line in all_code.split('\n'):
        if '0x0100' in line or 'STRATEGY' in line:
            for m in re.finditer(r'0x0100[0-9A-Fa-f]{4}', line):
                block0_addrs.add(m.group())
                block0_refs += 1
    print(f"  References to 0x0100xxxx: {block0_refs}")
    print(f"  Unique block0 addresses: {len(block0_addrs)}")
    if block0_addrs:
        for addr in sorted(block0_addrs)[:20]:
            print(f"    {addr}")
        if len(block0_addrs) > 20:
            print(f"    ... and {len(block0_addrs) - 20} more")

    # CAN ID annotations
    print(f"\n--- CAN ID annotations ---")
    for can_id in sorted(can_index.keys()):
        name, refs = can_index[can_id]
        print(f"  0x{can_id:03X} {name}: {len(refs)} functions")

    # Also search for CAN IDs in code
    print(f"\n--- CAN ID values in code ---")
    for can_id, name in sorted(CAN_IDS.items()):
        count = all_code.count(name)
        hex_count = all_code.upper().count(f"0x{can_id:03X}")
        if count > 0 or hex_count > 0:
            print(f"  0x{can_id:03X} {name}: {count} name refs, {hex_count} hex refs")

    # Memory region references
    print(f"\n--- Memory region references ---")
    for region_name in ["CALIBRATION", "STRATEGY_DATA", "STRATEGY_CODE", "STRATEGY_CONFIG", "RAM", "PERIPHERAL", "BLOCK2_CODE"]:
        count = all_code.count(region_name)
        if count > 0:
            print(f"  {region_name}: {count} references")

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed:.1f}s")
    print(f"Output: {c_path} ({c_size:,} bytes)")
    print(f"Output: {idx_path} ({idx_size:,} bytes)")


if __name__ == "__main__":
    main()
