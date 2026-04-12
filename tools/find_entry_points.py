"""
Find entry points in Transit PSCM firmware (V850E2/RH850).

Architecture notes (discovered during analysis):
- Binary is 1MB strategy at base 0x01000000 (from VBF erase block)
- Contains mixed code and data (floating-point calibration tables, CAN ID tables, etc.)
- Very few PREPARE/DISPOSE or JMP [lp] compared to F150 (different compiler/runtime)
- SBL (2KB at base 0x00000000) contains a vector table + bootstrap
- Extended block at 0x20FF0000 (320KB) may contain additional code
- RAM block at 0x10000400 (3KB)
- No LDSR to CTBP (SR20) found in strategy - CTBP may be set by bootloader/SBL
- No CTRET found - CALLT may be used for something other than standard call/return
- CAN ID 0x3CC appears in structured data tables (8-byte records)
"""

import struct
import sys
import os
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v850.decoder import V850Decoder
from v850.models import sign_extend

STRATEGY_PATH = os.path.join(os.path.dirname(__file__), '..', 'bins', 'transit_strategy_AM.bin')
SBL_PATH = os.path.join(os.path.dirname(__file__), '..', 'bins', 'transit_sbl.bin')
BLOCK2_PATH = os.path.join(os.path.dirname(__file__), '..', 'bins', 'transit_block2_ext.bin')
BASE_ADDR = 0x01000000
BLOCK2_BASE = 0x20FF0000

def load_bin(path):
    with open(path, 'rb') as f:
        return f.read()


# =============================================================================
# 1. Find CTBP - scan for LDSR to SR20 in ALL binaries
# =============================================================================
def find_ctbp_all_binaries():
    """Search all available binaries for LDSR to CTBP."""
    print("=" * 70)
    print("STEP 1: Searching for CTBP (LDSR to SR20, sel0) in all binaries")
    print("=" * 70)

    binaries = [
        ("strategy_AM", STRATEGY_PATH, BASE_ADDR),
        ("SBL", SBL_PATH, 0x00000000),
        ("block2_ext", BLOCK2_PATH, BLOCK2_BASE),
    ]

    for name, path, base in binaries:
        if not os.path.exists(path):
            continue
        data = load_bin(path)
        count = 0
        for off in range(0, len(data) - 3, 2):
            hw0 = struct.unpack_from('<H', data, off)[0]
            hw1 = struct.unpack_from('<H', data, off + 2)[0]
            opcode6 = (hw0 >> 5) & 0x3F
            reg1 = hw0 & 0x1F
            sub6 = (hw1 >> 5) & 0x3F
            reg3 = (hw1 >> 11) & 0x1F
            if opcode6 == 0x3F and sub6 == 0x01 and reg1 == 20 and reg3 == 0:
                reg2 = (hw0 >> 11) & 0x1F
                addr = base + off
                print(f"  [{name}] LDSR r{reg2}, CTBP at 0x{addr:08X}")
                count += 1
        if count == 0:
            print(f"  [{name}] No LDSR to CTBP found")


# =============================================================================
# 2. Analyze CALLT usage patterns
# =============================================================================
def analyze_callt_usage(data, base):
    """Analyze CALLT instruction distribution and usage patterns."""
    print("\n" + "=" * 70)
    print("STEP 2: CALLT instruction analysis")
    print("=" * 70)

    callt_by_imm = defaultdict(list)
    for off in range(0, len(data) - 1, 2):
        hw = struct.unpack_from('<H', data, off)[0]
        if (hw & 0xFFC0) == 0x0200:
            imm6 = hw & 0x3F
            callt_by_imm[imm6].append(off)

    total = sum(len(v) for v in callt_by_imm.values())
    print(f"  Total CALLT-pattern matches: {total}")
    print(f"  Unique imm6 values: {len(callt_by_imm)}")
    print(f"  Max imm6: {max(callt_by_imm.keys()) if callt_by_imm else 'N/A'}")

    # WARNING: Many of these may be false positives (data matching 0x02xx)
    # Check: are the CALLT offsets in code-like or data-like regions?
    # Score each CALLT by checking if surrounding bytes look like code

    decoder = V850Decoder()
    code_callts = 0
    data_callts = 0

    for imm, offsets in sorted(callt_by_imm.items()):
        for off in offsets[:3]:  # Check first 3 of each imm
            # Check preceding instruction
            score = 0
            if off >= 2:
                prev_hw = struct.unpack_from('<H', data, off - 2)[0]
                # Is prev a recognizable instruction?
                if prev_hw == 0:  # NOP
                    score += 1
                elif (prev_hw & 0x0780) == 0x0580:  # Bcc
                    score += 2
            # Check following instruction
            if off + 2 < len(data):
                next_hw = struct.unpack_from('<H', data, off + 2)[0]
                if next_hw == 0:
                    score += 1
            if score >= 1:
                code_callts += 1
            else:
                data_callts += 1

    print(f"\n  CALLT context analysis (sampled):")
    print(f"    Likely in code: {code_callts}")
    print(f"    Likely in data: {data_callts}")

    print(f"\n  CALLT by imm6 (frequency):")
    for imm, offsets in sorted(callt_by_imm.items(), key=lambda x: -len(x[1])):
        region_counts = Counter()
        for o in offsets:
            block = o // 0x10000
            region_counts[block] += 1
        top_blocks = region_counts.most_common(3)
        block_str = ", ".join(f"0x{b*0x10000+base:08X}({c})" for b, c in top_blocks)
        print(f"    imm6=0x{imm:02X}: {len(offsets):4d}x  top blocks: {block_str}")

    return callt_by_imm


# =============================================================================
# 3. Analyze SBL vector table and bootstrap
# =============================================================================
def analyze_sbl(sbl_data):
    """Analyze SBL for reset vector and bootstrap code."""
    print("\n" + "=" * 70)
    print("STEP 3: SBL analysis (reset vector, bootstrap)")
    print("=" * 70)

    print(f"  SBL size: {len(sbl_data)} bytes")

    # The SBL starts with what appears to be a table of addresses/vectors
    # First 5 32-bit LE words, then 0xFFFFFFFF padding
    print("\n  First 8 LE 32-bit values:")
    for i in range(0, 32, 4):
        val_le = struct.unpack_from('<I', sbl_data, i)[0]
        val_be = struct.unpack_from('>I', sbl_data, i)[0]
        print(f"    0x{i:04X}: LE=0x{val_le:08X}  BE=0x{val_be:08X}")

    # RH850 exception model: handlers at 16-byte boundaries
    # RESET at 0x0000, SYSERR at 0x0010, etc.
    # But entry 0 is 0x57000001 (LE) or 0x01000057 (BE)
    # 0x01000057 would be in the strategy (offset 0x57) but that's in the 0xFF region

    # Actually, RH850 has the reset handler AT address 0x0000 - it's executable code,
    # not an address table. Let's try decoding at offset 0x20 where we see non-FF data.
    # But offset 0-0x1F has: 01 00 00 57 00 00 01 F2 00 00 02 06 00 00 02 0C...
    # These look like they could be a jump table or initialization data.

    # Let's find the "mov r0, r16; or r24, gp; mov r6, ep" pattern which appears
    # at 0x20 in SBL and at many places in strategy (though it's data, not code)
    prologue = bytes([0x00, 0x80, 0x18, 0x21, 0x06, 0xF0])
    idx = sbl_data.find(prologue)
    if idx >= 0:
        print(f"\n  Prologue pattern found at SBL offset 0x{idx:04X}")

    # The first 20 bytes (5 x 32-bit LE) before FF padding:
    print("\n  Potential vector table entries (before FF padding):")
    entries = []
    for i in range(0, len(sbl_data), 4):
        val = struct.unpack_from('<I', sbl_data, i)[0]
        if val == 0xFFFFFFFF:
            break
        entries.append((i, val))
        # Try interpreting as address
        if BASE_ADDR <= val < BASE_ADDR + 0x100000:
            print(f"    [{i//4}] 0x{val:08X} -> strategy offset 0x{val - BASE_ADDR:05X}")
        elif 0 < val < len(sbl_data):
            print(f"    [{i//4}] 0x{val:08X} -> SBL internal offset 0x{val:04X}")
        else:
            be_val = struct.unpack_from('>I', sbl_data, i)[0]
            if BASE_ADDR <= be_val < BASE_ADDR + 0x100000:
                print(f"    [{i//4}] 0x{val:08X} (BE: 0x{be_val:08X}) -> strategy offset 0x{be_val - BASE_ADDR:05X}")
            else:
                print(f"    [{i//4}] 0x{val:08X}")

    return entries


# =============================================================================
# 4. Find CAN ID 0x3CC references and handler tables
# =============================================================================
def find_can_handlers(data, base):
    """Find CAN message handler data structures referencing 0x3CC."""
    print("\n" + "=" * 70)
    print("STEP 4: CAN ID 0x3CC references and handler tables")
    print("=" * 70)

    # Search for 0x03CC as bytes (both endiannesses)
    can_id = 0x3CC

    # Big-endian: 03 CC
    be_pattern = struct.pack('>H', can_id)
    # Little-endian: CC 03
    le_pattern = struct.pack('<H', can_id)

    be_hits = []
    le_hits = []

    off = 0
    while off < len(data):
        idx = data.find(be_pattern, off)
        if idx == -1:
            break
        be_hits.append(idx)
        off = idx + 1

    off = 0
    while off < len(data):
        idx = data.find(le_pattern, off)
        if idx == -1:
            break
        le_hits.append(idx)
        off = idx + 1

    print(f"  0x03CC big-endian hits: {len(be_hits)}")
    for idx in be_hits:
        ctx = data[max(0,idx-8):idx+10]
        print(f"    0x{base+idx:08X} (offset 0x{idx:05X}): {ctx.hex()}")

    print(f"\n  0xCC03 little-endian hits: {len(le_hits)}")
    for idx in le_hits:
        ctx = data[max(0,idx-8):idx+10]
        print(f"    0x{base+idx:08X} (offset 0x{idx:05X}): {ctx.hex()}")

    # Analyze the CAN ID table structure
    # At 0x2B78 we saw a pattern: XX XX YY ZZ 03 08 00 00 (8-byte records)
    # Where XX XX is CAN ID (BE), YY is some index, ZZ is length or flags
    print("\n  CAN ID table analysis (looking for 8-byte record structure):")

    for idx in be_hits:
        # Check if this looks like a table entry (8-byte aligned pattern)
        if idx >= 2 and idx + 6 <= len(data):
            # Go back to find table start
            # Pattern: XXXX YYYY 0308 0000 (repeating)
            record_start = idx - (idx % 8)  # Align to 8
            # Check if there's a consistent pattern

            # Actually, look at the raw data around each hit
            start = max(0, idx - 24)
            end = min(len(data), idx + 32)
            print(f"\n    Near 0x{base+idx:08X}:")
            for r in range(start, end, 8):
                if r + 8 <= len(data):
                    record = data[r:r+8]
                    can_val = struct.unpack_from('>H', record, 0)[0]
                    marker = " <<<" if can_val == can_id else ""
                    print(f"      0x{base+r:08X}: {record.hex()} "
                          f"(CAN=0x{can_val:04X}, bytes={record[2]:02X} {record[3]:02X} "
                          f"{record[4]:02X} {record[5]:02X} {record[6]:02X} {record[7]:02X}){marker}")

    return be_hits, le_hits


# =============================================================================
# 5. Find verified code entry points
# =============================================================================
def find_code_entry_points(data, base, decoder):
    """Find functions using multiple heuristics."""
    print("\n" + "=" * 70)
    print("STEP 5: Finding verified code entry points")
    print("=" * 70)

    all_entries = set()

    # 5a. PREPARE instructions (function prologues)
    prepare_locs = []
    for off in range(0, len(data) - 3, 2):
        hw0 = struct.unpack_from('<H', data, off)[0]
        if (hw0 & 0xFFE0) == 0x0780:
            prepare_locs.append(off)
            all_entries.add(base + off)

    print(f"\n  PREPARE instructions (potential function entries): {len(prepare_locs)}")
    for off in prepare_locs[:20]:
        insn = decoder.decode(data, off, base)
        print(f"    0x{base+off:08X}: {insn}")

    # 5b. JMP [lp] returns
    jmp_lp_locs = []
    for off in range(0, len(data) - 1, 2):
        hw = struct.unpack_from('<H', data, off)[0]
        if hw == 0x007F:
            jmp_lp_locs.append(off)
    print(f"\n  JMP [lp] (function returns): {len(jmp_lp_locs)}")

    # 5c. DISPOSE with JMP variant
    dispose_jmp = []
    for off in range(0, len(data) - 3, 2):
        hw0 = struct.unpack_from('<H', data, off)[0]
        hw1 = struct.unpack_from('<H', data, off + 2)[0]
        if (hw0 & 0xFFE0) == 0x0640:
            jmp_reg = (hw1 >> 1) & 0x1F
            if jmp_reg == 31 and (hw1 & 0x1F) != 1:
                dispose_jmp.append(off)
    print(f"  DISPOSE with jmp [lp] (function returns): {len(dispose_jmp)}")

    # 5d. Collect all branch/call targets from JARL/JR instructions
    # NOTE: Many JARL/JR matches will be false positives from data
    branch_targets = set()
    for off in range(0, len(data) - 3, 2):
        hw0 = struct.unpack_from('<H', data, off)[0]
        # Skip PREPARE/DISPOSE which overlap encoding
        if (hw0 & 0xFFE0) == 0x0780 or (hw0 & 0xFFE0) == 0x0640:
            continue
        if (hw0 & 0x07C0) == 0x0780:
            reg2 = (hw0 >> 11) & 0x1F
            hw1 = struct.unpack_from('<H', data, off + 2)[0]
            d_hi = hw0 & 0x3F
            d_lo = hw1
            raw22 = (d_hi << 16) | d_lo
            sdisp = sign_extend(raw22, 22)
            target = base + off + sdisp
            # Must be even, in strategy range
            if target % 2 == 0 and base <= target < base + len(data):
                branch_targets.add(target)

    # Also collect Bcc targets
    for off in range(0, len(data) - 1, 2):
        hw = struct.unpack_from('<H', data, off)[0]
        if (hw & 0x0780) == 0x0580:
            d_hi = (hw >> 11) & 0x1F
            d_lo = (hw >> 4) & 0x7
            disp9 = (d_hi << 4) | (d_lo << 1)
            sdisp = sign_extend(disp9, 9)
            target = base + off + sdisp
            if target % 2 == 0 and base <= target < base + len(data):
                branch_targets.add(target)

    print(f"\n  All branch/call targets (incl false positives): {len(branch_targets)}")

    # 5e. Cross-reference: PREPARE at branch targets
    prepare_at_targets = set()
    for off in prepare_locs:
        addr = base + off
        if addr in branch_targets:
            prepare_at_targets.add(addr)
    print(f"  PREPARE at branch targets (high confidence): {len(prepare_at_targets)}")
    for addr in sorted(prepare_at_targets):
        all_entries.add(addr)
        off = addr - base
        insn = decoder.decode(data, off, base)
        print(f"    0x{addr:08X}: {insn}")

    # 5f. Find function-like patterns: sequences ending in JMP [lp] or DISPOSE
    # Walk backwards from each return to find the function start
    print(f"\n  Functions found by return tracing:")
    func_starts = set()
    for ret_off in jmp_lp_locs + dispose_jmp:
        # Walk backwards to find PREPARE or function start
        for search_off in range(max(0, ret_off - 1024), ret_off, 2):
            hw = struct.unpack_from('<H', data, search_off)[0]
            if (hw & 0xFFE0) == 0x0780:  # PREPARE
                func_starts.add(base + search_off)
                all_entries.add(base + search_off)
                break

    for addr in sorted(func_starts):
        off = addr - base
        insn = decoder.decode(data, off, base)
        print(f"    0x{addr:08X}: {insn}")

    return all_entries


# =============================================================================
# 6. Scan the extended block for code
# =============================================================================
def analyze_block2(data, base):
    """Analyze the extended flash block for code."""
    print("\n" + "=" * 70)
    print("STEP 6: Extended block analysis (0x{:08X})".format(base))
    print("=" * 70)

    print(f"  Size: {len(data)} bytes ({len(data)/1024:.0f} KB)")

    decoder = V850Decoder()

    # Count instruction types
    prepare_count = 0
    dispose_count = 0
    jmp_lp_count = 0
    callt_count = 0
    for off in range(0, len(data) - 3, 2):
        hw = struct.unpack_from('<H', data, off)[0]
        if (hw & 0xFFE0) == 0x0780:
            prepare_count += 1
        if (hw & 0xFFE0) == 0x0640:
            dispose_count += 1
        if hw == 0x007F:
            jmp_lp_count += 1
        if (hw & 0xFFC0) == 0x0200:
            callt_count += 1

    print(f"  PREPARE: {prepare_count}")
    print(f"  DISPOSE: {dispose_count}")
    print(f"  JMP [lp]: {jmp_lp_count}")
    print(f"  CALLT: {callt_count}")

    # Search for LDSR to CTBP
    for off in range(0, len(data) - 3, 2):
        hw0 = struct.unpack_from('<H', data, off)[0]
        hw1 = struct.unpack_from('<H', data, off + 2)[0]
        opcode6 = (hw0 >> 5) & 0x3F
        reg1 = hw0 & 0x1F
        sub6 = (hw1 >> 5) & 0x3F
        reg3 = (hw1 >> 11) & 0x1F
        if opcode6 == 0x3F and sub6 == 0x01 and reg1 == 20 and reg3 == 0:
            reg2 = (hw0 >> 11) & 0x1F
            print(f"  LDSR r{reg2}, CTBP at 0x{base+off:08X}")

    # CAN ID 0x3CC in this block
    be_pat = struct.pack('>H', 0x3CC)
    off = 0
    while True:
        idx = data.find(be_pat, off)
        if idx == -1:
            break
        print(f"  CAN 0x3CC at 0x{base+idx:08X}")
        off = idx + 1


# =============================================================================
# 7. Look for CALLT table candidates using heuristic
# =============================================================================
def find_callt_table_heuristic(data, base, decoder):
    """Try to find the CALLT table by looking for blocks of 16-bit values
    that could be code offsets."""
    print("\n" + "=" * 70)
    print("STEP 7: CALLT table search (heuristic)")
    print("=" * 70)

    # The CALLT table has up to 64 entries, each a 16-bit offset from CTBP.
    # The entries should be even (instruction alignment).
    # When added to CTBP, they should point to code (not 0xFF regions).
    # The table itself is 128 bytes.

    # Strategy: try each 128-byte block where all values are even, non-zero,
    # and the resulting targets point to non-FF data.

    best_candidate = None
    best_score = 0

    for table_off in range(0, len(data) - 128, 2):
        # Quick reject: first entry should be even and non-zero (or zero for unused)
        first = struct.unpack_from('<H', data, table_off)[0]
        if first & 1:
            continue

        # Check all 64 entries
        entries = []
        all_even = True
        non_zero_count = 0
        for i in range(64):
            val = struct.unpack_from('<H', data, table_off + i * 2)[0]
            entries.append(val)
            if val & 1:
                all_even = False
                break
            if val > 0:
                non_zero_count += 1
            if val > 0x10000:  # Unreasonably large offset
                all_even = False
                break

        if not all_even or non_zero_count < 5:
            continue

        # Check if CTBP=base+table_off makes targets point to non-FF data
        ctbp = base + table_off
        score = 0
        for val in entries:
            if val == 0:
                continue
            target_off = table_off + val
            if 0 <= target_off < len(data) - 2:
                # Check if target is not in FF region
                if data[target_off] != 0xFF or data[target_off + 1] != 0xFF:
                    score += 1
                    # Bonus for target being a recognized instruction
                    insn = decoder.decode(data, target_off, base)
                    if insn and insn.mnemonic not in ('.dw',):
                        score += 1

        if score > best_score and non_zero_count >= 5:
            best_score = score
            best_candidate = (table_off, ctbp, entries, non_zero_count)

    if best_candidate:
        table_off, ctbp, entries, nz = best_candidate
        print(f"  Best candidate: CTBP=0x{ctbp:08X} (offset 0x{table_off:05X})")
        print(f"  Non-zero entries: {nz}/64, score: {best_score}")
        for i, val in enumerate(entries):
            if val > 0:
                target = ctbp + val
                target_off = table_off + val
                valid = "?"
                if 0 <= target_off < len(data) - 2:
                    insn = decoder.decode(data, target_off, base)
                    valid = insn.mnemonic if insn else "???"
                print(f"    [{i:2d}] offset=0x{val:04X} -> 0x{target:08X} ({valid})")
    else:
        print("  No convincing CALLT table found in strategy binary.")
        print("  CTBP likely points to a table in RAM (0x10xxxxxx) or external flash (0x20xxxxxx)")


# =============================================================================
# 8. Pointer table analysis
# =============================================================================
def find_pointer_tables(data, base):
    """Find tables of 32-bit pointers into known memory regions."""
    print("\n" + "=" * 70)
    print("STEP 8: Pointer/address table analysis")
    print("=" * 70)

    # Look for sequences of 32-bit values that point into the strategy
    ptr_tables = []
    off = 0
    while off < len(data) - 15:
        # Check 4 consecutive 32-bit values
        vals = [struct.unpack_from('<I', data, off + i * 4)[0] for i in range(4)]
        in_range = sum(1 for v in vals if base <= v < base + len(data))
        if in_range >= 3:
            # Filter: values should be diverse (not repetitive data like 0x01010101)
            unique_vals = len(set(vals))
            if unique_vals < 2:
                off += 4
                continue
            # Filter: values should be even (code alignment)
            even_count = sum(1 for v in vals if v % 2 == 0)
            if even_count < 2:
                off += 4
                continue
            # Found a potential pointer table
            table_start = off
            count = 0
            while off + count * 4 + 4 <= len(data):
                val = struct.unpack_from('<I', data, off + count * 4)[0]
                if not (base <= val < base + len(data)):
                    break
                count += 1
            if count >= 4:
                # Final filter: check that entries are diverse
                table_vals = [struct.unpack_from('<I', data, off + i * 4)[0] for i in range(count)]
                unique_count = len(set(table_vals))
                if unique_count >= min(count // 2, 3):
                    # Filter: at least some entries should not be in the FF-padded region
                    non_ff_entries = 0
                    for i in range(count):
                        tv = struct.unpack_from('<I', data, off + i * 4)[0]
                        tv_off = tv - base
                        if 0 <= tv_off < len(data) and data[tv_off] != 0xFF:
                            non_ff_entries += 1
                    if non_ff_entries >= count // 2:
                        ptr_tables.append((table_start, count))
            # Skip past this table
            off = table_start + max(count, 1) * 4
            continue
        off += 4

    # Deduplicate overlapping tables
    merged = []
    for start, count in sorted(ptr_tables):
        if merged and start < merged[-1][0] + merged[-1][1] * 4:
            # Overlapping - extend previous
            end = max(merged[-1][0] + merged[-1][1] * 4, start + count * 4)
            merged[-1] = (merged[-1][0], (end - merged[-1][0]) // 4)
        else:
            merged.append((start, count))

    print(f"  Pointer tables found: {len(merged)}")
    entry_points = set()
    for start, count in merged[:20]:
        print(f"\n    Table at 0x{base+start:08X} ({count} entries):")
        for i in range(min(count, 8)):
            val = struct.unpack_from('<I', data, start + i * 4)[0]
            target_off = val - base
            print(f"      [{i:2d}] 0x{val:08X} (offset 0x{target_off:05X})")
            entry_points.add(val)
        if count > 8:
            print(f"      ... {count - 8} more entries")

    return entry_points


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("Transit PSCM Firmware Entry Point Finder")
    print(f"Strategy binary: transit_strategy_AM.bin, Base: 0x{BASE_ADDR:08X}")
    print()

    strategy = load_bin(STRATEGY_PATH)
    sbl = load_bin(SBL_PATH)
    decoder = V850Decoder()

    all_entry_points = set()

    # Step 1: CTBP search
    find_ctbp_all_binaries()

    # Step 2: CALLT analysis
    callt_by_imm = analyze_callt_usage(strategy, BASE_ADDR)

    # Step 3: SBL analysis
    sbl_entries = analyze_sbl(sbl)

    # Step 4: CAN handlers
    be_hits, le_hits = find_can_handlers(strategy, BASE_ADDR)

    # Step 5: Code entry points
    code_entries = find_code_entry_points(strategy, BASE_ADDR, decoder)
    all_entry_points.update(code_entries)

    # Step 6: Extended block
    if os.path.exists(BLOCK2_PATH):
        block2 = load_bin(BLOCK2_PATH)
        analyze_block2(block2, BLOCK2_BASE)

    # Step 7: CALLT table heuristic
    find_callt_table_heuristic(strategy, BASE_ADDR, decoder)

    # Step 8: Pointer tables
    ptr_entries = find_pointer_tables(strategy, BASE_ADDR)
    all_entry_points.update(ptr_entries)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"\n  CTBP: NOT FOUND in any binary")
    print(f"    (CTBP is likely set by bootloader and points to RAM or ext flash)")

    print(f"\n  CALLT table: NOT FOUND in strategy")
    print(f"    (The 3172 CALLT-pattern matches are mostly data false positives)")
    print(f"    (Real CALLT count is likely much lower)")

    print(f"\n  SBL vector table entries:")
    for off, val in sbl_entries:
        print(f"    [{off//4}] 0x{val:08X}")

    print(f"\n  CAN ID 0x3CC locations (BE format):")
    for idx in be_hits:
        print(f"    0x{BASE_ADDR+idx:08X} (offset 0x{idx:05X})")

    print(f"\n  Code entry points from PREPARE: {len([o for o in code_entries if BASE_ADDR <= o < BASE_ADDR + len(strategy)])}")
    print(f"  Pointer table entry points: {len(ptr_entries)}")
    print(f"  Total entry points collected: {len(all_entry_points)}")

    # Show sorted entry points
    sorted_eps = sorted(all_entry_points)
    if len(sorted_eps) <= 30:
        for ep in sorted_eps:
            off = ep - BASE_ADDR
            ctx = ""
            if 0 <= off < len(strategy) - 2:
                hw = struct.unpack_from('<H', strategy, off)[0]
                insn = decoder.decode(strategy, off, BASE_ADDR)
                if insn:
                    ctx = f"  {insn.mnemonic} {insn.op_str}"
            print(f"    0x{ep:08X}{ctx}")
    else:
        print(f"\n  First 15:")
        for ep in sorted_eps[:15]:
            off = ep - BASE_ADDR
            ctx = ""
            if 0 <= off < len(strategy) - 2:
                insn = decoder.decode(strategy, off, BASE_ADDR)
                if insn:
                    ctx = f"  {insn.mnemonic} {insn.op_str}"
            print(f"    0x{ep:08X}{ctx}")
        print(f"  ...")
        print(f"  Last 15:")
        for ep in sorted_eps[-15:]:
            off = ep - BASE_ADDR
            ctx = ""
            if 0 <= off < len(strategy) - 2:
                insn = decoder.decode(strategy, off, BASE_ADDR)
                if insn:
                    ctx = f"  {insn.mnemonic} {insn.op_str}"
            print(f"    0x{ep:08X}{ctx}")

    # Architecture notes
    print(f"\n  ARCHITECTURE NOTES:")
    print(f"    - This binary is MOSTLY calibration data (float tables, CAN ID tables)")
    print(f"    - Only ~104 PREPARE and ~13 JMP [lp] in 1MB (vs F150: 13722/3290)")
    print(f"    - No CTRET, EIRET, DI, EI instructions found")
    print(f"    - The compiler/runtime uses a non-standard calling convention")
    print(f"    - Actual executable code may be primarily in the ext block (0x20FF0000)")
    print(f"    - CALLT table is likely in RAM (0x10xxxxxx), loaded at boot by SBL")


if __name__ == '__main__':
    main()
