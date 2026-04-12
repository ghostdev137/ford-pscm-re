#!/usr/bin/env python3
"""Scan firmware binaries for V850 function prologues."""
import struct
import os

BINS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bins')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')

blocks = [
    ('transit_calibration_AH.bin', 0x00FD0000, 'calibration'),
    ('transit_strategy_AM.bin',    0x01000000, 'strategy'),
    ('transit_block2_ext.bin',     0x20FF0000, 'EPS_code'),
]

all_prologues = []

for fname, base, region in blocks:
    path = os.path.join(BINS_DIR, fname)
    if not os.path.exists(path):
        continue
    data = open(path, 'rb').read()
    count = 0

    for i in range(0, len(data) - 4, 2):
        hw = struct.unpack_from('<H', data, i)[0]

        # PREPARE instruction (common function entry, saves registers)
        if (hw & 0x07E0) == 0x0780:
            all_prologues.append((base + i, region))
            count += 1
            continue

        # ADDI negative_imm, rX, SP (stack frame allocation)
        opcode6 = (hw >> 5) & 0x3F
        reg2 = (hw >> 11) & 0x1F
        if opcode6 == 0x30 and reg2 == 3:  # ADDI to SP
            if i + 2 < len(data):
                imm16 = struct.unpack_from('<h', data, i + 2)[0]
                if imm16 < 0 and imm16 > -1024:
                    all_prologues.append((base + i, region))
                    count += 1

    print(f"{region}: {count} prologues in {len(data):,} bytes")

print(f"\nTotal: {len(all_prologues)} potential function prologues")

os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(os.path.join(OUTPUT_DIR, 'prologue_entries.txt'), 'w') as f:
    f.write(f"# Function prologues found by binary scan\n")
    f.write(f"# Total: {len(all_prologues)}\n\n")
    for addr, region in sorted(all_prologues):
        f.write(f"{addr:#010x} {region}\n")

print(f"Wrote {os.path.join(OUTPUT_DIR, 'prologue_entries.txt')}")
