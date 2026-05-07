#!/usr/bin/env python3
"""
F-150 LCA cal-byte consumer attribution harness.

Goal: find which strategy function reads the bell-curve authority profile
at cal+0x1620..0x1680. Static xref is blocked by AUTOSAR Rte_Prm
indirection. Solution: emulate the LCA controller chain with sentinel
bytes overlaid onto the cal region; log every cal-region read with PC
so we know who reads what.

Targets the LCA chain (not the LKA override path):
  FUN_101a392a -> FUN_10186afa -> FUN_101aa05e -> FUN_101ab934 -> FUN_101ad86c

The LCA-local namespaces are fef238**/239**/23b**/23c** with c0/c1/c2/c3
path coefficients written into fef23b7c / fef23b70 / fef23b74 / fef23b78.

We call FUN_101ab934 (the main LCA controller) directly, after seeding
the path coefficients and a v-ego analog.
"""

from __future__ import annotations
import os
import struct
import sys
from pathlib import Path
from collections import defaultdict, Counter

REPO = Path(__file__).resolve().parent.parent
VENDOR = REPO / "vendor" / "unicorn-pr1918"
os.environ["LIBUNICORN_PATH"] = str(VENDOR / "build_python")
sys.path.insert(0, str(VENDOR / "bindings" / "python"))

import unicorn
from unicorn import (
    Uc, UC_ARCH_RH850, UcError, UC_PROT_ALL,
    UC_HOOK_CODE, UC_HOOK_BLOCK, UC_HOOK_MEM_UNMAPPED, UC_HOOK_MEM_READ,
)
from unicorn.rh850_const import (
    UC_RH850_REG_PC, UC_RH850_REG_SP, UC_RH850_REG_LP, UC_RH850_REG_EP,
    UC_RH850_REG_R4, UC_RH850_REG_R6, UC_RH850_REG_R7, UC_RH850_REG_R8,
    UC_RH850_REG_R10, UC_RH850_REG_R11, UC_RH850_REG_R29,
    UC_RH850_REG_CTBP, UC_RH850_REG_PSW,
)

ELF_PATH = REPO / "firmware" / "F150_2021_Lariat_BlueCruise" / "f150_pscm_full.elf"

# LCA controller chain
FUN_LCA_UPSTREAM = 0x101a392a
FUN_LCA_PIPELINE = 0x10186afa
FUN_LCA_NORMALIZE = 0x101aa05e
FUN_LCA_MAIN = 0x101ab934
FUN_LCA_OUTPUT = 0x101ad86c

# RAM regions
RAM_BASE = 0xFEB00000
RAM_SIZE = 0x00500000
STACK_BASE = 0xFE800000
STACK_SIZE = 0x10000
SENTINEL = 0xDEADBEE0

# Cal mirror region (we intercept all reads here)
CAL_VA_BASE = 0x101D0000
CAL_VA_END = 0x101E0000  # cover cal block 0
CAL_PROBE_LO = 0x101D1500  # zone of interest: schedule+bell families
CAL_PROBE_HI = 0x101D1700

# LCA local-state RAM (path coefficients)
ADDR_FEF23B70 = 0xFEF23B70  # c1 path_angle
ADDR_FEF23B74 = 0xFEF23B74  # c2 curvature
ADDR_FEF23B78 = 0xFEF23B78  # c3 curvature_rate
ADDR_FEF23B7C = 0xFEF23B7C  # c0 path_offset

# v-ego candidate locations (multiple — we don't know which yet, seed all)
ADDR_VEGO_CANDIDATES = [
    0xFEF20100,  # near feature-envelope block
    0xFEF20104,
    0xFEF20120,  # cal+0x0120 mirror = 10.0 LCA min speed
    0xFEF22000,  # generic vehicle-speed RAM
    0xFEF22004,
]


def load_elf_segments(uc: Uc) -> bytes:
    """Map and write all PT_LOAD segments. Return raw ELF bytes for cal access."""
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
    lo = min(v for v, _, _, _ in segs) & ~0xFFF
    hi = max((v + m + 0xFFF) & ~0xFFF for v, _, _, m in segs)
    uc.mem_map(lo, hi - lo, UC_PROT_ALL)
    print(f"  mapped strategy+cal 0x{lo:08x}..0x{hi:08x}")
    for vaddr, foff, fsz, _msz in segs:
        uc.mem_write(vaddr, data[foff:foff + fsz])
    return data


def setup_machine() -> tuple[Uc, bytes]:
    uc = Uc(UC_ARCH_RH850, 0)
    print("loading ELF...")
    elf_bytes = load_elf_segments(uc)
    uc.mem_map(RAM_BASE, RAM_SIZE, UC_PROT_ALL)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_ALL)
    uc.mem_map(SENTINEL & ~0xFFF, 0x1000, UC_PROT_ALL)
    return uc, elf_bytes


def write_f32(uc, addr, v):
    uc.mem_write(addr, struct.pack("<f", v))


def write_u16(uc, addr, v):
    uc.mem_write(addr, struct.pack("<H", v & 0xFFFF))


def write_s16(uc, addr, v):
    uc.mem_write(addr, struct.pack("<h", v))


def overlay_sentinel(uc: Uc) -> dict:
    """Replace cal+0x1500..0x1700 region with sentinel bytes for tracking.
    Each u16 entry's value is its file-offset (so when something reads
    0x1620 it returns 0x1620). Returns a map for verification."""
    sentinel_map = {}
    for off in range(CAL_PROBE_LO, CAL_PROBE_HI, 2):
        # Encode the cal offset as the value, so reads reveal the index
        cal_off = off - CAL_VA_BASE
        sentinel_val = cal_off & 0xFFFF
        uc.mem_write(off, struct.pack("<H", sentinel_val))
        sentinel_map[off] = sentinel_val
    print(f"  overlaid sentinel bytes 0x{CAL_PROBE_LO:08x}..0x{CAL_PROBE_HI:08x} ({len(sentinel_map)} u16 slots)")
    return sentinel_map


def seed_lca_inputs(uc: Uc, curvature: float, path_angle: float, v_ego: float) -> None:
    """Pre-seed LCA RAM state with path coefficients and a speed analog."""
    write_f32(uc, ADDR_FEF23B70, path_angle)
    write_f32(uc, ADDR_FEF23B74, curvature)
    write_f32(uc, ADDR_FEF23B78, 0.0)  # curvature_rate
    write_f32(uc, ADDR_FEF23B7C, 0.0)  # path_offset
    for addr in ADDR_VEGO_CANDIDATES:
        write_f32(uc, addr, v_ego)


def call_with_cal_trace(uc: Uc, entry: int, max_insns: int = 200_000) -> dict:
    """Call entry as leaf; record every cal-region MEM_READ with PC."""
    sp = STACK_BASE + STACK_SIZE - 0x100
    uc.mem_write(sp - 0x800, b"\x00" * 0x800)
    uc.reg_write(UC_RH850_REG_SP, sp)
    uc.reg_write(UC_RH850_REG_LP, SENTINEL)
    uc.reg_write(UC_RH850_REG_R6, 0)
    uc.reg_write(UC_RH850_REG_R29, sp - 0x100)
    uc.reg_write(UC_RH850_REG_R4, 0xFEC01984)  # gp from f150_gp_context_resolved.md
    uc.reg_write(UC_RH850_REG_EP, 0xFEF20000)
    uc.reg_write(UC_RH850_REG_CTBP, 0x0100220C)
    uc.reg_write(UC_RH850_REG_PSW, 0x00000020)

    state = {
        "blocks": 0, "trapped": False, "last_pc": 0, "reason": "",
        "cal_reads": [],  # list of (pc, addr, size, value)
    }

    def block_hook(_uc, addr, size, _ud):
        state["blocks"] += 1
        state["last_pc"] = addr
        state.setdefault("trace", []).append(addr)
        if addr == SENTINEL:
            state["reason"] = "returned"
            _uc.emu_stop()
            return
        if state["blocks"] > max_insns // 4:
            state["reason"] = f"block_limit at 0x{addr:08x}"
            _uc.emu_stop()
            return

    def mem_read(_uc, _access, addr, size, value, _ud):
        if CAL_PROBE_LO <= addr < CAL_PROBE_HI:
            state["cal_reads"].append((state["last_pc"], addr, size))

    def mem_unmapped(_uc, access, addr, size, value, _ud):
        # Map the page on demand and zero-fill so execution can continue.
        # Log the event so we know which addresses were missing.
        state.setdefault("unmapped_log", []).append((state["last_pc"], addr, size, access))
        page = addr & ~0xFFF
        try:
            _uc.mem_map(page, 0x1000, UC_PROT_ALL)
            _uc.mem_write(page, b"\x00" * 0x1000)
            return True
        except Exception:
            state["reason"] = f"unmapped acc={access} addr=0x{addr:08x} pc=0x{state['last_pc']:08x}"
            return False

    h1 = uc.hook_add(UC_HOOK_BLOCK, block_hook)
    h2 = uc.hook_add(UC_HOOK_MEM_READ, mem_read)
    h3 = uc.hook_add(UC_HOOK_MEM_UNMAPPED, mem_unmapped)
    try:
        uc.emu_start(entry, SENTINEL, count=max_insns)
    except UcError as e:
        if not state["reason"]:
            state["reason"] = f"UcError: {e}"
    finally:
        for h in (h1, h2, h3):
            uc.hook_del(h)

    state["pc"] = uc.reg_read(UC_RH850_REG_PC)
    return state


def sweep(entry: int, label: str):
    print(f"\n=== sweep {label} entry=0x{entry:08x} ===")
    pc_to_addrs = defaultdict(set)
    pc_count = Counter()

    sweeps = [
        # (curvature m^-1, path_angle rad, v_ego m/s)
        (0.000, 0.00, 5.0),
        (0.005, 0.05, 15.0),
        (0.010, 0.10, 25.0),
        (0.015, 0.15, 30.0),
        (0.020, 0.20, 35.0),
        (-0.010, -0.10, 20.0),
    ]

    for curvature, pa, v_ego in sweeps:
        uc, _ = setup_machine()
        overlay_sentinel(uc)
        seed_lca_inputs(uc, curvature, pa, v_ego)
        result = call_with_cal_trace(uc, entry, max_insns=80_000)
        n = len(result["cal_reads"])
        print(f"  κ={curvature:+.3f} pa={pa:+.2f} v={v_ego:5.1f}  blocks={result['blocks']:5d} reason={result['reason'][:40]:40s} cal_reads={n}")
        for pc, addr, size in result["cal_reads"]:
            pc_to_addrs[pc].add(addr)
            pc_count[pc] += 1

    if not pc_count:
        print("  no cal reads in probe range")
        return

    print(f"\n  per-PC summary (PCs that read cal+0x{CAL_PROBE_LO-CAL_VA_BASE:04x}..0x{CAL_PROBE_HI-CAL_VA_BASE:04x}):")
    for pc, count in pc_count.most_common(20):
        addrs = sorted(pc_to_addrs[pc])
        addr_summary = (
            f"{len(addrs)} addrs, range 0x{addrs[0]:08x}..0x{addrs[-1]:08x}"
            if len(addrs) > 4
            else "[" + ", ".join(f"0x{a:08x}" for a in addrs) + "]"
        )
        print(f"    PC 0x{pc:08x}  count={count:3d}  {addr_summary}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="lca_main",
                    choices=["lca_main", "lca_normalize", "lca_pipeline", "lca_upstream", "lca_output"])
    args = ap.parse_args()

    targets = {
        "lca_upstream": (FUN_LCA_UPSTREAM, "FUN_101a392a (upstream)"),
        "lca_pipeline": (FUN_LCA_PIPELINE, "FUN_10186afa (pipeline)"),
        "lca_normalize": (FUN_LCA_NORMALIZE, "FUN_101aa05e (normalize)"),
        "lca_main": (FUN_LCA_MAIN, "FUN_101ab934 (main controller)"),
        "lca_output": (FUN_LCA_OUTPUT, "FUN_101ad86c (output)"),
    }
    entry, label = targets[args.target]
    sweep(entry, label)
