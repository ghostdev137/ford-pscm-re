#!/usr/bin/env python3
"""
F-150 LKA driver-override harness.

Seeds the interaction-channel / angle / status RAM globals, calls
FUN_101a3b84 (the override state machine) with controlled inputs, reads
the resulting state byte at fef21a78. Purpose: validate the cal-threshold
hypotheses from analysis/f150/driver_override_findings.md.
"""

from __future__ import annotations
import os
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VENDOR = REPO / "vendor" / "unicorn-pr1918"
os.environ["LIBUNICORN_PATH"] = str(VENDOR / "build_python")
sys.path.insert(0, str(VENDOR / "bindings" / "python"))

import unicorn
from unicorn import Uc, UC_ARCH_RH850, UcError, UC_PROT_ALL, UC_HOOK_CODE, UC_HOOK_BLOCK, UC_HOOK_MEM_UNMAPPED
from unicorn.rh850_const import (
    UC_RH850_REG_PC, UC_RH850_REG_SP, UC_RH850_REG_LP, UC_RH850_REG_EP,
    UC_RH850_REG_R4, UC_RH850_REG_R6, UC_RH850_REG_R7, UC_RH850_REG_R8,
    UC_RH850_REG_R10, UC_RH850_REG_R11, UC_RH850_REG_R29,
    UC_RH850_REG_CTBP, UC_RH850_REG_PSW,
)

ELF_PATH = REPO / "firmware" / "F150_2021_Lariat_BlueCruise" / "f150_pscm_full.elf"

FUN_OVERRIDE   = 0x101a3b84  # main LKA controller / override state machine
FUN_INPUT_SNAP = 0x101a4d56  # loads inputs into fef21a6e/70/72/77
FUN_OUTPUT_WR  = 0x101a4e4a  # writes final fef21a78

# RAM regions we need to be writable
RAM_BASE  = 0xFEF00000
RAM_SIZE  = 0x00100000   # 1 MiB covers fef2xxxx + fef00000 peripherals likely read
STACK_BASE = 0xFEB00000
STACK_SIZE = 0x10000
SENTINEL  = 0xDEADBEE0   # return target; we trap on fetch here

# RAM globals (from analysis/f150/driver_override_findings.md)
ADDR_ANGLE    = 0xFEF21A6E  # _DAT_fef21a6e, s16 angle command clamped ±0x2800
ADDR_CHAN_A   = 0xFEF2197A  # upstream interaction-channel byte (maps into fef21a70 via FUN_10096f38)
ADDR_CHAN_B   = 0xFEF2197C  # upstream interaction-channel byte (maps into fef21a72 via FUN_10096f40)
ADDR_FEF21A70 = 0xFEF21A70  # processed chan (u16)
ADDR_FEF21A72 = 0xFEF21A72  # processed chan (u16)
ADDR_FEF21A74 = 0xFEF21A74  # aux state byte
ADDR_FEF21A75 = 0xFEF21A75  # aux state byte
ADDR_FEF21A77 = 0xFEF21A77  # mode/availability status byte (3=permit, 5=deny)
ADDR_FEF21A78 = 0xFEF21A78  # final LKA output (written by FUN_101a4e4a)

# Cal RAM-mirror threshold addresses (0xFEF263xx region is threshold family)
ADDR_FEF26382 = 0xFEF26382  # angle quiet-gate threshold
ADDR_FEF263D0 = 0xFEF263D0  # band low
ADDR_FEF263D2 = 0xFEF263D2  # band high
ADDR_FEF263DA = 0xFEF263DA  # persistence threshold 1
ADDR_FEF263DC = 0xFEF263DC  # persistence threshold 2
ADDR_FEF263DE = 0xFEF263DE  # earliest shared threshold (quiet gate)
ADDR_FEF26405 = 0xFEF26405
ADDR_FEF26406 = 0xFEF26406  # rate-detector small-change threshold
ADDR_FEF2622D = 0xFEF2622D  # cal byte read by 0x101A2100
ADDR_FEF2622E = 0xFEF2622E  # cal byte read by 0x101A210C


def load_elf_segments(uc: Uc) -> None:
    """Parse the F-150 ELF and map PT_LOAD segments. F-150 has 4 segments
    whose page-aligned ranges overlap, so we compute the union and map
    one contiguous region, then write each segment's bytes into it."""
    data = ELF_PATH.read_bytes()
    e_phoff = struct.unpack_from("<I", data, 0x1c)[0]
    e_phentsize = struct.unpack_from("<H", data, 0x2a)[0]
    e_phnum = struct.unpack_from("<H", data, 0x2c)[0]
    segs = []
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type, p_off, p_vaddr, p_paddr, p_fsz, p_msz, p_flg, p_aln = struct.unpack_from("<IIIIIIII", data, off)
        if p_type == 1:
            segs.append((p_vaddr, p_off, p_fsz, p_msz))
    lo = min(v for v,_,_,_ in segs) & ~0xFFF
    hi = max((v + m + 0xFFF) & ~0xFFF for v,_,_,m in segs)
    uc.mem_map(lo, hi - lo, UC_PROT_ALL)
    print(f"  mapped strategy+cal 0x{lo:08x}..0x{hi:08x}")
    for vaddr, foff, fsz, _msz in segs:
        uc.mem_write(vaddr, data[foff:foff + fsz])
        print(f"    wrote 0x{vaddr:08x} fsz=0x{fsz:x}")


def setup_machine() -> Uc:
    uc = Uc(UC_ARCH_RH850, 0)
    print("loading ELF...")
    load_elf_segments(uc)
    # RAM region (overlaps or is disjoint from ELF maps; ELF has two load
    # segments at 0x101bfc00 and 0x101ffc00 that are RAM-init regions, but
    # general fef2xxxx is not in the ELF).
    uc.mem_map(RAM_BASE, RAM_SIZE, UC_PROT_ALL)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_ALL)
    # Sentinel page for return trap
    uc.mem_map(SENTINEL & ~0xFFF, 0x1000, UC_PROT_ALL)
    return uc


def write_u8(uc, addr, v):  uc.mem_write(addr, bytes([v & 0xFF]))
def write_u16(uc, addr, v): uc.mem_write(addr, struct.pack("<H", v & 0xFFFF))
def write_s16(uc, addr, v): uc.mem_write(addr, struct.pack("<h", v))
def write_u32(uc, addr, v): uc.mem_write(addr, struct.pack("<I", v & 0xFFFFFFFF))
def read_u8(uc, addr):   return uc.mem_read(addr, 1)[0]
def read_u16(uc, addr):  return struct.unpack("<H", uc.mem_read(addr, 2))[0]
def read_s16(uc, addr):  return struct.unpack("<h", uc.mem_read(addr, 2))[0]


def seed_defaults(uc: Uc) -> None:
    """Put plausible stock defaults into RAM before the run."""
    # Threshold family — use rough guesses; they can be varied per-run
    write_u16(uc, ADDR_FEF263DE, 0x0040)  # earliest shared threshold
    write_u16(uc, ADDR_FEF263D0, 0x0020)
    write_u16(uc, ADDR_FEF263D2, 0x0080)
    write_u16(uc, ADDR_FEF263DA, 0x0010)
    write_u16(uc, ADDR_FEF263DC, 0x0020)
    write_u8 (uc, ADDR_FEF26405, 0x04)
    write_u8 (uc, ADDR_FEF26406, 0x04)
    write_u16(uc, ADDR_FEF26382, 0x0400)  # angle quiet-gate (raw int units)
    write_u8 (uc, ADDR_FEF2622D, 0x00)
    write_u8 (uc, ADDR_FEF2622E, 0x00)


def call_function(uc: Uc, entry: int, arg0: int = 0, *, max_insns: int = 200_000, trace: bool = False) -> dict:
    """Call `entry` as a leaf function, return r10 (result) + final state."""
    sp = STACK_BASE + STACK_SIZE - 0x100
    # Zero the stack so FP-relative locals start clean
    uc.mem_write(sp - 0x200, b"\x00" * 0x200)
    uc.reg_write(UC_RH850_REG_SP, sp)
    uc.reg_write(UC_RH850_REG_LP, SENTINEL)
    uc.reg_write(UC_RH850_REG_R6, arg0)
    # Fresh r29 workspace (FP) — give it room for the frame
    uc.reg_write(UC_RH850_REG_R29, sp - 0x100)
    # GP / EP guesses (if wrong, gp-relative reads will crash; we map RAM wide)
    uc.reg_write(UC_RH850_REG_R4, 0xFEF00000)  # gp guess
    uc.reg_write(UC_RH850_REG_EP, 0xFEF20000)  # ep guess
    uc.reg_write(UC_RH850_REG_CTBP, 0x0100220C)
    uc.reg_write(UC_RH850_REG_PSW, 0x00000020)

    state = {"blocks": 0, "trapped": False, "last_pc": 0, "reason": ""}

    def block_hook(_uc, addr, size, _ud):
        state["blocks"] += 1
        state["last_pc"] = addr
        if addr == SENTINEL:
            state["reason"] = "returned_to_sentinel"
            state["trapped"] = True
            _uc.emu_stop()
            return
        if state["blocks"] > max_insns // 4:
            state["reason"] = f"block_limit hit at 0x{addr:08x}"
            state["trapped"] = True
            _uc.emu_stop()
            return
        if trace and state["blocks"] <= 64:
            print(f"    block {state['blocks']:4d}  pc=0x{addr:08x} size={size}")

    def mem_unmapped(_uc, access, addr, size, value, _ud):
        state["reason"] = f"unmapped access={access} addr=0x{addr:08x} size={size} pc=0x{state['last_pc']:08x}"
        state["trapped"] = True
        return False  # let Unicorn raise

    h1 = uc.hook_add(UC_HOOK_BLOCK, block_hook)
    h2 = uc.hook_add(UC_HOOK_MEM_UNMAPPED, mem_unmapped)
    try:
        uc.emu_start(entry, SENTINEL, count=max_insns)
    except UcError as e:
        if not state["reason"]:
            state["reason"] = f"UcError: {e}"
        state["trapped"] = True
    finally:
        uc.hook_del(h1)
        uc.hook_del(h2)

    state["r10"] = uc.reg_read(UC_RH850_REG_R10)
    state["pc"]  = uc.reg_read(UC_RH850_REG_PC)
    return state


def run_single(angle: int, chan_a: int, chan_b: int, status: int, *, trace=False):
    uc = setup_machine()
    seed_defaults(uc)
    write_s16(uc, ADDR_ANGLE, angle)
    write_u16(uc, ADDR_FEF21A70, chan_a)
    write_u16(uc, ADDR_FEF21A72, chan_b)
    write_u8 (uc, ADDR_FEF21A77, status)
    write_u8 (uc, ADDR_FEF21A74, 0)
    write_u8 (uc, ADDR_FEF21A75, 0)
    write_u16(uc, ADDR_FEF21A78, 0xFFFF)  # sentinel for "was output written?"

    print(f"\n== angle={angle:+d}  chan_a=0x{chan_a:04x}  chan_b=0x{chan_b:04x}  status={status} ==")
    result = call_function(uc, FUN_OVERRIDE, arg0=0, trace=trace, max_insns=50_000)
    print(f"  blocks={result['blocks']}  reason={result['reason']}  last_pc=0x{result['last_pc']:08x}")
    print(f"  r10=0x{result['r10']:08x}")
    print(f"  post-state: fef21a78=0x{read_u16(uc, ADDR_FEF21A78):04x} "
          f"fef21a74=0x{read_u8(uc, ADDR_FEF21A74):02x} "
          f"fef21a75=0x{read_u8(uc, ADDR_FEF21A75):02x}")
    return result


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--angle", type=lambda s: int(s, 0), default=0x100)
    ap.add_argument("--chan-a", type=lambda s: int(s, 0), default=0x0020)
    ap.add_argument("--chan-b", type=lambda s: int(s, 0), default=0x0020)
    ap.add_argument("--status", type=lambda s: int(s, 0), default=3)
    args = ap.parse_args()
    run_single(args.angle, args.chan_a, args.chan_b, args.status, trace=args.trace)
