#!/usr/bin/env python3
"""
VBF Multi-Block Decompressor for Ford PSCM firmware.
Parses VBF v3.0 files with LZSS compression (data_format_identifier=0x10).
Extracts all data blocks into separate files.

LZSS params: EI=10, EJ=4, P=1, N=1024, ring_init=0x20 (space)
Block format: [addr:4BE][len:4BE][compressed_data:len][CRC16:2]
"""

import json
import os
import re
import struct
import sys
import zlib
from pathlib import Path

EI = 10
EJ = 4
P = 1
N = 1 << EI  # 1024
F = (1 << EJ) + P  # 17
RING_INIT = 0x20  # space character


def lzss_decode(compressed: bytes) -> bytes:
    """Decompress LZSS data with Ford/qvbf parameters."""
    ring = bytearray([RING_INIT] * (N * 2))
    output = bytearray()
    data_idx = 0
    buf = 0
    mask = 0
    r = 0

    def getbit(n):
        nonlocal data_idx, buf, mask
        x = 0
        for _ in range(n):
            if mask == 0:
                if data_idx >= len(compressed):
                    return -1
                buf = compressed[data_idx]
                data_idx += 1
                mask = 128
            x <<= 1
            if buf & mask:
                x += 1
            mask >>= 1
        return x

    while True:
        c = getbit(1)
        if c == -1:
            break
        if c:
            # Literal byte
            ch = getbit(8)
            if ch == -1:
                break
            output.append(ch)
            ring[r] = ch
            r = (r + 1) & (N - 1)
        else:
            # Reference
            i = getbit(EI)
            if i == -1:
                break
            j = getbit(EJ)
            if j == -1:
                break
            if i == 0:
                break  # End marker
            pos = i - 1
            for k in range(j + 2):
                ch = ring[(pos + k) & (N - 1)]
                output.append(ch)
                ring[r] = ch
                r = (r + 1) & (N - 1)

    return bytes(output)


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE used in VBF blocks."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def crc32_file(raw: bytes) -> int:
    """CRC32 over the full file bytes."""
    return zlib.crc32(raw) & 0xFFFFFFFF


def _match_brace(raw: bytes, open_brace: int) -> int:
    """Find the matching closing brace, respecting quoted strings."""
    depth = 0
    in_string = False
    escape = False

    for i in range(open_brace, len(raw)):
        ch = raw[i]
        if in_string:
            if escape:
                escape = False
                continue
            if ch == 0x5C:  # backslash
                escape = True
                continue
            if ch == 0x22:  # double quote
                in_string = False
            continue

        if ch == 0x22:  # double quote
            in_string = True
            continue
        if ch == 0x7B:  # {
            depth += 1
            continue
        if ch == 0x7D:  # }
            depth -= 1
            if depth == 0:
                return i

    return -1


def parse_vbf_header(raw: bytes) -> tuple:
    """Parse VBF text header, return (header_text, end_offset)."""
    lower = raw.lower()
    header_idx = lower.find(b'header')
    if header_idx < 0:
        head = lower[:min(2_000_000, len(raw))]
        vbf_idx = head.find(b'vbf_version')
        if vbf_idx < 0:
            raise ValueError("Could not find VBF header")
        open_brace = head.find(b'{', vbf_idx)
        if open_brace < 0:
            raise ValueError("Could not find VBF header opening brace")
    else:
        open_brace = lower.find(b'{', header_idx)
        if open_brace < 0:
            raise ValueError("Found 'header' but no opening brace")

    close_brace = _match_brace(raw, open_brace)
    if close_brace < 0:
        raise ValueError("Could not find end of VBF header")

    return raw[:close_brace + 1].decode('latin-1', errors='replace'), close_brace + 1


def parse_header_fields(header_text: str) -> tuple:
    """Parse simple VBF header fields and return (fields, file_checksum)."""
    lines = []
    for line in header_text.splitlines():
        if '//' in line:
            line = line.split('//', 1)[0]
        lines.append(line)
    text = '\n'.join(lines)

    fields = {}
    file_checksum = None
    for match in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?);', text, re.DOTALL):
        key = match.group(1)
        value = match.group(2).strip()
        if value.startswith('{') and value.endswith('}'):
            fields[key] = value[1:-1].strip()
            continue
        if value.startswith('"') and value.endswith('"'):
            fields[key] = value[1:-1]
            continue
        lowered = value.lower()
        if lowered.startswith('0x'):
            try:
                num = int(lowered, 16)
                fields[key] = num
                if key.lower() == 'file_checksum':
                    file_checksum = num & 0xFFFFFFFF
                continue
            except ValueError:
                pass
        try:
            if '.' in value:
                fields[key] = float(value)
            else:
                fields[key] = int(value)
        except ValueError:
            fields[key] = value
    return fields, file_checksum


def parse_vbf_blocks(raw: bytes, header_end: int) -> list:
    """Parse all data blocks after header. Returns list of (addr, compressed_data, crc_stored)."""
    blocks = []
    offset = header_end
    while offset + 8 < len(raw):
        addr = struct.unpack_from('>I', raw, offset)[0]
        length = struct.unpack_from('>I', raw, offset + 4)[0]
        if length == 0 or offset + 8 + length + 2 > len(raw):
            break
        compressed = raw[offset + 8: offset + 8 + length]
        crc_stored = struct.unpack_from('>H', raw, offset + 8 + length)[0]
        blocks.append((addr, compressed, crc_stored))
        offset += 8 + length + 2
    return blocks


def get_data_format(header_text: str) -> int:
    """Extract data_format_identifier from header."""
    m = re.search(r'data_format_identifier\s*=\s*(0x[0-9a-fA-F]+)', header_text)
    if m:
        return int(m.group(1), 16)
    return 0


def decompress_vbf(vbf_path: str, output_dir: str, prefix: str = None) -> list:
    """
    Decompress a VBF file, extracting all blocks.
    Returns list of (output_path, addr, decompressed_size, crc_ok).
    """
    raw = open(vbf_path, 'rb').read()
    header_text, header_end = parse_vbf_header(raw)
    header_fields, file_checksum = parse_header_fields(header_text)
    file_checksum_calc = crc32_file(raw)
    dfi = get_data_format(header_text)
    is_compressed = (dfi >> 4) != 0

    blocks = parse_vbf_blocks(raw, header_end)
    os.makedirs(output_dir, exist_ok=True)

    header_json_path = os.path.join(output_dir, f"{Path(vbf_path).name}.header.json")
    with open(header_json_path, 'w', encoding='utf-8') as f:
        json.dump(
            {
                "source_file": str(vbf_path),
                "header_end_offset": header_end,
                "header_fields": header_fields,
                "file_checksum_header": file_checksum,
                "file_checksum_calc": file_checksum_calc,
                "file_checksum_match": (
                    None if file_checksum is None else file_checksum == file_checksum_calc
                ),
            },
            f,
            indent=2,
            sort_keys=True,
        )
    if file_checksum is None:
        print(f"  file_checksum: not present in header")
    else:
        status = "OK" if file_checksum == file_checksum_calc else "MISMATCH"
        print(
            f"  file_checksum: header=0x{file_checksum:08X} "
            f"calc=0x{file_checksum_calc:08X} {status}"
        )

    results = []
    for idx, (addr, compressed, crc_stored) in enumerate(blocks):
        if is_compressed:
            data = lzss_decode(compressed)
        else:
            data = compressed
        crc_calc = crc16(data)
        crc_ok = (crc_calc == crc_stored)

        if prefix:
            out_name = f"{prefix}_block{idx}_0x{addr:08X}.bin"
        else:
            out_name = f"block{idx}_0x{addr:08X}.bin"

        out_path = os.path.join(output_dir, out_name)
        with open(out_path, 'wb') as f:
            f.write(data)

        results.append((out_path, addr, len(compressed), len(data), crc_ok, crc_stored, crc_calc))
        status = "OK" if crc_ok else f"MISMATCH (stored=0x{crc_stored:04X} calc=0x{crc_calc:04X})"
        print(f"  Block {idx}: addr=0x{addr:08X}  compressed={len(compressed)}  decompressed={len(data)}  CRC16={status}")

    return results


def main():
    base = Path(__file__).resolve().parent.parent
    fw_dir = base / "firmware" / "2025_Transit_PSCM"
    out_base = fw_dir / "decompressed"

    # Strategy VBFs (3 blocks each)
    strategy_suffixes = ["AG", "AH", "AL", "AM"]
    # ECU config VBFs (1 block each)
    config_suffixes = ["AD", "AF", "AH"]

    # Block name mapping by address
    block_names = {
        0x01000000: "block0_strategy",
        0x10000400: "block1_ram",
        0x20FF0000: "block2_ext",
        0x00FD0000: "cal",
    }

    all_results = []

    print("=" * 70)
    print("VBF Multi-Block Decompressor")
    print("=" * 70)

    # Process strategy VBFs
    for suffix in strategy_suffixes:
        vbf_name = f"KK21-14D003-{suffix}.VBF"
        vbf_path = fw_dir / vbf_name
        if not vbf_path.exists():
            print(f"\nWARNING: {vbf_name} not found, skipping")
            continue

        print(f"\n--- {vbf_name} ---")
        out_dir = out_base / suffix
        os.makedirs(out_dir, exist_ok=True)

        raw = open(vbf_path, 'rb').read()
        header_text, header_end = parse_vbf_header(raw)
        dfi = get_data_format(header_text)
        is_compressed = (dfi >> 4) != 0
        blocks = parse_vbf_blocks(raw, header_end)

        print(f"  Header size: {header_end} bytes")
        print(f"  Data format: 0x{dfi:02X} ({'compressed' if is_compressed else 'raw'})")
        print(f"  Blocks found: {len(blocks)}")

        for idx, (addr, compressed, crc_stored) in enumerate(blocks):
            # VBF block CRC16 is over the stored payload bytes for each block.

            if is_compressed:
                data = lzss_decode(compressed)
            else:
                data = compressed

            name = block_names.get(addr, f"block{idx}_0x{addr:08X}")
            out_path = out_dir / f"{name}.bin"
            with open(out_path, 'wb') as f:
                f.write(data)

            print(f"  Block {idx}: addr=0x{addr:08X}  {name}  compressed={len(compressed)}  decompressed={len(data)}  CRC16=0x{crc_stored:04X}")
            all_results.append((suffix, vbf_name, name, addr, len(compressed), len(data), crc_stored, str(out_path)))

    # Process ECU config VBFs
    for suffix in config_suffixes:
        vbf_name = f"LK41-14D007-{suffix}.VBF"
        vbf_path = fw_dir / vbf_name
        if not vbf_path.exists():
            print(f"\nWARNING: {vbf_name} not found, skipping")
            continue

        print(f"\n--- {vbf_name} ---")

        raw = open(vbf_path, 'rb').read()
        header_text, header_end = parse_vbf_header(raw)
        dfi = get_data_format(header_text)
        is_compressed = (dfi >> 4) != 0
        blocks = parse_vbf_blocks(raw, header_end)

        print(f"  Header size: {header_end} bytes")
        print(f"  Data format: 0x{dfi:02X} ({'compressed' if is_compressed else 'raw'})")
        print(f"  Blocks found: {len(blocks)}")

        for idx, (addr, compressed, crc_stored) in enumerate(blocks):
            if is_compressed:
                data = lzss_decode(compressed)
            else:
                data = compressed

            out_name = f"cal_{suffix}"
            out_path = out_base / f"{out_name}.bin"
            with open(out_path, 'wb') as f:
                f.write(data)

            print(f"  Block {idx}: addr=0x{addr:08X}  {out_name}  compressed={len(compressed)}  decompressed={len(data)}  CRC16=0x{crc_stored:04X}")
            all_results.append((suffix, vbf_name, out_name, addr, len(compressed), len(data), crc_stored, str(out_path)))

    # Verify against reference files
    print("\n" + "=" * 70)
    print("VERIFICATION against reference .bin files")
    print("=" * 70)

    ref_checks = [
        (fw_dir / "KK21-14D003-AG.bin", out_base / "AG" / "block0_strategy.bin", "AG block0"),
        (fw_dir / "KK21-14D003-AM.bin", out_base / "AM" / "block0_strategy.bin", "AM block0"),
        (fw_dir / "LK41-14D007-AD.bin", out_base / "cal_AD.bin", "cal_AD"),
        (fw_dir / "LK41-14D007-AH.bin", out_base / "cal_AH.bin", "cal_AH"),
    ]

    for ref_path, dec_path, label in ref_checks:
        if not ref_path.exists():
            print(f"  {label}: reference file not found")
            continue
        if not dec_path.exists():
            print(f"  {label}: decompressed file not found")
            continue
        ref_data = open(ref_path, 'rb').read()
        dec_data = open(dec_path, 'rb').read()
        if ref_data == dec_data:
            print(f"  {label}: MATCH ({len(ref_data)} bytes)")
        else:
            print(f"  {label}: MISMATCH (ref={len(ref_data)}, dec={len(dec_data)})")
            # Find first diff
            for i in range(min(len(ref_data), len(dec_data))):
                if ref_data[i] != dec_data[i]:
                    print(f"    First diff at offset 0x{i:X}: ref=0x{ref_data[i]:02X} dec=0x{dec_data[i]:02X}")
                    break

    # Write manifest
    print("\n" + "=" * 70)
    print("Writing manifest...")
    manifest_path = out_base / "manifest.txt"
    with open(manifest_path, 'w') as f:
        f.write("VBF Decompression Manifest\n")
        f.write(f"Generated by vbf_decompress.py\n")
        f.write("=" * 70 + "\n\n")

        # Expected sizes
        expected = {
            "block0_strategy": 1048560,
            "block1_ram": 3072,
            "block2_ext": 327680,
        }

        for suffix, vbf_name, block_name, addr, comp_size, dec_size, crc_stored, out_path in all_results:
            rel_path = os.path.relpath(out_path, str(out_base))

            # Check against expected size
            exp = expected.get(block_name, None)
            if exp is None and block_name.startswith("cal_"):
                exp = 65520
            size_status = ""
            if exp:
                if dec_size == exp:
                    size_status = f"  (expected: {exp} OK)"
                else:
                    size_status = f"  (expected: {exp} DIFFERS)"

            f.write(f"{rel_path}\n")
            f.write(f"  Source: {vbf_name}\n")
            f.write(f"  Address: 0x{addr:08X}\n")
            f.write(f"  Compressed: {comp_size} bytes\n")
            f.write(f"  Decompressed: {dec_size} bytes{size_status}\n")
            f.write(f"  CRC16: 0x{crc_stored:04X}\n")
            f.write("\n")

    print(f"Manifest written to: {manifest_path}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    expected = {
        "block0_strategy": 1048560,
        "block1_ram": 3072,
        "block2_ext": 327680,
    }
    total_files = len(all_results)
    print(f"  Total files extracted: {total_files}")

    # Size check
    print("\n  Size verification:")
    for suffix, vbf_name, block_name, addr, comp_size, dec_size, crc_stored, out_path in all_results:
        exp = expected.get(block_name)
        if exp is None and block_name.startswith("cal_"):
            exp = 65520
        if exp:
            match = "OK" if dec_size == exp else f"DIFFERS (got {dec_size})"
            print(f"    {os.path.basename(out_path)}: {dec_size} bytes  expected {exp}  {match}")
        else:
            print(f"    {os.path.basename(out_path)}: {dec_size} bytes")


if __name__ == '__main__':
    main()
