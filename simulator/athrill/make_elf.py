#!/usr/bin/env python3
"""
Create a minimal ELF32 (little-endian, V850) from raw firmware binary blocks.

Athrill2 loads ELF files natively. This script wraps our decompressed Ford PSCM
firmware blocks into a valid ELF32 so Athrill can load them without modification.

Usage:
    python make_elf.py <fw_dir> <output.elf>

Where fw_dir contains: block0_strategy.bin, block1_ram.bin, block2_ext.bin
And parent directory contains: cal_*.bin, sbl_*.bin
"""

import struct
import sys
import os

# V850 ELF constants
ET_EXEC = 2
EM_V850 = 87  # V850 architecture
EM_V800 = 36  # V800 — what Athrill2 actually expects
EV_CURRENT = 1
ELFCLASS32 = 1
ELFDATA2LSB = 1  # Little-endian
PT_LOAD = 1
PF_R = 4
PF_W = 2
PF_X = 1

# Ford PSCM memory map
BLOCKS = {
    "sbl":      (0x00000000, "sbl"),
    "cal":      (0x00FD0000, "cal"),
    "strategy": (0x01000000, "block0_strategy.bin"),
    "block1":   (0x10000400, "block1_ram.bin"),
    "block2":   (0x20FF0000, "block2_ext.bin"),
}


def find_file(fw_dir, name):
    """Find a firmware file by name or prefix."""
    # Direct match in fw_dir
    path = os.path.join(fw_dir, name)
    if os.path.exists(path):
        return path

    # Search parent for cal_*.bin or sbl_*.bin
    parent = os.path.dirname(fw_dir)
    for d in [fw_dir, parent]:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if name == "cal" and f.startswith("cal_") and f.endswith(".bin"):
                return os.path.join(d, f)
            if name == "sbl" and (f.startswith("sbl") or f.startswith("transit_sbl")) and f.endswith(".bin"):
                return os.path.join(d, f)
    return None


def make_elf(segments, entry_point, output_path):
    """
    Build a minimal ELF32 with LOAD segments.

    segments: list of (vaddr, data_bytes)
    """
    # ELF header: 52 bytes
    # Program headers: 32 bytes each
    ehdr_size = 52
    phdr_size = 32
    num_phdrs = len(segments)

    # Data starts after all headers
    data_offset = ehdr_size + (phdr_size * num_phdrs)
    # Align to 16 bytes
    data_offset = (data_offset + 15) & ~15

    # Build program headers and collect data
    phdrs = []
    file_offset = data_offset

    # Cal + block1 (RAM-image) are data-only; strategy + block2 are code.
    # Marking cal as non-executable stops Ghidra/BN from treating ccrh-prologue
    # byte patterns in cal data as phantom functions, while leaving xrefs from
    # strategy into cal addresses fully resolvable.
    CODE_SEGMENTS = {0x01000000, 0x20FF0000, 0x00000000}  # strategy, block2, sbl
    for vaddr, data in segments:
        filesz = len(data)
        memsz = filesz
        # Align file offset to 4 bytes
        padding = (4 - (file_offset % 4)) % 4
        file_offset += padding

        if vaddr in CODE_SEGMENTS:
            p_flags = PF_R | PF_X       # code: read+execute, no write
        else:
            p_flags = PF_R | PF_W       # data (cal, block1 RAM image)

        phdrs.append(struct.pack('<IIIIIIII',
            PT_LOAD,        # p_type
            file_offset,    # p_offset
            vaddr,          # p_vaddr
            vaddr,          # p_paddr
            filesz,         # p_filesz
            memsz,          # p_memsz
            p_flags,
            4,              # p_align
        ))
        file_offset += filesz

    # ELF header
    e_ident = bytes([
        0x7f, ord('E'), ord('L'), ord('F'),  # magic
        ELFCLASS32,     # 32-bit
        ELFDATA2LSB,    # little-endian
        EV_CURRENT,     # version
        0,              # OS/ABI
        0, 0, 0, 0, 0, 0, 0, 0  # padding
    ])

    ehdr = e_ident + struct.pack('<HHIIIIIHHHHHH',
        ET_EXEC,        # e_type
        EM_V800,        # e_machine (Athrill expects V800, not V850)
        EV_CURRENT,     # e_version
        entry_point,    # e_entry
        ehdr_size,      # e_phoff (program headers right after ehdr)
        0,              # e_shoff (no section headers)
        0,              # e_flags
        ehdr_size,      # e_ehsize
        phdr_size,      # e_phentsize
        num_phdrs,      # e_phnum
        0,              # e_shentsize
        0,              # e_shnum
        0,              # e_shstrndx
    )

    # Write the ELF
    with open(output_path, 'wb') as f:
        # ELF header
        f.write(ehdr)
        # Program headers
        for ph in phdrs:
            f.write(ph)

        # Pad to data_offset
        current = f.tell()
        if current < data_offset:
            f.write(b'\x00' * (data_offset - current))

        # Write segment data
        file_offset = data_offset
        for vaddr, data in segments:
            padding = (4 - (file_offset % 4)) % 4
            f.write(b'\x00' * padding)
            file_offset += padding
            f.write(data)
            file_offset += len(data)

    return file_offset  # total size


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <fw_dir> <output.elf>")
        sys.exit(1)

    fw_dir = sys.argv[1]
    output = sys.argv[2]

    segments = []

    for name, (addr, filename) in sorted(BLOCKS.items(), key=lambda x: x[1][0]):
        path = find_file(fw_dir, filename)
        if path is None:
            print(f"  SKIP: {name} ({filename}) not found")
            continue

        with open(path, 'rb') as f:
            data = f.read()

        segments.append((addr, data))
        print(f"  LOAD: {name:10s} @ 0x{addr:08X} ({len(data):,} bytes) from {os.path.basename(path)}")

    if not segments:
        print("ERROR: No firmware blocks found!")
        sys.exit(1)

    # Entry point: first instruction in strategy block
    entry = 0x01000000

    total = make_elf(segments, entry, output)
    print(f"\nCreated {output} ({total:,} bytes, {len(segments)} segments, entry=0x{entry:08X})")


if __name__ == '__main__':
    main()
