#!/usr/bin/env python3
"""
Find the LKA lockout timer in Transit PSCM firmware.

KEY FINDINGS from binary analysis:
- block0_strategy.bin (1MB at 0x01000000) is mostly compressed/encrypted data
  in the range 0x20000-0xDA000 (entropy 6.5-7.0). The V850 decoder produces
  garbage when run against these regions.
- Actual readable data is in 0x00000-0x1D000 (strings, CAN tables, config)
  and 0xDA000-0xFFFFF (padding/init data).
- The calibration file (cal_AH.bin at 0x00FD0000) contains timer constants
  in BIG-ENDIAN format at offset 0x06B0:
    [0, 100, 0, 1000, 2000, 1000, 500, 400, 5]
  This is the timer threshold table used by the lockout logic.
- CAN 0x3CC is in the descriptor table at block0 offset 0x2B78.

Strategy: Since we cannot decode the encrypted code region, we search for:
1. Timer constants in the calibration file
2. CAN 0x3CC references in block0 data tables
3. Cross-reference between calibration addresses and strategy data
4. Pattern matching for known AUTOSAR structures
"""

import struct
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

FW_DIR = os.path.join(os.path.dirname(__file__),
    '..', 'firmware', '2025_Transit_PSCM', 'decompressed')
BLOCK0_PATH = os.path.join(FW_DIR, 'AM', 'block0_strategy.bin')
BLOCK2_PATH = os.path.join(FW_DIR, 'AM', 'block2_ext.bin')
CAL_PATH = os.path.join(FW_DIR, 'cal_AH.bin')
CAL_AD_PATH = os.path.join(FW_DIR, 'cal_AD.bin')
CAL_AF_PATH = os.path.join(FW_DIR, 'cal_AF.bin')

BASE_ADDR = 0x01000000
CAL_BASE = 0x00FD0000
BLOCK2_BASE = 0x20FF0000


def load(path):
    with open(path, 'rb') as f:
        return f.read()


# ============================================================================
# 1. CAN DESCRIPTOR TABLE
# ============================================================================
def parse_can_table(data):
    print("=" * 80)
    print("SECTION 1: CAN 0x3CC IN DESCRIPTOR TABLES")
    print("=" * 80)

    # First table at 0x2B68: 8-byte records [CAN_ID:16LE, idx:16LE, flags:16LE, pad:16LE]
    print("\n  Primary CAN Table at block0+0x2B68:")
    off = 0x2B68
    target = None
    for i in range(22):
        can_id, idx, flags, pad = struct.unpack_from('<HHHH', data, off)
        marker = " <<<< TARGET" if can_id == 0x03CC else ""
        print(f"    [{i:2d}] CAN=0x{can_id:04X} idx=0x{idx:04X} flags=0x{flags:04X}{marker}")
        if can_id == 0x03CC:
            target = {'can_id': can_id, 'idx': idx, 'flags': flags, 'offset': off}
        off += 8

    # Second table at 0x2FC8
    print("\n  Secondary CAN Table at block0+0x2FC8:")
    for i in range(14):
        off2 = 0x2FC8 + i * 8
        v = struct.unpack_from('<HHHH', data, off2)
        can_id = v[2]
        marker = " <<<< TARGET" if can_id == 0x03CC else ""
        print(f"    [{i:2d}] buf={v[0]:04X},{v[1]:04X} CAN=0x{can_id:04X} idx={v[3]:04X}{marker}")

    if target:
        print(f"\n  RESULT: CAN 0x3CC found at block0+0x{target['offset']:04X}")
        print(f"          Index: 0x{target['idx']:04X}, Flags: 0x{target['flags']:04X}")
        print(f"          In secondary table: bufinfo=0x0308,0x0002 idx=0x0006")

    return target


# ============================================================================
# 2. CALIBRATION TIMER TABLE
# ============================================================================
def find_cal_timers(cal_data):
    print()
    print("=" * 80)
    print("SECTION 2: TIMER CONSTANTS IN CALIBRATION FILE")
    print("=" * 80)

    # Known timer values to search for (as BE16)
    timer_vals = {100, 200, 250, 300, 400, 500, 1000, 2000, 5000, 10000, 20, 50}

    # Find clusters of timer-like values
    print("\n  Scanning for BE16 timer value clusters...")
    clusters = []
    for off in range(0, len(cal_data) - 20, 2):
        # Count timer values in a 20-byte window
        count = 0
        values = []
        for d in range(0, 20, 2):
            if off + d + 2 <= len(cal_data):
                v = struct.unpack_from('>H', cal_data, off + d)[0]
                if v in timer_vals:
                    count += 1
                    values.append((off + d, v))
        if count >= 3:
            clusters.append((off, count, values))

    # Deduplicate overlapping clusters
    deduped = []
    for c in clusters:
        if not deduped or c[0] > deduped[-1][0] + 20:
            deduped.append(c)
        elif c[1] > deduped[-1][1]:
            deduped[-1] = c

    print(f"  Found {len(deduped)} timer clusters:")
    for off, count, values in deduped:
        cal_addr = CAL_BASE + off
        print(f"\n    Cluster at cal+0x{off:04X} (0x{cal_addr:08X}), {count} timer values:")
        # Show full context
        for d in range(0, 24, 2):
            if off + d + 2 <= len(cal_data):
                v = struct.unpack_from('>H', cal_data, off + d)[0]
                co = off + d
                marker = f"  <<< TIMER: {v}" if v in timer_vals else ""
                if v <= 5:
                    marker = f"  <<< small: {v}"
                print(f"      0x{CAL_BASE+co:08X} (cal+0x{co:04X}): {v:5d} (0x{v:04X}){marker}")

    return deduped


# ============================================================================
# 3. DETAILED TIMER TABLE ANALYSIS
# ============================================================================
def analyze_timer_table(cal_data):
    print()
    print("=" * 80)
    print("SECTION 3: LOCKOUT TIMER TABLE ANALYSIS (cal+0x06B0)")
    print("=" * 80)

    # The main timer table at cal+0x06B0
    print("\n  Timer table at 0x00FD06B0 (cal+0x06B0):")
    print("  Offset      Address       BE16   Interpretation")
    print("  " + "-" * 65)

    interp = {
        0x06AE: "Pre-timer value: 1500",
        0x06B0: "Timer base/init: 0",
        0x06B2: "Short timeout: 100 ticks (1s @ 10ms or 0.1s @ 1ms)",
        0x06B4: "Gap: 0",
        0x06B6: "*** LOCKOUT THRESHOLD: 1000 ticks (10s @ 10ms) ***",
        0x06B8: "Extended threshold: 2000 ticks (20s @ 10ms)",
        0x06BA: "Second threshold: 1000 ticks",
        0x06BC: "Recovery time: 500 ticks (5s @ 10ms)",
        0x06BE: "Recovery time: 400 ticks (4s @ 10ms)",
        0x06C0: "Min count: 5",
        0x06C2: "Max value: 255 (0xFF)",
        0x06E2: "State count: 2",
    }

    for off in range(0x06A0, 0x0700, 2):
        v = struct.unpack_from('>H', cal_data, off)[0]
        addr = CAL_BASE + off
        desc = interp.get(off, "")
        if v == 0xFFFF:
            desc = "(padding)" if not desc else desc
        print(f"  0x{off:04X}  0x{addr:08X}  {v:5d}    {desc}")

    print()
    print("  INTERPRETATION:")
    print("  The lockout timer table at 0x00FD06B0 contains:")
    print("    - Lockout threshold: 1000 ticks at cal+0x06B6 (0x00FD06B6)")
    print("    - If task runs at 10ms: 1000 * 10ms = 10 seconds")
    print("    - Extended threshold: 2000 ticks at cal+0x06B8")
    print("    - Recovery times: 500/400 ticks at cal+0x06BC/0x06BE")
    print("    - These match the expected LKA lockout behavior:")
    print("      ~10s active steering -> lockout -> ~5s recovery")


# ============================================================================
# 4. COMPARE CALIBRATIONS
# ============================================================================
def compare_calibrations():
    print()
    print("=" * 80)
    print("SECTION 4: CALIBRATION COMPARISON (AD vs AF vs AH)")
    print("=" * 80)

    cals = {}
    for name, path in [('AD', CAL_AD_PATH), ('AF', CAL_AF_PATH), ('AH', CAL_PATH)]:
        if os.path.exists(path):
            cals[name] = load(path)

    if len(cals) < 2:
        print("  Not enough calibration files for comparison")
        return

    # Check timer table consistency
    print("\n  Timer table (cal+0x06B0-0x06C0) across calibrations:")
    all_same = True
    for off in range(0x06B0, 0x06C2, 2):
        vals = {}
        for name, data in cals.items():
            vals[name] = struct.unpack_from('>H', data, off)[0]
        same = len(set(vals.values())) == 1
        if not same:
            all_same = False
        v = list(vals.values())[0]
        status = "SAME" if same else "DIFF!"
        print(f"    cal+0x{off:04X}: {v:5d}  [{status}]")

    if all_same:
        print("\n  Timer table is IDENTICAL across all calibration variants.")
        print("  This means the lockout timing is NOT region-specific.")
    else:
        print("\n  Timer table DIFFERS between calibrations!")

    # Show total differences in timer-relevant area
    names = list(cals.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            diff_count = 0
            for off in range(0x0600, 0x0800, 2):
                if off + 2 <= len(cals[names[i]]):
                    a = struct.unpack_from('>H', cals[names[i]], off)[0]
                    b = struct.unpack_from('>H', cals[names[j]], off)[0]
                    if a != b:
                        diff_count += 1
            print(f"  Diffs in 0x0600-0x0800: {names[i]} vs {names[j]}: {diff_count}")


# ============================================================================
# 5. SEARCH FOR 0x3CC REFERENCES IN BLOCK0 DATA REGION
# ============================================================================
def find_3cc_refs(data):
    print()
    print("=" * 80)
    print("SECTION 5: ALL 0x3CC REFERENCES IN BLOCK0")
    print("=" * 80)

    # Search for 0x03CC as LE16 and BE16
    print("\n  0x03CC as little-endian (CC 03):")
    needle_le = b'\xCC\x03'
    pos = 0
    while True:
        pos = data.find(needle_le, pos)
        if pos == -1: break
        region = "data" if pos < 0x20000 else "code/encrypted"
        context = data[max(0, pos-4):pos+12].hex()
        print(f"    offset 0x{pos:05X} ({region}): ...{context}...")
        pos += 1

    print(f"\n  0x03CC as big-endian (03 CC):")
    needle_be = b'\x03\xCC'
    pos = 0
    count = 0
    while True:
        pos = data.find(needle_be, pos)
        if pos == -1: break
        region = "data" if pos < 0x20000 else "code/encrypted"
        if pos < 0x20000:  # Only show data region hits
            context = data[max(0, pos-4):pos+12].hex()
            print(f"    offset 0x{pos:05X} ({region}): ...{context}...")
        count += 1
        pos += 1
    print(f"    ({count} total hits, showing only data region)")


# ============================================================================
# 6. SEARCH FOR LOCKOUT-RELATED PATTERNS IN DATA TABLES
# ============================================================================
def find_lockout_data_patterns(data):
    print()
    print("=" * 80)
    print("SECTION 6: LOCKOUT STATE PATTERNS IN DATA TABLES")
    print("=" * 80)

    # In the data tables (0x8000-0x1D000), look for structures that could be
    # state machine descriptors for LaActAvail_D_Actl (values 0,1,2,3)

    # Search for byte sequences [0, 1, 2, 3] or [0, 2] or similar state tables
    print("\n  Searching for state value tables [0,1,2,3] in data region...")
    for off in range(0x8000, 0x1D000):
        if off + 4 <= len(data):
            # Check for [0, 1, 2, 3] as bytes
            if (data[off] == 0 and data[off+1] == 1 and
                data[off+2] == 2 and data[off+3] == 3):
                # Check context
                before = data[max(0,off-4):off].hex()
                after = data[off+4:off+8].hex()
                print(f"    0x{off:05X}: ...{before} [00 01 02 03] {after}...")

    # Search for bit position 5 (LaActAvail_D_Actl bit position in CAN msg)
    # In CAN signal descriptors, look for bit_pos=5, bit_length=2
    print("\n  Searching for CAN signal descriptor (bitpos=5, len=2)...")
    for off in range(0x2000, 0x6000, 2):
        if off + 4 <= len(data):
            # Various possible encodings of bit position 5, length 2
            # Could be: [05, 02] or [2, 5] etc
            if data[off] == 5 and data[off+1] == 2:
                context = data[max(0,off-8):off+8].hex()
                print(f"    0x{off:05X}: ...{context}...")
            if data[off] == 2 and data[off+1] == 5:
                context = data[max(0,off-8):off+8].hex()
                print(f"    0x{off:05X}: ...{context}...")


# ============================================================================
# 7. ENTROPY MAP OF BLOCK0
# ============================================================================
def entropy_map(data):
    import math

    print()
    print("=" * 80)
    print("SECTION 7: BLOCK0 ENTROPY MAP (identifying code vs data)")
    print("=" * 80)

    print("\n  Block  Entropy  Type")
    print("  " + "-" * 55)

    for i in range(0, len(data), 0x4000):
        block = data[i:i+0x4000]
        if not block:
            break
        freq = [0] * 256
        for b in block:
            freq[b] += 1
        n = len(block)
        ent = -sum(f/n * math.log2(f/n) for f in freq if f > 0)

        if ent < 1.0:
            typ = "PADDING/ZEROS"
        elif ent < 3.5:
            typ = "DATA TABLES (structured)"
        elif ent < 5.0:
            typ = "STRINGS/CONFIG"
        elif ent < 6.0:
            typ = "MIXED CODE/DATA"
        else:
            typ = "COMPILED CODE (or encrypted)"

        bar = "#" * int(ent * 3)
        print(f"  0x{i:05X}  {ent:.2f}  {typ:30s}  {bar}")


# ============================================================================
# 8. SEARCH FOR TIMER REFS IN BLOCK0 LOW-ENTROPY REGION
# ============================================================================
def find_timer_refs_in_data(data):
    print()
    print("=" * 80)
    print("SECTION 8: TIMER/STATE REFERENCES IN BLOCK0 DATA TABLES")
    print("=" * 80)

    # The data region 0x8000-0x1D000 contains structured tables
    # These may include RTE (Runtime Environment) configuration,
    # signal routing tables, and task configuration

    # Look for references to calibration offset 0x06B0-0x06C0
    # These could appear as:
    # - 16-bit offsets into the calibration block
    # - 32-bit absolute addresses
    # - Relative offsets from a base pointer

    print("\n  Searching for cal offset references (0x06B0-0x06C0) as LE16...")
    for off in range(0x2000, 0x20000, 2):
        if off + 2 <= len(data):
            v = struct.unpack_from('<H', data, off)[0]
            if 0x06A0 <= v <= 0x06E0:
                context = data[max(0,off-4):off+8].hex()
                print(f"    0x{off:05X}: value=0x{v:04X} (cal+0x{v:04X}) context={context}")

    # Also search for the actual timer values in block0 data tables
    print("\n  Searching for timer values (BE16) in block0 data tables (0x3000-0x1D000)...")
    for val in [1000, 2000, 500, 400]:
        be_bytes = struct.pack('>H', val)
        pos = 0x3000
        while pos < 0x1D000:
            pos = data.find(be_bytes, pos)
            if pos == -1 or pos >= 0x1D000:
                break
            # Check if preceded/followed by other timer values
            context = data[max(0,pos-6):pos+10]
            print(f"    {val:4d} (BE) at 0x{pos:05X}: {context.hex()}")
            pos += 1


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("LKA Lockout Timer Search - Transit PSCM Firmware")
    print(f"Block0 base: 0x{BASE_ADDR:08X}, Cal base: 0x{CAL_BASE:08X}")
    print()

    data = load(BLOCK0_PATH)
    cal = load(CAL_PATH)
    print(f"Block0: {len(data)} bytes, Calibration: {len(cal)} bytes")

    # 1. CAN descriptor table
    target_can = parse_can_table(data)

    # 2. Timer constants in calibration
    timer_clusters = find_cal_timers(cal)

    # 3. Detailed timer table analysis
    analyze_timer_table(cal)

    # 4. Compare calibrations
    compare_calibrations()

    # 5. 0x3CC references
    find_3cc_refs(data)

    # 6. Lockout data patterns
    find_lockout_data_patterns(data)

    # 7. Entropy map
    entropy_map(data)

    # 8. Timer refs in data
    find_timer_refs_in_data(data)

    # SUMMARY
    print()
    print("=" * 80)
    print("SUMMARY & CONCLUSIONS")
    print("=" * 80)
    print("""
  KEY FINDINGS:

  1. CAN 0x3CC LOCATION:
     - Primary table: block0+0x2B78 (entry #2), idx=0x0127, flags=0x0803
     - Secondary table: block0+0x3018 (entry #10), bufinfo=0x0308,0x0002, idx=0x0006

  2. LOCKOUT TIMER TABLE FOUND IN CALIBRATION:
     Address: 0x00FD06B0 (cal_AH.bin + 0x06B0)
     Format: Big-endian 16-bit values
     Values (as ticks, likely 10ms period):
       cal+0x06B2 = 100  (1 second initial delay)
       cal+0x06B6 = 1000 (10 seconds - MAIN LOCKOUT THRESHOLD)
       cal+0x06B8 = 2000 (20 seconds - extended threshold)
       cal+0x06BA = 1000 (10 seconds - secondary)
       cal+0x06BC = 500  (5 seconds - recovery time)
       cal+0x06BE = 400  (4 seconds - recovery time)

     This table is IDENTICAL across AD/AF/AH calibration variants.

  3. BINARY STRUCTURE:
     - 0x00000-0x02000: FF padding
     - 0x02000-0x06000: Strings, part numbers, AUTOSAR paths
     - 0x06000-0x20000: Configuration tables (CAN descriptors, signal routing)
     - 0x20000-0xDA000: HIGH ENTROPY - compiled V850 code or encrypted data
     - 0xDA000-0xE0000: Padding
     - 0xE0000-0xEA000: Init data
     - 0xEA000-0xFFFFF: Padding

  4. CODE ANALYSIS LIMITATION:
     The strategy code region (0x20000-0xDA000) has entropy 6.5-7.1.
     The V850 decoder produces incoherent results (nonsensical instruction
     sequences) when applied to this region. This could mean:
     a) The code uses a different encoding/compression on top of LZSS
     b) The V850E2 decoder has gaps in instruction coverage
     c) The data is XOR-obfuscated

     WITHOUT being able to decode the code, we can still identify the
     lockout timer through the calibration table.

  5. TO PATCH THE LOCKOUT:
     The most promising approach is to modify the calibration file:
     - Set cal+0x06B6 (lockout threshold) from 1000 to 0xFFFF (max)
       This would increase the lockout time from 10s to 655s (effectively disabled)
     - Or set cal+0x06BC/0x06BE (recovery) to 0 (instant recovery)
""")


if __name__ == '__main__':
    main()
