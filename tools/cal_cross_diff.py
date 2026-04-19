#!/usr/bin/env python3
"""Byte-diff two Ford PSCM cal blobs and cluster changes into contiguous regions.

Designed for F-150 BDL (2022 baseline) vs EDL (2021 BlueCruise), both 195,584 B
at `0x101D0000`, little-endian. Also usable for any same-length cal pair.

Output:
  - CSV: one row per diff region (start, end, length, a_repr, b_repr, class, note)
  - Markdown summary: human-readable diff report grouped by class/region size

Classifier-aware: if a `--classification` CSV is passed (from cal_classifier.py
run on the `--b` blob), each diff region is tagged with the class of the
underlying region it falls inside.

No external deps.
"""

from __future__ import annotations

import argparse
import csv
import struct
import sys


def load_classification(path: str) -> list[tuple[int, int, str, str]]:
    """Return list of (start, end, class, confidence) sorted by start."""
    rows = []
    with open(path) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            start = int(row["start_hex"], 16)
            end = int(row["end_hex"], 16)
            rows.append((start, end, row["class"], row["confidence"]))
    rows.sort()
    return rows


def lookup_class(classes: list[tuple[int, int, str, str]], off: int) -> tuple[str, str]:
    # Linear scan is fine for a few thousand rows.
    for start, end, cls, conf in classes:
        if start <= off < end:
            return cls, conf
    return "unclassified", "low"


def find_diff_regions(a: bytes, b: bytes, merge_gap: int = 4) -> list[tuple[int, int]]:
    """Return list of (start, end) regions where a != b, merging tiny gaps."""
    assert len(a) == len(b), "blobs must be same length"
    n = len(a)
    diffs = [i for i in range(n) if a[i] != b[i]]
    if not diffs:
        return []

    regions: list[list[int]] = []
    cur_start = diffs[0]
    cur_end = diffs[0] + 1
    for off in diffs[1:]:
        if off - cur_end <= merge_gap:
            cur_end = off + 1
        else:
            regions.append([cur_start, cur_end])
            cur_start = off
            cur_end = off + 1
    regions.append([cur_start, cur_end])
    return [(s, e) for s, e in regions]


def repr_region(data: bytes, start: int, end: int, max_bytes: int = 24) -> str:
    n = end - start
    if n <= max_bytes:
        return " ".join(f"{b:02x}" for b in data[start:end])
    head = " ".join(f"{b:02x}" for b in data[start:start + max_bytes])
    return f"{head} ... ({n} B)"


def interpret_region(data: bytes, start: int, end: int, le: bool) -> str:
    """Try to interpret a region's contents as floats or u16s."""
    n = end - start
    fmt_f = "<f" if le else ">f"
    fmt_h = "<H" if le else ">H"

    # 4-byte aligned, multiple of 4 bytes: try floats
    if start % 4 == 0 and n % 4 == 0 and n <= 48:
        try:
            floats = [struct.unpack_from(fmt_f, data, start + i)[0]
                      for i in range(0, n, 4)]
            import math
            if all(not math.isnan(f) and not math.isinf(f) and abs(f) < 1e7 for f in floats):
                if any(abs(f) > 1e-6 for f in floats):
                    return "f=[" + ", ".join(f"{f:.4g}" for f in floats) + "]"
        except struct.error:
            pass

    # 2-byte aligned, multiple of 2: try u16
    if start % 2 == 0 and n % 2 == 0 and n <= 32:
        try:
            u16s = [struct.unpack_from(fmt_h, data, start + i)[0]
                    for i in range(0, n, 2)]
            return "u16=[" + ", ".join(str(u) for u in u16s) + "]"
        except struct.error:
            pass

    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--a", required=True, help="baseline cal (e.g., BDL)")
    ap.add_argument("--b", required=True, help="target cal (e.g., EDL)")
    ap.add_argument("--be", action="store_true", help="big-endian")
    ap.add_argument("--base", type=lambda s: int(s, 0), default=0,
                    help="absolute base address (e.g., 0x101D0000)")
    ap.add_argument("--classification",
                    help="optional CSV from cal_classifier.py on --b")
    ap.add_argument("--merge-gap", type=int, default=4,
                    help="bytes of identical content to bridge across (default 4)")
    ap.add_argument("--csv", help="output CSV path")
    ap.add_argument("--summary", help="output markdown summary path")
    ap.add_argument("--a-label", default="A")
    ap.add_argument("--b-label", default="B")
    args = ap.parse_args()

    a = open(args.a, "rb").read()
    b = open(args.b, "rb").read()
    if len(a) != len(b):
        print(f"error: lengths differ ({len(a)} vs {len(b)})", file=sys.stderr)
        return 2

    regions = find_diff_regions(a, b, merge_gap=args.merge_gap)
    classes = load_classification(args.classification) if args.classification else []
    le = not args.be

    rows = []
    for start, end in regions:
        cls, conf = lookup_class(classes, start) if classes else ("unclassified", "low")
        a_repr = repr_region(a, start, end)
        b_repr = repr_region(b, start, end)
        a_interp = interpret_region(a, start, end, le)
        b_interp = interpret_region(b, start, end, le)
        rows.append({
            "start_hex": f"0x{start:05x}",
            "abs_hex": f"0x{args.base + start:08x}" if args.base else "",
            "end_hex": f"0x{end:05x}",
            "length": end - start,
            "class": cls,
            "confidence": conf,
            f"{args.a_label}_bytes": a_repr,
            f"{args.b_label}_bytes": b_repr,
            f"{args.a_label}_interp": a_interp,
            f"{args.b_label}_interp": b_interp,
        })

    if args.csv:
        with open(args.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else
                               ["start_hex", "abs_hex", "end_hex", "length",
                                "class", "confidence",
                                f"{args.a_label}_bytes", f"{args.b_label}_bytes",
                                f"{args.a_label}_interp", f"{args.b_label}_interp"])
            w.writeheader()
            for r in rows:
                w.writerow(r)

    if args.summary:
        write_summary(args.summary, rows, args, a, b)

    # Stats.
    total_bytes = sum(r["length"] for r in rows)
    print(f"{len(rows)} diff regions, {total_bytes:,} B changed "
          f"({100.0 * total_bytes / len(a):.2f}% of cal)", file=sys.stderr)
    by_class: dict[str, int] = {}
    for r in rows:
        by_class[r["class"]] = by_class.get(r["class"], 0) + r["length"]
    for cls in sorted(by_class, key=lambda c: -by_class[c]):
        pct = 100.0 * by_class[cls] / total_bytes if total_bytes else 0
        print(f"  {cls:20s} {by_class[cls]:6d} B  ({pct:5.1f}% of changes)",
              file=sys.stderr)

    return 0


def write_summary(path: str, rows: list[dict], args, a: bytes, b: bytes) -> None:
    total_bytes = sum(r["length"] for r in rows)
    by_class: dict[str, list[dict]] = {}
    for r in rows:
        by_class.setdefault(r["class"], []).append(r)

    with open(path, "w") as fh:
        fh.write(f"# Cal cross-diff: {args.a_label} vs {args.b_label}\n\n")
        fh.write(f"- `{args.a_label}`: `{args.a}` ({len(a):,} B)\n")
        fh.write(f"- `{args.b_label}`: `{args.b}` ({len(b):,} B)\n")
        fh.write(f"- merge-gap: {args.merge_gap} bytes of identical content bridged\n\n")

        fh.write(f"**{len(rows)} diff regions, {total_bytes:,} bytes changed "
                 f"({100.0 * total_bytes / len(a):.2f}% of cal).**\n\n")

        fh.write("## By underlying region class\n\n")
        fh.write("| Class | Regions | Bytes changed |\n")
        fh.write("|---|---:|---:|\n")
        for cls in sorted(by_class, key=lambda c: -sum(r["length"] for r in by_class[c])):
            b_changed = sum(r["length"] for r in by_class[cls])
            fh.write(f"| `{cls}` | {len(by_class[cls])} | {b_changed:,} |\n")
        fh.write("\n")

        # Show large changes first.
        rows_sorted = sorted(rows, key=lambda r: -r["length"])

        fh.write("## All diff regions (largest first)\n\n")
        fh.write(f"| Offset | Abs | Len | Class | {args.a_label} | {args.b_label} |\n")
        fh.write("|---|---|---:|---|---|---|\n")
        for r in rows_sorted:
            # Prefer typed interpretation when available.
            a_col = r.get(f"{args.a_label}_interp") or r[f"{args.a_label}_bytes"]
            b_col = r.get(f"{args.b_label}_interp") or r[f"{args.b_label}_bytes"]
            # Truncate for readability in md table.
            if len(a_col) > 80:
                a_col = a_col[:77] + "..."
            if len(b_col) > 80:
                b_col = b_col[:77] + "..."
            # Escape pipes.
            a_col = a_col.replace("|", "\\|")
            b_col = b_col.replace("|", "\\|")
            fh.write(f"| {r['start_hex']} | {r['abs_hex']} | {r['length']} | "
                     f"`{r['class']}` | {a_col} | {b_col} |\n")


if __name__ == "__main__":
    sys.exit(main())
