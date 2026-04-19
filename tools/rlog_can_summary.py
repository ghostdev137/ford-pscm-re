#!/usr/bin/env python3
"""
Summarize selected CAN frames from comma rlogs using openpilot's logreader and
opendbc decoder.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def parse_int(text: str) -> int:
    return int(text, 0)


def import_openpilot(openpilot_root: Path) -> Tuple[object, object]:
    sys.path.insert(0, str(openpilot_root))
    sys.path.insert(0, str(openpilot_root / "opendbc_repo"))
    from openpilot.tools.lib.logreader import LogReader  # type: ignore
    from opendbc.can import CANParser  # type: ignore

    return LogReader, CANParser


def ensure_openpilot_python(openpilot_root: Path) -> None:
    try:
        import capnp  # noqa: F401
        import zstandard  # noqa: F401
    except ModuleNotFoundError:
        venv_python = openpilot_root / ".venv" / "bin" / "python"
        if Path(sys.executable) != venv_python and venv_python.exists():
            os.execv(str(venv_python), [str(venv_python), *sys.argv])
        raise


def infer_message_name(can_id: int) -> str:
    names = {
        0x082: "EPAS_INFO",
        0x07E: "SteeringPinion_Data",
        0x091: "Yaw_Data_FD1",
        0x213: "DesiredTorqBrk",
        0x3CA: "Lane_Assist_Data1",
        0x415: "BrakeSysFeatures",
    }
    return names.get(can_id, hex(can_id))


def iter_paths(paths: Iterable[str]) -> Iterable[Path]:
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for child in sorted(p.glob("rlog*.zst")):
                yield child
        else:
            yield p


def summarize_one(
    path: Path,
    ids: List[int],
    limit: int,
    LogReader: object,
    CANParser: object,
) -> None:
    print(f"\n== {path} ==")
    seen: Dict[int, Dict[int, Counter[bytes]]] = defaultdict(lambda: defaultdict(Counter))
    first_ts: Dict[Tuple[int, int, bytes], int] = {}
    counts: Dict[int, Counter[int]] = defaultdict(Counter)

    for msg in LogReader(str(path)):
        if msg.which() != "can":
            continue
        t = msg.logMonoTime
        for c in msg.can:
            if c.address not in ids:
                continue
            dat = bytes(c.dat)
            seen[c.address][c.src][dat] += 1
            counts[c.address][c.src] += 1
            first_ts.setdefault((c.address, c.src, dat), t)

    for can_id in ids:
        msg_name = infer_message_name(can_id)
        if can_id not in seen:
            continue
        print(f"\n  {msg_name} ({can_id:#05x})")
        for src in sorted(seen[can_id]):
            total = counts[can_id][src]
            unique = len(seen[can_id][src])
            print(f"    src {src}: total={total} unique={unique}")
            parser = CANParser("ford_lincoln_base_pt", [(msg_name, 1)], src)
            for dat, count in seen[can_id][src].most_common(limit):
                parser.update([(first_ts[(can_id, src, dat)], [(can_id, dat, src)])])
                print(f"      {count:5d} {dat.hex()} {dict(parser.vl[msg_name])}")


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("paths", nargs="+", help="rlog file(s) or directory containing rlogs")
    p.add_argument(
        "--openpilot-root",
        type=Path,
        default=Path("/Users/rossfisher/openpilot"),
        help="Path to the openpilot checkout with .venv-ready dependencies",
    )
    p.add_argument(
        "--id",
        action="append",
        type=parse_int,
        default=[],
        help="CAN ID to summarize, e.g. --id 0x3CA",
    )
    p.add_argument("--top", type=int, default=6, help="Payloads to print per src")
    return p


def main() -> int:
    args = build_argparser().parse_args()
    ids = args.id or [0x3CA, 0x213, 0x082, 0x07E, 0x091, 0x415]
    ensure_openpilot_python(args.openpilot_root)
    LogReader, CANParser = import_openpilot(args.openpilot_root)

    for path in iter_paths(args.paths):
        summarize_one(path, ids, args.top, LogReader, CANParser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
