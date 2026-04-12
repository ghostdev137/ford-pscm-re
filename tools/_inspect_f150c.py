#!/usr/bin/env python3
"""
Determine exact block layout:
- Is the 16-byte name field only in some files (cal/supplementary)?
- What are the trailing bytes (CRC16 per block? CRC32 file checksum)?
- Are there multiple blocks per file?
"""
import struct, os, re, zlib

def find_header_end(raw):
    depth = 0
    in_header = False
    for i in range(len(raw)):
        if not in_header and raw[i:i+6] == b'header':
            in_header = True
        if in_header:
            if raw[i] == 0x7B:
                depth += 1
            elif raw[i] == 0x7D:
                depth -= 1
                if depth == 0:
                    return i + 1
    return -1

def crc16_ccitt(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def crc32_check(data, expected):
    calc = zlib.crc32(data) & 0xFFFFFFFF
    return calc, calc == expected

def hexdump(data, offset=0, rows=4):
    for i in range(0, min(len(data), rows*16), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
        asc_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"    {offset+i:08x}: {hex_part:<48}  {asc_part}")

base_2021 = "C:/Users/Zorro/Desktop/pscm-repo/firmware/F150_2021_Lariat_BlueCruise"
base_2022 = "C:/Users/Zorro/Desktop/pscm-repo/firmware/F150_2022"

files = [
    (base_2021, "ML34-14D007-EDL.VBF"),
    (base_2021, "ML34-14D004-EP.VBF"),
    (base_2021, "ML34-14D005-AB.VBF"),
    (base_2021, "ML3V-14D003-BD.VBF"),
    (base_2022, "ML34-14D007-BDL"),
    (base_2022, "ML34-14D004-BP"),
    (base_2022, "ML34-14D005-AB"),
    (base_2022, "ML3V-14D003-BD"),
]

for fdir, fname in files:
    fpath = os.path.join(fdir, fname)
    if not os.path.exists(fpath):
        print(f"MISSING: {fpath}")
        continue
    raw = open(fpath, 'rb').read()
    hdr_end = find_header_end(raw)
    hdr_text = raw[:hdr_end].decode('ascii', errors='replace')

    fc_m = re.search(r'file_checksum\s*=\s*(0x[0-9a-fA-F]+)', hdr_text)
    dfi_m = re.search(r'data_format_identifier\s*=\s*(0x[0-9a-fA-F]+)', hdr_text)
    sw_m = re.search(r'sw_part_type\s*=\s*(\w+)', hdr_text)
    file_checksum = int(fc_m.group(1), 16) if fc_m else None
    dfi = int(dfi_m.group(1), 16) if dfi_m else 0
    sw_type = sw_m.group(1) if sw_m else '?'

    print(f"\n{'='*65}")
    print(f"FILE: {fname}  size={len(raw)}  hdr_end={hdr_end}  sw={sw_type}  dfi=0x{dfi:02x}")
    print(f"  file_checksum=0x{file_checksum:08X}" if file_checksum else "  file_checksum=N/A")

    data_section = raw[hdr_end:]
    print(f"  data_section size: {len(data_section)}")
    print(f"  Last 16 bytes of file:")
    hexdump(raw[-16:], len(raw)-16, 1)

    # Try to parse blocks assuming: [u32 addr][u32 len][data*len][u16 crc16]
    # Then at the end: [u32 file_crc32] or nothing
    # First try standard Transit layout
    offset = hdr_end
    blocks_found = []
    print(f"\n  --- Attempting standard layout (addr4+len4+data+crc16) ---")
    off = hdr_end
    for attempt in range(10):
        if off + 8 >= len(raw):
            break
        addr = struct.unpack_from('>I', raw, off)[0]
        blen = struct.unpack_from('>I', raw, off+4)[0]
        if blen == 0:
            print(f"  Block {attempt}: zero length at off={off}, stopping")
            break
        if off + 8 + blen + 2 > len(raw) + 4:  # allow some slack
            print(f"  Block {attempt}: len={blen} would exceed file at off={off}")
            break
        # Check if it fits
        end_off = off + 8 + blen
        if end_off + 2 <= len(raw):
            crc_stored = struct.unpack_from('>H', raw, end_off)[0]
            crc_calc = crc16_ccitt(raw[off+8:end_off])
            crc_ok = (crc_stored == crc_calc)
            print(f"  Block {attempt}: addr=0x{addr:08x}  len={blen}  CRC16 stored=0x{crc_stored:04x} calc=0x{crc_calc:04x} {'OK' if crc_ok else 'MISMATCH'}")
            blocks_found.append((addr, blen, crc_ok, off))
            off = end_off + 2
        else:
            print(f"  Block {attempt}: addr=0x{addr:08x}  len={blen}  would go past EOF")
            break

    print(f"  Offset after blocks: {off}  file_size: {len(raw)}  diff: {len(raw)-off}")
    if len(raw) - off == 4:
        tail4 = struct.unpack_from('>I', raw, off)[0]
        print(f"  Trailing 4 bytes: 0x{tail4:08x}")
        if file_checksum:
            print(f"  vs file_checksum: 0x{file_checksum:08x}  match={tail4 == file_checksum}")
        # Try CRC32 of data section
        crc32_val = zlib.crc32(raw[hdr_end:off]) & 0xFFFFFFFF
        print(f"  CRC32 of blocks data: 0x{crc32_val:08x}  match={crc32_val == file_checksum}")
    elif len(raw) - off == 0:
        print(f"  No trailing bytes (file_checksum may be in header only)")
        # Check if CRC32 of data matches
        if file_checksum:
            crc32_val = zlib.crc32(raw[hdr_end:off]) & 0xFFFFFFFF
            print(f"  CRC32 of blocks data: 0x{crc32_val:08x}  match={crc32_val == file_checksum}")
    elif len(raw) - off == 2:
        tail2 = struct.unpack_from('>H', raw, off)[0]
        print(f"  Trailing 2 bytes: 0x{tail2:04x}")
    else:
        print(f"  Trailing {len(raw)-off} bytes")

    # Also check: does 0x101d etc parse as a valid flash region address?
    # 0x1000_0000 range is typical for many ARM MCUs
    print(f"\n  Address analysis:")
    if blocks_found:
        for addr, blen, crc_ok, off in blocks_found:
            region = "???"
            if 0x10000000 <= addr <= 0x1FFFFFFF:
                region = "FLASH (0x1xxx_xxxx)"
            elif 0xFEC00000 <= addr <= 0xFFFFFFFF:
                region = "HIGH_MEM/PERIPHERAL"
            elif 0x00000000 <= addr <= 0x00FFFFFF:
                region = "LOW_FLASH"
            print(f"    addr=0x{addr:08x}  len=0x{blen:06x}={blen}  end=0x{addr+blen:08x}  region={region}")

    # For SBL file which failed, show more details
    if 'SBL' in sw_type or addr == 0xfebe0000 if blocks_found else False:
        print(f"  SBL special analysis:")
        hexdump(raw[hdr_end:hdr_end+32], hdr_end, 2)
