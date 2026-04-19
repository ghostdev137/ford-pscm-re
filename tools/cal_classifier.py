#!/usr/bin/env python3
"""Classify every byte of a Ford PSCM calibration blob.

Designed for F-150 cal (195,584 bytes, little-endian, `0x101D0000`). Also
handles Transit/Escape (65,520 B, big-endian) when `--be` is passed.

Output: CSV with one row per contiguous region covering 0..N exactly once.
Columns: start, end, length, class, confidence, repr_values, note.

Classes:
  reserved_ff           run of 0xFF (>=4 bytes)
  reserved_zero         run of 0x00 (>=8 bytes)
  float_axis            monotonic float32 axis (>=3 entries, increasing or decreasing)
  float_table           run of float32s, mixed monotonicity (values plausible)
  float_scalar          isolated plausible float32 not in a table
  u16_axis              monotonic u16 axis (>=3 entries, plausible timer/breakpoint range)
  u16_table             run of u16s, not strictly monotonic but structured
  u16_pair              exactly 2 u16s flanked by non-u16 regions
  timer_cluster         run of u16 values all in [0, 60000] with timer sentinels (100,500,1000,...)
  packed_bytes          run of single-byte flags/enums (e.g., 0x01/0x01 patterns)
  mixed                 region contains a mix of scalars and small structs
  unknown               doesn't fit any heuristic

No external deps.
"""

from __future__ import annotations

import argparse
import csv
import struct
import sys
from dataclasses import dataclass, field


# --- plausibility helpers ---------------------------------------------------

FLOAT_MAG_MAX = 1e7      # cal values shouldn't exceed ~1e6; allow headroom
FLOAT_MAG_MIN = 1e-6     # anything smaller is either 0 or denormalized noise
TIMER_MAX = 60001        # 1-minute timer ceiling at 1ms tick
TIMER_SENTINELS = {100, 200, 250, 300, 400, 500, 600, 750, 800, 1000, 1200, 1500,
                   2000, 2500, 3000, 4000, 5000, 6000, 7500, 8000, 10000, 10001,
                   12000, 15000, 20000, 25000, 30000, 60000}


def plausible_float(f: float) -> bool:
    import math
    if math.isnan(f) or math.isinf(f):
        return False
    if f == 0.0:
        return True
    a = abs(f)
    if a < FLOAT_MAG_MIN or a > FLOAT_MAG_MAX:
        return False
    return True


def u32_to_float(data: bytes, off: int, le: bool) -> float:
    fmt = "<f" if le else ">f"
    return struct.unpack_from(fmt, data, off)[0]


def u16(data: bytes, off: int, le: bool) -> int:
    fmt = "<H" if le else ">H"
    return struct.unpack_from(fmt, data, off)[0]


# --- region records ---------------------------------------------------------


@dataclass
class Region:
    start: int
    end: int           # exclusive
    cls: str
    confidence: str    # "high" | "medium" | "low"
    repr_values: str   # short human-readable sample
    note: str = ""

    @property
    def length(self) -> int:
        return self.end - self.start


# --- detectors --------------------------------------------------------------


def find_ff_runs(data: bytes, min_len: int = 4) -> list[Region]:
    out: list[Region] = []
    n = len(data)
    i = 0
    while i < n:
        if data[i] == 0xFF:
            j = i
            while j < n and data[j] == 0xFF:
                j += 1
            if j - i >= min_len:
                out.append(Region(i, j, "reserved_ff", "high",
                                  f"0xFF × {j - i}", "padding/unused"))
            i = j
        else:
            i += 1
    return out


def find_zero_runs(data: bytes, min_len: int = 8) -> list[Region]:
    out: list[Region] = []
    n = len(data)
    i = 0
    while i < n:
        if data[i] == 0x00:
            j = i
            while j < n and data[j] == 0x00:
                j += 1
            if j - i >= min_len:
                out.append(Region(i, j, "reserved_zero", "high",
                                  f"0x00 × {j - i}",
                                  "may be deprecated/disabled field cleared by Ford"))
            i = j
        else:
            i += 1
    return out


def find_float_axes(data: bytes, le: bool, occupied: list[bool]) -> list[Region]:
    """Monotonic float32 runs (>=3 entries) at 4-byte alignment."""
    out: list[Region] = []
    n = len(data)
    i = 0
    while i + 12 <= n:
        if any(occupied[i:i + 4]):
            i += 4
            continue

        floats: list[float] = []
        j = i
        while j + 4 <= n and not any(occupied[j:j + 4]):
            f = u32_to_float(data, j, le)
            if not plausible_float(f):
                break
            floats.append(f)
            j += 4

        if len(floats) >= 3:
            inc = all(floats[k] <= floats[k + 1] for k in range(len(floats) - 1))
            dec = all(floats[k] >= floats[k + 1] for k in range(len(floats) - 1))
            strict = len(set(floats)) == len(floats)
            if (inc or dec) and strict:
                sample = ", ".join(f"{f:.4g}" for f in floats[:6])
                if len(floats) > 6:
                    sample += f", ... ({len(floats)} total)"
                out.append(Region(
                    i, i + 4 * len(floats), "float_axis", "medium",
                    f"[{sample}]",
                    f"monotonic {'inc' if inc else 'dec'}"
                ))
                i += 4 * len(floats)
                continue
        i += 4
    return out


def find_float_tables(data: bytes, le: bool, occupied: list[bool]) -> list[Region]:
    """Runs of plausible float32s (>=3) that aren't strictly monotonic."""
    out: list[Region] = []
    n = len(data)
    i = 0
    while i + 12 <= n:
        if any(occupied[i:i + 4]):
            i += 4
            continue
        floats: list[float] = []
        j = i
        while j + 4 <= n and not any(occupied[j:j + 4]):
            f = u32_to_float(data, j, le)
            if not plausible_float(f):
                break
            floats.append(f)
            j += 4

        if len(floats) >= 3:
            sample = ", ".join(f"{f:.4g}" for f in floats[:6])
            if len(floats) > 6:
                sample += f", ... ({len(floats)} total)"
            out.append(Region(
                i, i + 4 * len(floats), "float_table", "low",
                f"[{sample}]", "contiguous plausible float32s"
            ))
            i += 4 * len(floats)
        else:
            i += 4
    return out


def find_float_scalars(data: bytes, le: bool, occupied: list[bool]) -> list[Region]:
    """Isolated plausible float32s (alignment 4, not in an already-classified region)."""
    out: list[Region] = []
    n = len(data)
    i = 0
    while i + 4 <= n:
        if not any(occupied[i:i + 4]):
            f = u32_to_float(data, i, le)
            if plausible_float(f) and f != 0.0:
                out.append(Region(
                    i, i + 4, "float_scalar", "low",
                    f"{f:.6g}",
                    "standalone float32"
                ))
        i += 4
    return out


def find_u16_axes(data: bytes, le: bool, occupied: list[bool]) -> list[Region]:
    """Monotonic u16 runs (>=4 entries) — breakpoint-style axes."""
    out: list[Region] = []
    n = len(data)
    i = 0
    while i + 8 <= n:
        if any(occupied[i:i + 2]):
            i += 2
            continue
        values: list[int] = []
        j = i
        while j + 2 <= n and not any(occupied[j:j + 2]):
            v = u16(data, j, le)
            if v > 65000:
                break
            values.append(v)
            j += 2

        if len(values) >= 4:
            inc = all(values[k] <= values[k + 1] for k in range(len(values) - 1))
            dec = all(values[k] >= values[k + 1] for k in range(len(values) - 1))
            strict = len(set(values)) == len(values)
            if (inc or dec) and strict and max(values) > 16:
                sample = ", ".join(str(v) for v in values[:8])
                if len(values) > 8:
                    sample += f", ... ({len(values)} total)"
                out.append(Region(
                    i, i + 2 * len(values), "u16_axis", "medium",
                    f"[{sample}]",
                    f"monotonic u16 axis, {'inc' if inc else 'dec'}"
                ))
                i += 2 * len(values)
                continue
        i += 2
    return out


def find_timer_clusters(data: bytes, le: bool, occupied: list[bool]) -> list[Region]:
    """Runs (>=4) of u16s that look like timer values."""
    out: list[Region] = []
    n = len(data)
    i = 0
    while i + 8 <= n:
        if any(occupied[i:i + 2]):
            i += 2
            continue
        values: list[int] = []
        j = i
        while j + 2 <= n and not any(occupied[j:j + 2]):
            v = u16(data, j, le)
            if v > TIMER_MAX:
                break
            values.append(v)
            j += 2

        if len(values) >= 4:
            hits = sum(1 for v in values if v in TIMER_SENTINELS or v == 0)
            if hits >= len(values) // 2 and hits >= 2:
                sample = ", ".join(str(v) for v in values[:8])
                if len(values) > 8:
                    sample += f", ... ({len(values)} total)"
                out.append(Region(
                    i, i + 2 * len(values), "timer_cluster", "medium",
                    f"[{sample}]",
                    f"{hits}/{len(values)} look like timer sentinels"
                ))
                i += 2 * len(values)
                continue
        i += 2
    return out


def find_u16_tables(data: bytes, le: bool, occupied: list[bool]) -> list[Region]:
    """Runs of u16s (>=4) that aren't monotonic or timer-like but cluster tightly."""
    out: list[Region] = []
    n = len(data)
    i = 0
    while i + 8 <= n:
        if any(occupied[i:i + 2]):
            i += 2
            continue
        values: list[int] = []
        j = i
        while j + 2 <= n and not any(occupied[j:j + 2]):
            v = u16(data, j, le)
            if v > 10000:
                break
            values.append(v)
            j += 2

        if len(values) >= 4:
            sample = ", ".join(str(v) for v in values[:8])
            if len(values) > 8:
                sample += f", ... ({len(values)} total)"
            out.append(Region(
                i, i + 2 * len(values), "u16_table", "low",
                f"[{sample}]",
                "contiguous u16 values in plausible range"
            ))
            i += 2 * len(values)
        else:
            i += 2
    return out


def find_packed_bytes(data: bytes, occupied: list[bool]) -> list[Region]:
    """Runs of small single-byte values (flags / enums / counts), 0..15 dominant."""
    out: list[Region] = []
    n = len(data)
    i = 0
    while i < n:
        if occupied[i]:
            i += 1
            continue
        j = i
        smalls = 0
        while j < n and not occupied[j] and data[j] <= 15:
            if data[j] <= 4:
                smalls += 1
            j += 1
        if j - i >= 6 and smalls >= (j - i) // 2:
            sample = ", ".join(f"0x{b:02x}" for b in data[i:min(j, i + 12)])
            if j - i > 12:
                sample += f", ... ({j - i} total)"
            out.append(Region(
                i, j, "packed_bytes", "low",
                f"[{sample}]",
                "bytes <= 15, likely flags/enums/counts"
            ))
            i = j
        else:
            i = max(i + 1, j)
    return out


# --- assembly ---------------------------------------------------------------


def classify(data: bytes, le: bool) -> list[Region]:
    n = len(data)
    occupied = [False] * n
    regions: list[Region] = []

    # High-confidence first: FF/00 runs.
    for r in find_ff_runs(data):
        regions.append(r)
        for k in range(r.start, r.end):
            occupied[k] = True
    for r in find_zero_runs(data):
        regions.append(r)
        for k in range(r.start, r.end):
            occupied[k] = True

    # Float axes (monotonic) — strongest non-reserved signal.
    for r in find_float_axes(data, le, occupied):
        regions.append(r)
        for k in range(r.start, r.end):
            occupied[k] = True

    # u16 axes (monotonic).
    for r in find_u16_axes(data, le, occupied):
        regions.append(r)
        for k in range(r.start, r.end):
            occupied[k] = True

    # Timer clusters.
    for r in find_timer_clusters(data, le, occupied):
        regions.append(r)
        for k in range(r.start, r.end):
            occupied[k] = True

    # Non-monotonic float tables.
    for r in find_float_tables(data, le, occupied):
        regions.append(r)
        for k in range(r.start, r.end):
            occupied[k] = True

    # Non-monotonic u16 tables.
    for r in find_u16_tables(data, le, occupied):
        regions.append(r)
        for k in range(r.start, r.end):
            occupied[k] = True

    # Packed byte sequences.
    for r in find_packed_bytes(data, occupied):
        regions.append(r)
        for k in range(r.start, r.end):
            occupied[k] = True

    # Isolated float scalars (last — any aligned unoccupied float32).
    for r in find_float_scalars(data, le, occupied):
        regions.append(r)
        for k in range(r.start, r.end):
            occupied[k] = True

    # Gap-fill: coalesce runs of unoccupied bytes into "unknown" regions.
    i = 0
    while i < n:
        if not occupied[i]:
            j = i
            while j < n and not occupied[j]:
                j += 1
            sample = " ".join(f"{b:02x}" for b in data[i:min(j, i + 12)])
            if j - i > 12:
                sample += " ..."
            regions.append(Region(
                i, j, "unknown", "low", sample,
                "no classifier heuristic matched"
            ))
            i = j
        else:
            i += 1

    regions.sort(key=lambda r: r.start)
    return regions


# --- verification -----------------------------------------------------------


def verify_full_coverage(regions: list[Region], n: int) -> list[str]:
    errs: list[str] = []
    if not regions:
        errs.append("no regions emitted")
        return errs
    if regions[0].start != 0:
        errs.append(f"first region starts at {regions[0].start}, not 0")
    if regions[-1].end != n:
        errs.append(f"last region ends at {regions[-1].end}, not {n}")
    for a, b in zip(regions, regions[1:]):
        if a.end != b.start:
            errs.append(f"gap or overlap: {a.start:#x}-{a.end:#x} then {b.start:#x}-{b.end:#x}")
    return errs


# --- CLI --------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("blob", help="path to raw cal blob")
    ap.add_argument("--be", action="store_true", help="big-endian (Transit/Escape)")
    ap.add_argument("--base", type=lambda s: int(s, 0), default=0,
                    help="absolute base address for reporting (e.g., 0x101D0000)")
    ap.add_argument("--csv", help="output CSV path (stdout if omitted)")
    ap.add_argument("--summary", help="output markdown summary path")
    ap.add_argument("--verify-full-coverage", action="store_true",
                    help="exit non-zero if coverage has gaps/overlaps")
    args = ap.parse_args()

    with open(args.blob, "rb") as f:
        data = f.read()

    le = not args.be
    regions = classify(data, le)

    errs = verify_full_coverage(regions, len(data))
    if errs:
        print("COVERAGE ERRORS:", file=sys.stderr)
        for e in errs:
            print(f"  {e}", file=sys.stderr)
        if args.verify_full_coverage:
            return 2

    # CSV output.
    out_csv = open(args.csv, "w", newline="") if args.csv else sys.stdout
    try:
        w = csv.writer(out_csv)
        w.writerow(["start_hex", "start_abs_hex", "end_hex", "length",
                    "class", "confidence", "repr_values", "note"])
        for r in regions:
            w.writerow([
                f"0x{r.start:05x}",
                f"0x{args.base + r.start:08x}" if args.base else "",
                f"0x{r.end:05x}",
                r.length,
                r.cls,
                r.confidence,
                r.repr_values,
                r.note,
            ])
    finally:
        if args.csv:
            out_csv.close()

    if args.summary:
        write_summary(args.summary, regions, len(data), args.base, le)

    # Always print one-line summary to stderr.
    by_class: dict[str, int] = {}
    bytes_by_class: dict[str, int] = {}
    for r in regions:
        by_class[r.cls] = by_class.get(r.cls, 0) + 1
        bytes_by_class[r.cls] = bytes_by_class.get(r.cls, 0) + r.length
    print(f"classified {len(data)} bytes into {len(regions)} regions", file=sys.stderr)
    for cls in sorted(by_class.keys(), key=lambda c: -bytes_by_class[c]):
        pct = 100.0 * bytes_by_class[cls] / len(data)
        print(f"  {cls:20s} {by_class[cls]:5d} regions  {bytes_by_class[cls]:7d} B  ({pct:5.1f}%)",
              file=sys.stderr)

    return 0


def write_summary(path: str, regions: list[Region], n: int, base: int, le: bool) -> None:
    by_class: dict[str, list[Region]] = {}
    for r in regions:
        by_class.setdefault(r.cls, []).append(r)

    endian = "little-endian" if le else "big-endian"
    with open(path, "w") as fh:
        fh.write(f"# Cal byte classification ({endian}, {n:,} B, base 0x{base:08x})\n\n")
        fh.write("Generated by `tools/cal_classifier.py`.\n\n")
        fh.write("## Coverage summary\n\n")
        fh.write("| Class | Regions | Bytes | % of cal |\n")
        fh.write("|---|---:|---:|---:|\n")
        total_bytes = 0
        for cls in sorted(by_class, key=lambda c: -sum(r.length for r in by_class[c])):
            b = sum(r.length for r in by_class[cls])
            total_bytes += b
            pct = 100.0 * b / n
            fh.write(f"| `{cls}` | {len(by_class[cls])} | {b:,} | {pct:.2f}% |\n")
        fh.write(f"| **total** | **{len(regions)}** | **{total_bytes:,}** | **100.00%** |\n\n")

        fh.write("## Region detail by class\n\n")
        for cls in sorted(by_class):
            fh.write(f"### `{cls}` — {len(by_class[cls])} regions, "
                     f"{sum(r.length for r in by_class[cls]):,} B\n\n")
            fh.write("| Offset | Abs | Length | Repr | Note |\n")
            fh.write("|---|---|---:|---|---|\n")
            for r in by_class[cls][:80]:
                repr_short = r.repr_values if len(r.repr_values) <= 80 else r.repr_values[:77] + "..."
                abs_addr = f"0x{base + r.start:08x}" if base else ""
                fh.write(f"| 0x{r.start:05x} | {abs_addr} | {r.length} | {repr_short} | {r.note} |\n")
            if len(by_class[cls]) > 80:
                fh.write(f"\n*(+{len(by_class[cls]) - 80} more, see CSV for full list)*\n\n")
            else:
                fh.write("\n")


if __name__ == "__main__":
    sys.exit(main())
