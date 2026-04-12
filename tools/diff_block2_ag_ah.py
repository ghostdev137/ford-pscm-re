#!/usr/bin/env python3
"""
AG vs AH block2_ext.bin: comprehensive shift-aware diff analysis.

Strategy: Use 8-byte block matching with a sliding search window to build
a byte-level correspondence map between AG and AH. Then compare aligned
instructions to separate relocations from real changes.
"""

import sys, struct, os
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v850.decoder import V850Decoder
from v850.models import sign_extend

BASE_ADDR = 0x20FF0000
CODE_END = 0x35000

AG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    "..", "firmware", "2025_Transit_PSCM", "decompressed", "AG", "block2_ext.bin")
AH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    "..", "firmware", "2025_Transit_PSCM", "decompressed", "AH", "block2_ext.bin")

decoder = V850Decoder()

BRANCH_MNEMONICS = {
    "bv","bl","be","bnh","bn","bt","blt","ble",
    "bnv","bnl","bne","bh","bp","bsa","bge","bgt",
    "jr","jarl"
}
CONST_MNEMONICS = {"movhi", "movea", "addi", "ori", "andi", "xori", "mulhi", "satsubi"}

def load_bins():
    with open(AG_PATH, "rb") as f:
        ag = f.read()
    with open(AH_PATH, "rb") as f:
        ah = f.read()
    return ag, ah

def full_disasm(data, limit=CODE_END):
    insns = []
    pos = 0
    while pos < limit and pos + 1 < len(data):
        insn = decoder.decode(data, pos, BASE_ADDR)
        if insn is None:
            pos += 2
            continue
        insns.append((pos, insn))
        pos += insn.size
    return insns

def build_shift_map(ag, ah, code_end=CODE_END, block_size=8, search_range=600):
    """
    Build a shift map: for each position in AG, what's the offset to AH?
    Uses block matching with a sliding window.
    Returns array where shift_map[ag_off] = shift (ah_off = ag_off + shift).
    """
    shift_map = [None] * code_end

    # First pass: find matching 8-byte blocks
    # Build a hash map of AH blocks for fast lookup
    ah_blocks = {}
    for ah_pos in range(0, code_end, 2):
        if ah_pos + block_size <= len(ah):
            key = ah[ah_pos:ah_pos + block_size]
            if key not in ah_blocks:
                ah_blocks[key] = []
            ah_blocks[key].append(ah_pos)

    # For each AG position, find best matching AH block nearby
    current_shift = 0
    for ag_pos in range(0, code_end, 2):
        if ag_pos + block_size > len(ag):
            break

        block = ag[ag_pos:ag_pos + block_size]

        # First try current shift (fast path)
        ah_pos = ag_pos + current_shift
        if 0 <= ah_pos < code_end and ah_pos + block_size <= len(ah):
            if ah[ah_pos:ah_pos + block_size] == block:
                for i in range(min(2, block_size)):
                    if ag_pos + i < code_end:
                        shift_map[ag_pos + i] = current_shift
                continue

        # Look up in hash map
        candidates = ah_blocks.get(block, [])
        best = None
        best_dist = search_range + 1
        for ah_cand in candidates:
            dist = abs(ah_cand - (ag_pos + current_shift))
            if dist < best_dist:
                best_dist = dist
                best = ah_cand

        if best is not None and best_dist <= search_range:
            new_shift = best - ag_pos
            current_shift = new_shift
            for i in range(min(2, block_size)):
                if ag_pos + i < code_end:
                    shift_map[ag_pos + i] = new_shift

    # Fill gaps by interpolation
    last_known = None
    for i in range(code_end):
        if shift_map[i] is not None:
            last_known = shift_map[i]
        elif last_known is not None:
            shift_map[i] = last_known

    return shift_map

def main():
    print("=" * 80)
    print("AG vs AH block2_ext.bin COMPREHENSIVE DIFF ANALYSIS")
    print("=" * 80)

    ag, ah = load_bins()
    total_diff = sum(1 for i in range(len(ag)) if ag[i] != ah[i])
    code_diff = sum(1 for i in range(CODE_END) if ag[i] != ah[i])
    print(f"Binary size: {len(ag)} bytes")
    print(f"Total differing bytes: {total_diff} (code: {code_diff}, pad: {total_diff-code_diff})")
    print()

    # Build shift map
    print("Building byte-level shift map...")
    shift_map = build_shift_map(ag, ah)

    # Analyze shift map
    shift_counts = Counter(s for s in shift_map if s is not None)
    none_count = sum(1 for s in shift_map if s is None)

    print(f"Shift coverage: {CODE_END - none_count}/{CODE_END} bytes mapped ({100*(CODE_END-none_count)/CODE_END:.1f}%)")
    print(f"\nShift value distribution:")
    for shift, count in shift_counts.most_common(20):
        print(f"  Shift {shift:+5d}: {count:6d} bytes ({100*count/CODE_END:.1f}%)")

    # Find shift transitions
    print(f"\nShift transition points:")
    prev_shift = shift_map[0]
    transitions = []
    for i in range(1, CODE_END):
        if shift_map[i] != prev_shift and shift_map[i] is not None:
            if prev_shift is not None:
                delta = shift_map[i] - prev_shift
                transitions.append((i, prev_shift, shift_map[i], delta))
            prev_shift = shift_map[i]

    for off, old_s, new_s, delta in transitions:
        action = f"AH {'inserted' if delta > 0 else 'deleted'} {abs(delta)} bytes"
        print(f"  0x{off:05X} (0x{BASE_ADDR+off:08X}): {old_s:+d} -> {new_s:+d} ({action})")
    print()

    # Disassemble both
    print("Disassembling...")
    ag_insns = full_disasm(ag, CODE_END)
    ah_insns = full_disasm(ah, CODE_END)
    ah_insn_map = {off: insn for off, insn in ah_insns}
    print(f"  AG: {len(ag_insns)} instructions, AH: {len(ah_insns)} instructions")
    print()

    # Match instructions using shift map
    identical = []
    branch_reloc = []
    branch_real = []
    const_reloc = []
    const_real = []
    disp_reloc = []
    disp_real = []
    register_change = []
    opcode_change = []
    unmatched = []
    ah_matched = set()

    for ag_off, ag_i in ag_insns:
        shift = shift_map[ag_off] if ag_off < len(shift_map) else None
        if shift is None:
            unmatched.append((ag_off, ag_i))
            continue

        ah_off = ag_off + shift
        ah_i = ah_insn_map.get(ah_off)
        if ah_i is None:
            # Try nearby (alignment might be off by 2)
            for delta in [-2, 2, -4, 4]:
                ah_i = ah_insn_map.get(ah_off + delta)
                if ah_i is not None:
                    ah_off += delta
                    break
        if ah_i is None:
            unmatched.append((ag_off, ag_i))
            continue

        ah_matched.add(ah_off)

        # Compare
        if ag_i.raw == ah_i.raw:
            identical.append((ag_off, ag_i, ah_off, ah_i))
            continue

        if ag_i.size != ah_i.size or ag_i.mnemonic != ah_i.mnemonic:
            opcode_change.append((ag_off, ag_i, ah_off, ah_i, shift))
            continue

        mn = ag_i.mnemonic

        # Branch
        if mn in BRANCH_MNEMONICS:
            ag_tgt = ag_i.branch_target
            ah_tgt = ah_i.branch_target
            if ag_tgt is not None and ah_tgt is not None:
                tgt_delta = ah_tgt - ag_tgt
                if tgt_delta == shift:
                    branch_reloc.append((ag_off, ag_i, ah_off, ah_i))
                else:
                    # Check if target is in a differently-shifted region
                    ag_tgt_off = ag_tgt - BASE_ADDR
                    if 0 <= ag_tgt_off < len(shift_map) and shift_map[ag_tgt_off] is not None:
                        expected_tgt_shift = shift_map[ag_tgt_off]
                        if tgt_delta == expected_tgt_shift:
                            branch_reloc.append((ag_off, ag_i, ah_off, ah_i))
                        else:
                            branch_real.append((ag_off, ag_i, ah_off, ah_i, tgt_delta, expected_tgt_shift))
                    else:
                        branch_real.append((ag_off, ag_i, ah_off, ah_i, tgt_delta, shift))
            continue

        # Constant/immediate
        if mn in CONST_MNEMONICS and ag_i.size >= 4:
            ag_hw0 = struct.unpack_from('<H', ag_i.raw, 0)[0]
            ah_hw0 = struct.unpack_from('<H', ah_i.raw, 0)[0]
            ag_imm = struct.unpack_from('<H', ag_i.raw, 2)[0]
            ah_imm = struct.unpack_from('<H', ah_i.raw, 2)[0]

            if ag_hw0 != ah_hw0 and ag_imm == ah_imm:
                register_change.append((ag_off, ag_i, ah_off, ah_i, shift))
            elif ag_hw0 != ah_hw0 and ag_imm != ah_imm:
                # Both register and immediate changed
                opcode_change.append((ag_off, ag_i, ah_off, ah_i, shift))
            else:
                # Same registers, different immediate
                const_real.append((ag_off, ag_i, ah_off, ah_i, ag_imm, ah_imm, shift))
            continue

        # Load/store with 32-bit encoding
        if ag_i.size >= 4:
            ag_hw0 = struct.unpack_from('<H', ag_i.raw, 0)[0]
            ah_hw0 = struct.unpack_from('<H', ah_i.raw, 0)[0]
            ag_hw1 = struct.unpack_from('<H', ag_i.raw, 2)[0]
            ah_hw1 = struct.unpack_from('<H', ah_i.raw, 2)[0]
            if ag_hw0 == ah_hw0 and ag_hw1 != ah_hw1:
                disp_real.append((ag_off, ag_i, ah_off, ah_i,
                                  sign_extend((ah_hw1 - ag_hw1) & 0xFFFF, 16), shift))
            elif ag_hw0 != ah_hw0:
                register_change.append((ag_off, ag_i, ah_off, ah_i, shift))
            continue

        # 16-bit same mnemonic different raw
        register_change.append((ag_off, ag_i, ah_off, ah_i, shift))

    # AH-only instructions
    ah_unmatched = [(off, insn) for off, insn in ah_insns if off not in ah_matched]

    # Print results
    print("=" * 80)
    print("INSTRUCTION COMPARISON RESULTS")
    print("=" * 80)
    print(f"  Matched pairs:")
    print(f"    Identical (byte-for-byte):  {len(identical):6d}")
    print(f"    Branch relocations:         {len(branch_reloc):6d}")
    print(f"    Constant relocations:       {len(const_reloc):6d}")
    print(f"    Displacement relocations:   {len(disp_reloc):6d}")
    n_reloc = len(identical) + len(branch_reloc) + len(const_reloc) + len(disp_reloc)
    print(f"    --- Total relocations:      {n_reloc:6d}")
    print(f"    Real branch changes:        {len(branch_real):6d}")
    print(f"    Real constant changes:      {len(const_real):6d}")
    print(f"    Real displacement changes:  {len(disp_real):6d}")
    print(f"    Register field changes:     {len(register_change):6d}")
    print(f"    Opcode/size changes:        {len(opcode_change):6d}")
    n_real = len(branch_real) + len(const_real) + len(disp_real) + len(register_change) + len(opcode_change)
    print(f"    --- Total real changes:     {n_real:6d}")
    print(f"  Unmatched AG instructions:    {len(unmatched):6d}")
    print(f"  Unmatched AH instructions:    {len(ah_unmatched):6d}")
    print()

    # Resolve MOVHI+MOVEA pairs in constant changes
    if const_real:
        print("=" * 80)
        print(f"CONSTANT/IMMEDIATE CHANGES ({len(const_real)})")
        print("=" * 80)

        const_by_off = {ag_off: item for item in const_real for ag_off in [item[0]]}
        used = set()
        resolved_pairs = []
        standalone_consts = []

        for ag_off, ag_i, ah_off, ah_i, ag_imm, ah_imm, shift in const_real:
            if ag_off in used:
                continue
            if ag_i.mnemonic == "movhi":
                # Look for paired movea
                for ag_off2, ag_i2, ah_off2, ah_i2, ag_imm2, ah_imm2, shift2 in const_real:
                    if ag_off2 == ag_off + 4 and ag_i2.mnemonic == "movea":
                        ag_val = ((ag_imm << 16) + sign_extend(ag_imm2, 16)) & 0xFFFFFFFF
                        ah_val = ((ah_imm << 16) + sign_extend(ah_imm2, 16)) & 0xFFFFFFFF
                        delta = ah_val - ag_val
                        if delta > 0x7FFFFFFF:
                            delta -= 0x100000000
                        resolved_pairs.append({
                            "ag_off": ag_off, "ah_off": ah_off,
                            "ag_val": ag_val, "ah_val": ah_val,
                            "delta": delta, "shift": shift,
                            "is_reloc": False,  # will check below
                        })
                        # Check if this is a relocation to a differently-shifted target
                        ag_tgt_off = ag_val - BASE_ADDR
                        if 0 <= ag_tgt_off < len(shift_map) and shift_map[ag_tgt_off] is not None:
                            expected_shift = shift_map[ag_tgt_off]
                            if delta == expected_shift:
                                resolved_pairs[-1]["is_reloc"] = True
                        used.add(ag_off)
                        used.add(ag_off + 4)
                        break

            if ag_off not in used:
                # Check standalone constant for relocation
                imm_delta = sign_extend((ah_imm - ag_imm) & 0xFFFF, 16)
                standalone_consts.append((ag_off, ag_i, ah_off, ah_i, ag_imm, ah_imm, imm_delta, shift))
                used.add(ag_off)

        reloc_pairs = [p for p in resolved_pairs if p["is_reloc"]]
        real_pairs = [p for p in resolved_pairs if not p["is_reloc"]]

        print(f"\n  MOVHI+MOVEA resolved address pairs: {len(resolved_pairs)}")
        print(f"    Relocations: {len(reloc_pairs)}")
        print(f"    Real value changes: {len(real_pairs)}")

        if real_pairs:
            print(f"\n  Non-relocation address constant changes:")
            for p in real_pairs:
                print(f"    0x{BASE_ADDR+p['ag_off']:08X} (AG) -> 0x{BASE_ADDR+p['ah_off']:08X} (AH)")
                print(f"      Value: 0x{p['ag_val']:08X} -> 0x{p['ah_val']:08X} (delta={p['delta']:+d})")

        if standalone_consts:
            print(f"\n  Standalone immediate changes ({len(standalone_consts)}):")
            for ag_off, ag_i, ah_off, ah_i, ag_imm, ah_imm, imm_delta, shift in standalone_consts:
                print(f"    0x{BASE_ADDR+ag_off:08X}: {ag_i.mnemonic:8s} "
                      f"0x{ag_imm:04X} -> 0x{ah_imm:04X} (delta={imm_delta:+d})")
        print()

    # Branch real changes
    if branch_real:
        print("=" * 80)
        print(f"REAL BRANCH TARGET CHANGES ({len(branch_real)})")
        print("=" * 80)
        for item in branch_real[:20]:
            ag_off, ag_i, ah_off, ah_i, tgt_delta, expected = item
            print(f"  0x{BASE_ADDR+ag_off:08X}: {ag_i.mnemonic:6s} {ag_i.op_str}")
            print(f"  0x{BASE_ADDR+ah_off:08X}: {ah_i.mnemonic:6s} {ah_i.op_str}")
            print(f"    Target moved by {tgt_delta:+d}, expected {expected:+d}")
            print()

    # Displacement changes
    if disp_real:
        print("=" * 80)
        print(f"DISPLACEMENT CHANGES ({len(disp_real)})")
        print("=" * 80)
        for ag_off, ag_i, ah_off, ah_i, delta_d, shift in disp_real[:20]:
            print(f"  0x{BASE_ADDR+ag_off:08X}: {ag_i.mnemonic:8s} {ag_i.op_str}")
            print(f"  0x{BASE_ADDR+ah_off:08X}: {ah_i.mnemonic:8s} {ah_i.op_str}")
            print(f"    Disp delta={delta_d:+d}")
        print()

    # Register changes
    if register_change:
        print("=" * 80)
        print(f"REGISTER FIELD CHANGES ({len(register_change)})")
        print("=" * 80)
        for ag_off, ag_i, ah_off, ah_i, shift in register_change[:30]:
            print(f"  0x{BASE_ADDR+ag_off:08X}: {ag_i.mnemonic:10s} {ag_i.op_str}")
            print(f"  0x{BASE_ADDR+ah_off:08X}: {ah_i.mnemonic:10s} {ah_i.op_str}")
        print()

    # Opcode changes
    if opcode_change:
        print("=" * 80)
        print(f"OPCODE/SIZE CHANGES ({len(opcode_change)})")
        print("=" * 80)
        # Sub-categorize
        size_diff = [(a,b,c,d,s) for a,b,c,d,s in opcode_change if b.size != d.size]
        mn_diff = [(a,b,c,d,s) for a,b,c,d,s in opcode_change if b.size == d.size and b.mnemonic != d.mnemonic]
        other = [(a,b,c,d,s) for a,b,c,d,s in opcode_change if b.size == d.size and b.mnemonic == d.mnemonic]

        print(f"  Different mnemonic: {len(mn_diff)}")
        print(f"  Different size: {len(size_diff)}")
        print(f"  Same mnemonic+size, both regs+imm changed: {len(other)}")

        if mn_diff:
            print(f"\n  --- Different mnemonic (first 40) ---")
            for ag_off, ag_i, ah_off, ah_i, shift in mn_diff[:40]:
                print(f"    0x{BASE_ADDR+ag_off:08X}: {ag_i.mnemonic:10s} {ag_i.op_str:30s} [{ag_i.raw.hex()}]")
                print(f"    0x{BASE_ADDR+ah_off:08X}: {ah_i.mnemonic:10s} {ah_i.op_str:30s} [{ah_i.raw.hex()}]")
                print()

        if size_diff:
            print(f"\n  --- Different size (first 20) ---")
            for ag_off, ag_i, ah_off, ah_i, shift in size_diff[:20]:
                print(f"    0x{BASE_ADDR+ag_off:08X} ({ag_i.size}B): {ag_i.mnemonic:10s} {ag_i.op_str}")
                print(f"    0x{BASE_ADDR+ah_off:08X} ({ah_i.size}B): {ah_i.mnemonic:10s} {ah_i.op_str}")
                print()
    print()

    # Look at shift transition points closely
    print("=" * 80)
    print("SHIFT TRANSITION ANALYSIS (code insertions/deletions)")
    print("=" * 80)
    prev_shift = shift_map[0]
    for i in range(1, CODE_END):
        if shift_map[i] != prev_shift and shift_map[i] is not None:
            if prev_shift is not None:
                change = shift_map[i] - prev_shift
                if abs(change) >= 4:  # skip tiny noise
                    print(f"\n  At AG offset 0x{i:05X} (0x{BASE_ADDR+i:08X}):")
                    print(f"    Shift: {prev_shift:+d} -> {shift_map[i]:+d} ({change:+d})")
                    if change > 0:
                        print(f"    -> {change} bytes INSERTED in AH")
                        # Show what's at this spot in AH
                        ah_pos = i + shift_map[i]
                        inserted_insns = [(off, insn) for off, insn in ah_insns
                                          if i + prev_shift <= off < ah_pos]
                        if inserted_insns:
                            print(f"    Inserted instructions:")
                            for off, insn in inserted_insns[:8]:
                                print(f"      0x{BASE_ADDR+off:08X}: {insn.mnemonic:10s} {insn.op_str}")
                            if len(inserted_insns) > 8:
                                print(f"      ... ({len(inserted_insns)} total)")
                    else:
                        print(f"    -> {-change} bytes DELETED from AH")
                        deleted_insns = [(off, insn) for off, insn in ag_insns
                                         if i <= off < i + (-change)]
                        if deleted_insns:
                            print(f"    Deleted instructions:")
                            for off, insn in deleted_insns[:8]:
                                print(f"      0x{BASE_ADDR+off:08X}: {insn.mnemonic:10s} {insn.op_str}")
                            if len(deleted_insns) > 8:
                                print(f"      ... ({len(deleted_insns)} total)")
            prev_shift = shift_map[i]
    print()

    # Grand summary
    print("=" * 80)
    print("GRAND SUMMARY")
    print("=" * 80)

    total_matched = len(identical) + len(branch_reloc) + len(const_reloc) + len(disp_reloc) + \
                    len(branch_real) + len(const_real) + len(disp_real) + \
                    len(register_change) + len(opcode_change)

    print(f"""
CODE AREA: 0x{BASE_ADDR:08X} - 0x{BASE_ADDR+CODE_END:08X}
AG: {len(ag_insns)} instructions | AH: {len(ah_insns)} instructions (delta: {len(ah_insns)-len(ag_insns):+d})

MATCHING SUMMARY:
  {len(identical):6d} instructions identical after shift alignment
  {len(branch_reloc):6d} branch relocations (targets shifted with code)
  {len(const_reloc):6d} constant relocations (addresses shifted with code)
  {len(disp_reloc):6d} displacement relocations
  ------
  {n_reloc:6d} total relocations (purely mechanical changes)

REAL FUNCTIONAL CHANGES:
  {len(branch_real):6d} branch targets point to different code
  {len(const_real):6d} constant/immediate values changed
  {len(disp_real):6d} memory displacements changed
  {len(register_change):6d} register allocations changed
  {len(opcode_change):6d} different opcodes/instruction sizes
  ------
  {n_real:6d} total real changes

UNMATCHED (near insertion/deletion points):
  {len(unmatched):6d} AG instructions without AH match
  {len(ah_unmatched):6d} AH instructions without AG match

PADDING CHANGES: {sum(1 for i in range(CODE_END, len(ag)) if i < len(ah) and ag[i] != ah[i])} bytes

SHIFT TRANSITIONS: {len(transitions)} points where code was inserted/deleted
""")

    # Final: top 20 interesting changes
    print("=" * 80)
    print("TOP 20 MOST INTERESTING CHANGES (sorted by likely significance)")
    print("=" * 80)

    interesting = []

    # Opcode changes are most interesting
    for ag_off, ag_i, ah_off, ah_i, shift in opcode_change:
        interesting.append((100, ag_off, "OPCODE",
            f"AG: {ag_i.mnemonic} {ag_i.op_str} [{ag_i.raw.hex()}]",
            f"AH: {ah_i.mnemonic} {ah_i.op_str} [{ah_i.raw.hex()}]"))

    # Branch real changes
    for item in branch_real:
        ag_off, ag_i, ah_off, ah_i, tgt_delta, expected = item
        interesting.append((90, ag_off, "BRANCH",
            f"AG: {ag_i.mnemonic} {ag_i.op_str}",
            f"AH: {ah_i.mnemonic} {ah_i.op_str} (tgt delta={tgt_delta:+d} vs expected {expected:+d})"))

    # Constant changes (non-trivial)
    for item in const_real:
        ag_off = item[0]
        ag_i, ah_i = item[1], item[3]
        interesting.append((80, ag_off, "CONSTANT",
            f"AG: {ag_i.mnemonic} {ag_i.op_str}",
            f"AH: {ah_i.mnemonic} {ah_i.op_str}"))

    # Displacement changes
    for ag_off, ag_i, ah_off, ah_i, delta_d, shift in disp_real:
        interesting.append((70, ag_off, "DISPLACEMENT",
            f"AG: {ag_i.mnemonic} {ag_i.op_str}",
            f"AH: {ah_i.mnemonic} {ah_i.op_str} (delta={delta_d:+d})"))

    # Register changes
    for ag_off, ag_i, ah_off, ah_i, shift in register_change:
        interesting.append((60, ag_off, "REGISTER",
            f"AG: {ag_i.mnemonic} {ag_i.op_str}",
            f"AH: {ah_i.mnemonic} {ah_i.op_str}"))

    interesting.sort(key=lambda x: (-x[0], x[1]))

    for rank, (score, off, cat, ag_str, ah_str) in enumerate(interesting[:20], 1):
        print(f"\n  #{rank:2d} [{cat}] at 0x{BASE_ADDR+off:08X}")
        print(f"      {ag_str}")
        print(f"      {ah_str}")

    print("\n\nANALYSIS COMPLETE.")

if __name__ == "__main__":
    main()
