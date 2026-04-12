#!/usr/bin/env python3
"""
binary_scan.py - Ford PSCM V850E2 firmware binary analysis
Searches for as-built validation addresses, MOVHI/MOVEA pairs,
AG vs AM differences, and DID DE01 handling.
"""

import struct
import os
import sys
from collections import defaultdict

BINS = r"C:\Users\Zorro\Desktop\fwproject\bins"
AM_PATH = os.path.join(BINS, "transit_strategy_AM.bin")
AG_PATH = os.path.join(BINS, "transit_strategy_AG.bin")
BASE_ADDR = 0x01000000

def load(path):
    with open(path, "rb") as f:
        return f.read()

def hex_context(data, offset, width=16):
    """Return hex dump around offset."""
    start = max(0, offset - width)
    end = min(len(data), offset + width)
    chunk = data[start:end]
    hex_str = " ".join(f"{b:02X}" for b in chunk)
    marker_pos = offset - start
    return f"  file[0x{start:06X}..0x{end:06X}]: {hex_str}"

def sign_extend(val, bits):
    if val & (1 << (bits - 1)):
        val -= (1 << bits)
    return val

# ============================================================
print("=" * 80)
print("APPROACH 1: Raw address byte search (BE data)")
print("=" * 80)

am = load(AM_PATH)

# Addresses to search as big-endian 4-byte patterns
addr_patterns = {
    "Cal 00FD21A8": bytes.fromhex("00FD21A8"),
    "Cal 00FD2860": bytes.fromhex("00FD2860"),
    "Cal 00FD327C": bytes.fromhex("00FD327C"),
    "Cal 00FD3280": bytes.fromhex("00FD3280"),
    "Cfg 010E1140": bytes.fromhex("010E1140"),
    "Cfg 010E1179": bytes.fromhex("010E1179"),
    "Cfg 010E1180": bytes.fromhex("010E1180"),
    "RAM 40022330": bytes.fromhex("40022330"),
    "RAM 40022340": bytes.fromhex("40022340"),
}

# Also search LE versions of the same addresses
addr_patterns_le = {}
for name, be_bytes in list(addr_patterns.items()):
    val = int.from_bytes(be_bytes, 'big')
    le_bytes = val.to_bytes(4, 'little')
    addr_patterns_le[name + " (LE)"] = le_bytes

all_addr_patterns = {**addr_patterns, **addr_patterns_le}

for name, pat in sorted(all_addr_patterns.items()):
    matches = []
    idx = 0
    while True:
        idx = am.find(pat, idx)
        if idx == -1:
            break
        matches.append(idx)
        idx += 1
    if matches:
        print(f"\n{name} ({pat.hex().upper()}): {len(matches)} match(es)")
        for m in matches[:20]:
            addr = BASE_ADDR + m
            print(f"  offset 0x{m:06X} (addr 0x{addr:08X})")
            print(hex_context(am, m, 24))
    else:
        print(f"\n{name} ({pat.hex().upper()}): no matches")

# 16-bit DID patterns
print("\n--- 16-bit DID patterns ---")
did_patterns = {
    "DE00 (BE)": bytes([0xDE, 0x00]),
    "DE01 (BE)": bytes([0xDE, 0x01]),
    "DE02 (BE)": bytes([0xDE, 0x02]),
    "DE00 (LE)": bytes([0x00, 0xDE]),
    "DE01 (LE)": bytes([0x01, 0xDE]),
    "DE02 (LE)": bytes([0x02, 0xDE]),
}

for name, pat in sorted(did_patterns.items()):
    matches = []
    idx = 0
    while True:
        idx = am.find(pat, idx)
        if idx == -1:
            break
        matches.append(idx)
        idx += 1
    if matches:
        print(f"\n{name} ({pat.hex().upper()}): {len(matches)} match(es)")
        for m in matches[:30]:
            addr = BASE_ADDR + m
            print(f"  offset 0x{m:06X} (addr 0x{addr:08X})")
            print(hex_context(am, m, 20))
    else:
        print(f"\n{name} ({pat.hex().upper()}): no matches")


# ============================================================
print("\n" + "=" * 80)
print("APPROACH 2: MOVHI+MOVEA scan in code regions")
print("=" * 80)

# First, find PREPARE instructions to identify code regions
prepare_offsets = []
for off in range(0, len(am) - 4, 2):
    hw0 = struct.unpack_from('<H', am, off)[0]
    if (hw0 & 0xFFE0) == 0x0780:
        prepare_offsets.append(off)

print(f"\nFound {len(prepare_offsets)} PREPARE instructions")
if prepare_offsets:
    print(f"First 10: {[f'0x{o:06X}' for o in prepare_offsets[:10]]}")
    print(f"Last 10:  {[f'0x{o:06X}' for o in prepare_offsets[-10:]]}")

# Build a set of "code regions" - 256-byte windows around each PREPARE
code_offsets = set()
for p in prepare_offsets:
    for o in range(max(0, p - 128), min(len(am), p + 512)):
        code_offsets.add(o)

# Key MOVHI imm16 values we care about
target_hi_values = {
    0x00FD: "calibration (0x00FDxxxx)",
    0x00FE: "calibration (0x00FExxxx)",
    0x0100: "strategy base (0x0100xxxx)",
    0x0101: "strategy (0x0101xxxx)",
    0x010E: "zeroed region (0x010Exxxx)",
    0x4002: "RAM (0x4002xxxx)",
    0x4003: "RAM (0x4003xxxx)",
}

# Scan for MOVHI (32-bit instruction)
# V850E2 MOVHI: bits[15:11]=reg2, bits[10:5]=opcode6=0x32(110010), bits[4:0]=reg1
# hw1 = imm16
# DISPOSE also has opcode6=0x32 but reg2=0

movhi_results = defaultdict(list)

for off in range(0, len(am) - 4, 2):
    hw0 = struct.unpack_from('<H', am, off)[0]
    opcode6 = (hw0 >> 5) & 0x3F
    if opcode6 != 0x32:
        continue
    reg2 = (hw0 >> 11) & 0x1F
    if reg2 == 0:
        continue  # DISPOSE
    reg1 = hw0 & 0x1F
    hw1 = struct.unpack_from('<H', am, off + 2)[0]
    imm16 = hw1

    if imm16 in target_hi_values:
        in_code = off in code_offsets
        addr_hi = imm16 << 16
        # Look for following MOVEA
        movea_info = None
        for delta in [4, 6, 8, 10, 12]:
            if off + delta + 4 > len(am):
                break
            nhw0 = struct.unpack_from('<H', am, off + delta)[0]
            nop6 = (nhw0 >> 5) & 0x3F
            nreg1 = nhw0 & 0x1F
            nreg2 = (nhw0 >> 11) & 0x1F
            if nop6 == 0x31 and nreg1 == reg2:  # MOVEA using same reg
                nhw1 = struct.unpack_from('<H', am, off + delta + 2)[0]
                imm16_lo = sign_extend(nhw1, 16)
                full_addr = (addr_hi + imm16_lo) & 0xFFFFFFFF
                movea_info = (off + delta, full_addr, nreg2)
                break
            # Also check for LD.W, ST.W, etc with displacement from reg2
            if nop6 in (0x38, 0x39, 0x3A, 0x3B) and nreg1 == reg2:
                nhw1 = struct.unpack_from('<H', am, off + delta + 2)[0]
                imm16_lo = sign_extend(nhw1, 16)
                full_addr = (addr_hi + imm16_lo) & 0xFFFFFFFF
                movea_info = (off + delta, full_addr, nreg2)
                break

        entry = {
            "offset": off,
            "addr": BASE_ADDR + off,
            "reg1": reg1,
            "reg2": reg2,
            "imm16": imm16,
            "in_code_region": in_code,
            "movea": movea_info,
        }
        movhi_results[imm16].append(entry)

for hi_val in sorted(movhi_results.keys()):
    entries = movhi_results[hi_val]
    desc = target_hi_values.get(hi_val, "")
    print(f"\nMOVHI imm16=0x{hi_val:04X} ({desc}): {len(entries)} occurrences")

    # Show all, but highlight code-region ones
    code_entries = [e for e in entries if e["in_code_region"]]
    data_entries = [e for e in entries if not e["in_code_region"]]

    print(f"  In code regions: {len(code_entries)}, In data regions: {len(data_entries)}")

    for e in entries[:50]:
        tag = "CODE" if e["in_code_region"] else "DATA"
        line = f"  [{tag}] 0x{e['offset']:06X} (0x{e['addr']:08X}): MOVHI 0x{e['imm16']:04X}, r{e['reg1']}, r{e['reg2']}"
        if e["movea"]:
            moff, maddr, mreg = e["movea"]
            line += f"  -> full_addr=0x{maddr:08X} (next_instr@0x{moff:06X})"
        print(line)

# ============================================================
print("\n" + "=" * 80)
print("APPROACH 2b: Specifically find references to key addresses via MOVHI+MOVEA")
print("=" * 80)

# Collect all resolved full addresses from MOVHI+MOVEA
key_addresses = [
    0x00FD21A8, 0x00FD2860, 0x00FD327C, 0x00FD3280,
    0x010E1140, 0x010E1179, 0x010E1180,
    0x40022330, 0x40022340,
]

# Build all MOVHI+MOVEA resolved addresses
all_resolved = []
for hi_val, entries in movhi_results.items():
    for e in entries:
        if e["movea"]:
            moff, maddr, mreg = e["movea"]
            all_resolved.append((e["offset"], maddr, e))

# Check which resolved addresses are close to our targets
print("\nResolved addresses near key targets:")
for target in key_addresses:
    nearby = [(off, addr, e) for off, addr, e in all_resolved if abs(addr - target) < 256]
    if nearby:
        print(f"\n  Target 0x{target:08X}:")
        for off, addr, e in nearby:
            tag = "CODE" if e["in_code_region"] else "DATA"
            print(f"    [{tag}] MOVHI@0x{off:06X} -> 0x{addr:08X} (delta={addr-target:+d})")


# ============================================================
print("\n" + "=" * 80)
print("APPROACH 3: AG vs AM comparison")
print("=" * 80)

ag = load(AG_PATH)

if len(ag) != len(am):
    print(f"WARNING: size mismatch AG={len(ag)} AM={len(am)}")
else:
    # Find all differing regions
    diff_regions = []
    i = 0
    while i < len(ag):
        if ag[i] != am[i]:
            start = i
            while i < len(ag) and ag[i] != am[i]:
                i += 1
            diff_regions.append((start, i))
        else:
            i += 1

    print(f"\nTotal differing regions: {len(diff_regions)}")
    print(f"Total differing bytes: {sum(e-s for s,e in diff_regions)}")

    for start, end in diff_regions:
        length = end - start
        addr_start = BASE_ADDR + start
        addr_end = BASE_ADDR + end
        # Check if AM region is all zeros
        am_all_zero = all(b == 0 for b in am[start:end])
        ag_all_zero = all(b == 0 for b in ag[start:end])
        tag = ""
        if am_all_zero:
            tag = " [AM=ALL ZEROS]"
        elif ag_all_zero:
            tag = " [AG=ALL ZEROS]"

        print(f"\n  Region 0x{start:06X}-0x{end:06X} (addr 0x{addr_start:08X}-0x{addr_end:08X}), {length} bytes{tag}")

        if length <= 64:
            print(f"    AG: {ag[start:end].hex(' ').upper()}")
            print(f"    AM: {am[start:end].hex(' ').upper()}")
        else:
            print(f"    AG first 32: {ag[start:start+32].hex(' ').upper()}")
            print(f"    AG last 32:  {ag[end-32:end].hex(' ').upper()}")
            print(f"    AM first 32: {am[start:start+32].hex(' ').upper()}")
            print(f"    AM last 32:  {am[end-32:end].hex(' ').upper()}")

    # Specifically analyze the zeroed-out region 0xE0000-0xE1120
    print("\n--- Detailed analysis of AG data in 0xE0000-0xE1200 ---")
    region_start = 0xE0000
    region_end = 0xE1200
    ag_region = ag[region_start:region_end]
    am_region = am[region_start:region_end]

    # Show non-zero content from AG in this region
    print(f"\nAG non-zero ranges in 0x{region_start:06X}-0x{region_end:06X}:")
    i = 0
    while i < len(ag_region):
        if ag_region[i] != 0:
            start_nz = i
            while i < len(ag_region) and ag_region[i] != 0:
                i += 1
            end_nz = i
            length_nz = end_nz - start_nz
            off = region_start + start_nz
            addr = BASE_ADDR + off
            if length_nz <= 48:
                print(f"  0x{off:06X} (0x{addr:08X}), {length_nz}b: {ag_region[start_nz:end_nz].hex(' ').upper()}")
            else:
                print(f"  0x{off:06X} (0x{addr:08X}), {length_nz}b: {ag_region[start_nz:start_nz+32].hex(' ').upper()} ...")
        else:
            i += 1

    # Try to interpret the AG region as potential data structures
    print(f"\nAG region 0xE0000 interpreted as 32-bit BE words:")
    for i in range(0, min(256, len(ag_region)), 4):
        val_be = struct.unpack_from('>I', ag_region, i)[0]
        val_le = struct.unpack_from('<I', ag_region, i)[0]
        if val_be != 0:
            off = region_start + i
            print(f"  0x{off:06X}: BE=0x{val_be:08X}  LE=0x{val_le:08X}")


# ============================================================
print("\n" + "=" * 80)
print("APPROACH 4: DID DE01 handling - comprehensive search")
print("=" * 80)

# Search for 0xDE01 in various encodings
patterns_de01 = {
    "DE01 (raw BE 16)": b'\xDE\x01',
    "01DE (raw LE 16)": b'\x01\xDE',
    "0000DE01 (BE 32)": b'\x00\x00\xDE\x01',
    "01DE0000 (LE 32)": b'\x01\xDE\x00\x00',
}

for name, pat in patterns_de01.items():
    matches = []
    idx = 0
    while True:
        idx = am.find(pat, idx)
        if idx == -1:
            break
        matches.append(idx)
        idx += 1
    print(f"\n{name}: {len(matches)} matches")
    for m in matches[:30]:
        addr = BASE_ADDR + m
        in_code = m in code_offsets
        tag = "CODE" if in_code else "DATA"
        # Show wider context
        ctx_start = max(0, m - 8)
        ctx_end = min(len(am), m + len(pat) + 16)
        ctx = am[ctx_start:ctx_end]
        print(f"  [{tag}] 0x{m:06X} (0x{addr:08X}): {ctx.hex(' ').upper()}")


# ============================================================
print("\n" + "=" * 80)
print("APPROACH 5: Search for 730-02 as-built byte patterns")
print("=" * 80)

# The as-built block 730-02 contains LKA config
# Search for 0x0730 and 0x7302 patterns
for name, pat in [
    ("0730 BE", b'\x07\x30'),
    ("3007 LE", b'\x30\x07'),
    ("F730 (DID?)", b'\xF7\x30'),
]:
    matches = []
    idx = 0
    while True:
        idx = am.find(pat, idx)
        if idx == -1:
            break
        matches.append(idx)
        idx += 1
    if matches and len(matches) < 50:
        print(f"\n{name}: {len(matches)} matches")
        for m in matches[:20]:
            addr = BASE_ADDR + m
            ctx_start = max(0, m - 4)
            ctx_end = min(len(am), m + 12)
            ctx = am[ctx_start:ctx_end]
            in_code = m in code_offsets
            tag = "CODE" if in_code else "DATA"
            print(f"  [{tag}] 0x{m:06X} (0x{addr:08X}): {ctx.hex(' ').upper()}")
    else:
        print(f"\n{name}: {len(matches)} matches (too many or none)")


# ============================================================
print("\n" + "=" * 80)
print("SUMMARY: Key findings for LKA reset investigation")
print("=" * 80)

# Report MOVHI+MOVEA pairs that resolve to addresses in the zeroed region
print("\nCode references to zeroed region (0x010E0000-0x010E2000):")
for hi_val, entries in movhi_results.items():
    for e in entries:
        if e["movea"]:
            moff, maddr, mreg = e["movea"]
            if 0x010E0000 <= maddr < 0x010E2000:
                tag = "CODE" if e["in_code_region"] else "DATA"
                print(f"  [{tag}] MOVHI@0x{e['offset']:06X} -> 0x{maddr:08X}")

# Report code references to calibration area
print("\nCode references to calibration area (0x00FD0000-0x00FF0000):")
for hi_val, entries in movhi_results.items():
    for e in entries:
        if e["movea"]:
            moff, maddr, mreg = e["movea"]
            if 0x00FD0000 <= maddr < 0x00FF0000:
                tag = "CODE" if e["in_code_region"] else "DATA"
                print(f"  [{tag}] MOVHI@0x{e['offset']:06X} -> 0x{maddr:08X}")

# Report code references to RAM area
print("\nCode references to RAM area (0x40020000-0x40030000):")
for hi_val, entries in movhi_results.items():
    for e in entries:
        if e["movea"]:
            moff, maddr, mreg = e["movea"]
            if 0x40020000 <= maddr < 0x40030000:
                tag = "CODE" if e["in_code_region"] else "DATA"
                print(f"  [{tag}] MOVHI@0x{e['offset']:06X} -> 0x{maddr:08X}")

print("\nDone.")
