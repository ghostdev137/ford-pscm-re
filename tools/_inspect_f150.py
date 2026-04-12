#!/usr/bin/env python3
import struct, os

base = "C:/Users/Zorro/Desktop/pscm-repo/firmware/F150_2021_Lariat_BlueCruise"
files = [
    "ML34-14D007-EDL.VBF",
    "ML34-14D004-EP.VBF",
    "ML34-14D005-AB.VBF",
    "ML3V-14D003-BD.VBF",
]

for fname in files:
    fpath = os.path.join(base, fname)
    raw = open(fpath, 'rb').read()
    print(f"\n{'='*60}")
    print(f"FILE: {fname}  size={len(raw)} bytes")

    # Find header end: look for };\n\n\n}
    pat = b'};\n\n\n}'
    pos = raw.find(pat)
    if pos == -1:
        pat2 = b'};\r\n\r\n\r\n}'
        pos2 = raw.find(pat2)
        print(f"  LF pattern not found, CRLF at: {pos2}")
        pos = pos2
        if pos == -1:
            # Try just }; and scan
            for i in range(len(raw)-2):
                if raw[i:i+2] == b'};':
                    print(f"  Found }}; at {i}")
                    print(f"  Context: {repr(raw[i:i+20])}")
                    break
            continue

    hdr_end = pos + len(pat)
    print(f"  Pattern at offset: {pos}, header ends at: {hdr_end}")
    print(f"  Header tail: {repr(raw[max(0,pos-20):hdr_end])}")
    print(f"  Next 80 bytes after header:")
    chunk = raw[hdr_end:hdr_end+80]
    for i in range(0, len(chunk), 16):
        hex_part = ' '.join(f'{b:02x}' for b in chunk[i:i+16])
        asc_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk[i:i+16])
        print(f"    {hdr_end+i:08x}: {hex_part:<48}  {asc_part}")

    # Interpretation A: addr/len at hdr_end
    addr_a = struct.unpack_from('>I', raw, hdr_end)[0]
    len_a  = struct.unpack_from('>I', raw, hdr_end+4)[0]
    print(f"\n  Interp A: addr=0x{addr_a:08x}  len=0x{len_a:08x} ({len_a})")
    print(f"    addr+len = 0x{addr_a+len_a:08x}")
    print(f"    file_remaining after header = {len(raw)-hdr_end}")

    # Interpretation B: u16+u16+u32
    m1 = struct.unpack_from('>H', raw, hdr_end)[0]
    m2 = struct.unpack_from('>H', raw, hdr_end+2)[0]
    l_b = struct.unpack_from('>I', raw, hdr_end+4)[0]
    print(f"  Interp B: u16=0x{m1:04x}  u16=0x{m2:04x}  u32_len=0x{l_b:08x} ({l_b})")

    # Try: skip 8 bytes, look for null-terminated string
    name_start = hdr_end + 8
    name_bytes = raw[name_start:name_start+20]
    print(f"  Bytes at +8: {' '.join(f'{b:02x}' for b in name_bytes)}  '{name_bytes.decode('ascii','replace')}'")

    # Parse text header for file_checksum and data_format_identifier
    hdr_text = raw[:hdr_end].decode('ascii', errors='replace')
    import re
    fc = re.search(r'file_checksum\s*=\s*(0x[0-9a-fA-F]+)', hdr_text)
    dfi = re.search(r'data_format_identifier\s*=\s*(0x[0-9a-fA-F]+)', hdr_text)
    print(f"  file_checksum: {fc.group(1) if fc else 'not found'}")
    print(f"  data_format_identifier: {dfi.group(1) if dfi else 'not found'}")
