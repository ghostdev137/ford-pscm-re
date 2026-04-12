#!/usr/bin/env python3
"""
Block0 Strategy Decompiler for 2025 Transit PSCM.

Properly identifies CODE vs DATA regions in block0 using strict heuristics,
then uses recursive descent disassembly + decompilation.
Also searches for LKA lockout timer candidates.

Key challenge: V850 ISA is so dense that data decodes as plausible instructions.
We use 256-byte windows with branch + load/store + r0-write checks.
"""

import os
import sys
import struct
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_DIR)

from tools.v850.decoder import V850Decoder
from tools.v850.models import Instruction
from tools.v850.analyzer import FirmwareAnalyzer
from tools.v850.structurer import Decompiler

# ============================================================================
# Configuration
# ============================================================================
BLOCK0_PATH = os.path.join(PROJECT_DIR, "firmware", "2025_Transit_PSCM",
                           "decompressed", "AM", "block0_strategy.bin")
BLOCK2_PATH = os.path.join(PROJECT_DIR, "bins", "transit_block2_ext.bin")
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "output")

BLOCK0_BASE = 0x01000000
BLOCK2_BASE = 0x20FF0000

# Known DATA regions (file offsets) to always exclude
KNOWN_DATA_REGIONS = [
    (0x0000, 0x2000),   # 0xFF fill header
    (0x2000, 0x5400),   # Strings, AUTOSAR names, part numbers
    (0x8400, 0x9400),   # Pointer/config tables
    (0xDB74, 0xDD00),   # DID table + descriptors
]

WINDOW_SIZE = 256


# ============================================================================
# Strict Code/Data Classification
# ============================================================================

def classify_code_regions(data, base_addr, decoder):
    """Classify 256-byte windows as CODE using strict criteria.

    A window is CODE only if:
    - >90% instructions decode to known mnemonics
    - At least 2 branch instructions (control flow)
    - At least 2 load/store instructions (memory access)
    - No more than 2 writes to r0 (r0 is hardwired to 0 on V850)
    - Not in a known data region

    Returns list of (start_offset, end_offset) for CODE regions.
    """
    data_len = len(data)

    # Build set of known-data window indices
    known_data = set()
    for start, end in KNOWN_DATA_REGIONS:
        for off in range(start, min(end, data_len), WINDOW_SIZE):
            known_data.add(off // WINDOW_SIZE)

    code_windows = []

    for win_start in range(0, data_len, WINDOW_SIZE):
        win_idx = win_start // WINDOW_SIZE
        win_end = min(win_start + WINDOW_SIZE, data_len)
        window = data[win_start:win_end]
        win_len = len(window)

        if win_len < 16:
            continue
        if win_idx in known_data:
            continue

        # Quick reject: >50% 0xFF or 0x00
        zero_count = window.count(0x00)
        ff_count = window.count(0xFF)
        if (zero_count + ff_count) > win_len * 0.5:
            continue

        # Decode instructions and count characteristics
        off = 0
        branch_count = 0
        load_store = 0
        unknown_count = 0
        r0_writes = 0
        total = 0

        while off < win_len:
            insn = decoder.decode(data, win_start + off, base_addr)
            if insn is None:
                off += 2
                unknown_count += 1
                total += 1
                continue

            total += 1
            if insn.mnemonic in ('.dw', '.fill'):
                unknown_count += 1
            else:
                if insn.is_branch or insn.mnemonic in ('jr', 'jarl', 'jmp'):
                    branch_count += 1
                if insn.mnemonic.startswith(('ld.', 'st.')):
                    load_store += 1
                # r0 writes = data artifact (r0 is always 0)
                parts = insn.op_str.split(', ')
                if (len(parts) >= 2 and parts[-1] == 'r0'
                        and insn.mnemonic in ('mov', 'movea', 'movhi', 'add',
                                              'and', 'or', 'xor', 'sub')):
                    r0_writes += 1

            off += insn.size

        if total == 0:
            continue

        known_ratio = (total - unknown_count) / total

        # Strict criteria
        if (known_ratio > 0.90
                and branch_count >= 2
                and load_store >= 2
                and r0_writes <= 2):
            code_windows.append(win_idx)

    # Merge adjacent windows
    if not code_windows:
        return []

    regions = []
    start = code_windows[0] * WINDOW_SIZE
    end = start + WINDOW_SIZE
    for i in range(1, len(code_windows)):
        win_off = code_windows[i] * WINDOW_SIZE
        if win_off <= end:
            end = win_off + WINDOW_SIZE
        else:
            regions.append((start, min(end, data_len)))
            start = win_off
            end = win_off + WINDOW_SIZE
    regions.append((start, min(end, data_len)))

    return regions


# ============================================================================
# Entry Point Discovery
# ============================================================================

def find_entry_points(data, base_addr, code_regions, decoder):
    """Find function entry points within verified code regions.

    Uses PREPARE instructions as primary seeds, then adds JARL targets
    and post-return addresses, all constrained to verified code regions.
    """
    entries = set()

    # Build interval lookup for code regions
    def in_code_region(offset):
        for start, end in code_regions:
            if start <= offset < end:
                return True
        return False

    # Pass 1: PREPARE instructions in code regions
    for reg_start, reg_end in code_regions:
        off = reg_start
        while off + 4 <= reg_end:
            hw = struct.unpack_from('<H', data, off)[0]
            if (hw & 0xFFE0) == 0x0780:
                insn = decoder.decode(data, off, base_addr)
                if insn and insn.mnemonic == 'prepare':
                    entries.add(base_addr + off)
            off += 2

    # Pass 2: JARL targets and post-return addresses
    for reg_start, reg_end in code_regions:
        off = reg_start
        while off < reg_end:
            insn = decoder.decode(data, off, base_addr)
            if insn is None:
                off += 2
                continue

            # JARL targets
            if insn.is_call and insn.branch_target is not None:
                tgt_off = insn.branch_target - base_addr
                if 0 <= tgt_off < len(data) and in_code_region(tgt_off):
                    entries.add(insn.branch_target)

            # JR / branch targets
            if insn.is_branch and insn.branch_target is not None and not insn.is_call:
                tgt_off = insn.branch_target - base_addr
                if 0 <= tgt_off < len(data) and in_code_region(tgt_off):
                    entries.add(insn.branch_target)

            # Post-return = next function
            if insn.is_return:
                next_off = off + insn.size
                if in_code_region(next_off):
                    entries.add(base_addr + next_off)

            off += insn.size

    return sorted(entries)


# ============================================================================
# Post-decompilation Quality Filter
# ============================================================================

def is_garbage_function(code):
    """Detect garbage (data-as-code) in decompiled output.

    Garbage indicators:
    - Excessive r0 = 0 (r0 is always 0)
    - Excessive mem32[(ep + 0xF0)] = ep patterns
    - Writes to r0 via assignment
    - Self-referencing nonsense
    """
    lines = code.count('\n')
    if lines < 5:
        return False  # Too small to judge

    r0_zero = code.count('r0 = 0')
    ep_f0 = code.count('ep + 0xF0')
    r0_assign = code.count('r0 = (')

    # Garbage threshold: >5% of lines are r0=0
    if r0_zero > lines * 0.05:
        return True
    # Garbage: repeated ep+0xF0 stores
    if ep_f0 > lines * 0.03:
        return True
    # Garbage: writing to r0 (impossible in real code)
    if r0_assign > 3:
        return True

    return False


# ============================================================================
# Lockout Timer Candidate Detection
# ============================================================================

def analyze_lockout_candidates(functions):
    """Search decompiled functions for LKA lockout timer patterns.

    The lockout timer:
    - Sets LaActAvail_D_Actl (2-bit: 0=suppress, 1=suppress LKA, 2=avail, 3=all)
    - Has a 10-second timer (500@20ms, 1000@10ms, 10000@1ms)
    - Has a 200-300ms recovery timer
    - Reads calibration values (0x00FDxxxx)
    - Uses state machine with values 0/1/2/3
    """
    candidates = []

    for func_addr, code in sorted(functions.items()):
        score = 0
        reasons = []
        lines = code.count('\n')

        # === Strong indicators (LKA-specific) ===

        # Comparisons against BOTH 2 AND 3 (LaActAvail values)
        has_cmp2 = ('== 2)' in code or '>= 2)' in code or '<= 2)' in code
                    or '< 2)' in code or '> 2)' in code)
        has_cmp3 = ('== 3)' in code or '>= 3)' in code or '<= 3)' in code
                    or '< 3)' in code or '> 3)' in code)
        if has_cmp2 and has_cmp3:
            score += 10
            reasons.append('cmp_2_AND_3')

        # State machine assignments: writing 0, 1, 2, 3
        state_assigns = sum(1 for v in ['= 0;', '= 1;', '= 2;', '= 3;'] if v in code)
        if state_assigns >= 3:
            score += 5
            reasons.append('state_' + str(state_assigns))

        # Timer constants (10-second lockout)
        for c in [500, 1000, 10000]:
            hex_c = '0x' + format(c, 'X')
            if hex_c in code:
                score += 5
                reasons.append('timer_' + str(c))

        # Recovery time constants (200-300ms)
        for c in [200, 250, 300]:
            hex_c = '0x' + format(c, 'X')
            if hex_c in code:
                score += 3
                reasons.append('recov_' + str(c))

        # === Medium indicators ===

        # Calibration references (0x00FDxxxx)
        cal = code.count('0x00FD')
        if cal >= 2:
            score += cal * 2
            reasons.append('cal_' + str(cal))

        # CAN RAM buffers (0x4000xxxx)
        ram40 = sum(code.count('0x400' + str(i)) for i in range(4))
        if ram40 >= 3:
            score += 3
            reasons.append('can_' + str(ram40))

        # === Weak indicators ===

        # Multiple branches (state machine)
        if_count = code.count('if (')
        if if_count >= 5:
            score += 2
            reasons.append('branches_' + str(if_count))

        # While loops (timer counting)
        while_count = code.count('while (')
        if while_count >= 1:
            score += 1
            reasons.append('while_' + str(while_count))

        # Medium function size
        if 30 <= lines <= 300:
            score += 1
            reasons.append('size_' + str(lines))

        if score >= 5:
            candidates.append({
                'addr': func_addr,
                'score': score,
                'reasons': reasons,
                'code': code,
                'lines': lines,
            })

    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates


# ============================================================================
# Main
# ============================================================================

def main():
    t0 = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load binaries
    print(f"Loading block0: {BLOCK0_PATH}")
    with open(BLOCK0_PATH, 'rb') as f:
        block0_data = f.read()
    print(f"  Size: {len(block0_data):,} bytes, base: 0x{BLOCK0_BASE:08X}")

    if os.path.exists(BLOCK2_PATH):
        print(f"Loading block2: {BLOCK2_PATH}")
        with open(BLOCK2_PATH, 'rb') as f:
            block2_data = f.read()
        print(f"  Size: {len(block2_data):,} bytes, base: 0x{BLOCK2_BASE:08X}")
    else:
        block2_data = None
        print(f"Block2 not found, skipping cross-references")

    decoder = V850Decoder()

    # ================================================================
    # Step 1: Classify code vs data regions (STRICT)
    # ================================================================
    print("\n" + "="*70)
    print("STEP 1: Classifying code vs data regions (strict)...")
    print("="*70)

    code_regions = classify_code_regions(block0_data, BLOCK0_BASE, decoder)

    total_code_bytes = sum(end - start for start, end in code_regions)
    print(f"Found {len(code_regions)} code regions, {total_code_bytes:,} bytes total "
          f"({100*total_code_bytes/len(block0_data):.1f}% of block0)")

    for i, (start, end) in enumerate(code_regions):
        addr_start = BLOCK0_BASE + start
        addr_end = BLOCK0_BASE + end
        if i < 15 or i >= len(code_regions) - 5:
            print(f"  Region {i:3d}: 0x{addr_start:08X} - 0x{addr_end:08X} "
                  f"({end-start:,} bytes)")
        elif i == 15:
            print(f"  ... ({len(code_regions) - 20} more regions)")

    # ================================================================
    # Step 2: Find entry points in code regions
    # ================================================================
    print("\n" + "="*70)
    print("STEP 2: Finding entry points in verified code regions...")
    print("="*70)

    entry_points = find_entry_points(block0_data, BLOCK0_BASE,
                                     code_regions, decoder)
    print(f"Found {len(entry_points)} entry points")

    for ep in entry_points[:10]:
        print(f"  Entry: 0x{ep:08X}")
    if len(entry_points) > 20:
        print(f"  ... ({len(entry_points) - 20} more)")
        for ep in entry_points[-10:]:
            print(f"  Entry: 0x{ep:08X}")

    # ================================================================
    # Step 3: Recursive descent disassembly
    # ================================================================
    print("\n" + "="*70)
    print("STEP 3: Recursive descent disassembly...")
    print("="*70)

    analyzer = FirmwareAnalyzer(block0_data, BLOCK0_BASE, "block0_strategy")

    t1 = time.time()
    functions = analyzer.disassemble_recursive(entry_points)
    t2 = time.time()

    total_insns = sum(len(insns) for insns in functions.values())
    print(f"Discovered {len(functions)} functions, {total_insns:,} instructions "
          f"in {t2-t1:.1f}s")

    # ================================================================
    # Step 4: Decompile all functions
    # ================================================================
    print("\n" + "="*70)
    print("STEP 4: Decompiling functions...")
    print("="*70)

    decompiler = Decompiler(block0_data, BLOCK0_BASE)
    decompiled = {}
    errors = 0

    for i, func_addr in enumerate(sorted(functions.keys())):
        insns = functions[func_addr]
        if i % 500 == 0 and i > 0:
            elapsed = time.time() - t0
            print(f"  Progress: {i}/{len(functions)} ({elapsed:.0f}s)")

        try:
            code = decompiler.decompile_instructions(func_addr, insns)
            decompiled[func_addr] = code
        except Exception as exc:
            errors += 1
            lines = [f"// DECOMPILE ERROR at 0x{func_addr:08X}: {exc}"]
            lines.append(f"// {len(insns)} instructions")
            for insn in insns[:20]:
                lines.append(f"//   {insn}")
            if len(insns) > 20:
                lines.append(f"//   ... ({len(insns) - 20} more)")
            decompiled[func_addr] = "\n".join(lines)

    print(f"Decompiled {len(decompiled)} functions ({errors} errors)")

    # ================================================================
    # Step 5: Filter garbage functions
    # ================================================================
    print("\n" + "="*70)
    print("STEP 5: Filtering garbage (data-as-code)...")
    print("="*70)

    clean = {}
    garbage_count = 0
    for fa, code in decompiled.items():
        if is_garbage_function(code):
            garbage_count += 1
        else:
            clean[fa] = code

    print(f"Clean functions: {len(clean)} (filtered {garbage_count} garbage)")

    # ================================================================
    # Step 6: Write output
    # ================================================================
    print("\n" + "="*70)
    print("STEP 6: Writing output...")
    print("="*70)

    out_path = os.path.join(OUTPUT_DIR, "block0_code_decompile.c")
    with open(out_path, 'w') as f:
        f.write("// ============================================================\n")
        f.write("// Block0 Strategy Decompilation - 2025 Transit PSCM\n")
        f.write(f"// Base: 0x{BLOCK0_BASE:08X}, Size: {len(block0_data):,} bytes\n")
        f.write(f"// Functions: {len(clean)} clean, {garbage_count} garbage filtered\n")
        f.write(f"// Code regions: {len(code_regions)}, "
                f"Total code: {total_code_bytes:,} bytes "
                f"({100*total_code_bytes/len(block0_data):.1f}%)\n")
        f.write("// ============================================================\n\n")

        for func_addr in sorted(clean.keys()):
            f.write(f"\n/* ---- 0x{func_addr:08X} ---- */\n")
            f.write(clean[func_addr])
            f.write("\n\n")

    print(f"Written: {out_path}")
    file_size = os.path.getsize(out_path)
    print(f"  Size: {file_size:,} bytes")

    # ================================================================
    # Step 7: Search for lockout timer candidates
    # ================================================================
    print("\n" + "="*70)
    print("STEP 7: Searching for LKA lockout timer candidates...")
    print("="*70)

    candidates = analyze_lockout_candidates(clean)

    print(f"Found {len(candidates)} candidate functions")

    cand_path = os.path.join(OUTPUT_DIR, "block0_lockout_candidates.txt")
    with open(cand_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("LKA Lockout Timer Candidates - Block0 Strategy\n")
        f.write(f"Total candidates: {len(candidates)}\n")
        f.write("="*70 + "\n\n")

        for i, cand in enumerate(candidates):
            addr = cand['addr']
            score = cand['score']
            reasons = ", ".join(cand['reasons'])
            lines = cand['lines']

            print(f"  #{i+1}: func_0x{addr:08X} score={score} "
                  f"({lines} lines) [{reasons}]")

            f.write(f"\n{'='*70}\n")
            f.write(f"CANDIDATE #{i+1}: func_0x{addr:08X}\n")
            f.write(f"Score: {score}, Lines: {lines}\n")
            f.write(f"Reasons: {reasons}\n")
            f.write(f"{'='*70}\n\n")
            f.write(cand['code'])
            f.write("\n\n")

    print(f"Written: {cand_path}")

    # ================================================================
    # Summary
    # ================================================================
    elapsed = time.time() - t0
    print(f"\n{'='*70}")
    print(f"DONE in {elapsed:.1f}s")
    print(f"  Code regions: {len(code_regions)} ({total_code_bytes:,} bytes)")
    print(f"  Entry points: {len(entry_points)}")
    print(f"  Functions discovered: {len(functions)}")
    print(f"  Functions decompiled: {len(decompiled)} ({errors} errors)")
    print(f"  Clean functions: {len(clean)} ({garbage_count} garbage filtered)")
    print(f"  Lockout candidates: {len(candidates)}")
    print(f"  Output: {out_path}")
    print(f"  Candidates: {cand_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
