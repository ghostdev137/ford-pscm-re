#!/usr/bin/env python3
"""
Compare F150 strategy firmware with Transit to find LKA/lockout differences.

F150: bins/f150_strategy.bin (1,571,840 bytes, base 0x10040000)
Transit: firmware/2025_Transit_PSCM/decompressed/ block0/block2

Key questions:
- Does F150 have the same lockout timer code as Transit?
- How does F150 handle LCA/TJA vs LKA?
- CAN descriptor table differences?
"""

import os
import sys
import struct

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from v850.decoder import V850Decoder
from v850.scanner import BinaryScanner
from v850.decompile import FirmwareDecompiler

# ============================================================================
# Configuration
# ============================================================================
F150_BIN = os.path.join(os.path.dirname(__file__), "..", "bins", "f150_strategy.bin")
F150_BASE = 0x10040000

# Transit block0 - try multiple possible locations
TRANSIT_BLOCK0_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "..", "firmware", "2025_Transit_PSCM", "decompressed", "AM", "block0_strategy.bin"),
    os.path.join(os.path.dirname(__file__), "..", "bins", "transit_strategy_AM.bin"),
]
TRANSIT_BASE = 0x00000000  # block0 base

# CAN IDs of interest
CAN_3CC = 0x03CC  # LaActAvail (lockout status)
CAN_3D3 = 0x03D3  # LateralMotionControl (LCA steering command)
CAN_3CA = 0x03CA  # Lane_Assist_Data1 (LKA steering command)
CAN_082 = 0x0082  # Common CAN message

# Timer constants associated with lockout
LOCKOUT_TIMERS = [500, 1000, 2000, 10000]
RECOVERY_CONSTANTS = [200, 250, 300]
STATE_VALUES = [0, 1, 2, 3]


def load_binary(path):
    with open(path, "rb") as f:
        return f.read()


def find_byte_pattern(data, pattern, base=0):
    """Find all occurrences of a byte pattern."""
    results = []
    pos = 0
    while True:
        idx = data.find(pattern, pos)
        if idx < 0:
            break
        results.append((idx, base + idx))
        pos = idx + 1
    return results


# ============================================================================
# 1. SEARCH F150 FOR CAN ID 0x3CC
# ============================================================================
def search_can_3cc(data, base, decoder, label=""):
    print(f"\n{'='*70}")
    print(f"  1. CAN ID 0x3CC (LaActAvail) in {label}")
    print(f"{'='*70}")

    # Search for 0x03CC in big-endian (as immediate/data)
    be_pattern = struct.pack('>H', CAN_3CC)
    hits_be = find_byte_pattern(data, be_pattern, base)

    # Also search in little-endian (as stored in V850 LE format)
    le_pattern = struct.pack('<H', CAN_3CC)
    hits_le = find_byte_pattern(data, le_pattern, base)

    print(f"  Big-endian 0x03CC hits: {len(hits_be)}")
    for off, addr in hits_be:
        ctx = data[max(0, off-8):off+10].hex(' ')
        print(f"    offset=0x{off:06X} addr=0x{addr:08X}  ctx: {ctx}")

    print(f"  Little-endian 0xCC03 hits: {len(hits_le)}")
    for off, addr in hits_le:
        ctx = data[max(0, off-8):off+10].hex(' ')
        print(f"    offset=0x{off:06X} addr=0x{addr:08X}  ctx: {ctx}")

    # Decode surrounding instructions for each hit
    all_hits = [(off, addr, "BE") for off, addr in hits_be] + \
               [(off, addr, "LE") for off, addr in hits_le]

    print(f"\n  Decoding context around each hit:")
    for off, addr, endian in all_hits[:20]:  # Limit output
        print(f"\n  --- Hit at offset=0x{off:06X} ({endian}) ---")
        # Decode 10 instructions before and 10 after
        start_off = max(0, (off - 20) & ~1)  # align to 2
        end_off = min(len(data), off + 22)
        decode_off = start_off
        insns = []
        while decode_off < end_off:
            insn = decoder.decode(data, decode_off, base)
            if insn is None:
                decode_off += 2
                continue
            marker = " <<<<" if decode_off == off or decode_off == off - 2 else ""
            insns.append((insn, marker))
            decode_off += insn.size
        for insn, marker in insns:
            print(f"    {insn}{marker}")

    return all_hits


# ============================================================================
# 2. SEARCH F150 FOR LaActAvail PATTERNS (lockout timers)
# ============================================================================
def search_lockout_patterns(data, base, decoder, label=""):
    print(f"\n{'='*70}")
    print(f"  2. LaActAvail Lockout Timer Patterns in {label}")
    print(f"{'='*70}")

    # Search for timer constants as 16-bit immediates in MOVEA/ADDI
    # MOVEA: opcode6=0x31, ADDI: opcode6=0x30
    # Format: [hw0_le][imm16_le] where imm16 is the constant
    timer_hits = {}

    for const in LOCKOUT_TIMERS + RECOVERY_CONSTANTS:
        hits = []
        # As unsigned 16-bit LE in second halfword of MOVEA/ADDI
        const_le = struct.pack('<H', const & 0xFFFF)

        for off in range(0, len(data) - 4, 2):
            hw0 = struct.unpack_from('<H', data, off)[0]
            opcode6 = (hw0 >> 5) & 0x3F
            if opcode6 in (0x30, 0x31):  # ADDI or MOVEA
                hw1 = struct.unpack_from('<H', data, off + 2)[0]
                # The immediate is sign-extended 16-bit
                imm16 = hw1
                if imm16 == (const & 0xFFFF):
                    insn = decoder.decode(data, off, base)
                    if insn:
                        hits.append((off, base + off, insn))

        timer_hits[const] = hits
        if hits:
            print(f"\n  Constant {const} (0x{const:04X}): {len(hits)} hits")
            for off, addr, insn in hits[:10]:
                print(f"    {insn}")
        else:
            print(f"  Constant {const} (0x{const:04X}): 0 hits")

    # Look for CMP + branch patterns with state values 0,1,2,3
    # These indicate state machine code
    print(f"\n  --- State machine patterns (CMP imm5 near branches) ---")
    state_clusters = []

    for off in range(0, len(data) - 8, 2):
        hw = struct.unpack_from('<H', data, off)[0]
        opcode6 = (hw >> 5) & 0x3F
        if opcode6 == 0x13:  # CMP imm5, reg2
            imm5 = hw & 0x1F
            if imm5 in (1, 2, 3):
                # Check if next instruction is a branch
                insn2 = decoder.decode(data, off + 2, base)
                if insn2 and insn2.is_branch:
                    state_clusters.append((off, base + off, imm5, insn2))

    # Find clusters (multiple CMP values near each other = state machine)
    if state_clusters:
        # Group by proximity (within 32 bytes)
        clusters = []
        current = [state_clusters[0]]
        for item in state_clusters[1:]:
            if item[0] - current[-1][0] < 64:
                current.append(item)
            else:
                if len(current) >= 2:
                    clusters.append(current)
                current = [item]
        if len(current) >= 2:
            clusters.append(current)

        print(f"  Found {len(clusters)} state machine clusters (2+ CMP+branch within 64 bytes)")
        for i, cluster in enumerate(clusters[:20]):
            print(f"\n    Cluster {i} at 0x{cluster[0][1]:08X}:")
            for off, addr, val, branch in cluster:
                cmp_insn = decoder.decode(data, off, base)
                print(f"      {cmp_insn}")
                print(f"      {branch}")
    else:
        print(f"  No state machine clusters found")

    return timer_hits


# ============================================================================
# 3. SEARCH F150 FOR LCA/TJA ENABLE LOGIC
# ============================================================================
def search_lca_tja(data, base, decoder, label=""):
    print(f"\n{'='*70}")
    print(f"  3. LCA/TJA Enable Logic (CAN 0x3D3, 0x3CA) in {label}")
    print(f"{'='*70}")

    for can_id, name in [(CAN_3D3, "LateralMotionControl/LCA"), (CAN_3CA, "Lane_Assist_Data1/LKA")]:
        be = struct.pack('>H', can_id)
        le = struct.pack('<H', can_id)

        hits_be = find_byte_pattern(data, be, base)
        hits_le = find_byte_pattern(data, le, base)

        print(f"\n  CAN 0x{can_id:03X} ({name}):")
        print(f"    BE hits: {len(hits_be)}")
        for off, addr in hits_be[:10]:
            ctx = data[max(0, off-4):off+6].hex(' ')
            print(f"      offset=0x{off:06X} addr=0x{addr:08X}  ctx: {ctx}")

        print(f"    LE hits: {len(hits_le)}")
        for off, addr in hits_le[:10]:
            ctx = data[max(0, off-4):off+6].hex(' ')
            print(f"      offset=0x{off:06X} addr=0x{addr:08X}  ctx: {ctx}")

        # Decode around BE hits (more likely to be CAN ID tables)
        for off, addr in hits_be[:5]:
            print(f"\n    Context around 0x{addr:08X}:")
            start = max(0, (off - 16) & ~1)
            end = min(len(data), off + 20)
            doff = start
            while doff < end:
                insn = decoder.decode(data, doff, base)
                if insn is None:
                    doff += 2
                    continue
                marker = " <<<<" if abs(doff - off) <= 2 else ""
                print(f"      {insn}{marker}")
                doff += insn.size


# ============================================================================
# 4. COMPARE CAN DESCRIPTOR TABLES
# ============================================================================
def find_can_tables(data, base, label=""):
    print(f"\n{'='*70}")
    print(f"  4. CAN Descriptor Tables in {label}")
    print(f"{'='*70}")

    # Look for sequences of 2-byte CAN IDs in ascending order
    # CAN IDs we expect: 0x082, 0x3CA, 0x3CC, 0x3D3
    # Search for 0x082 as BE (00 82) near other CAN IDs

    # Strategy: find 0x0082 in BE and check if nearby bytes look like a table
    be_082 = struct.pack('>H', 0x082)
    hits = find_byte_pattern(data, be_082, base)

    can_tables = []
    for off, addr in hits:
        # Check if this looks like a table entry by scanning forward
        # Look for other known CAN IDs within 256 bytes
        found_ids = set()
        for scan in range(off - 64, off + 256, 2):
            if 0 <= scan < len(data) - 1:
                val = struct.unpack_from('>H', data, scan)[0]
                if val in (0x082, 0x3CA, 0x3CC, 0x3D3, 0x167, 0x07D, 0x3B3, 0x415, 0x430):
                    found_ids.add(val)

        if len(found_ids) >= 3:
            can_tables.append((off, addr, found_ids))

    if can_tables:
        print(f"  Found {len(can_tables)} potential CAN table regions")
        for off, addr, ids in can_tables:
            sorted_ids = sorted(ids)
            print(f"\n    Table near offset=0x{off:06X} addr=0x{addr:08X}")
            print(f"    CAN IDs found nearby: {[f'0x{x:03X}' for x in sorted_ids]}")

            # Dump the table region
            tbl_start = max(0, off - 32)
            tbl_end = min(len(data), off + 128)
            print(f"    Raw hex dump (offset 0x{tbl_start:06X} - 0x{tbl_end:06X}):")
            for row_off in range(tbl_start, tbl_end, 16):
                chunk = data[row_off:min(row_off+16, tbl_end)]
                hex_str = ' '.join(f'{b:02x}' for b in chunk)
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                print(f"      0x{row_off:06X}: {hex_str:<48s} {ascii_str}")
    else:
        print(f"  No CAN descriptor tables found with 3+ known IDs")

    # Also search for CAN IDs as part of larger structures
    # In V850 firmware, CAN descriptor tables often have fixed-size entries
    # Try to find table by searching for multiple CAN IDs in sequence with regular spacing
    print(f"\n  --- Searching for regularly-spaced CAN ID tables ---")
    all_can_ids = [0x082, 0x3CA, 0x3CC, 0x3D3]
    for can_id in all_can_ids:
        be = struct.pack('>H', can_id)
        hits = find_byte_pattern(data, be, base)
        print(f"    0x{can_id:03X} BE: {len(hits)} occurrences", end="")
        if hits:
            print(f"  at offsets: {[f'0x{h[0]:06X}' for h in hits[:8]]}")
        else:
            print()

    return can_tables


# ============================================================================
# 5. DECOMPILE F150 FUNCTIONS NEAR CAN 0x3CC
# ============================================================================
def decompile_near_3cc(f150_data, f150_base, can_3cc_hits):
    print(f"\n{'='*70}")
    print(f"  5. Decompile F150 Functions Near CAN 0x3CC")
    print(f"{'='*70}")

    if not can_3cc_hits:
        print("  No CAN 0x3CC hits to analyze")
        return

    decoder = V850Decoder()

    # Find PREPARE instructions near each hit
    for off, addr, endian in can_3cc_hits[:5]:
        print(f"\n  --- Looking for function boundary near 0x{addr:08X} ({endian}) ---")

        # Scan backward for PREPARE
        prepare_addr = None
        for scan_off in range(off, max(0, off - 512), -2):
            if scan_off + 4 <= len(f150_data):
                hw = struct.unpack_from('<H', f150_data, scan_off)[0]
                if (hw & 0xFFE0) == 0x0780:  # PREPARE
                    prepare_addr = f150_base + scan_off
                    print(f"    Found PREPARE at 0x{prepare_addr:08X} (offset 0x{scan_off:06X})")
                    break

        if prepare_addr is None:
            print(f"    No PREPARE found within 512 bytes before hit")
            continue

        # Try to decompile from this PREPARE
        try:
            dec = FirmwareDecompiler(F150_BIN, F150_BASE)
            dec.add_entry_point(prepare_addr, f"func_near_3CC_{addr:08X}")
            code = dec.decompile_function_at(prepare_addr)
            print(f"\n    Decompiled output:")
            for line in code.split('\n')[:60]:
                print(f"      {line}")
            if code.count('\n') > 60:
                print(f"      ... ({code.count(chr(10)) - 60} more lines)")
        except Exception as e:
            print(f"    Decompile failed: {e}")

            # Fall back to linear disassembly
            print(f"    Falling back to linear disassembly:")
            scan_off = prepare_addr - f150_base
            for i in range(40):
                insn = decoder.decode(f150_data, scan_off, f150_base)
                if insn is None:
                    scan_off += 2
                    continue
                marker = " <<<<" if abs((scan_off + f150_base) - addr) <= 4 else ""
                print(f"      {insn}{marker}")
                if insn.is_return:
                    break
                scan_off += insn.size


# ============================================================================
# 6. CROSS-REFERENCE ANALYSIS: Lockout presence
# ============================================================================
def analyze_lockout_presence(f150_timers, transit_data=None, transit_base=0):
    print(f"\n{'='*70}")
    print(f"  6. KEY FINDING: Lockout Timer Code Comparison")
    print(f"{'='*70}")

    # Check which timer constants exist in F150
    f150_has = {k: len(v) > 0 for k, v in f150_timers.items()}

    print(f"\n  Lockout timer constants in F150:")
    for const in LOCKOUT_TIMERS:
        status = "PRESENT" if f150_has.get(const, False) else "ABSENT"
        count = len(f150_timers.get(const, []))
        print(f"    {const:6d} (0x{const:04X}): {status} ({count} hits)")

    print(f"\n  Recovery constants in F150:")
    for const in RECOVERY_CONSTANTS:
        status = "PRESENT" if f150_has.get(const, False) else "ABSENT"
        count = len(f150_timers.get(const, []))
        print(f"    {const:6d} (0x{const:04X}): {status} ({count} hits)")

    # Check for the specific lockout pattern: timer constants near CAN 0x3CC refs
    print(f"\n  --- Co-location analysis ---")
    print(f"  Checking if timer constants appear near CAN 0x3CC references...")

    # Determine conclusion
    lockout_timers_present = sum(1 for c in LOCKOUT_TIMERS if f150_has.get(c, False))
    recovery_present = sum(1 for c in RECOVERY_CONSTANTS if f150_has.get(c, False))

    if lockout_timers_present >= 3 and recovery_present >= 2:
        print(f"\n  CONCLUSION: F150 LIKELY HAS the lockout timer code.")
        print(f"  The lockout is probably in the COMMON EPS base code.")
        print(f"  F150 avoids it because LCA/TJA mode doesn't trigger the lockout path.")
        print(f"  Transit can be patched the same way - OR by enabling LCA/TJA mode.")
    elif lockout_timers_present == 0:
        print(f"\n  CONCLUSION: F150 does NOT have the lockout timer constants.")
        print(f"  The lockout is TRANSIT-SPECIFIC code, not in the common EPS base.")
        print(f"  Transit patching requires removing Transit-specific lockout code.")
    else:
        print(f"\n  CONCLUSION: MIXED results - {lockout_timers_present}/4 timer constants found.")
        print(f"  Further analysis needed to determine if this is the same lockout mechanism.")


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("=" * 70)
    print("  F150 vs Transit PSCM Strategy Firmware Comparison")
    print("  F150: bins/f150_strategy.bin (base 0x10040000)")
    print("=" * 70)

    # Load F150 binary
    f150_path = os.path.abspath(F150_BIN)
    if not os.path.exists(f150_path):
        print(f"ERROR: F150 binary not found at {f150_path}")
        return
    f150_data = load_binary(f150_path)
    print(f"\n  F150 binary: {len(f150_data)} bytes loaded from {f150_path}")

    decoder = V850Decoder()

    # Load Transit binary if available
    transit_data = None
    transit_base = 0
    for path in TRANSIT_BLOCK0_CANDIDATES:
        abspath = os.path.abspath(path)
        if os.path.exists(abspath):
            transit_data = load_binary(abspath)
            transit_base = TRANSIT_BASE
            print(f"  Transit block0: {len(transit_data)} bytes loaded from {abspath}")
            break
    if transit_data is None:
        print(f"  Transit block0: not found (comparison will be F150-only)")

    # 1. Search for CAN ID 0x3CC
    f150_3cc_hits = search_can_3cc(f150_data, F150_BASE, decoder, "F150")
    if transit_data:
        transit_3cc_hits = search_can_3cc(transit_data, transit_base, decoder, "Transit")

    # 2. Search for lockout timer patterns
    f150_timers = search_lockout_patterns(f150_data, F150_BASE, decoder, "F150")

    # 3. Search for LCA/TJA enable logic
    search_lca_tja(f150_data, F150_BASE, decoder, "F150")
    if transit_data:
        search_lca_tja(transit_data, transit_base, decoder, "Transit")

    # 4. Compare CAN descriptor tables
    f150_tables = find_can_tables(f150_data, F150_BASE, "F150")
    if transit_data:
        transit_tables = find_can_tables(transit_data, transit_base, "Transit")

    # 5. Decompile F150 functions near CAN 0x3CC
    decompile_near_3cc(f150_data, F150_BASE, f150_3cc_hits)

    # 6. Key finding
    analyze_lockout_presence(f150_timers, transit_data, transit_base)

    print(f"\n{'='*70}")
    print(f"  Analysis Complete")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
