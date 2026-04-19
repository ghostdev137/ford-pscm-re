#!/usr/bin/env python3
"""
Minimal Unicorn RH850 harness for Transit PSCM firmware.

This is intentionally a "fuck around and find out" harness, not a faithful
boot emulator. It loads the real Transit blobs, seeds the obvious AUTOSAR
runtime state, and reports where execution falls over so we can iterate on
SP/GP/EP/caller context instead of guessing blind.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import unicorn
from unicorn import Uc, UcError
from unicorn.rh850_const import (
    UC_RH850_REG_CTBP,
    UC_RH850_REG_CTPC,
    UC_RH850_REG_EP,
    UC_RH850_REG_LP,
    UC_RH850_REG_PC,
    UC_RH850_REG_PSW,
    UC_RH850_REG_R1,
    UC_RH850_REG_R2,
    UC_RH850_REG_R4,
    UC_RH850_REG_R5,
    UC_RH850_REG_R6,
    UC_RH850_REG_R7,
    UC_RH850_REG_R8,
    UC_RH850_REG_R9,
    UC_RH850_REG_R10,
    UC_RH850_REG_R11,
    UC_RH850_REG_R12,
    UC_RH850_REG_R13,
    UC_RH850_REG_R14,
    UC_RH850_REG_R15,
    UC_RH850_REG_R16,
    UC_RH850_REG_R17,
    UC_RH850_REG_R18,
    UC_RH850_REG_R19,
    UC_RH850_REG_R20,
    UC_RH850_REG_R21,
    UC_RH850_REG_R22,
    UC_RH850_REG_R23,
    UC_RH850_REG_R24,
    UC_RH850_REG_R25,
    UC_RH850_REG_R26,
    UC_RH850_REG_R27,
    UC_RH850_REG_R28,
    UC_RH850_REG_R29,
    UC_RH850_REG_R30,
    UC_RH850_REG_R31,
    UC_RH850_REG_SP,
)

PAGE = 0x1000
REPO = Path(__file__).resolve().parent.parent
FW_ROOT = REPO / "firmware" / "Transit_2025" / "decompressed"

STRATEGY_BASE = 0x01000000
CAL_BASE = 0x00FD0000
RAM_INIT_BASE = 0x10000400
BLOCK2_BASE = 0x20FF0000
EP_BASE = 0x40010100
EP_WINDOW_BASE = 0x40010000
EP_WINDOW_SIZE = 0x20000
STACK_BASE = 0x40018000
STACK_SIZE = 0x8000
PAYLOAD_BASE = 0x40014000
PAYLOAD_SIZE = 0x1000
PERIPH_BASE = 0xFF000000
PERIPH_SIZE = 0x10000
SYSIO_BASE = 0xFFFFF000
SYSIO_SIZE = 0x1000
LOWMEM_BASE = 0x00000000
LOWMEM_SIZE = 0x1000
CAN_BASE = 0xFFD00000
CAN_SIZE = 0x10000

CTBP_DEFAULT = 0x0100220C
PSW_SUPERVISOR = 0x20

ENTRY_ALIASES = {
    "reset": 0x00000000,
    "strategy": 0x01000000,
    "lka": 0x0108D914,
    "apa": 0x0108E2BE,
    "destorq": 0x0108F484,
    "brkspeed": 0x0108D0B2,
    "com": 0x010BC360,
    "lka_archived": 0x0108D684,
    "apa_archived": 0x0108E02E,
    "destorq_archived": 0x0108F094,
}

CAN_CONTEXT = {
    0x0108D914: {"can_id": 0x3CA, "payload_hex": "2000000000000000"},
    0x0108E2BE: {"can_id": 0x3A8, "payload_hex": "4600000000000000"},
    0x0108F484: {"can_id": 0x213, "payload_hex": "0000000000000000"},
    0x0108D684: {"can_id": 0x3CA, "payload_hex": "2000000000000000"},
    0x0108E02E: {"can_id": 0x3A8, "payload_hex": "4600000000000000"},
    0x0108F094: {"can_id": 0x213, "payload_hex": "0000000000000000"},
}

CAN_RX_TABLE_OFFSET = 0x2BE0
CAN_RX_TABLE_SIZE = 0x110
INIT_MARKER = 0x001000EF
INIT_TABLE_OFFSET = 0x9230
INIT_TABLE_MAX_ENTRIES = 100

TASK_SEQUENCES = {
    "base_tasks": [0x010BA50C, 0x010BC360, 0x010CD53C, 0x010DA378],
    "com_chain": [0x010BC360, 0x010CD53C, 0x010DA378],
}

REG_NAMES = {
    UC_RH850_REG_PC: "pc",
    UC_RH850_REG_SP: "sp",
    UC_RH850_REG_R4: "gp/r4",
    UC_RH850_REG_R5: "tp/r5",
    UC_RH850_REG_EP: "ep/r30",
    UC_RH850_REG_LP: "lp/r31",
    UC_RH850_REG_CTBP: "ctbp",
    UC_RH850_REG_PSW: "psw",
    UC_RH850_REG_R1: "r1",
    UC_RH850_REG_R2: "r2",
    UC_RH850_REG_R6: "r6",
    UC_RH850_REG_R7: "r7",
    UC_RH850_REG_R8: "r8",
    UC_RH850_REG_R9: "r9",
    UC_RH850_REG_R10: "r10",
    UC_RH850_REG_R11: "r11",
    UC_RH850_REG_R12: "r12",
    UC_RH850_REG_R13: "r13",
    UC_RH850_REG_R14: "r14",
    UC_RH850_REG_R15: "r15",
    UC_RH850_REG_R16: "r16",
    UC_RH850_REG_R17: "r17",
    UC_RH850_REG_R18: "r18",
    UC_RH850_REG_R19: "r19",
    UC_RH850_REG_R20: "r20",
    UC_RH850_REG_R21: "r21",
    UC_RH850_REG_R22: "r22",
    UC_RH850_REG_R23: "r23",
    UC_RH850_REG_R24: "r24",
    UC_RH850_REG_R25: "r25",
    UC_RH850_REG_R26: "r26",
    UC_RH850_REG_R27: "r27",
    UC_RH850_REG_R28: "r28",
    UC_RH850_REG_R29: "r29",
}

REG_BY_NAME = {name: reg for reg, name in REG_NAMES.items()}
for reg in range(32):
    REG_BY_NAME[f"r{reg}"] = reg
REG_BY_NAME["gp"] = UC_RH850_REG_R4
REG_BY_NAME["tp"] = UC_RH850_REG_R5
REG_BY_NAME["ep"] = UC_RH850_REG_EP
REG_BY_NAME["lp"] = UC_RH850_REG_LP
REG_BY_NAME["pc"] = UC_RH850_REG_PC
REG_BY_NAME["sp"] = UC_RH850_REG_SP


def align_up(size: int) -> int:
    return int(math.ceil(size / PAGE) * PAGE)


def parse_int(text: str) -> int:
    return int(text, 0)


def resolve_entry(value: str) -> int:
    if value.lower() in ENTRY_ALIASES:
        return ENTRY_ALIASES[value.lower()]
    return parse_int(value)


def compute_be_lsb(start_bit: int, size: int) -> int:
    be_bits = [j + i * 8 for i in range(64) for j in range(7, -1, -1)]
    idx = be_bits.index(start_bit)
    return be_bits[idx + size - 1]


def set_signal_be(dat: bytearray, start_bit: int, size: int, raw_value: int) -> None:
    lsb = compute_be_lsb(start_bit, size)
    i = lsb // 8
    bits = size
    if size < 64:
        raw_value &= (1 << size) - 1

    while 0 <= i < len(dat) and bits > 0:
        shift = lsb % 8 if (lsb // 8) == i else 0
        chunk = min(bits, 8 - shift)
        mask = ((1 << chunk) - 1) << shift
        dat[i] &= ~mask
        dat[i] |= (raw_value & ((1 << chunk) - 1)) << shift
        bits -= chunk
        raw_value >>= chunk
        i -= 1


def encode_signal_be(dat: bytearray, start_bit: int, size: int, factor: float, offset: float, value: float) -> None:
    raw = int(math.floor((value - offset) / factor + 0.5))
    if raw < 0:
        raw = (1 << size) + raw
    set_signal_be(dat, start_bit, size, raw)


def build_openpilot_lka_payload(
    lat_active: bool,
    desired_angle_deg: float,
    current_angle_deg: float,
    desired_curvature: float,
) -> bytes:
    relative_angle = float(max(-5.8, min(5.8, desired_angle_deg - current_angle_deg)))
    direction = 0
    ramp_type = 0
    ref_angle_mrad = 0.0
    curvature = 0.0

    if lat_active:
        # Matches the current ford-lka branch logic: direction follows current wheel sign.
        direction = 2 if current_angle_deg > 0.0 else 4
        ramp_type = 1 if abs(relative_angle) >= 5.0 else 0
        ref_angle_mrad = max(-102.4, min(102.3, math.radians(relative_angle) * 1000.0))
        curvature = max(-0.01023, min(0.01023, -desired_curvature))

    dat = bytearray(8)
    encode_signal_be(dat, 38, 2, 1.0, 0.0, 0.0)             # LkaDrvOvrrd_D_Rq
    encode_signal_be(dat, 7, 3, 1.0, 0.0, float(direction))  # LkaActvStats_D2_Req
    encode_signal_be(dat, 19, 12, 0.05, -102.4, ref_angle_mrad)
    encode_signal_be(dat, 39, 1, 1.0, 0.0, float(ramp_type))
    encode_signal_be(dat, 15, 12, 5e-6, -0.01024, curvature)
    encode_signal_be(dat, 4, 3, 1.0, 0.0, 0.0)               # LdwActvStats_D_Req
    encode_signal_be(dat, 1, 2, 1.0, 0.0, 3.0)               # LdwActvIntns_D_Req
    return bytes(dat)


def build_openpilot_lmc_heartbeat_payload() -> bytes:
    # Transit ford-lka replays stock camera LMC values with LatCtl_D_Rq=0.
    # In the emulator we don't have captured stock camera state, so synthesize a
    # disabled heartbeat with the same message shape and a "Precise" mode bit.
    dat = bytearray(8)
    encode_signal_be(dat, 63, 6, 2.0, 0.0, 0.0)               # LatCtlRng_L_Max
    encode_signal_be(dat, 51, 1, 1.0, 0.0, 0.0)               # HandsOffCnfm_B_Rq
    encode_signal_be(dat, 36, 3, 1.0, 0.0, 0.0)               # LatCtl_D_Rq
    encode_signal_be(dat, 53, 2, 1.0, 0.0, 0.0)               # LatCtlRampType_D_Rq
    encode_signal_be(dat, 33, 2, 1.0, 0.0, 1.0)               # LatCtlPrecision_D_Rq
    encode_signal_be(dat, 47, 10, 0.01, -5.12, 0.0)           # LatCtlPathOffst_L_Actl
    encode_signal_be(dat, 31, 11, 0.0005, -0.5, 0.0)          # LatCtlPath_An_Actl
    encode_signal_be(dat, 12, 13, 2.5e-7, -0.001024, 0.0)     # LatCtlCurv_NoRate_Actl
    encode_signal_be(dat, 7, 11, 2e-5, -0.02, 0.0)            # LatCtlCurv_No_Actl
    return bytes(dat)


def build_message_context(args: argparse.Namespace) -> Dict[str, int | str]:
    if args.message_mode == "openpilot-lka":
        payload = build_openpilot_lka_payload(
            lat_active=args.lat_active,
            desired_angle_deg=args.desired_angle_deg,
            current_angle_deg=args.current_angle_deg,
            desired_curvature=args.desired_curvature,
        )
        return {
            "can_id": 0x3CA,
            "payload_hex": payload.hex(),
            "description": (
                f"openpilot 0x3CA desired={args.desired_angle_deg:.2f}deg "
                f"current={args.current_angle_deg:.2f}deg curv={args.desired_curvature:.5f}"
            ),
        }

    if args.message_mode == "openpilot-lmc-heartbeat":
        payload = build_openpilot_lmc_heartbeat_payload()
        return {
            "can_id": 0x3D3,
            "payload_hex": payload.hex(),
            "description": "openpilot Transit heartbeat 0x3D3 (LatCtl_D_Rq=0 synthetic passthrough)",
        }

    payload_hex = args.payload_hex or str(infer_can_context(args.start).get("payload_hex", ""))
    can_id = int(infer_can_context(args.start).get("can_id", 0))
    return {
        "can_id": can_id,
        "payload_hex": payload_hex,
        "description": "raw payload",
    }


def parse_mailbox_override(spec: str) -> Tuple[int, bytes]:
    can_id_text, payload_hex = spec.split("=", 1)
    can_id = parse_int(can_id_text.strip())
    payload = bytes.fromhex(payload_hex.strip()).ljust(8, b"\x00")[:8]
    return can_id, payload


def parse_watch_range(spec: str) -> Tuple[int, int]:
    start_text, end_text = spec.split(":", 1)
    start = parse_int(start_text.strip())
    end = parse_int(end_text.strip())
    if end <= start:
        raise ValueError(f"watch range end must exceed start: {spec}")
    return start, end


def parse_replay_record(line: str) -> Dict[int, bytes]:
    raw = json.loads(line)
    if not isinstance(raw, dict):
        raise ValueError("replay line must be a JSON object")

    out: Dict[int, bytes] = {}
    for key, value in raw.items():
        can_id = parse_int(str(key))
        if isinstance(value, dict):
            payload_hex = str(value.get("payload", value.get("payload_hex", "")))
        else:
            payload_hex = str(value)
        out[can_id] = bytes.fromhex(payload_hex).ljust(8, b"\x00")[:8]
    return out


def parse_poke(spec: str) -> Tuple[int, bytes]:
    addr_text, data_hex = spec.split("=", 1)
    addr = parse_int(addr_text.strip())
    data = bytes.fromhex(data_hex.strip())
    if not data:
        raise ValueError(f"empty poke data: {spec}")
    return addr, data


def pick_calibration(variant: str, explicit: Optional[Path]) -> Path:
    if explicit is not None:
        return explicit

    preferred = sorted((FW_ROOT / variant).glob("cal_*.bin"))
    if preferred:
        return preferred[0]

    for name in ("cal_AH.bin", "cal_AF.bin", "cal_AD.bin"):
        path = FW_ROOT / name
        if path.exists():
            return path

    raise FileNotFoundError("No calibration blob found; pass --cal explicitly.")


def parse_can_rx_slots(strategy_path: Path) -> Dict[int, int]:
    data = strategy_path.read_bytes()
    out: Dict[int, int] = {}
    end = min(len(data), CAN_RX_TABLE_OFFSET + CAN_RX_TABLE_SIZE)
    for off in range(CAN_RX_TABLE_OFFSET, end, 8):
        can_id = int.from_bytes(data[off : off + 2], "big")
        flags = data[off + 2]
        slot = data[off + 3]
        if can_id == 0 or flags == 0:
            continue
        out[can_id] = slot
    return out


def infer_can_context(start: int) -> Dict[str, int | str]:
    return CAN_CONTEXT.get(start, {})


class TransitHarness:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.mu = Uc(unicorn.UC_ARCH_RH850, unicorn.UC_MODE_LITTLE_ENDIAN)
        self.message_context = build_message_context(args)
        self.trace: List[Tuple[int, int]] = []
        self.mem_faults: List[Dict[str, int]] = []
        self.cal_reads: List[Dict[str, int]] = []
        self.ram_writes: List[Dict[str, int]] = []
        self.trace_events: List[Dict[str, int]] = []
        self.watch_reads: List[Dict[str, int]] = []
        self.watch_writes: List[Dict[str, int]] = []
        self.auto_pages: set[int] = set()
        self.can_slots: Dict[int, int] = {}
        self.low_fetch_stubs: List[Dict[str, int]] = []
        self.recent_mem: collections.deque[Dict[str, int]] = collections.deque(maxlen=64)

    def log(self, msg: str) -> None:
        print(msg, flush=True)

    def map_blob(self, base: int, path: Path, label: str) -> None:
        data = path.read_bytes()
        map_base = base & ~(PAGE - 1)
        delta = base - map_base
        size = align_up(len(data) + delta)
        self.mu.mem_map(map_base, size)
        self.mu.mem_write(base, data)
        self.log(f"mapped {label:<12} {base:#010x}-{base + len(data):#010x} {path.name}")

    def map_runtime(self) -> None:
        self.mu.mem_map(LOWMEM_BASE, LOWMEM_SIZE)
        self.mu.mem_map(EP_WINDOW_BASE, EP_WINDOW_SIZE)
        self.mu.mem_map(PERIPH_BASE, PERIPH_SIZE)
        self.mu.mem_map(SYSIO_BASE, SYSIO_SIZE)
        self.mu.mem_map(CAN_BASE, CAN_SIZE)
        self._apply_init_table()
        self._seed_bsw_state()
        self._seed_payload()
        self._apply_pokes()

        if self.args.inject_can:
            self._inject_can_mailboxes()

    def _seed_payload(self) -> None:
        payload_hex = str(self.message_context.get("payload_hex", ""))
        payload = bytes.fromhex(payload_hex) if payload_hex else b"\x00" * 8
        self.mu.mem_write(PAYLOAD_BASE, payload.ljust(8, b"\x00"))

    def _seed_bsw_state(self) -> None:
        # Match the Athrill bootstrap: set the known AUTOSAR bytes/words, then
        # fill only the small EP state window's zero gaps with 0x01.
        words32 = {
            0x40010100: 0x00030003,
            0x40010104: 0x00010001,
            0x40010108: 0x00020001,
            0x40010180: 0x00030002,
        }
        words16 = {
            0x40010102: 0x0003,
            0x40010106: 0x0002,
            0x40010118: 0x0003,
            0x40010138: 0x0001,
            0x40010182: 0x0003,
            0x40010184: 0x0001,
            0x400101A0: 0x0001,
            0x400101C4: 0x0003,
        }
        bytes1 = {
            0x4001010C: 0x01,
            0x4001010E: 0x03,
            0x40010110: 0x01,
            0x40010112: 0x02,
            0x4001011E: 0x01,
            0x40010120: 0x01,
            0x4001012A: 0xFF,
            0x4001012E: 0x01,
            0x40010140: 0x02,
            0x40010142: 0x01,
            0x40010145: 0x03,
            0x40010146: 0x01,
            0x40010150: 0xFF,
            0x4001015E: 0x01,
            0x40010160: 0x02,
            0x40010161: 0x01,
            0x40010165: 0x04,
            0x40010168: 0x01,
            0x4001016E: 0x01,
            0x40010170: 0x03,
            0x40010174: 0x01,
            0x40010178: 0x01,
            0x4001017E: 0x01,
        }
        for addr, value in words32.items():
            self.mu.mem_write(addr, value.to_bytes(4, "little"))
        for addr, value in words16.items():
            self.mu.mem_write(addr, value.to_bytes(2, "little"))
        for addr, value in bytes1.items():
            self.mu.mem_write(addr, bytes([value]))

        for addr in range(0x40010100, 0x40010500):
            if self.mu.mem_read(addr, 1) == b"\x00":
                self.mu.mem_write(addr, b"\x01")

    def _apply_pokes(self) -> None:
        for spec in self.args.poke:
            addr, data = parse_poke(spec)
            self.mu.mem_write(addr, data)
            self.log(f"poke {addr:#010x} <- {data.hex()}")

    def _apply_init_table(self) -> None:
        strategy = (FW_ROOT / self.args.variant / "block0_strategy.bin").read_bytes()
        count = 0
        total = 0
        for off in range(INIT_TABLE_OFFSET, min(len(strategy), INIT_TABLE_OFFSET + INIT_TABLE_MAX_ENTRIES * 16), 16):
            marker = int.from_bytes(strategy[off : off + 4], "big")
            if marker != INIT_MARKER:
                break
            ram_end = int.from_bytes(strategy[off + 4 : off + 8], "big")
            ram_start = int.from_bytes(strategy[off + 8 : off + 12], "big")
            ctrl = int.from_bytes(strategy[off + 12 : off + 16], "big")
            count += 1
            if ram_end < ram_start:
                continue
            size = ram_end - ram_start + 1
            op = (ctrl >> 24) & 0xFF
            if (op & 0xF0) == 0xA0:
                self.mu.mem_write(ram_start, b"\x00" * size)
                total += size
                continue
            if op == 0x01:
                rom_src = ctrl & 0x00FFFFFF
                if rom_src < STRATEGY_BASE:
                    rom_src += STRATEGY_BASE
                rom_off = rom_src - STRATEGY_BASE
                self.mu.mem_write(ram_start, strategy[rom_off : rom_off + size])
                total += size
                continue
        self.log(f"applied init table entries={count} bytes={total}")

    def _build_mailboxes(self) -> Dict[int, bytes]:
        msgs = {
            0x415: bytes.fromhex("00c8000000000000"),
            0x3A8: bytes.fromhex("4600000000000000"),
            0x3CA: build_openpilot_lka_payload(True, 2.5, 0.0, 0.0),
            0x213: bytes(8),
            0x091: bytes(8),
        }

        selected_can_id = int(self.message_context.get("can_id", 0))
        selected_payload_hex = str(self.message_context.get("payload_hex", ""))
        if selected_can_id and selected_payload_hex:
            msgs[selected_can_id] = bytes.fromhex(selected_payload_hex).ljust(8, b"\x00")[:8]

        for spec in self.args.mailbox:
            can_id, payload = parse_mailbox_override(spec)
            msgs[can_id] = payload
        return msgs

    def _inject_can_mailboxes(self, overrides: Optional[Dict[int, bytes]] = None) -> None:
        msgs = self._build_mailboxes()
        if overrides:
            msgs.update(overrides)
        used_slots: set[int] = set()
        next_fallback_slot = 0
        new_data_0 = 0
        new_data_1 = 0

        for can_id, payload in msgs.items():
            slot = self.can_slots.get(can_id)
            while slot is None and next_fallback_slot in used_slots:
                next_fallback_slot += 1
            if slot is None:
                slot = next_fallback_slot
                next_fallback_slot += 1
            used_slots.add(slot)

            mbox = CAN_BASE + 0x0100 + slot * 0x10
            self.mu.mem_write(mbox + 0x00, (can_id << 18).to_bytes(4, "little"))
            self.mu.mem_write(mbox + 0x04, (0x00080001).to_bytes(4, "little"))
            self.mu.mem_write(mbox + 0x08, payload[:4])
            self.mu.mem_write(mbox + 0x0C, payload[4:8])
            if slot < 32:
                new_data_0 |= 1 << slot
            else:
                new_data_1 |= 1 << (slot - 32)

        self.mu.mem_write(CAN_BASE + 0x0040, new_data_0.to_bytes(4, "little"))
        self.mu.mem_write(CAN_BASE + 0x0048, new_data_1.to_bytes(4, "little"))

    def seed_registers(self) -> None:
        self.mu.reg_write(UC_RH850_REG_PC, self.args.start)
        self.mu.reg_write(UC_RH850_REG_SP, self.args.sp)
        self.mu.reg_write(UC_RH850_REG_R4, self.args.gp)
        self.mu.reg_write(UC_RH850_REG_R5, self.args.tp)
        self.mu.reg_write(UC_RH850_REG_EP, self.args.ep)
        self.mu.reg_write(UC_RH850_REG_LP, self.args.lp)
        self.mu.reg_write(UC_RH850_REG_CTBP, self.args.ctbp)
        self.mu.reg_write(UC_RH850_REG_PSW, self.args.psw)

        # Clear caller-saved scratch by default so register dependencies stand out.
        for reg in (
            UC_RH850_REG_R1,
            UC_RH850_REG_R2,
            UC_RH850_REG_R6,
            UC_RH850_REG_R7,
            UC_RH850_REG_R8,
            UC_RH850_REG_R9,
            UC_RH850_REG_R10,
            UC_RH850_REG_R11,
            UC_RH850_REG_R12,
            UC_RH850_REG_R13,
            UC_RH850_REG_R14,
            UC_RH850_REG_R15,
            UC_RH850_REG_R16,
            UC_RH850_REG_R17,
            UC_RH850_REG_R18,
            UC_RH850_REG_R19,
            UC_RH850_REG_R20,
            UC_RH850_REG_R21,
            UC_RH850_REG_R22,
            UC_RH850_REG_R23,
            UC_RH850_REG_R24,
            UC_RH850_REG_R25,
            UC_RH850_REG_R26,
            UC_RH850_REG_R27,
            UC_RH850_REG_R28,
            UC_RH850_REG_R29,
            UC_RH850_REG_R30,
            UC_RH850_REG_R31,
        ):
            if reg in (UC_RH850_REG_PC, UC_RH850_REG_SP, UC_RH850_REG_R4, UC_RH850_REG_R5, UC_RH850_REG_EP, UC_RH850_REG_LP):
                continue
            self.mu.reg_write(reg, 0)

        if self.args.seed_can_caller:
            can_id = int(self.message_context.get("can_id", 0))
            self.mu.reg_write(UC_RH850_REG_R6, PAYLOAD_BASE)
            self.mu.reg_write(UC_RH850_REG_R7, can_id)
            self.mu.reg_write(UC_RH850_REG_R8, 8)

        for spec in self.args.reg:
            name, value = spec.split("=", 1)
            reg = REG_BY_NAME.get(name.strip().lower())
            if reg is None:
                raise ValueError(f"Unknown register override: {name}")
            self.mu.reg_write(reg, parse_int(value.strip()))

    def install_hooks(self) -> None:
        self.mu.hook_add(unicorn.UC_HOOK_CODE, self._hook_code)
        self.mu.hook_add(unicorn.UC_HOOK_MEM_READ, self._hook_mem_read)
        self.mu.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._hook_mem_write)
        self.mu.hook_add(
            unicorn.UC_HOOK_MEM_READ_UNMAPPED
            | unicorn.UC_HOOK_MEM_WRITE_UNMAPPED
            | unicorn.UC_HOOK_MEM_FETCH_UNMAPPED,
            self._hook_unmapped,
        )

    def _hook_code(self, uc: Uc, address: int, size: int, _user: object) -> None:
        if self.args.trace_limit and len(self.trace) < self.args.trace_limit:
            self.trace.append((address, size))
        if self._trace_address(address) and len(self.trace_events) < self.args.trace_limit:
            self.trace_events.append(
                {
                    "pc": address,
                    "size": size,
                    "r6": uc.reg_read(UC_RH850_REG_R6),
                    "r7": uc.reg_read(UC_RH850_REG_R7),
                    "r8": uc.reg_read(UC_RH850_REG_R8),
                    "r14": uc.reg_read(UC_RH850_REG_R14),
                    "r29": uc.reg_read(UC_RH850_REG_R29),
                }
            )

    def _hook_mem_read(self, uc: Uc, access: int, address: int, size: int, value: int, _user: object) -> None:
        read_value = value & 0xFFFFFFFF
        try:
            read_value = int.from_bytes(uc.mem_read(address, size), "little")
        except UcError:
            pass
        self.recent_mem.append(
            {
                "kind": 0,
                "address": address,
                "size": size,
                "value": read_value,
                "pc": uc.reg_read(UC_RH850_REG_PC),
            }
        )
        if CAL_BASE <= address < CAL_BASE + 0x10000:
            self.cal_reads.append(
                {
                    "access": access,
                    "address": address,
                    "size": size,
                    "value": read_value,
                    "pc": uc.reg_read(UC_RH850_REG_PC),
                }
            )
        if self._watch_address(address):
            self.watch_reads.append(
                {
                    "address": address,
                    "size": size,
                    "pc": uc.reg_read(UC_RH850_REG_PC),
                }
            )

    def _hook_mem_write(self, uc: Uc, access: int, address: int, size: int, value: int, _user: object) -> None:
        self.recent_mem.append(
            {
                "kind": 1,
                "address": address,
                "size": size,
                "value": value & 0xFFFFFFFF,
                "pc": uc.reg_read(UC_RH850_REG_PC),
            }
        )
        if EP_WINDOW_BASE <= address < EP_WINDOW_BASE + EP_WINDOW_SIZE:
            self.ram_writes.append(
                {
                    "access": access,
                    "address": address,
                    "size": size,
                    "value": value & 0xFFFFFFFF,
                    "pc": uc.reg_read(UC_RH850_REG_PC),
                }
            )
        if self._watch_address(address):
            self.watch_writes.append(
                {
                    "address": address,
                    "size": size,
                    "value": value & 0xFFFFFFFF,
                    "pc": uc.reg_read(UC_RH850_REG_PC),
                }
            )

    def _trace_address(self, address: int) -> bool:
        if not self.args.trace_range:
            return False
        return any(start <= address < end for start, end in self.args.trace_range)

    def _watch_address(self, address: int) -> bool:
        if not self.args.watch:
            return False
        return any(start <= address < end for start, end in self.args.watch)

    def _reset_runtime_logs(self) -> None:
        self.trace.clear()
        self.trace_events.clear()
        self.mem_faults.clear()
        self.cal_reads.clear()
        self.ram_writes.clear()
        self.watch_reads.clear()
        self.watch_writes.clear()
        self.low_fetch_stubs.clear()
        self.recent_mem.clear()

    def _hook_unmapped(
        self,
        uc: Uc,
        access: int,
        address: int,
        size: int,
        value: int,
        _user: object,
    ) -> bool:
        page = address & ~(PAGE - 1)
        pc = uc.reg_read(UC_RH850_REG_PC)
        self.mem_faults.append(
            {
                "access": access,
                "address": address,
                "size": size,
                "value": value & 0xFFFFFFFF,
                "pc": pc,
            }
        )
        self.log(
            f"unmapped access type={access} addr={address:#010x} size={size} "
            f"value={value & 0xFFFFFFFF:#010x} pc={pc:#010x}"
        )

        if (
            self.args.stub_low_fetch
            and access == unicorn.UC_MEM_FETCH_UNMAPPED
            and address < self.args.stub_low_fetch_max
            and len(self.low_fetch_stubs) < self.args.stub_low_fetch_limit
        ):
            resume_pc = uc.reg_read(UC_RH850_REG_CTPC) or uc.reg_read(UC_RH850_REG_LP)
            self.low_fetch_stubs.append(
                {
                    "pc": pc,
                    "fault_addr": address,
                    "resume_pc": resume_pc,
                }
            )
            self.log(f"  stubbed low fetch {address:#010x} -> resume {resume_pc:#010x}")
            uc.reg_write(UC_RH850_REG_PC, resume_pc)
            return True

        if not self.args.autopage or len(self.auto_pages) >= self.args.autopage_limit:
            return False

        try:
            uc.mem_map(page, PAGE)
            self.auto_pages.add(page)
            self.log(f"  autopaged zero page at {page:#010x}")
            return True
        except UcError:
            return False

    def dump_state(self) -> None:
        self.log("\nregisters:")
        for reg, name in REG_NAMES.items():
            try:
                value = self.mu.reg_read(reg)
            except UcError:
                continue
            self.log(f"  {name:<6} {value:#010x}")

        if self.trace:
            self.log("\ntrace:")
            for address, size in self.trace[-self.args.trace_tail :]:
                self.log(f"  {address:#010x} (+{size})")
        if self.trace_events:
            self.log("\ntrace hits:")
            for item in self.trace_events[-self.args.trace_tail :]:
                self.log(
                    "  pc={pc:#010x} size={size} r6={r6:#010x} r7={r7:#06x} r8={r8:#010x} r14={r14:#010x} r29={r29:#010x}".format(
                        **item
                    )
                )

        if self.mem_faults:
            self.log("\nlast faults:")
            for fault in self.mem_faults[-min(8, len(self.mem_faults)):]:
                self.log(
                    "  pc={pc:#010x} access={access} addr={address:#010x} size={size} value={value:#010x}".format(
                        **fault
                    )
                )

        if self.cal_reads:
            self.log("\ncal reads:")
            for read in self.cal_reads[-min(8, len(self.cal_reads)):]:
                self.log(
                    "  pc={pc:#010x} cal={address:#010x} size={size} value={value:#010x}".format(
                        **read
                    )
                )

        if self.ram_writes:
            self.log("\nram writes:")
            for write in self.ram_writes[-min(16, len(self.ram_writes)):]:
                self.log(
                    "  pc={pc:#010x} ram={address:#010x} size={size} value={value:#010x}".format(
                        **write
                    )
                )
        if self.watch_reads:
            self.log("\nwatch reads:")
            for item in self.watch_reads[-min(16, len(self.watch_reads)):]:
                self.log("  pc={pc:#010x} addr={address:#010x} size={size}".format(**item))
        if self.watch_writes:
            self.log("\nwatch writes:")
            for item in self.watch_writes[-min(16, len(self.watch_writes)):]:
                self.log(
                    "  pc={pc:#010x} addr={address:#010x} size={size} value={value:#010x}".format(
                        **item
                    )
                )
        if self.low_fetch_stubs:
            self.log("\nlow fetch stubs:")
            for item in self.low_fetch_stubs[-min(16, len(self.low_fetch_stubs)):]:
                self.log(
                    "  pc={pc:#010x} fault={fault_addr:#010x} resume={resume_pc:#010x}".format(
                        **item
                    )
                )
        if self.recent_mem:
            self.log("\nrecent mem:")
            for item in list(self.recent_mem)[-min(24, len(self.recent_mem)):]:
                kind_name = "read" if item["kind"] == 0 else "write"
                self.log(
                    f"  {kind_name:<5} pc={item['pc']:#010x} addr={item['address']:#010x} "
                    f"size={item['size']} value={item['value']:#010x}"
                )

        ep_dump = self.mu.mem_read(EP_BASE, 0x80)
        self.log(f"\nEP[0:0x80] @ {EP_BASE:#010x}:\n{ep_dump.hex()}")

    def run(self) -> int:
        variant_dir = FW_ROOT / self.args.variant
        if not variant_dir.exists():
            raise FileNotFoundError(f"Variant directory missing: {variant_dir}")
        self.can_slots = parse_can_rx_slots(variant_dir / "block0_strategy.bin")

        self.map_blob(STRATEGY_BASE, variant_dir / "block0_strategy.bin", "strategy")
        self.map_blob(RAM_INIT_BASE, variant_dir / "block1_ram.bin", "ram_init")
        self.map_blob(BLOCK2_BASE, variant_dir / "block2_ext.bin", "block2")
        self.map_blob(CAL_BASE, pick_calibration(self.args.variant, self.args.cal), "cal")
        self.map_runtime()
        self.seed_registers()
        self.install_hooks()

        starts = TASK_SEQUENCES.get(self.args.sequence, [self.args.start])
        replay_records: List[Dict[int, bytes]] = []
        if self.args.replay:
            for raw_line in self.args.replay.read_text().splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                replay_records.append(parse_replay_record(line))
            if self.args.replay_steps:
                replay_records = replay_records[: self.args.replay_steps]

        run_count = max(1, len(replay_records))
        rc = 0
        try:
            for run_idx in range(run_count):
                replay_desc = ""
                if replay_records:
                    overrides = replay_records[run_idx]
                    self._inject_can_mailboxes(overrides)
                    replay_desc = " ".join(f"{can_id:#05x}={payload.hex()}" for can_id, payload in sorted(overrides.items()))
                self._reset_runtime_logs()
                for start in starts:
                    self.mu.reg_write(UC_RH850_REG_PC, start)
                    self.mu.reg_write(UC_RH850_REG_LP, self.args.lp)
                    self.log(
                        f"starting step={run_idx + 1}/{run_count} @ {start:#010x} count={self.args.count} "
                        f"sp={self.args.sp:#010x} gp={self.args.gp:#010x} tp={self.args.tp:#010x} "
                        f"ep={self.args.ep:#010x} lp={self.args.lp:#010x} ctbp={self.args.ctbp:#010x} psw={self.args.psw:#x}"
                    )
                    self.log(
                        f"message mode={self.args.message_mode} can_id={int(self.message_context.get('can_id', 0)):#05x} "
                        f"payload={str(self.message_context.get('payload_hex', '')).ljust(16, '0')[:16]} "
                        f"({self.message_context.get('description', '')})"
                    )
                    if replay_desc:
                        self.log(f"replay {replay_desc}")
                    self.mu.emu_start(start, 0, count=self.args.count)
                    if self.args.dump_each_step:
                        self.dump_state()
            self.log("emulation completed without Unicorn exception")
            return 0
        except UcError as exc:
            self.log(f"emulation stopped with Unicorn error: {exc}")
            rc = 1
            return rc
        finally:
            self.dump_state()


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--variant", default="AM", help="Transit strategy variant under firmware/.../decompressed/")
    p.add_argument("--cal", type=Path, help="Calibration blob override")
    p.add_argument("--start", type=resolve_entry, default=ENTRY_ALIASES["lka"], help="Entry alias or absolute address")
    p.add_argument(
        "--message-mode",
        choices=("raw", "openpilot-lka", "openpilot-lmc-heartbeat"),
        default="raw",
        help="Build the input payload from raw hex or from the ford-lka branch semantics",
    )
    p.add_argument("--sequence", choices=sorted(TASK_SEQUENCES), help="Run a preset sequence of entrypoints in one emulator state")
    p.add_argument("--count", type=int, default=64, help="Max instructions to execute")
    p.add_argument("--trace-limit", type=int, default=128, help="Max executed PCs to record")
    p.add_argument("--trace-tail", type=int, default=16, help="How many trace entries to print")
    p.add_argument(
        "--trace-range",
        action="append",
        type=parse_watch_range,
        default=[],
        help="PC range to include in filtered trace hits, e.g. --trace-range 0x0108d000:0x01090000",
    )
    p.add_argument(
        "--watch",
        action="append",
        type=parse_watch_range,
        default=[],
        help="RAM address range to log reads/writes for, e.g. --watch 0x40010000:0x40011000",
    )
    p.add_argument("--autopage", action="store_true", help="Auto-map zero pages on unmapped access")
    p.add_argument("--autopage-limit", type=int, default=16, help="Max zero pages to auto-map")
    p.add_argument("--stub-low-fetch", action="store_true", help="Return from low-memory fetches via CTPC/LP instead of faulting")
    p.add_argument("--stub-low-fetch-max", type=parse_int, default=0x10000, help="Upper bound for low-memory fetch stub addresses")
    p.add_argument("--stub-low-fetch-limit", type=int, default=64, help="Max low-memory fetches to stub before failing")
    p.add_argument("--sp", type=parse_int, default=STACK_BASE + STACK_SIZE - 0x20)
    p.add_argument("--gp", type=parse_int, default=CAL_BASE)
    p.add_argument("--tp", type=parse_int, default=0)
    p.add_argument("--ep", type=parse_int, default=EP_BASE)
    p.add_argument("--lp", type=parse_int, default=0)
    p.add_argument("--ctbp", type=parse_int, default=CTBP_DEFAULT)
    p.add_argument("--psw", type=parse_int, default=PSW_SUPERVISOR)
    p.add_argument("--seed-can-caller", action="store_true", default=True)
    p.add_argument("--no-seed-can-caller", action="store_false", dest="seed_can_caller")
    p.add_argument("--inject-can", action="store_true", default=True)
    p.add_argument("--no-inject-can", action="store_false", dest="inject_can")
    p.add_argument("--desired-angle-deg", type=float, default=2.5, help="openpilot-lka target wheel angle")
    p.add_argument("--current-angle-deg", type=float, default=0.0, help="openpilot-lka current wheel angle")
    p.add_argument("--desired-curvature", type=float, default=0.0, help="openpilot-lka planner curvature (1/m)")
    p.add_argument("--lat-active", action="store_true", default=True, help="openpilot-lka emits an active frame")
    p.add_argument("--no-lat-active", action="store_false", dest="lat_active")
    p.add_argument(
        "--reg",
        action="append",
        default=[],
        help="Extra register override, e.g. --reg r14=0x40014000",
    )
    p.add_argument(
        "--payload-hex",
        default="",
        help="Optional 0x3CA/0x213/etc payload bytes placed at PAYLOAD_BASE as hex, e.g. 11223344",
    )
    p.add_argument(
        "--mailbox",
        action="append",
        default=[],
        help="Override one injected CAN mailbox, e.g. --mailbox 0x3CA=837e686d00000000",
    )
    p.add_argument(
        "--poke",
        action="append",
        default=[],
        help="Write raw bytes into emulated memory, e.g. --poke 0xfffff979=01 or --poke 0xfffff978=0000",
    )
    p.add_argument("--replay", type=Path, help="JSONL file of mailbox snapshots to replay across repeated runs")
    p.add_argument("--replay-steps", type=int, default=0, help="Optional cap on replay snapshots used")
    p.add_argument("--dump-each-step", action="store_true", help="Dump trace/watch state after every replay step")
    return p


def main() -> int:
    args = build_argparser().parse_args()
    harness = TransitHarness(args)
    return harness.run()


if __name__ == "__main__":
    raise SystemExit(main())
