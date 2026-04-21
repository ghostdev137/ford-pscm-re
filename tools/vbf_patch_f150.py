"""
F-150 PSCM VBF patcher.

Applies byte-level patches to an F-150 VBF and recomputes the header
`file_checksum` (a standard zlib CRC32 over everything after the ASCII header).

Usage:
    python tools/vbf_patch_f150.py input.vbf output.vbf --patch OFFSET:HEX

Examples:
    # Zero the LKA 10-sec lockout pair
    python tools/vbf_patch_f150.py ML34-14D007-EDL.VBF LKA_unlock.vbf \\
        --patch 0x07ADC:0000 --patch 0x07ADE:0000

Multiple --patch flags apply in order. OFFSET is the cal-data offset
(relative to data_start; for the Lariat BlueCruise cal this is the flash
offset from 0x101D0000).
"""
import argparse, binascii, re, struct, sys

def find_header_end(data: bytes) -> int:
    """Return the first non-ASCII byte offset (start of binary region)."""
    for i, b in enumerate(data):
        if b > 127 or (b < 9 and b != 0):
            return i
    raise ValueError("no binary region found")


def find_data_start(data: bytes) -> int:
    """Return the offset of the start of the block's payload bytes.

    F-150 cal layout: ...};\\n\\n\\n} <8-byte block hdr> <16-byte name tag> <data...>.
    We locate the data by finding the 16-byte ASCII name tag of the form
    `SWPN-XXXXXX-XXX\\0`.
    """
    # Search for the ML/LK/XX-XXXXX-XXX pattern after the ASCII header
    header_end = find_header_end(data)
    # Name tag is right after an 8-byte block header; look for the first
    # 4+ char ASCII run matching Ford part-number pattern, tag is 16 bytes (name + zero padding)
    # Search a wider window (some VBFs have a few filler bytes before the tag)
    window = data[header_end:header_end + 128]
    m = re.search(rb'([A-Z0-9]{2,4}-[A-Z0-9]{5,6}-[A-Z0-9]{2,4})', window)
    if not m:
        return None
    tag_start = header_end + m.start()
    # Skip the 16-byte tag (ASCII name padded with NULs)
    return tag_start + 16


def find_crc_region_start(data: bytes, target_crc: int) -> int:
    """Find the byte offset X such that CRC32(data[X:]) == target_crc."""
    header_end = find_header_end(data)
    for candidate in range(max(0, header_end - 32), min(len(data), header_end + 32)):
        if binascii.crc32(data[candidate:]) & 0xFFFFFFFF == target_crc:
            return candidate
    raise ValueError(f"could not find CRC region for 0x{target_crc:08X}")


def parse_header_checksum(data: bytes) -> tuple[int, int, int]:
    """Return (value, start_offset, end_offset) of the file_checksum hex string."""
    header_text = data[:4000].decode('latin-1', errors='replace')
    m = re.search(r'file_checksum\s*=\s*(0x[0-9A-Fa-f]+)', header_text)
    if not m:
        raise ValueError("file_checksum not found in header")
    val_str = m.group(1)
    start = header_text.index(val_str)
    return int(val_str, 16), start, start + len(val_str)


def apply_patches(data, patches, data_start=None):
    """Apply (cal_offset, bytes) patches in-place, using the VBF's data_start.
    If data_start is None, auto-detect via name-tag heuristic (F-150 style)."""
    if data_start is None:
        data_start = find_data_start(bytes(data))
    if data_start is None:
        raise ValueError(
            "this VBF lacks an embedded name tag — pass --data-start explicitly"
        )
    for cal_off, new_bytes in patches:
        abs_off = data_start + cal_off
        data[abs_off:abs_off + len(new_bytes)] = new_bytes


def update_checksum(data: bytearray, target_original_crc: int) -> int:
    """Recompute file_checksum over the patched binary region and rewrite header."""
    crc_start = find_crc_region_start(bytes(data), target_original_crc)
    new_crc = binascii.crc32(bytes(data[crc_start:])) & 0xFFFFFFFF
    val, start, end = parse_header_checksum(bytes(data))
    new_str = f'0x{new_crc:08X}'
    # Preserve original field width by space-padding
    field_width = end - start
    new_field = new_str.ljust(field_width)
    for i, c in enumerate(new_field):
        data[start + i] = ord(c)
    return new_crc


def parse_patch_arg(s: str) -> tuple[int, bytes]:
    off_str, hex_str = s.split(':', 1)
    return int(off_str, 0), bytes.fromhex(hex_str.replace(' ', ''))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input')
    ap.add_argument('output')
    ap.add_argument('--patch', action='append', default=[],
                    help='cal_offset:hex (e.g. 0x07ADC:0000). Repeatable.')
    ap.add_argument('--data-start', type=lambda s: int(s, 0),
                    help='Override auto-detection of the cal data_start. '
                         'Transit VBFs embed the part-number string inside cal data '
                         'at cal offset 0x18, which fools the name-tag heuristic — '
                         'pass --data-start 0x571 for AH-revision Transit cals.')
    args = ap.parse_args()

    raw = open(args.input, 'rb').read()
    orig_crc, _, _ = parse_header_checksum(raw)
    # Verify CRC of stock file, and remember the CRC region start
    crc_start = find_crc_region_start(raw, orig_crc)
    computed = binascii.crc32(raw[crc_start:]) & 0xFFFFFFFF
    if computed != orig_crc:
        sys.exit(f"stock CRC mismatch: header={orig_crc:#x} computed={computed:#x}")
    print(f'stock file_checksum = 0x{orig_crc:08X} (verified at offset {crc_start})')

    patches = [parse_patch_arg(p) for p in args.patch]
    print(f'applying {len(patches)} patch(es):')
    for off, b in patches:
        print(f'  cal+0x{off:05X}: {b.hex()}')

    data = bytearray(raw)
    apply_patches(data, patches, data_start=args.data_start)
    if args.data_start is not None:
        print(f'using explicit data_start = 0x{args.data_start:x}')
    # Recompute CRC32 over patched region
    new_crc = binascii.crc32(bytes(data[crc_start:])) & 0xFFFFFFFF
    # Rewrite file_checksum in header
    val, start, end = parse_header_checksum(bytes(data))
    new_str = f'0x{new_crc:08X}'
    field_width = end - start
    new_field = new_str.ljust(field_width)
    for i, c in enumerate(new_field):
        data[start + i] = ord(c)
    print(f'new file_checksum  = 0x{new_crc:08X}')

    open(args.output, 'wb').write(bytes(data))
    print(f'wrote {args.output} ({len(data)} bytes)')


if __name__ == '__main__':
    main()
