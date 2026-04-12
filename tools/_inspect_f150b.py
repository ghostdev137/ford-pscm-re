#!/usr/bin/env python3
"""Deep inspect all F-150 VBF files - handle both LF and CRLF headers."""
import struct, os, re

def find_header_end(raw):
    """Find end of VBF header using brace counting. Returns offset just after closing }."""
    depth = 0
    in_header = False
    i = 0
    while i < len(raw):
        # Look for 'header' keyword
        if not in_header and raw[i:i+6] == b'header':
            in_header = True
        if in_header:
            if raw[i] == 0x7B:  # {
                depth += 1
            elif raw[i] == 0x7D:  # }
                depth -= 1
                if depth == 0:
                    return i + 1  # offset just after the closing }
        i += 1
    return -1

def hexdump(data, offset=0, rows=8):
    for i in range(0, min(len(data), rows*16), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
        asc_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"    {offset+i:08x}: {hex_part:<48}  {asc_part}")

base_2021 = "C:/Users/Zorro/Desktop/pscm-repo/firmware/F150_2021_Lariat_BlueCruise"
base_2022 = "C:/Users/Zorro/Desktop/pscm-repo/firmware/F150_2022"

files_2021 = [
    (base_2021, "ML34-14D007-EDL.VBF"),
    (base_2021, "ML34-14D004-EP.VBF"),
    (base_2021, "ML34-14D005-AB.VBF"),
    (base_2021, "ML3V-14D003-BD.VBF"),
]
files_2022 = [
    (base_2022, "ML34-14D007-BDL"),
    (base_2022, "ML34-14D004-BP"),
    (base_2022, "ML34-14D005-AB"),
    (base_2022, "ML3V-14D003-BD"),
]

all_files = files_2021 + files_2022

for fdir, fname in all_files:
    fpath = os.path.join(fdir, fname)
    if not os.path.exists(fpath):
        print(f"\nMISSING: {fpath}")
        continue
    raw = open(fpath, 'rb').read()
    hdr_end = find_header_end(raw)

    print(f"\n{'='*65}")
    print(f"FILE: {fname}  size={len(raw)}  hdr_end={hdr_end}")

    if hdr_end < 0:
        print("  ERROR: Could not find header end!")
        continue

    # Show what immediately follows the header
    print(f"  Bytes just before hdr_end: {repr(raw[max(0,hdr_end-10):hdr_end])}")
    print(f"  First 64 bytes after header:")
    hexdump(raw[hdr_end:hdr_end+64], hdr_end, 4)

    # Parse header text
    hdr_text = raw[:hdr_end].decode('ascii', errors='replace')
    fc = re.search(r'file_checksum\s*=\s*(0x[0-9a-fA-F]+)', hdr_text)
    dfi = re.search(r'data_format_identifier\s*=\s*(0x[0-9a-fA-F]+)', hdr_text)
    sw_type = re.search(r'sw_part_type\s*=\s*(\w+)', hdr_text)
    print(f"  sw_part_type: {sw_type.group(1) if sw_type else 'N/A'}")
    print(f"  data_format_identifier: {dfi.group(1) if dfi else '0x00'}")
    print(f"  file_checksum: {fc.group(1) if fc else 'N/A'}")

    # Skip any whitespace/newlines after the header
    skip = hdr_end
    while skip < len(raw) and raw[skip] in (0x0a, 0x0d, 0x20, 0x09):
        skip += 1
    print(f"  After whitespace skip: offset={skip}")
    print(f"  First 64 bytes at skip point:")
    hexdump(raw[skip:skip+64], skip, 4)

    # Try all interpretations at skip point
    if len(raw) > skip + 8:
        # Interp A: straight u32 addr BE + u32 len BE
        addr_a = struct.unpack_from('>I', raw, skip)[0]
        len_a  = struct.unpack_from('>I', raw, skip+4)[0]
        remaining = len(raw) - skip
        print(f"\n  Interp A (addr4+len4 at skip): addr=0x{addr_a:08x}  len={len_a}  remaining={remaining}")
        if len_a < remaining and len_a > 0:
            print(f"    -> plausible? addr range OK={0 <= addr_a < 0x40000000}, len fits={len_a < remaining}")

        # Interp B: skip a 16-byte name first, then addr+len
        name16 = raw[skip:skip+16]
        addr_b = struct.unpack_from('>I', raw, skip+16)[0]
        len_b  = struct.unpack_from('>I', raw, skip+20)[0]
        print(f"  Interp B (name16 then addr4+len4): name={repr(name16)}")
        print(f"    addr=0x{addr_b:08x}  len={len_b}")

        # Look for the part name string after header
        # It seems it's at hdr_end+8 for EDL; let's look for ASCII name pattern
        for offset_try in [0, 8, 16, 24, 32]:
            chunk = raw[skip+offset_try:skip+offset_try+16]
            printable = sum(1 for b in chunk if 32 <= b < 127)
            if printable > 10:
                print(f"  At skip+{offset_try}: {repr(chunk)}")
