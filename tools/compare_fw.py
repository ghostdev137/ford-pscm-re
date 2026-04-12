#!/usr/bin/env python3
"""
Deep comparison of Ford PSCM V850E2 firmware binaries.
Compares transit_strategy_AG.bin vs transit_strategy_AM.bin,
and transit_calibration_AH.bin vs f150_calibration.bin.
"""

import struct
import sys
import os

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BINS = os.path.join(os.path.dirname(__file__), '..', 'bins')
STRATEGY_BASE = 0x01000000

def load(name):
    path = os.path.join(BINS, name)
    with open(path, 'rb') as f:
        return f.read()

def hexdump(data, offset=0, base=0, width=16, max_lines=32):
    """Pretty hex dump with address."""
    lines = []
    for i in range(0, len(data), width):
        if i // width >= max_lines:
            lines.append(f"  ... ({len(data) - i} more bytes)")
            break
        chunk = data[i:i+width]
        addr = base + offset + i
        hexpart = ' '.join(f'{b:02X}' for b in chunk)
        ascpart = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"  {addr:08X} | {hexpart:<{width*3-1}} | {ascpart}")
    return '\n'.join(lines)

def find_diff_regions(a, b, min_gap=4):
    """Find regions where a and b differ. Merge if gap <= min_gap."""
    assert len(a) == len(b)
    regions = []
    in_diff = False
    start = 0
    for i in range(len(a)):
        if a[i] != b[i]:
            if not in_diff:
                start = i
                in_diff = True
            end = i
        elif in_diff:
            # Check if gap to next diff is small enough to merge
            # Look ahead
            found_next = False
            for j in range(i, min(i + min_gap + 1, len(a))):
                if a[j] != b[j]:
                    found_next = True
                    break
            if not found_next:
                regions.append((start, end + 1))
                in_diff = False
    if in_diff:
        regions.append((start, end + 1))
    return regions

def check_v850_code(data, offset=0):
    """Check for V850E2 instruction patterns in data."""
    patterns = {
        'PREPARE': 0,
        'DISPOSE': 0,
        'MOVHI': 0,
        'MOVEA': 0,
        'LD.W': 0,
        'ST.W': 0,
        'JR': 0,
        'JARL': 0,
        'CMP': 0,
        'BR_cond': 0,
        'MOV_imm5': 0,
        'ADD': 0,
    }
    if len(data) < 2:
        return patterns, False

    i = 0
    while i < len(data) - 1:
        hw = struct.unpack_from('<H', data, i)[0]

        # PREPARE: format XIII - bits[15:5] == 0b00000111100 -> hw & 0xFFE0 == 0x0780
        if hw & 0xFFE0 == 0x0780:
            patterns['PREPARE'] += 1
        # DISPOSE: hw & 0xFFE0 == 0x0640
        if hw & 0xFFE0 == 0x0640:
            patterns['DISPOSE'] += 1
        # MOVHI: bits[15:11] == 11000 -> hw & 0xF800 == 0xC000 (32-bit)
        # Actually MOVHI = 110010 xxxxxxx rrrrr -> top 6 bits = 0b110010
        if (hw >> 5) & 0x7FF == 0x320:  # MOVHI format
            patterns['MOVHI'] += 1
        # MOVEA: top 6 bits = 0b110001
        if (hw >> 5) & 0x7FF == 0x318:
            patterns['MOVEA'] += 1
        # Conditional branch (16-bit): various Bcond patterns
        # Bcond: bits[15:12]=1011, bits[3:0]=cond
        if hw & 0xF000 == 0xB000:
            patterns['BR_cond'] += 1
        # MOV imm5,reg2: bits[15:11]=00100
        if hw & 0xF800 == 0x2000:
            patterns['MOV_imm5'] += 1
        # CMP imm5,reg2: bits[15:11]=01011
        if hw & 0xF800 == 0x2800:
            patterns['CMP'] += 1
        # ADD reg1,reg2: bits[15:11]=01110
        if hw & 0xF800 == 0x3800:
            patterns['ADD'] += 1
        # JR 22-bit: hw & 0xF800 == 0x0780? No. JR = 00000010110xxxxx + disp
        # JARL 22-bit: 0b00000_11110_xxxxx
        if hw & 0xFFE0 == 0x07C0:
            patterns['JARL'] += 1
        if hw & 0xFFE0 == 0x05C0:
            patterns['JR'] += 1
        # LD.W: 32-bit, second hw bits[10:7]=0b0111, first hw bits[15:11]=00111
        # Actually LD.W = 0b00000111001 in extended. Let's use simpler heuristic.
        # For 32-bit loads: top byte patterns

        i += 2

    total = sum(patterns.values())
    is_code = total > len(data) // 16  # rough heuristic: at least 1 instruction per 16 bytes
    return patterns, is_code

def find_address_patterns(data, base=STRATEGY_BASE):
    """Find 32-bit LE values that look like addresses."""
    addrs = []
    for i in range(0, len(data) - 3, 2):  # aligned
        val = struct.unpack_from('<I', data, i)[0]
        # Check if it falls in known memory ranges
        if 0x01000000 <= val <= 0x01200000:  # strategy flash
            addrs.append((i, val, 'strategy_flash'))
        elif 0x00FD0000 <= val <= 0x01000000:  # calibration flash
            addrs.append((i, val, 'calibration_flash'))
        elif 0xFEDF0000 <= val <= 0xFEE00000:  # peripheral I/O
            addrs.append((i, val, 'peripheral_io'))
        elif 0x03FF0000 <= val <= 0x04000000:  # local RAM
            addrs.append((i, val, 'local_ram'))
    return addrs

def find_did_values(data):
    """Find DID-like patterns (DE00-DEFF, F1xx, etc.)."""
    dids = []
    for i in range(0, len(data) - 1):
        val = struct.unpack_from('>H', data, i)[0]  # Big-endian DID
        if 0xDE00 <= val <= 0xDEFF:
            dids.append((i, val))
        elif 0xF100 <= val <= 0xF1FF:
            dids.append((i, val))
        elif 0xF190 <= val <= 0xF19F:
            dids.append((i, val))
    return dids

def analyze_cal_padding(data, name, base):
    """Analyze FF-padded vs populated regions in calibration."""
    block_size = 256
    populated = []
    ff_padded = []
    for i in range(0, len(data), block_size):
        block = data[i:i+block_size]
        ff_count = block.count(0xFF)
        ratio = ff_count / len(block)
        if ratio > 0.95:
            ff_padded.append((i, i + len(block), ratio))
        else:
            populated.append((i, i + len(block), ratio))
    return populated, ff_padded

# ============================================================
print("=" * 80)
print("FORD PSCM V850E2 FIRMWARE DEEP COMPARISON")
print("=" * 80)

ag = load('transit_strategy_AG.bin')
am = load('transit_strategy_AM.bin')
print(f"\nLoaded transit_strategy_AG.bin: {len(ag)} bytes")
print(f"Loaded transit_strategy_AM.bin: {len(am)} bytes")

# ============================================================
print("\n" + "=" * 80)
print("SECTION 1: ALL DIFF REGIONS BETWEEN AG AND AM")
print("=" * 80)

total_diff_bytes = sum(1 for i in range(len(ag)) if ag[i] != am[i])
print(f"\nTotal differing bytes: {total_diff_bytes}")

regions = find_diff_regions(ag, am, min_gap=8)
print(f"Number of diff regions (gap<=8 merged): {len(regions)}")

# Classify regions
zeroed_regions = []  # AM zeroed out (removed)
added_regions = []   # AG zeroed (added in AM)
code_regions = []    # Likely code changes
data_regions = []    # Data changes
small_regions = []   # Tiny changes (< 8 bytes)

for idx, (start, end) in enumerate(regions):
    size = end - start
    ag_data = ag[start:end]
    am_data = am[start:end]
    am_zero = am_data.count(0x00) == len(am_data) and size > 4
    ag_zero = ag_data.count(0x00) == len(ag_data) and size > 4
    _, is_code_ag = check_v850_code(ag_data)
    _, is_code_am = check_v850_code(am_data)

    entry = (idx, start, end, size)
    if am_zero:
        zeroed_regions.append(entry)
    elif ag_zero:
        added_regions.append(entry)
    elif is_code_ag or is_code_am:
        code_regions.append(entry)
    elif size < 8:
        small_regions.append(entry)
    else:
        data_regions.append(entry)

print(f"\nClassification:")
print(f"  Zeroed in AM (REMOVED):    {len(zeroed_regions)} regions, {sum(e[3] for e in zeroed_regions)} bytes")
print(f"  Zeroed in AG (ADDED in AM):{len(added_regions)} regions, {sum(e[3] for e in added_regions)} bytes")
print(f"  Likely code changes:       {len(code_regions)} regions, {sum(e[3] for e in code_regions)} bytes")
print(f"  Data changes (>=8 bytes):  {len(data_regions)} regions, {sum(e[3] for e in data_regions)} bytes")
print(f"  Small changes (<8 bytes):  {len(small_regions)} regions")

# Show ZEROED regions (most interesting - removed LKA code)
print(f"\n{'=' * 70}")
print("REGIONS ZEROED OUT IN AM (removed/disabled in newer firmware):")
print(f"{'=' * 70}")
for idx, start, end, size in zeroed_regions:
    addr_start = STRATEGY_BASE + start
    addr_end = STRATEGY_BASE + end
    ag_data = ag[start:end]
    patterns_ag, is_code_ag = check_v850_code(ag_data)
    active = {k: v for k, v in patterns_ag.items() if v > 0}
    ctype = "CODE" if is_code_ag else "DATA"
    print(f"\n  #{idx+1}: 0x{start:05X}-0x{end:05X} (addr 0x{addr_start:08X}-0x{addr_end:08X}) "
          f"{size} bytes [{ctype}]")
    if active:
        print(f"    V850 patterns: {active}")
    print(f"    AG content:")
    print(hexdump(ag_data, start, STRATEGY_BASE, max_lines=16))

# Show ADDED regions
if added_regions:
    print(f"\n{'=' * 70}")
    print("REGIONS ADDED IN AM (new in newer firmware):")
    print(f"{'=' * 70}")
    for idx, start, end, size in added_regions:
        addr_start = STRATEGY_BASE + start
        am_data = am[start:end]
        print(f"\n  #{idx+1}: 0x{start:05X}-0x{end:05X} (addr 0x{addr_start:08X}) {size} bytes")
        print(hexdump(am_data, start, STRATEGY_BASE, max_lines=8))

# Show LARGE data/code diff regions (top 20 by size)
print(f"\n{'=' * 70}")
print("TOP 30 LARGEST DIFF REGIONS (code + data):")
print(f"{'=' * 70}")
all_nonzero = code_regions + data_regions
all_nonzero.sort(key=lambda x: x[3], reverse=True)
for entry in all_nonzero[:30]:
    idx, start, end, size = entry
    addr_start = STRATEGY_BASE + start
    ag_data = ag[start:end]
    am_data = am[start:end]
    patterns_ag, is_code_ag = check_v850_code(ag_data)
    active = {k: v for k, v in patterns_ag.items() if v > 0}
    ctype = "CODE" if is_code_ag else "DATA"
    print(f"\n  #{idx+1}: 0x{start:05X}-0x{end:05X} (addr 0x{addr_start:08X}) {size} bytes [{ctype}]")
    if active:
        print(f"    V850 patterns: {active}")
    print(f"    AG:")
    print(hexdump(ag_data, start, STRATEGY_BASE, max_lines=6))
    print(f"    AM:")
    print(hexdump(am_data, start, STRATEGY_BASE, max_lines=6))

# ============================================================
print("\n" + "=" * 80)
print("SECTION 2: DEEP ANALYSIS OF 0xE0000-0xE1120 REGION (AG)")
print("=" * 80)

region_start = 0xE0000
region_end = 0xE1120
region_data = ag[region_start:region_end]
region_am = am[region_start:region_end]

print(f"\nRegion size: {len(region_data)} bytes")
print(f"AG non-zero bytes: {sum(1 for b in region_data if b != 0)}")
print(f"AM non-zero bytes: {sum(1 for b in region_am if b != 0)}")

print(f"\n--- Full hex dump of AG 0xE0000-0xE1120 ---")
print(hexdump(region_data, region_start, STRATEGY_BASE, max_lines=300))

print(f"\n--- V850 instruction analysis ---")
patterns, is_code = check_v850_code(region_data)
print(f"Detected patterns: {patterns}")
print(f"Likely code: {is_code}")

print(f"\n--- Address-like values in AG 0xE0000-0xE1120 ---")
addrs = find_address_patterns(region_data, STRATEGY_BASE)
for off, val, region_type in addrs:
    abs_off = region_start + off
    print(f"  offset 0x{abs_off:05X}: 0x{val:08X} ({region_type})")

print(f"\n--- DID values in AG 0xE0000-0xE1120 ---")
dids = find_did_values(region_data)
for off, val in dids:
    abs_off = region_start + off
    print(f"  offset 0x{abs_off:05X}: 0x{val:04X}")

# Look for specific byte patterns that might be LKA-related strings or constants
print(f"\n--- Notable byte patterns ---")
# Search for common LKA/TJA constants
for pattern_name, pattern_bytes in [
    ("LKA", b'LKA'), ("TJA", b'TJA'), ("LCA", b'LCA'), ("ESA", b'ESA'),
    ("LANE", b'LANE'), ("lane", b'lane'),
]:
    idx = region_data.find(pattern_bytes)
    if idx >= 0:
        print(f"  Found '{pattern_name}' at offset 0x{region_start + idx:05X}")

# ============================================================
print("\n" + "=" * 80)
print("SECTION 3: AS-BUILT RELATED REGIONS")
print("=" * 80)

for label, rstart, rend in [
    ("As-built template/validation", 0x3040, 0x3170),
    ("Config table", 0x8600, 0x86C0),
    ("DID table", 0xDB74, 0xDD00),
]:
    ag_sec = ag[rstart:rend]
    am_sec = am[rstart:rend]
    differs = ag_sec != am_sec
    diff_count = sum(1 for i in range(len(ag_sec)) if ag_sec[i] != am_sec[i])

    print(f"\n{'-' * 70}")
    print(f"{label} (0x{rstart:05X}-0x{rend:05X}, {rend-rstart} bytes)")
    print(f"  Differs: {differs} ({diff_count} bytes different)")

    if differs:
        # Show specific diffs
        for i in range(len(ag_sec)):
            if ag_sec[i] != am_sec[i]:
                addr = STRATEGY_BASE + rstart + i
                # Show context: 16-byte aligned block around the diff
                block_start = (i // 16) * 16
                block_end = min(block_start + 16, len(ag_sec))
                if i == block_start or (i > 0 and ag_sec[i-1] == am_sec[i-1]):
                    print(f"\n  Diff at offset 0x{rstart + i:05X} (addr 0x{addr:08X}):")
                    print(f"    AG: {' '.join(f'{b:02X}' for b in ag_sec[block_start:block_end])}")
                    print(f"    AM: {' '.join(f'{b:02X}' for b in am_sec[block_start:block_end])}")
    else:
        print("  (Identical in both versions)")
        # Still dump it for reference
        print(f"  Content:")
        print(hexdump(ag_sec, rstart, STRATEGY_BASE, max_lines=8))
        if len(ag_sec) > 128:
            print("  ...")

# ============================================================
print("\n" + "=" * 80)
print("SECTION 4: CALIBRATION COMPARISON (F150 vs Transit)")
print("=" * 80)

f150_cal = load('f150_calibration.bin')
transit_cal = load('transit_calibration_AH.bin')

F150_CAL_BASE = 0x101C0000
TRANSIT_CAL_BASE = 0x00FD0000

print(f"\nf150_calibration.bin:        {len(f150_cal)} bytes, base 0x{F150_CAL_BASE:08X}")
print(f"transit_calibration_AH.bin:  {len(transit_cal)} bytes, base 0x{TRANSIT_CAL_BASE:08X}")

f150_ff = f150_cal.count(0xFF)
transit_ff = transit_cal.count(0xFF)
print(f"\nF150 cal FF bytes:    {f150_ff}/{len(f150_cal)} ({100*f150_ff/len(f150_cal):.1f}%)")
print(f"Transit cal FF bytes: {transit_ff}/{len(transit_cal)} ({100*transit_ff/len(transit_cal):.1f}%)")

print(f"\n--- Transit calibration: populated vs FF-padded regions ---")
pop, pad = analyze_cal_padding(transit_cal, "transit", TRANSIT_CAL_BASE)
print(f"Populated blocks (256-byte, <95% FF): {len(pop)}")
print(f"FF-padded blocks (256-byte, >=95% FF): {len(pad)}")

print(f"\nPopulated regions in Transit cal:")
# Merge consecutive populated blocks
if pop:
    merged = []
    cs, ce = pop[0][0], pop[0][1]
    for s, e, _ in pop[1:]:
        if s == ce:
            ce = e
        else:
            merged.append((cs, ce))
            cs, ce = s, e
    merged.append((cs, ce))
    for s, e in merged:
        addr_s = TRANSIT_CAL_BASE + s
        addr_e = TRANSIT_CAL_BASE + e
        print(f"  0x{s:05X}-0x{e:05X} (addr 0x{addr_s:08X}-0x{addr_e:08X}) {e-s} bytes")
        # Show first 32 bytes
        print(hexdump(transit_cal[s:s+min(64, e-s)], s, TRANSIT_CAL_BASE, max_lines=4))

print(f"\nFF-padded regions in Transit cal:")
if pad:
    merged_pad = []
    cs, ce = pad[0][0], pad[0][1]
    for s, e, _ in pad[1:]:
        if s == ce:
            ce = e
        else:
            merged_pad.append((cs, ce))
            cs, ce = s, e
    merged_pad.append((cs, ce))
    for s, e in merged_pad:
        addr_s = TRANSIT_CAL_BASE + s
        addr_e = TRANSIT_CAL_BASE + e
        print(f"  0x{s:05X}-0x{e:05X} (addr 0x{addr_s:08X}-0x{addr_e:08X}) {e-s} bytes")

print(f"\n--- F150 calibration: populated vs FF-padded regions ---")
pop150, pad150 = analyze_cal_padding(f150_cal, "f150", F150_CAL_BASE)
print(f"Populated blocks: {len(pop150)}")
print(f"FF-padded blocks: {len(pad150)}")

if pop150:
    merged150 = []
    cs, ce = pop150[0][0], pop150[0][1]
    for s, e, _ in pop150[1:]:
        if s == ce:
            ce = e
        else:
            merged150.append((cs, ce))
            cs, ce = s, e
    merged150.append((cs, ce))
    print(f"\nPopulated regions in F150 cal:")
    for s, e in merged150:
        addr_s = F150_CAL_BASE + s
        addr_e = F150_CAL_BASE + e
        print(f"  0x{s:05X}-0x{e:05X} (addr 0x{addr_s:08X}-0x{addr_e:08X}) {e-s} bytes")

# ============================================================
# Compare overlapping content where both cals have data
print(f"\n--- Content comparison: F150 vs Transit cal (overlapping populated areas) ---")
# Both files same size?
min_len = min(len(f150_cal), len(transit_cal))
print(f"Comparing first {min_len} bytes")

# Find where both are non-FF
both_populated = 0
only_f150 = 0
only_transit = 0
both_ff = 0
for i in range(min_len):
    f_is_ff = f150_cal[i] == 0xFF
    t_is_ff = transit_cal[i] == 0xFF
    if not f_is_ff and not t_is_ff:
        both_populated += 1
    elif not f_is_ff:
        only_f150 += 1
    elif not t_is_ff:
        only_transit += 1
    else:
        both_ff += 1

print(f"Both populated (non-FF): {both_populated} bytes")
print(f"Only F150 populated:     {only_f150} bytes")
print(f"Only Transit populated:  {only_transit} bytes")
print(f"Both FF:                 {both_ff} bytes")

# Show the areas where F150 has data but Transit is FF (these are LKA params)
print(f"\n--- Areas where F150 has data but Transit is FF (potential LKA params) ---")
in_region = False
regions_f150_only = []
for i in range(min_len):
    f_pop = f150_cal[i] != 0xFF
    t_ff = transit_cal[i] == 0xFF
    if f_pop and t_ff:
        if not in_region:
            rstart = i
            in_region = True
    else:
        if in_region:
            regions_f150_only.append((rstart, i))
            in_region = False
if in_region:
    regions_f150_only.append((rstart, min_len))

# Merge with small gaps
merged_f150_only = []
if regions_f150_only:
    cs, ce = regions_f150_only[0]
    for s, e in regions_f150_only[1:]:
        if s - ce <= 8:
            ce = e
        else:
            merged_f150_only.append((cs, ce))
            cs, ce = s, e
    merged_f150_only.append((cs, ce))

print(f"Found {len(merged_f150_only)} regions with F150-only data:")
for s, e in merged_f150_only:
    size = e - s
    f150_addr = F150_CAL_BASE + s
    transit_addr = TRANSIT_CAL_BASE + s
    print(f"\n  Offset 0x{s:05X}-0x{e:05X} ({size} bytes)")
    print(f"  F150 addr: 0x{f150_addr:08X}  Transit addr: 0x{transit_addr:08X}")
    print(f"  F150 content:")
    print(hexdump(f150_cal[s:e], s, F150_CAL_BASE, max_lines=8))

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
