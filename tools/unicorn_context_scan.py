#!/usr/bin/env python3
"""
Brute-force a small caller-state search for Transit RH850 Unicorn handler entry.

Each candidate runs in a subprocess so native Unicorn crashes do not kill the
scanner. Results are summarized to stdout and optionally written as JSON.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


REPO = Path(__file__).resolve().parent.parent
PYTHON = REPO / ".venv" / "bin" / "python"
HARNESS = REPO / "tools" / "unicorn_transit_harness.py"

DEFAULT_MAILBOXES = [
    "0x3CA=837e686d00000000",
    "0x213=ffff000400020440",
    "0x415=0000f4ef0ffe0ffe",
    "0x091=7ef47ebb202ef000",
]

PAYLOADS = {
    "lka": "837e686d00000000",
    "destorq": "ffff000400020440",
}


def parse_int(text: str) -> int:
    return int(text, 0)


def parse_csv_ints(values: str) -> List[int]:
    return [parse_int(part.strip()) for part in values.split(",") if part.strip()]


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--variant", default="AM")
    p.add_argument("--start", choices=("lka", "destorq"), help="Named start alias")
    p.add_argument("--start-addr", help="Absolute start address override, e.g. 0x0108F494")
    p.add_argument("--payload-hex", help="Explicit payload override for --start-addr mode")
    p.add_argument("--count", type=int, default=128)
    p.add_argument("--r14", default="0x4000e4ce,0x4000e4cc,0x4000e4d0,0x0")
    p.add_argument("--r11", default="0x0")
    p.add_argument("--r29", default="0x0,0x3")
    p.add_argument("--lp", default="0x0,0xfffffff0")
    p.add_argument(
        "--grid-reg",
        action="append",
        default=[],
        help="Extra grid register, e.g. --grid-reg gp=0x0,0x40010100",
    )
    p.add_argument("--output", type=Path, help="Optional JSON result path")
    return p


def extract_summary(stdout: str) -> Dict[str, object]:
    pc_match = re.search(r"^  pc\s+(0x[0-9a-fA-F]+)$", stdout, re.MULTILINE)
    err_match = re.search(r"emulation stopped with Unicorn error: (.+)", stdout)
    completed = "emulation completed without Unicorn exception" in stdout
    crashed = "mapped strategy" in stdout and "registers:" not in stdout and not completed and not err_match
    unmapped = stdout.count("unmapped access type=")
    watch_reads = stdout.count("watch reads:")
    watch_writes = stdout.count("watch writes:")
    ram_writes = stdout.count("ram writes:")
    return {
        "final_pc": pc_match.group(1) if pc_match else None,
        "error": err_match.group(1) if err_match else None,
        "completed": completed,
        "native_crash_like": crashed,
        "unmapped_count": unmapped,
        "watch_reads_sections": watch_reads,
        "watch_writes_sections": watch_writes,
        "ram_writes_sections": ram_writes,
    }


def main() -> int:
    args = build_argparser().parse_args()
    if not args.start and not args.start_addr:
        raise SystemExit("pass --start or --start-addr")
    payload = args.payload_hex or (PAYLOADS[args.start] if args.start else None)
    if not payload:
        raise SystemExit("no payload available; pass --payload-hex")

    r14_vals = parse_csv_ints(args.r14)
    r11_vals = parse_csv_ints(args.r11)
    r29_vals = parse_csv_ints(args.r29)
    lp_vals = parse_csv_ints(args.lp)
    extra_grids: List[tuple[str, List[int]]] = []
    for spec in args.grid_reg:
        name, values = spec.split("=", 1)
        extra_grids.append((name.strip(), parse_csv_ints(values)))

    start_arg = args.start_addr or args.start

    results: List[Dict[str, object]] = []
    value_lists = [r14_vals, r11_vals, r29_vals, lp_vals] + [vals for _, vals in extra_grids]
    for combo in itertools.product(*value_lists):
        r14, r11, r29, lp = combo[:4]
        extra_vals = combo[4:]
        cmd = [
            str(PYTHON),
            str(HARNESS),
            "--variant", args.variant,
            "--start", start_arg,
            "--message-mode", "raw",
            "--payload-hex", payload,
            "--count", str(args.count),
            "--autopage",
            "--reg", f"r14={r14:#x}",
            "--reg", f"r11={r11:#x}",
            "--reg", f"r29={r29:#x}",
            "--lp", f"{lp:#x}",
        ]
        for (name, _), value in zip(extra_grids, extra_vals):
            cmd.extend(["--reg", f"{name}={value:#x}"])
        for mailbox in DEFAULT_MAILBOXES:
            cmd.extend(["--mailbox", mailbox])

        proc = subprocess.run(
            cmd,
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        summary = extract_summary(proc.stdout)
        row: Dict[str, object] = {
            "start": start_arg,
            "r14": f"{r14:#x}",
            "r11": f"{r11:#x}",
            "r29": f"{r29:#x}",
            "lp": f"{lp:#x}",
            "returncode": proc.returncode,
            **summary,
        }
        for (name, _), value in zip(extra_grids, extra_vals):
            row[name] = f"{value:#x}"
        results.append(row)
        brief = {
            "start": row["start"],
            "r14": row["r14"],
            "r11": row["r11"],
            "r29": row["r29"],
            "lp": row["lp"],
            "rc": proc.returncode,
            "pc": row["final_pc"],
            "err": row["error"],
            "crash": row["native_crash_like"],
            "unmapped": row["unmapped_count"],
        }
        for name, _ in extra_grids:
            brief[name] = row[name]
        print(json.dumps(brief, sort_keys=True))

    if args.output:
        args.output.write_text(json.dumps(results, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
