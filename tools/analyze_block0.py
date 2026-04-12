#!/usr/bin/env python3
"""
Block0 (Strategy) Binary Analyzer for Ford PSCM (EPS Steering)
Analyzes content types, data structures, calibration tables, code regions.
"""

import sys
import os
import struct
from collections import defaultdict, Counter

# Add tools dir to path for v850_disasm
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v850_disasm import V850Decoder, Instruction

# Paths
BASE = "C:/Users/Zorro/Desktop/fwproject"
AM_BIN = f"{BASE}/firmware/2025_Transit_PSCM/decompressed/AM/block0_strategy.bin"
AG_BIN = f"{BASE}/firmware/2025_Transit_PSCM/decompressed/AG/block0_strategy.bin"
CAL_BIN = f"{BASE}/firmware/2025_Transit_PSCM/decompressed/cal_AH.bin"
OUT_FILE = f"{BASE}/output/block0_analysis.txt"

BASE_ADDR = 0x01000000
CAL_BASE = 0x00FD0000
WINDOW = 256

# Known CAN IDs for PSCM
KNOWN_CAN_IDS = [0x082, 0x083, 0x091, 0x092, 0x0A5, 0x0B6, 0x0C8, 0x0D0,
                 0x130, 0x165, 0x167, 0x176, 0x211, 0x215, 0x3B3, 0x3CA,
                 0x3CB, 0x3CC, 0x3CD, 0x3D3, 0x3D7, 0x3E6, 0x3E7, 0x3F1,
                 0x414, 0x428, 0x430, 0x432, 0x44B, 0x466, 0x4B0]

# Valid MOVHI upper halves for address construction
VALID_MOVHI = {0x0100, 0x0101, 0x0102, 0x0103, 0x0104, 0x0105, 0x0106,
               0x0107, 0x0108, 0x0109, 0x010A, 0x010B, 0x010C, 0x010D,
               0x010E, 0x010F, 0x00FD, 0x4002, 0x20FF, 0xFEDF, 0xFFF8,
               0x0000, 0xFFFF}


def load_binary(path):
    with open(path, 'rb') as f:
        return f.read()


def classify_window(data, offset, size=WINDOW):
    """Classify a window of bytes."""
    chunk = data[offset:offset+size]
    if len(chunk) == 0:
        return "empty"

    n = len(chunk)
    ff_count = chunk.count(0xFF)
    zero_count = chunk.count(0x00)
    printable = sum(1 for b in chunk if 32 <= b < 127 or b in (9, 10, 13))

    if ff_count > n * 0.9:
        return "ff_padding"
    if zero_count > n * 0.9:
        return "zero_fill"
    if printable > n * 0.5:
        return "ascii_strings"

    # Check for float patterns
    float_count = 0
    for i in range(0, n - 3, 4):
        val = struct.unpack_from('>f', chunk, i)[0]
        raw = struct.unpack_from('>I', chunk, i)[0]
        if raw == 0:
            continue
        exp = (raw >> 23) & 0xFF
        if 0x01 <= exp <= 0xFE:  # valid float exponent
            if abs(val) > 1e-10 and abs(val) < 1e10:
                float_count += 1
    if float_count > n // 16:  # >25% of 4-byte slots are valid floats
        return "float_table"

    # Check for pointer tables
    ptr_count = 0
    for i in range(0, n - 3, 4):
        val = struct.unpack_from('>I', chunk, i)[0]
        # Check common address ranges
        if (0x01000000 <= val <= 0x010FFFFF or  # block0 strategy
            0x00FD0000 <= val <= 0x00FFFFFF or  # calibration
            0x40020000 <= val <= 0x4002FFFF or  # peripherals
            0x20FF0000 <= val <= 0x20FFFFFF or  # RAM
            0xFEDF0000 <= val <= 0xFEDFFFFF or  # peripheral
            0xFFF80000 <= val <= 0xFFF8FFFF):   # peripheral
            ptr_count += 1
    if ptr_count > n // 16:
        return "pointer_table"

    return "unknown_data"


def classify_window_code(data, offset, decoder, base_addr, size=WINDOW):
    """Try to classify as code by attempting V850 decode."""
    recognized = 0
    total = 0
    movhi_vals = set()
    pos = offset
    end = min(offset + size, len(data))

    while pos < end - 1:
        insn = decoder.decode(data, pos, base_addr)
        if insn and insn.mnemonic != ".dw":
            recognized += insn.size
            # Track MOVHI values
            if insn.mnemonic == "movhi":
                parts = insn.op_str.split(',')
                if len(parts) >= 1:
                    try:
                        v = int(parts[0].strip(), 0)
                        if v < 0:
                            v = v & 0xFFFF
                        movhi_vals.add(v)
                    except:
                        pass
            pos += insn.size
        else:
            pos += 2
        total += 1

    if total == 0:
        return False, set()

    ratio = recognized / (end - offset) if (end - offset) > 0 else 0
    # Check for valid MOVHI values to confirm it's real code
    has_valid_movhi = bool(movhi_vals & VALID_MOVHI)
    return ratio > 0.7 and (has_valid_movhi or ratio > 0.85), movhi_vals


def extract_strings(data, min_len=8):
    """Extract ASCII strings."""
    strings = []
    current = []
    start = None
    for i, b in enumerate(data):
        if 32 <= b < 127:
            if not current:
                start = i
            current.append(chr(b))
        else:
            if len(current) >= min_len:
                strings.append((start, ''.join(current)))
            current = []
            start = None
    if len(current) >= min_len:
        strings.append((start, ''.join(current)))
    return strings


def find_float_tables(data):
    """Find groups of consecutive IEEE 754 floats (big-endian)."""
    tables = []
    i = 0
    n = len(data)
    while i < n - 3:
        floats_here = []
        start = i
        while i < n - 3:
            raw = struct.unpack_from('>I', data, i)[0]
            if raw == 0:
                # Zero float is valid in a table
                floats_here.append((i, 0.0, raw))
                i += 4
                continue
            exp = (raw >> 23) & 0xFF
            if exp == 0 or exp == 0xFF:
                break
            val = struct.unpack_from('>f', data, i)[0]
            if abs(val) < 1e-15 or abs(val) > 1e15:
                break
            floats_here.append((i, val, raw))
            i += 4

        if len(floats_here) >= 4:
            tables.append((start, floats_here))

        i = max(i + 1, start + 4)  # advance past non-float

    return tables


def find_pointer_tables(data, base=BASE_ADDR):
    """Find tables of big-endian 32-bit pointers."""
    tables = []
    i = 0
    n = len(data)
    while i < n - 3:
        ptrs = []
        start = i
        while i < n - 3:
            val = struct.unpack_from('>I', data, i)[0]
            if (0x01000000 <= val <= 0x010FFFFF or
                0x00FD0000 <= val <= 0x00FFFFFF or
                0x40020000 <= val <= 0x4002FFFF or
                0x20FF0000 <= val <= 0x20FFFFFF or
                0xFEDF0000 <= val <= 0xFEDFFFFF):
                ptrs.append((i, val))
                i += 4
            else:
                break

        if len(ptrs) >= 3:
            tables.append((start, ptrs))

        i = max(i + 4, start + 4)

    return tables


def find_can_descriptors(data):
    """Find known CAN IDs in the binary and surrounding structure."""
    results = []
    for i in range(0, len(data) - 3, 2):
        # Try big-endian 16-bit
        val16 = struct.unpack_from('>H', data, i)[0]
        if val16 in KNOWN_CAN_IDS:
            # Get context: 16 bytes before and after
            ctx_start = max(0, i - 16)
            ctx_end = min(len(data), i + 18)
            ctx = data[ctx_start:ctx_end]
            results.append((i, val16, ctx, i - ctx_start))

        # Try big-endian 32-bit (CAN ID might be in a 32-bit field)
        if i < len(data) - 3:
            val32 = struct.unpack_from('>I', data, i)[0]
            if val32 in KNOWN_CAN_IDS and val32 != val16:
                ctx_start = max(0, i - 16)
                ctx_end = min(len(data), i + 20)
                ctx = data[ctx_start:ctx_end]
                results.append((i, val32, ctx, i - ctx_start))

    # Deduplicate by offset
    seen = set()
    unique = []
    for off, canid, ctx, rel in results:
        if off not in seen:
            seen.add(off)
            unique.append((off, canid, ctx, rel))
    return unique


def decode_did_table(data, offset_table, offset_descriptors):
    """Decode DID table structure starting at given offsets."""
    results = []

    # Read table entries
    i = offset_table
    entries = []
    while i < min(offset_table + 512, len(data) - 1):
        did = struct.unpack_from('>H', data, i)[0]
        if did == 0x0000 or did == 0xFFFF:
            break
        entries.append((i, did))
        i += 2

    # Read descriptors
    desc_entries = []
    i = offset_descriptors
    while i < min(offset_descriptors + 2048, len(data) - 7):
        raw = data[i:i+8]
        if all(b == 0xFF for b in raw) or all(b == 0 for b in raw):
            break
        desc_entries.append((i, raw))
        i += 8  # Try 8-byte descriptor stride

    return entries, desc_entries


def find_steering_floats(data):
    """Find float values that match typical steering parameters."""
    categories = {
        'torque_nm': [],      # 0.1-50.0 Nm
        'angle_deg': [],      # 1-900 degrees
        'speed_kph': [],      # 1-250 kph
        'gain': [],           # 0.001-10.0
        'time_sec': [],       # 0.001-30.0
        'current_amp': [],    # 0.1-100.0
    }

    for i in range(0, len(data) - 3, 4):
        raw = struct.unpack_from('>I', data, i)[0]
        exp = (raw >> 23) & 0xFF
        if exp == 0 or exp == 0xFF:
            continue
        val = struct.unpack_from('>f', data, i)[0]
        if val != val:  # NaN
            continue

        if 0.1 <= val <= 50.0:
            categories['torque_nm'].append((i, val))
        if 1.0 <= val <= 900.0:
            categories['angle_deg'].append((i, val))
        if 1.0 <= val <= 250.0:
            categories['speed_kph'].append((i, val))
        if 0.001 <= val <= 10.0:
            categories['gain'].append((i, val))
        if 0.001 <= val <= 30.0:
            categories['time_sec'].append((i, val))
        if 0.1 <= val <= 100.0:
            categories['current_amp'].append((i, val))

    return categories


def find_code_regions(data, decoder, base_addr, step=256):
    """Find code regions by scanning with V850 decoder."""
    regions = []
    n = len(data)
    in_code = False
    code_start = 0
    all_movhi = set()

    for w_start in range(0, n, step):
        is_code, movhi_vals = classify_window_code(data, w_start, decoder, base_addr, step)
        if is_code:
            if not in_code:
                code_start = w_start
                in_code = True
                all_movhi = set()
            all_movhi |= movhi_vals
        else:
            if in_code:
                regions.append((code_start, w_start, all_movhi))
                in_code = False
                all_movhi = set()

    if in_code:
        regions.append((code_start, n, all_movhi))

    return regions


def compare_binaries(am_data, ag_data):
    """Compare AM vs AG block0 and find diff regions."""
    diffs = []
    n = min(len(am_data), len(ag_data))
    in_diff = False
    diff_start = 0

    for i in range(n):
        if am_data[i] != ag_data[i]:
            if not in_diff:
                diff_start = i
                in_diff = True
        else:
            if in_diff:
                diffs.append((diff_start, i))
                in_diff = False

    if in_diff:
        diffs.append((diff_start, n))

    return diffs


def main():
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    out = open(OUT_FILE, 'w', encoding='utf-8')

    def pr(s=""):
        print(s)
        out.write(s + "\n")

    am_data = load_binary(AM_BIN)
    ag_data = load_binary(AG_BIN)
    cal_data = load_binary(CAL_BIN)
    decoder = V850Decoder()

    pr("=" * 100)
    pr("BLOCK0 STRATEGY BINARY ANALYSIS — Ford PSCM (EPS Steering)")
    pr(f"File: AM/block0_strategy.bin ({len(am_data)} bytes, base 0x{BASE_ADDR:08X})")
    pr("=" * 100)

    # =========================================================================
    # SECTION 1: Content Type Map
    # =========================================================================
    pr("\n" + "=" * 100)
    pr("SECTION 1: BINARY CONTENT TYPE MAP (256-byte windows)")
    pr("=" * 100)

    type_counts = Counter()
    region_types = []
    code_tested = set()

    # First pass: classify without code detection (fast)
    for w in range(0, len(am_data), WINDOW):
        t = classify_window(am_data, w)
        region_types.append((w, t))
        type_counts[t] += WINDOW

    # Second pass: check "unknown_data" regions for code
    pr("\n  [Running V850 code detection on unknown regions...]")
    code_regions_refined = []
    for idx, (w, t) in enumerate(region_types):
        if t == "unknown_data":
            is_code, movhi_vals = classify_window_code(am_data, w, decoder, BASE_ADDR)
            if is_code:
                region_types[idx] = (w, "code")
                type_counts["unknown_data"] -= WINDOW
                type_counts["code"] += WINDOW

    # Merge consecutive same-type regions
    merged = []
    prev_type = None
    prev_start = 0
    for w, t in region_types:
        if t != prev_type:
            if prev_type is not None:
                merged.append((prev_start, w, prev_type))
            prev_start = w
            prev_type = t
    if prev_type is not None:
        merged.append((prev_start, len(am_data), prev_type))

    pr("\n  Region Map:")
    pr(f"  {'Start':>10s} {'End':>10s} {'Size':>8s}  {'Type':<20s}")
    pr(f"  {'-'*10} {'-'*10} {'-'*8}  {'-'*20}")
    for start, end, rtype in merged:
        size = end - start
        pr(f"  0x{start+BASE_ADDR:08X} 0x{end+BASE_ADDR:08X} {size:7d}  {rtype}")

    pr(f"\n  Summary:")
    total = len(am_data)
    for t, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
        pr(f"    {t:<20s}: {cnt:8d} bytes ({100*cnt/total:5.1f}%)")

    # =========================================================================
    # SECTION 2a: ASCII Strings
    # =========================================================================
    pr("\n" + "=" * 100)
    pr("SECTION 2a: ASCII STRINGS (>8 chars)")
    pr("=" * 100)

    strings = extract_strings(am_data, 8)
    pr(f"\n  Found {len(strings)} strings\n")

    # Categorize
    autosar = []
    ford_parts = []
    error_codes = []
    function_names = []
    other_strings = []

    for off, s in strings:
        sl = s.lower()
        if any(x in sl for x in ['rte_', 'swc_', 'bsw_', 'com_', 'dem_', 'dcm_', 'os_', 'det_',
                                   'memmap', 'autosar', 'schm_']):
            autosar.append((off, s))
        elif any(x in s for x in ['JX7A', 'JX7T', 'LX6T', 'N1MH', 'K2GC', 'Ford', 'FORD']):
            ford_parts.append((off, s))
        elif any(x in sl for x in ['error', 'fault', 'fail', 'dtc', 'diag']):
            error_codes.append((off, s))
        elif '_' in s and any(c.isupper() for c in s):
            function_names.append((off, s))
        else:
            other_strings.append((off, s))

    if autosar:
        pr(f"  AUTOSAR-related ({len(autosar)}):")
        for off, s in autosar[:50]:
            pr(f"    0x{off:06X} (addr 0x{off+BASE_ADDR:08X}): {s}")
        if len(autosar) > 50:
            pr(f"    ... and {len(autosar)-50} more")

    if ford_parts:
        pr(f"\n  Ford part numbers / identifiers ({len(ford_parts)}):")
        for off, s in ford_parts[:30]:
            pr(f"    0x{off:06X} (addr 0x{off+BASE_ADDR:08X}): {s}")

    if error_codes:
        pr(f"\n  Error / fault / diagnostic strings ({len(error_codes)}):")
        for off, s in error_codes[:30]:
            pr(f"    0x{off:06X} (addr 0x{off+BASE_ADDR:08X}): {s}")

    if function_names:
        pr(f"\n  Function-like names ({len(function_names)}):")
        for off, s in function_names[:80]:
            pr(f"    0x{off:06X} (addr 0x{off+BASE_ADDR:08X}): {s}")
        if len(function_names) > 80:
            pr(f"    ... and {len(function_names)-80} more")

    if other_strings:
        pr(f"\n  Other strings ({len(other_strings)}):")
        for off, s in other_strings[:60]:
            pr(f"    0x{off:06X} (addr 0x{off+BASE_ADDR:08X}): {s}")
        if len(other_strings) > 60:
            pr(f"    ... and {len(other_strings)-60} more")

    # =========================================================================
    # SECTION 2b: Pointer Tables
    # =========================================================================
    pr("\n" + "=" * 100)
    pr("SECTION 2b: POINTER TABLES (BE 32-bit)")
    pr("=" * 100)

    ptr_tables = find_pointer_tables(am_data)
    pr(f"\n  Found {len(ptr_tables)} pointer tables\n")

    for start, ptrs in ptr_tables[:40]:
        targets = defaultdict(int)
        for _, val in ptrs:
            if 0x01000000 <= val <= 0x010FFFFF:
                targets['strategy'] += 1
            elif 0x00FD0000 <= val <= 0x00FFFFFF:
                targets['calibration'] += 1
            elif 0x40020000 <= val <= 0x4002FFFF:
                targets['peripheral'] += 1
            elif 0x20FF0000 <= val <= 0x20FFFFFF:
                targets['RAM'] += 1
            elif 0xFEDF0000 <= val <= 0xFEDFFFFF:
                targets['FEDF_periph'] += 1
            else:
                targets['other'] += 1
        tgt_str = ", ".join(f"{k}:{v}" for k, v in sorted(targets.items(), key=lambda x: -x[1]))
        pr(f"  Table at 0x{start:06X} (addr 0x{start+BASE_ADDR:08X}): {len(ptrs)} pointers -> [{tgt_str}]")
        for off, val in ptrs[:8]:
            pr(f"    0x{off:06X}: 0x{val:08X}")
        if len(ptrs) > 8:
            pr(f"    ... ({len(ptrs)-8} more)")
    if len(ptr_tables) > 40:
        pr(f"\n  ... and {len(ptr_tables)-40} more pointer tables")

    # =========================================================================
    # SECTION 2c: Float Tables
    # =========================================================================
    pr("\n" + "=" * 100)
    pr("SECTION 2c: FLOAT TABLES (IEEE 754 BE)")
    pr("=" * 100)

    float_tables = find_float_tables(am_data)
    pr(f"\n  Found {len(float_tables)} float tables\n")

    for start, floats in float_tables[:50]:
        vals = [f[1] for f in floats]
        pr(f"  Float table at 0x{start:06X} (addr 0x{start+BASE_ADDR:08X}): {len(floats)} values")
        # Try to categorize
        min_v = min(v for v in vals if v != 0) if any(v != 0 for v in vals) else 0
        max_v = max(vals)
        pr(f"    Range: {min_v:.6g} .. {max_v:.6g}")
        for off, val, raw in floats[:12]:
            pr(f"    0x{off:06X}: 0x{raw:08X} = {val:.6g}")
        if len(floats) > 12:
            pr(f"    ... ({len(floats)-12} more)")
    if len(float_tables) > 50:
        pr(f"\n  ... and {len(float_tables)-50} more float tables")

    # =========================================================================
    # SECTION 2d: CAN Message Descriptors
    # =========================================================================
    pr("\n" + "=" * 100)
    pr("SECTION 2d: CAN MESSAGE DESCRIPTORS")
    pr("=" * 100)

    can_hits = find_can_descriptors(am_data)
    pr(f"\n  Found {len(can_hits)} CAN ID references\n")

    # Group by CAN ID
    by_canid = defaultdict(list)
    for off, canid, ctx, rel in can_hits:
        by_canid[canid].append((off, ctx, rel))

    for canid in sorted(by_canid.keys()):
        hits = by_canid[canid]
        pr(f"  CAN ID 0x{canid:03X}: {len(hits)} references")
        for off, ctx, rel in hits[:5]:
            hex_ctx = ctx.hex()
            # Insert marker at the CAN ID position
            pr(f"    Offset 0x{off:06X} (addr 0x{off+BASE_ADDR:08X})")
            pr(f"      Context: {hex_ctx}")
            # Try to decode surrounding structure
            # Common: [flags(1) | DLC(1) | CAN_ID(2) | period(2) | ...]
            if off >= 2 and off + 6 < len(am_data):
                pre = am_data[off-2:off]
                post = am_data[off+2:off+8]
                pr(f"      Pre-bytes: {pre.hex()}, Post-bytes: {post.hex()}")
        if len(hits) > 5:
            pr(f"    ... ({len(hits)-5} more)")

    # =========================================================================
    # SECTION 2e: DID/As-Built Tables
    # =========================================================================
    pr("\n" + "=" * 100)
    pr("SECTION 2e: DID / AS-BUILT TABLES")
    pr("=" * 100)

    did_table_off = 0xDB74
    did_desc_off = 0xDC10

    pr(f"\n  DID Table at offset 0x{did_table_off:06X} (addr 0x{did_table_off+BASE_ADDR:08X})")

    # Decode DID entries
    entries, descs = decode_did_table(am_data, did_table_off, did_desc_off)

    pr(f"  Found {len(entries)} DID entries:")
    for off, did in entries:
        # Known DIDs
        known = {
            0x004C: "Part Number", 0x0202: "Strategy", 0x203D: "Calibration ID",
            0x205A: "Software Version", 0x205B: "Hardware Version",
            0x3003: "Vehicle Config", 0x301A: "As-Built Block 1",
            0x301F: "As-Built Block 2", 0x3020: "As-Built Block 3",
            0x330C: "EPAS Config", 0x3B4B: "Steering Torque",
            0xD100: "Routine Control", 0xD111: "Reset ECU",
            0xD117: "IOC", 0xD118: "IOC 2",
            0xDD00: "DTC Status", 0xDD01: "DTC Info",
            0xDD05: "DTC Snapshot", 0xDD06: "DTC Extended",
            0xDD09: "DTC Severity", 0xDE00: "Freeze Frame",
            0xDE01: "Snapshot Record", 0xDE02: "Snapshot Data",
            0xDE03: "Snapshot DID", 0xEE01: "ECU Serial",
            0xEE02: "VIN", 0xEE03: "Production Date",
            0xEE04: "ECU Mfg Date", 0xEE05: "Supplier ID",
            0xEE06: "Software Number", 0xEE20: "ECU ID",
        }
        name = known.get(did, "")
        pr(f"    0x{off:06X}: DID 0x{did:04X} {name}")

    # Dump raw descriptor bytes
    pr(f"\n  DID Descriptors at offset 0x{did_desc_off:06X} (addr 0x{did_desc_off+BASE_ADDR:08X})")
    # Try multiple strides to find the right structure
    pr("  Attempting stride detection...")

    # Dump raw hex for analysis
    raw_region = am_data[did_desc_off:did_desc_off+256]
    for i in range(0, min(256, len(raw_region)), 16):
        hex_str = raw_region[i:i+16].hex()
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw_region[i:i+16])
        pr(f"    0x{did_desc_off+i:06X}: {hex_str}  {ascii_str}")

    # Try to find repeating structure
    for stride in [4, 6, 8, 10, 12, 16]:
        # Check if there's a pattern with this stride
        pattern_ok = True
        count = 0
        for j in range(0, 128, stride):
            chunk = raw_region[j:j+stride]
            if len(chunk) < stride:
                break
            count += 1
        if count >= 4:
            pr(f"\n  Trying stride={stride}:")
            for j in range(0, min(128, len(raw_region)), stride):
                chunk = raw_region[j:j+stride]
                if len(chunk) < stride:
                    break
                pr(f"    [{j//stride:3d}] {chunk.hex()}")

    # =========================================================================
    # SECTION 3: Steering Calibration Data
    # =========================================================================
    pr("\n" + "=" * 100)
    pr("SECTION 3: STEERING CALIBRATION DATA (float analysis)")
    pr("=" * 100)

    steer_floats = find_steering_floats(am_data)

    # Find clusters of consecutive floats in each category
    for cat_name, cat_data in sorted(steer_floats.items()):
        if not cat_data:
            continue
        # Find clusters (consecutive offsets within 32 bytes)
        clusters = []
        if cat_data:
            cluster = [cat_data[0]]
            for i in range(1, len(cat_data)):
                if cat_data[i][0] - cat_data[i-1][0] <= 32:
                    cluster.append(cat_data[i])
                else:
                    if len(cluster) >= 4:
                        clusters.append(cluster)
                    cluster = [cat_data[i]]
            if len(cluster) >= 4:
                clusters.append(cluster)

        if clusters:
            pr(f"\n  {cat_name}: {len(clusters)} clusters of 4+ values")
            for ci, cl in enumerate(clusters[:15]):
                vals = [v for _, v in cl]
                pr(f"    Cluster at 0x{cl[0][0]:06X}-0x{cl[-1][0]:06X} "
                   f"(addr 0x{cl[0][0]+BASE_ADDR:08X}): {len(cl)} values, "
                   f"range {min(vals):.4g}..{max(vals):.4g}")
                for off, val in cl[:10]:
                    pr(f"      0x{off:06X}: {val:.6g}")
                if len(cl) > 10:
                    pr(f"      ... ({len(cl)-10} more)")
            if len(clusters) > 15:
                pr(f"    ... and {len(clusters)-15} more clusters")

    # Compare with calibration binary
    pr("\n  --- Comparison with calibration binary (cal_AH.bin) ---")
    cal_floats_tables = find_float_tables(cal_data)
    pr(f"  Calibration binary has {len(cal_floats_tables)} float tables ({len(cal_data)} bytes)")
    if cal_floats_tables:
        pr("  First 10 calibration float tables:")
        for start, floats in cal_floats_tables[:10]:
            vals = [f[1] for f in floats]
            min_v = min(v for v in vals if v != 0) if any(v != 0 for v in vals) else 0
            max_v = max(vals)
            pr(f"    0x{start:06X} (addr 0x{start+CAL_BASE:08X}): {len(floats)} values, "
               f"range {min_v:.4g}..{max_v:.4g}")

    # Check for pointers from block0 -> calibration
    pr("\n  Pointers from block0 to calibration:")
    cal_ptr_count = 0
    cal_ptr_offsets = []
    for i in range(0, len(am_data) - 3, 4):
        val = struct.unpack_from('>I', am_data, i)[0]
        if 0x00FD0000 <= val <= 0x00FFFFFF:
            cal_ptr_count += 1
            cal_ptr_offsets.append((i, val))
    pr(f"  Found {cal_ptr_count} pointers to calibration range (0x00FD0000-0x00FFFFFF)")
    for off, val in cal_ptr_offsets[:20]:
        pr(f"    0x{off:06X} (addr 0x{off+BASE_ADDR:08X}) -> 0x{val:08X}")
    if len(cal_ptr_offsets) > 20:
        pr(f"    ... and {len(cal_ptr_offsets)-20} more")

    # =========================================================================
    # SECTION 4: Code Regions
    # =========================================================================
    pr("\n" + "=" * 100)
    pr("SECTION 4: CODE REGIONS (V850 instruction analysis)")
    pr("=" * 100)

    # Use merged region_types for code detection
    code_merged = [(s, e, t) for s, e, t in merged if t == "code"]
    total_code = sum(e - s for s, e, _ in code_merged)

    pr(f"\n  Found {len(code_merged)} code regions, total {total_code} bytes ({100*total_code/total:.1f}%)\n")

    for start, end, _ in code_merged:
        size = end - start
        # Get MOVHI values in this region
        _, movhi_vals = classify_window_code(am_data, start, decoder, BASE_ADDR, min(size, 4096))
        movhi_str = ", ".join(f"0x{v:04X}" for v in sorted(movhi_vals)) if movhi_vals else "none"
        pr(f"  0x{start:06X}-0x{end:06X} (addr 0x{start+BASE_ADDR:08X}-0x{end+BASE_ADDR:08X}): "
           f"{size:6d} bytes  MOVHI: [{movhi_str}]")

    # =========================================================================
    # SECTION 5: AG vs AM Comparison
    # =========================================================================
    pr("\n" + "=" * 100)
    pr("SECTION 5: AG vs AM BLOCK0 COMPARISON")
    pr("=" * 100)

    diffs = compare_binaries(am_data, ag_data)
    total_diff_bytes = sum(e - s for s, e in diffs)
    pr(f"\n  {len(diffs)} diff regions, {total_diff_bytes} bytes changed total\n")

    for start, end in diffs:
        size = end - start
        region_addr = start + BASE_ADDR

        # Determine what type of data changed
        region_type = "unknown"
        for rs, re, rt in merged:
            if start >= rs and start < re:
                region_type = rt
                break

        pr(f"  Diff at 0x{start:06X}-0x{end:06X} (addr 0x{region_addr:08X}): {size} bytes [{region_type}]")

        if size <= 128:
            # Show old vs new for small diffs
            ag_chunk = ag_data[start:end]
            am_chunk = am_data[start:end]

            # Try float interpretation
            if size >= 4 and size % 4 == 0:
                has_floats = False
                for j in range(0, size, 4):
                    ag_raw = struct.unpack_from('>I', ag_chunk, j)[0]
                    am_raw = struct.unpack_from('>I', am_chunk, j)[0]
                    ag_exp = (ag_raw >> 23) & 0xFF
                    am_exp = (am_raw >> 23) & 0xFF
                    if (0x01 <= ag_exp <= 0xFE) and (0x01 <= am_exp <= 0xFE):
                        ag_f = struct.unpack_from('>f', ag_chunk, j)[0]
                        am_f = struct.unpack_from('>f', am_chunk, j)[0]
                        if abs(ag_f) < 1e10 and abs(am_f) < 1e10:
                            pr(f"    0x{start+j:06X}: AG={ag_f:.6g} -> AM={am_f:.6g}")
                            has_floats = True
                if has_floats:
                    continue

            # Try pointer interpretation
            if size >= 4 and size % 4 == 0:
                has_ptrs = False
                for j in range(0, size, 4):
                    ag_val = struct.unpack_from('>I', ag_chunk, j)[0]
                    am_val = struct.unpack_from('>I', am_chunk, j)[0]
                    if ((0x01000000 <= ag_val <= 0x010FFFFF or
                         0x00FD0000 <= ag_val <= 0x00FFFFFF) and
                        (0x01000000 <= am_val <= 0x010FFFFF or
                         0x00FD0000 <= am_val <= 0x00FFFFFF)):
                        pr(f"    0x{start+j:06X}: AG=0x{ag_val:08X} -> AM=0x{am_val:08X}")
                        has_ptrs = True
                if has_ptrs:
                    continue

            # Raw hex
            for j in range(0, size, 16):
                ag_hex = ag_chunk[j:j+16].hex()
                am_hex = am_chunk[j:j+16].hex()
                if ag_hex != am_hex:
                    pr(f"    0x{start+j:06X}: AG={ag_hex}")
                    pr(f"    {'':>10s}  AM={am_hex}")
        else:
            # Large diff - summarize
            ag_chunk = ag_data[start:end]
            am_chunk = am_data[start:end]

            # Check for float table changes
            float_changes = 0
            for j in range(0, min(size, 512) - 3, 4):
                ag_raw = struct.unpack_from('>I', ag_chunk, j)[0]
                am_raw = struct.unpack_from('>I', am_chunk, j)[0]
                if ag_raw != am_raw:
                    ag_exp = (ag_raw >> 23) & 0xFF
                    am_exp = (am_raw >> 23) & 0xFF
                    if (0x01 <= ag_exp <= 0xFE) and (0x01 <= am_exp <= 0xFE):
                        float_changes += 1

            if float_changes > 0:
                pr(f"    Contains ~{float_changes} float value changes (first 512 bytes checked)")
                # Show first few
                shown = 0
                for j in range(0, min(size, 512) - 3, 4):
                    ag_raw = struct.unpack_from('>I', ag_chunk, j)[0]
                    am_raw = struct.unpack_from('>I', am_chunk, j)[0]
                    if ag_raw != am_raw:
                        ag_exp = (ag_raw >> 23) & 0xFF
                        am_exp = (am_raw >> 23) & 0xFF
                        if (0x01 <= ag_exp <= 0xFE) and (0x01 <= am_exp <= 0xFE):
                            ag_f = struct.unpack_from('>f', ag_chunk, j)[0]
                            am_f = struct.unpack_from('>f', am_chunk, j)[0]
                            if abs(ag_f) < 1e10 and abs(am_f) < 1e10:
                                pr(f"      0x{start+j:06X}: AG={ag_f:.6g} -> AM={am_f:.6g}")
                                shown += 1
                                if shown >= 10:
                                    pr(f"      ... ({float_changes - shown} more float changes)")
                                    break

            # Show first bytes of raw diff
            pr(f"    First 32 bytes: AG={ag_chunk[:32].hex()}")
            pr(f"    {'':>16s}  AM={am_chunk[:32].hex()}")

    pr("\n" + "=" * 100)
    pr("END OF ANALYSIS")
    pr("=" * 100)

    out.close()
    print(f"\nOutput written to {OUT_FILE}")


if __name__ == "__main__":
    main()
