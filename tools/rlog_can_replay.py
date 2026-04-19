#!/usr/bin/env python3
"""
Extract CAN mailbox snapshots from comma rlogs for Unicorn replay.

Each output line is a JSON object keyed by CAN ID string, e.g.:
{"0x3CA":"837e686d00000000","0x213":"ffff000400020440"}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def parse_int(text: str) -> int:
    return int(text, 0)


def import_openpilot(openpilot_root: Path) -> object:
    sys.path.insert(0, str(openpilot_root))
    from openpilot.tools.lib.logreader import LogReader  # type: ignore

    return LogReader


def ensure_openpilot_python(openpilot_root: Path) -> None:
    try:
        import capnp  # noqa: F401
        import zstandard  # noqa: F401
    except ModuleNotFoundError:
        venv_python = openpilot_root / ".venv" / "bin" / "python"
        if Path(sys.executable) != venv_python and venv_python.exists():
            os.execv(str(venv_python), [str(venv_python), *sys.argv])
        raise


def iter_paths(paths: Iterable[str]) -> Iterable[Path]:
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            for child in sorted(path.glob("rlog*.zst")):
                yield child
        else:
            yield path


def parse_preferred_src(spec: str) -> Tuple[int, int]:
    can_id_text, src_text = spec.split("=", 1)
    return parse_int(can_id_text.strip()), parse_int(src_text.strip())


def choose_source(can_id: int, src: int, preferred: Dict[int, int]) -> bool:
    preferred_src = preferred.get(can_id)
    if preferred_src is None:
        return True
    return src == preferred_src


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("paths", nargs="+", help="rlog file(s) or directories")
    p.add_argument(
        "--openpilot-root",
        type=Path,
        default=Path("/Users/rossfisher/openpilot"),
        help="Path to openpilot checkout with a working .venv",
    )
    p.add_argument(
        "--id",
        action="append",
        type=parse_int,
        default=[],
        help="CAN ID to track, e.g. --id 0x3CA",
    )
    p.add_argument(
        "--prefer-src",
        action="append",
        default=[],
        help="Per-ID source selector, e.g. --prefer-src 0x3CA=128",
    )
    p.add_argument(
        "--emit-on",
        action="append",
        type=parse_int,
        default=[],
        help="Only emit a snapshot when one of these IDs changes",
    )
    p.add_argument(
        "--require-all",
        action="store_true",
        help="Do not emit until every tracked ID has been observed at least once",
    )
    p.add_argument("--limit", type=int, default=0, help="Optional cap on emitted snapshots")
    p.add_argument("--output", type=Path, help="Write JSONL to this file instead of stdout")
    return p


def main() -> int:
    args = build_argparser().parse_args()
    ids = args.id or [0x3CA, 0x213, 0x415, 0x091]
    emit_on = set(args.emit_on or [0x3CA, 0x213])
    preferred_src = dict(parse_preferred_src(spec) for spec in args.prefer_src)

    ensure_openpilot_python(args.openpilot_root)
    LogReader = import_openpilot(args.openpilot_root)

    last_by_id: Dict[int, bytes] = {}
    emitted = 0
    lines: List[str] = []

    for path in iter_paths(args.paths):
        for msg in LogReader(str(path)):
            if msg.which() != "can":
                continue
            for can_msg in msg.can:
                if can_msg.address not in ids:
                    continue
                if not choose_source(can_msg.address, can_msg.src, preferred_src):
                    continue

                payload = bytes(can_msg.dat)
                prev = last_by_id.get(can_msg.address)
                if prev == payload:
                    continue

                last_by_id[can_msg.address] = payload
                if can_msg.address not in emit_on:
                    continue
                if args.require_all and any(can_id not in last_by_id for can_id in ids):
                    continue

                snapshot = {f"{can_id:#05x}": last_by_id[can_id].hex() for can_id in ids if can_id in last_by_id}
                line = json.dumps(snapshot, sort_keys=True)
                lines.append(line)
                emitted += 1
                if args.limit and emitted >= args.limit:
                    break
            if args.limit and emitted >= args.limit:
                break
        if args.limit and emitted >= args.limit:
            break

    if args.output:
        args.output.write_text("\n".join(lines) + ("\n" if lines else ""))
    else:
        for line in lines:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
