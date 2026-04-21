"""Sweep FUN_101a3b84 inputs and diff the LKA workspace after each run."""
import os, sys, struct
sys.path.insert(0, "/Users/rossfisher/ford-pscm-re/tools")
from unicorn_f150_override_harness import (
    setup_machine, seed_defaults, call_function, FUN_OVERRIDE,
    write_u8, write_u16, write_s16, read_u8, read_u16,
    ADDR_ANGLE, ADDR_FEF21A70, ADDR_FEF21A72, ADDR_FEF21A74,
    ADDR_FEF21A75, ADDR_FEF21A77, ADDR_FEF21A78,
)

# Watch region: the entire LKA workspace 0xFEF21A60..0xFEF21A80
WATCH_BASE = 0xFEF21A60
WATCH_SIZE = 0x20


def snapshot(uc) -> bytes:
    return bytes(uc.mem_read(WATCH_BASE, WATCH_SIZE))


def diff_snap(a: bytes, b: bytes) -> list:
    return [(i, a[i], b[i]) for i in range(len(a)) if a[i] != b[i]]


def run(label, angle, chan_a, chan_b, status, prev_a=0, prev_b=0):
    uc = setup_machine()
    seed_defaults(uc)
    write_s16(uc, ADDR_ANGLE, angle)
    write_u16(uc, ADDR_FEF21A70, chan_a)
    write_u16(uc, ADDR_FEF21A72, chan_b)
    write_u8(uc, ADDR_FEF21A77, status)
    write_u8(uc, ADDR_FEF21A74, 0)
    write_u8(uc, ADDR_FEF21A75, 0)
    # Previous values live in the local struct at r29+0x5e / +0x60;
    # our harness puts r29 at sp-0x100, so pre-seed those slots too.
    # sp = STACK_BASE+STACK_SIZE-0x100 = 0xFEB10000 - 0x100 = 0xFEB0FF00
    # r29 = sp - 0x100 = 0xFEB0FE00; +0x5e = 0xFEB0FE5E, +0x60 = 0xFEB0FE60
    uc.mem_write(0xFEB0FE5E, struct.pack("<H", prev_a))
    uc.mem_write(0xFEB0FE60, struct.pack("<H", prev_b))
    write_u16(uc, ADDR_FEF21A78, 0xFFFF)  # "not written" sentinel

    pre = snapshot(uc)
    result = call_function(uc, FUN_OVERRIDE, arg0=0, max_insns=200_000)
    post = snapshot(uc)

    changes = diff_snap(pre, post)
    r10 = result["r10"]
    reason = result["reason"] or "no-trap"
    change_str = " ".join(f"[{WATCH_BASE+i:#x}]:{a:02x}->{b:02x}" for i, a, b in changes) or "(no change)"
    print(f"{label:40s}  blocks={result['blocks']:4d}  r10=0x{r10:08x}  {reason}")
    print(f"    changes: {change_str}")
    return changes, r10


print("\n=== quiet-path baseline ===")
run("angle=0  chan=0   status=3 (full quiet)", 0, 0, 0, 3)
run("angle=0  chan=0   status=5 (deny stat)",  0, 0, 0, 5)

print("\n=== angle sweep (stock thresholds, chan=0) ===")
for a in (0, 0x100, 0x400, 0x800, 0x1000, 0x2000, 0x2800):
    run(f"angle={a:#06x}  chan=0  status=3", a, 0, 0, 3)

print("\n=== chan-A sweep (angle=0, chan_b=0) ===")
for c in (0x00, 0x20, 0x40, 0x80, 0x100, 0x200, 0x400, 0x1000):
    run(f"angle=0  chan_a={c:#06x}  status=3", 0, c, 0, 3)

print("\n=== chan-B sweep (angle=0, chan_a=0) ===")
for c in (0x00, 0x20, 0x40, 0x80, 0x100, 0x200, 0x400, 0x1000):
    run(f"angle=0  chan_a=0  chan_b={c:#06x}  status=3", 0, 0, c, 3)

print("\n=== both channels high — should escalate ===")
for c in (0x00, 0x40, 0x100, 0x400, 0x1000):
    run(f"angle=0  chan_a=chan_b={c:#06x}  status=3", 0, c, c, 3)

print("\n=== with rate (prev vs current differ) ===")
run("chan=0x100 prev=0  (big positive rate)", 0, 0x100, 0x100, 3, prev_a=0, prev_b=0)
run("chan=0x100 prev=0x100  (no rate)",       0, 0x100, 0x100, 3, prev_a=0x100, prev_b=0x100)
