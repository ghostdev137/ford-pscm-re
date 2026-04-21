"""Prove the override-threshold hypothesis:
raising _DAT_fef263de should shift the channel quiet-gate boundary.
"""
import os, sys, struct
sys.path.insert(0, "/Users/rossfisher/ford-pscm-re/tools")
from unicorn_f150_override_harness import (
    setup_machine, seed_defaults, call_function, FUN_OVERRIDE,
    write_u8, write_u16, write_s16, read_u8,
    ADDR_ANGLE, ADDR_FEF21A70, ADDR_FEF21A72, ADDR_FEF21A74,
    ADDR_FEF21A75, ADDR_FEF21A77, ADDR_FEF21A78,
    ADDR_FEF263DE, ADDR_FEF26382,
)


def find_boundary(threshold_de, fixed_angle=0):
    """Sweep chan_a and find the smallest value at which fef21a64 flips."""
    last_flat = None
    for chan in range(0, 0x400, 0x10):
        uc = setup_machine()
        seed_defaults(uc)
        write_u16(uc, ADDR_FEF263DE, threshold_de)
        write_s16(uc, ADDR_ANGLE, fixed_angle)
        write_u16(uc, ADDR_FEF21A70, chan)
        write_u16(uc, ADDR_FEF21A72, 0)
        write_u8(uc, ADDR_FEF21A77, 3)
        write_u8(uc, 0xFEF21A64, 0)
        write_u8(uc, 0xFEF21A65, 0)
        call_function(uc, FUN_OVERRIDE, arg0=0, max_insns=200_000)
        flag = read_u8(uc, 0xFEF21A64)
        if flag == 1:
            return chan, last_flat
        last_flat = chan
    return None, last_flat


print("Boundary-finding sweep — lowest chan_a at which quiet-gate fails:\n")
print(f"{'threshold_de':>12s}  {'first_flip':>12s}  {'last_quiet':>12s}")
for th in (0x10, 0x20, 0x40, 0x80, 0x100, 0x200):
    flip, last_quiet = find_boundary(th)
    print(f"  0x{th:04x}       {f'0x{flip:04x}' if flip else 'none':>12s}  {f'0x{last_quiet:04x}' if last_quiet is not None else 'n/a':>12s}")
