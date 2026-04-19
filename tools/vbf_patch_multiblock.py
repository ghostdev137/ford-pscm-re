#!/usr/bin/env python3
"""Patch one or more decompressed blocks inside a Ford multi-block VBF.

This is aimed at Transit/Escape strategy EXE files where only one block is
patched and the remaining blocks should be preserved byte-for-byte.

Example:
    python tools/vbf_patch_multiblock.py \
      firmware/Transit_2025/KK21-14D003-AH.VBF \
      firmware/patched/Transit_2025/KK21-14D003-AH_LCA_RX_PROBE.VBF \
      --patch 0x01000000:0x2C70:03D7011401080000 \
      --patch 0x01000000:0x2C78:03D3011501080000
"""

from __future__ import annotations

import argparse
import binascii
import re
import struct
from pathlib import Path
from typing import Iterable

from vbf_decompress import crc16, parse_header_fields, parse_vbf_blocks, parse_vbf_header
from vbf_lzss_encode import lzss_encode


def find_crc_region_start(data: bytes, target_crc: int) -> int:
    """Find the byte offset X such that CRC32(data[X:]) == target_crc."""
    header_text, header_end = parse_vbf_header(data)
    for candidate in range(max(0, header_end - 32), min(len(data), header_end + 32)):
        if binascii.crc32(data[candidate:]) & 0xFFFFFFFF == target_crc:
            return candidate
    raise ValueError(f"could not find CRC region for 0x{target_crc:08X}")


def parse_header_checksum(data: bytes) -> tuple[int, int, int]:
    """Return (value, start_offset, end_offset) of the file_checksum hex string."""
    header_text = data[:4000].decode("latin-1", errors="replace")
    m = re.search(r"file_checksum\s*=\s*(0x[0-9A-Fa-f]+)", header_text)
    if not m:
        raise ValueError("file_checksum not found in header")
    val_str = m.group(1)
    start = header_text.index(val_str)
    return int(val_str, 16), start, start + len(val_str)


def decompress_blocks(raw: bytes) -> tuple[bytes, int, list[dict]]:
    header_text, header_end = parse_vbf_header(raw)
    blocks = []
    for addr, compressed, stored_crc in parse_vbf_blocks(raw, header_end):
        dec = None
        blocks.append(
            {
                "addr": addr,
                "compressed": compressed,
                "crc_stored": stored_crc,
                "decompressed": dec,
            }
        )
    return header_text, header_end, blocks


def ensure_decompressed(block: dict, decoder) -> bytes:
    if block["decompressed"] is None:
        block["decompressed"] = decoder(block["compressed"])
    return block["decompressed"]


def patch_block(block: dict, patches: Iterable[tuple[int, bytes]]) -> None:
    data = bytearray(block["decompressed"])
    for offset, new_bytes in patches:
        end = offset + len(new_bytes)
        if end > len(data):
            raise ValueError(
                f"patch overruns block 0x{block['addr']:08X}: "
                f"offset=0x{offset:X} len=0x{len(new_bytes):X} size=0x{len(data):X}"
            )
        data[offset:end] = new_bytes
    block["decompressed"] = bytes(data)
    block["compressed"] = lzss_encode(block["decompressed"])
    block["crc_stored"] = crc16(block["decompressed"])


def rebuild_vbf(header_text: bytes | str, blocks: list[dict]) -> bytes:
    if isinstance(header_text, str):
        out = bytearray(header_text.encode("latin-1"))
    else:
        out = bytearray(header_text)
    for block in blocks:
        out += struct.pack(">I", block["addr"])
        out += struct.pack(">I", len(block["compressed"]))
        out += block["compressed"]
        out += struct.pack(">H", block["crc_stored"])
    return bytes(out)


def rewrite_header_checksum(data: bytearray, new_crc: int) -> None:
    _, start, end = parse_header_checksum(bytes(data))
    field_width = end - start
    new_field = f"0x{new_crc:08X}".ljust(field_width)
    for i, c in enumerate(new_field):
        data[start + i] = ord(c)


def parse_patch_arg(text: str) -> tuple[int, int, bytes]:
    try:
        block_str, off_str, hex_str = text.split(":", 2)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "patch must be BLOCK_ADDR:BLOCK_OFFSET:HEX"
        ) from exc
    return int(block_str, 0), int(off_str, 0), bytes.fromhex(hex_str.replace(" ", ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument(
        "--patch",
        action="append",
        default=[],
        type=parse_patch_arg,
        help="BLOCK_ADDR:BLOCK_OFFSET:HEX (repeatable)",
    )
    args = ap.parse_args()

    raw = Path(args.input).read_bytes()
    header_fields, orig_crc = parse_header_fields(parse_vbf_header(raw)[0])
    if orig_crc is None:
        raise SystemExit("file_checksum missing in header")
    crc_start = find_crc_region_start(raw, orig_crc)
    calc_crc = binascii.crc32(raw[crc_start:]) & 0xFFFFFFFF
    if calc_crc != orig_crc:
        raise SystemExit(
            f"stock file_checksum mismatch: header=0x{orig_crc:08X} calc=0x{calc_crc:08X}"
        )

    header_text, _, blocks = decompress_blocks(raw)

    from vbf_decompress import lzss_decode

    by_addr = {block["addr"]: block for block in blocks}
    grouped: dict[int, list[tuple[int, bytes]]] = {}
    for block_addr, offset, new_bytes in args.patch:
        grouped.setdefault(block_addr, []).append((offset, new_bytes))

    for block_addr, patch_list in grouped.items():
        if block_addr not in by_addr:
            raise SystemExit(f"block 0x{block_addr:08X} not found in VBF")
        block = by_addr[block_addr]
        ensure_decompressed(block, lzss_decode)
        patch_block(block, patch_list)

    rebuilt = bytearray(rebuild_vbf(header_text, blocks))
    new_crc = binascii.crc32(bytes(rebuilt[crc_start:])) & 0xFFFFFFFF
    rewrite_header_checksum(rebuilt, new_crc)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(rebuilt)

    print(f"input:  {args.input}")
    print(f"output: {args.output}")
    print(f"header file_checksum: 0x{orig_crc:08X} -> 0x{new_crc:08X}")
    for block in blocks:
        print(
            f"block 0x{block['addr']:08X}: compressed={len(block['compressed'])} "
            f"crc16=0x{block['crc_stored']:04X}"
        )


if __name__ == "__main__":
    main()
