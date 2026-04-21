#!/usr/bin/env python3
"""
Transit LKA override-hunt harness.

Same pattern as unicorn_f150_override_harness.py, adapted to Transit's
V850E2M memory map. Purpose: find Transit's analog of FUN_101a3b84
(the F-150 override state machine) by calling candidate functions in
the 0x010B4xxx-0x010B7xxx region with controlled inputs and watching
for input-sensitive RAM state changes.
"""

from __future__ import annotations
import os
import sys
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VENDOR = REPO / "vendor" / "unicorn-pr1918"
os.environ["LIBUNICORN_PATH"] = str(VENDOR / "build_python")
sys.path.insert(0, str(VENDOR / "bindings" / "python"))

import unicorn
from unicorn import Uc, UC_ARCH_RH850, UcError, UC_PROT_ALL, UC_HOOK_BLOCK, UC_HOOK_MEM_UNMAPPED
from unicorn.rh850_const import (
    UC_RH850_REG_PC, UC_RH850_REG_SP, UC_RH850_REG_LP, UC_RH850_REG_EP,
    UC_RH850_REG_R4, UC_RH850_REG_R6, UC_RH850_REG_R29,
    UC_RH850_REG_R10, UC_RH850_REG_CTBP, UC_RH850_REG_PSW,
)

# Firmware paths (AH revision — user's truck)
FW_DIR = REPO / "firmware" / "Transit_2025" / "decompressed"
STRATEGY_BIN = FW_DIR / "AH" / "block0_strategy.bin"   # 1,048,560 B @ 0x01000000
RAM_INIT_BIN = FW_DIR / "AH" / "block1_ram.bin"        #     3,072 B @ 0x10000400
BLOCK2_BIN   = FW_DIR / "AH" / "block2_ext.bin"        #   327,680 B @ 0x20FF0000
CAL_BIN      = FW_DIR / "cal_AH.bin"                   #    65,520 B @ 0x00FD0000

# Load addresses
STRATEGY_BASE = 0x01000000
CAL_BASE      = 0x00FD0000
RAM_INIT_BASE = 0x10000400
BLOCK2_BASE   = 0x20FF0000

# Runtime memory windows
LOWMEM_BASE   = 0x00000000
LOWMEM_SIZE   = 0x1000
# One contiguous region covers EP workspace + stack on Transit
EP_BASE       = 0x40010000
EP_SIZE       = 0x20000           # 0x40010000..0x40030000
STACK_BASE    = 0x40020000        # upper half used as stack
STACK_SIZE    = 0x10000
RAM_BASE      = 0xFEF00000     # Transit local RAM window (same family as F-150)
RAM_SIZE      = 0x00100000
PERIPH_BASE   = 0xFF000000
PERIPH_SIZE   = 0x10000
SYSIO_BASE    = 0xFFFF0000      # widen for v850 SFR access around 0xffffa870
SYSIO_SIZE    = 0x10000
CAN_BASE      = 0xFFD00000
CAN_SIZE      = 0x10000
SENTINEL      = 0xDEADBEE0

# Known Transit LKA candidates (from memory + repo notes)
FUN_LKA_CAN_HANDLER     = 0x0108D684   # 0x3CA CAN RX handler (archived)
FUN_LKA_CAN_HANDLER_NEW = 0x0108D914   # updated handler
FUN_LCA_DISPATCHER      = 0x010B4AD4   # LCA/LKA dispatcher per lca_revert_state
FUN_ANGLE_SCALER        = 0x010babf8   # mulhi 0x67c2 angle scaler
CTBP_DEFAULT            = 0x0100220C


def load_firmware(uc: Uc) -> None:
    """Map and load all Transit firmware blobs into the emulator."""
    def map_and_write(base: int, blob: Path, label: str) -> None:
        data = blob.read_bytes()
        map_base = base & ~0xFFF
        map_size = (len(data) + (base - map_base) + 0xFFF) & ~0xFFF
        uc.mem_map(map_base, map_size, UC_PROT_ALL)
        uc.mem_write(base, data)
        print(f"  mapped {label:12s} 0x{map_base:08x}..0x{map_base+map_size:08x} ({len(data)} B)")

    map_and_write(STRATEGY_BASE, STRATEGY_BIN, "strategy")
    map_and_write(CAL_BASE,      CAL_BIN,      "cal")
    map_and_write(BLOCK2_BASE,   BLOCK2_BIN,   "block2")
    map_and_write(RAM_INIT_BASE, RAM_INIT_BIN, "ram_init")


def setup_machine() -> Uc:
    uc = Uc(UC_ARCH_RH850, 0)
    print("loading Transit AH firmware...")
    load_firmware(uc)
    # Runtime-only regions
    uc.mem_map(LOWMEM_BASE,  LOWMEM_SIZE,  UC_PROT_ALL)
    # EP region includes stack (stack sits in upper half)
    uc.mem_map(EP_BASE,      EP_SIZE,      UC_PROT_ALL)
    uc.mem_map(RAM_BASE,     RAM_SIZE,     UC_PROT_ALL)
    uc.mem_map(PERIPH_BASE,  PERIPH_SIZE,  UC_PROT_ALL)
    uc.mem_map(SYSIO_BASE,   SYSIO_SIZE,   UC_PROT_ALL)
    uc.mem_map(CAN_BASE,     CAN_SIZE,     UC_PROT_ALL)
    uc.mem_map(SENTINEL & ~0xFFF, 0x1000, UC_PROT_ALL)
    return uc


def call_function(uc: Uc, entry: int, arg0: int = 0, arg1: int = 0,
                  max_blocks: int = 2000, trace: bool = False) -> dict:
    sp = STACK_BASE + STACK_SIZE - 0x100
    uc.mem_write(sp - 0x400, b"\x00" * 0x400)
    uc.reg_write(UC_RH850_REG_SP,  sp)
    uc.reg_write(UC_RH850_REG_LP,  SENTINEL)
    uc.reg_write(UC_RH850_REG_R6,  arg0)
    uc.reg_write(UC_RH850_REG_R29, sp - 0x200)
    uc.reg_write(UC_RH850_REG_R4,  0xFEF00000)  # gp guess
    uc.reg_write(UC_RH850_REG_EP,  EP_BASE + 0x100)
    uc.reg_write(UC_RH850_REG_CTBP, CTBP_DEFAULT)
    uc.reg_write(UC_RH850_REG_PSW, 0x00000020)

    state = {"blocks": 0, "trapped": False, "last_pc": 0, "reason": ""}

    def block_hook(_uc, addr, size, _ud):
        state["blocks"] += 1
        state["last_pc"] = addr
        if addr == SENTINEL:
            state["reason"] = "returned_to_sentinel"
            _uc.emu_stop()
            return
        if state["blocks"] > max_blocks:
            state["reason"] = f"block_limit at 0x{addr:08x}"
            _uc.emu_stop()
            return
        if trace and state["blocks"] <= 128:
            print(f"    block {state['blocks']:4d}  pc=0x{addr:08x} size={size}")

    def mem_unmapped(_uc, access, addr, size, value, _ud):
        state["reason"] = f"unmapped access={access} addr=0x{addr:08x} size={size} pc=0x{state['last_pc']:08x}"
        state["trapped"] = True
        return False

    h1 = uc.hook_add(UC_HOOK_BLOCK, block_hook)
    h2 = uc.hook_add(UC_HOOK_MEM_UNMAPPED, mem_unmapped)
    try:
        # timeout in microseconds — avoid infinite translation-loop hangs
        uc.emu_start(entry, SENTINEL, timeout=2_000_000, count=max_blocks * 20)
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


def smoke_test(only: int = None):
    """Prove emulator can execute Transit strategy at a known-valid entry.
    Pass `only=ADDR` to run a single entry. Skip angle_scaler by default —
    it uses FP extension opcodes not supported by Unicorn RH850."""
    entries = [
        ("lca_dispatcher",      FUN_LCA_DISPATCHER),
        ("lka_can_handler",     FUN_LKA_CAN_HANDLER),
        ("lka_can_handler_new", FUN_LKA_CAN_HANDLER_NEW),
    ]
    if only is not None:
        entries = [(f"addr_0x{only:08x}", only)]
    for label, addr in entries:
        uc = setup_machine()
        result = call_function(uc, addr, max_blocks=200)
        print(f"{label:22s} @ 0x{addr:08x}  blocks={result['blocks']:4d}  "
              f"last_pc=0x{result['last_pc']:08x}  {result['reason'] or 'clean exit'}",
              flush=True)


if __name__ == "__main__":
    smoke_test()
