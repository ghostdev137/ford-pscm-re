#!/usr/bin/env python3
"""Rank plausible Ghidra processor languages against a raw firmware blob."""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


RESULT_RE = re.compile(
    r"RESULT total_fns=(?P<total>\d+) sampled=(?P<sampled>\d+) clean=(?P<clean>\d+) "
    r"warnings=(?P<warnings>\d+) baddata=(?P<baddata>\d+) failed=(?P<failed>\d+)"
)


@dataclass(frozen=True)
class Candidate:
    language: str
    align: int
    note: str


TRANSIT_SMART_CANDIDATES = [
    Candidate("v850e3:LE:32:default", 2, "Installed patched RH850/V850E3 path"),
    Candidate("v850:LE:32:default", 2, "Installed patched V850E2M path"),
    Candidate("V850:LE:32:default", 2, "Stock Ghidra V850 family"),
    Candidate("tricore:LE:32:tc172x", 2, "Infineon/Siemens TriCore TC17xx"),
    Candidate("tricore:LE:32:tc176x", 2, "Infineon/Siemens TriCore TC176x"),
    Candidate("tricore:LE:32:tc29x", 2, "Infineon/Siemens TriCore TC29x"),
    Candidate("PowerPC:BE:32:e500", 4, "Freescale/NXP e500 big-endian"),
    Candidate("PowerPC:LE:32:e500", 4, "Freescale/NXP e500 little-endian"),
    Candidate("ARM:LE:32:v7", 2, "Generic ARM/Thumb v7 little-endian"),
    Candidate("ARM:LE:32:Cortex", 2, "ARM Cortex/Thumb little-endian"),
    Candidate("SuperH4:LE:32:default", 2, "Renesas SuperH-4 little-endian"),
    Candidate("SuperH:BE:32:SH-2A", 2, "Renesas SuperH SH-2A big-endian"),
    Candidate("MIPS:LE:32:default", 4, "MIPS32 little-endian"),
    Candidate("MIPS:BE:32:default", 4, "MIPS32 big-endian"),
]

TRANSIT_SHORTLIST_CANDIDATES = [
    Candidate("v850e3:LE:32:default", 2, "Installed patched RH850/V850E3 path"),
    Candidate("v850:LE:32:default", 2, "Installed patched V850E2M path"),
    Candidate("V850:LE:32:default", 2, "Stock Ghidra V850 family"),
    Candidate("tricore:LE:32:tc172x", 2, "Infineon/Siemens TriCore TC17xx"),
    Candidate("PowerPC:BE:32:e500", 4, "Freescale/NXP e500 big-endian"),
    Candidate("ARM:LE:32:v7", 2, "Generic ARM/Thumb v7 little-endian"),
    Candidate("SuperH4:LE:32:default", 2, "Renesas SuperH-4 little-endian"),
    Candidate("MIPS:LE:32:default", 4, "MIPS32 little-endian"),
]


def default_analyze_headless() -> str:
    path = Path("/opt/homebrew/Cellar/ghidra/12.0.4/libexec/support/analyzeHeadless")
    return str(path)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def score(result: dict[str, int]) -> float:
    sampled = result["sampled"]
    clean_pct = (result["clean"] / sampled * 100.0) if sampled else 0.0
    coverage = min(result["total"], 1000) / 100.0
    penalty = (result["baddata"] * 0.1) + (result["failed"] * 2.0)
    return clean_pct * 20.0 + result["clean"] + coverage - penalty


def run_candidate(
    analyze_headless: str,
    blob: str,
    base_addr: str,
    start_addr: str,
    end_addr: str,
    script_path: str,
    project_root: str,
    candidate: Candidate,
    timeout: int,
) -> dict[str, object]:
    proj_dir = Path(project_root) / re.sub(r"[^A-Za-z0-9_.-]+", "_", candidate.language)
    proj_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        analyze_headless,
        str(proj_dir),
        "probe",
        "-import",
        blob,
        "-loader",
        "BinaryLoader",
        "-loader-baseAddr",
        base_addr,
        "-processor",
        candidate.language,
        "-scriptPath",
        script_path,
        "-postScript",
        "SeededLiftReport.java",
        start_addr,
        end_addr,
        str(candidate.align),
        "100",
        "40",
        "-deleteProject",
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = proc.stdout
    except subprocess.TimeoutExpired as exc:
        return {
            "language": candidate.language,
            "align": candidate.align,
            "note": candidate.note,
            "rc": "timeout",
            "error": f"timed out after {timeout}s",
            "tail": (exc.stdout or "")[-1200:] if isinstance(exc.stdout, str) else "",
        }

    match = RESULT_RE.search(output)
    if not match:
        tail = "\n".join(output.strip().splitlines()[-20:])
        return {
            "language": candidate.language,
            "align": candidate.align,
            "note": candidate.note,
            "rc": proc.returncode,
            "error": "no RESULT line",
            "tail": tail,
        }

    result = {k: int(v) for k, v in match.groupdict().items()}
    result.update(
        {
            "language": candidate.language,
            "align": candidate.align,
            "note": candidate.note,
            "rc": proc.returncode,
            "score": score(result),
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("blob", help="Raw firmware blob to import with BinaryLoader")
    parser.add_argument("--base-addr", default="0x01000000")
    parser.add_argument("--start-addr", default="0x01000000")
    parser.add_argument("--end-addr", default="0x010FFFEF")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--analyze-headless", default=default_analyze_headless())
    parser.add_argument(
        "--preset",
        choices=("transit-shortlist", "transit-smart"),
        default="transit-shortlist",
        help="Candidate family set to probe",
    )
    parser.add_argument(
        "--script-path",
        default=str(repo_root() / "tools" / "scripts"),
        help="Ghidra script path containing SeededLiftReport.java",
    )
    args = parser.parse_args()

    blob = os.path.abspath(args.blob)
    analyze_headless = os.path.abspath(args.analyze_headless)
    script_path = os.path.abspath(args.script_path)

    if not os.path.exists(blob):
        raise SystemExit(f"blob not found: {blob}")
    if not os.path.exists(analyze_headless):
        raise SystemExit(f"analyzeHeadless not found: {analyze_headless}")
    if not os.path.isdir(script_path):
        raise SystemExit(f"script path not found: {script_path}")

    candidates = (
        TRANSIT_SHORTLIST_CANDIDATES
        if args.preset == "transit-shortlist"
        else TRANSIT_SMART_CANDIDATES
    )

    with tempfile.TemporaryDirectory(prefix="ghidra-probe-") as project_root:
        results = []
        for candidate in candidates:
            print(f"== {candidate.language} ==", flush=True)
            print(f"note: {candidate.note}", flush=True)
            print(
                "cmd: "
                + shlex.join(
                    [
                        analyze_headless,
                        os.path.join(project_root, "probe"),
                        "probe",
                        "-import",
                        blob,
                        "-loader",
                        "BinaryLoader",
                        "-loader-baseAddr",
                        args.base_addr,
                        "-processor",
                        candidate.language,
                    ]
                )
            ,
                flush=True,
            )
            result = run_candidate(
                analyze_headless=analyze_headless,
                blob=blob,
                base_addr=args.base_addr,
                start_addr=args.start_addr,
                end_addr=args.end_addr,
                script_path=script_path,
                project_root=project_root,
                candidate=candidate,
                timeout=args.timeout,
            )
            results.append(result)
            if "score" in result:
                sampled = result["sampled"]
                clean_pct = (result["clean"] / sampled * 100.0) if sampled else 0.0
                print(
                    f"RESULT total={result['total']} sampled={sampled} clean={result['clean']} "
                    f"warnings={result['warnings']} baddata={result['baddata']} "
                    f"failed={result['failed']} clean_pct={clean_pct:.1f} score={result['score']:.1f}",
                    flush=True,
                )
            else:
                print(f"ERROR rc={result['rc']} {result['error']}", flush=True)
                tail = result.get("tail")
                if tail:
                    print(tail, flush=True)
            print(flush=True)

    ranked = [r for r in results if "score" in r]
    ranked.sort(key=lambda r: (r["score"], r["clean"], r["total"]), reverse=True)

    print("== ranked ==")
    for idx, result in enumerate(ranked, start=1):
        sampled = result["sampled"]
        clean_pct = (result["clean"] / sampled * 100.0) if sampled else 0.0
        print(
            f"{idx:02d}. {result['language']:<24} total={result['total']:<5} "
            f"sampled={sampled:<3} clean={result['clean']:<3} warnings={result['warnings']:<3} "
            f"baddata={result['baddata']:<3} failed={result['failed']:<3} "
            f"clean_pct={clean_pct:5.1f} score={result['score']:6.1f}  {result['note']}"
        )

    failed = [r for r in results if "score" not in r]
    if failed:
        print("\n== failed ==")
        for result in failed:
            print(f"- {result['language']}: rc={result['rc']} {result['error']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
