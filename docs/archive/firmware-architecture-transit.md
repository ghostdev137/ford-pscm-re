---
title: Transit PSCM firmware architecture
nav_order: 22
---

# Transit PSCM firmware architecture (LK41-14D007-AH / KK21-14D003-AH)

Consolidated from a Ghidra-based RE session on 2026-04-12. Complements `calibration-map.md`, `lka.md`, `apa.md`. Aims to be the high-level map a new contributor reads first.

## Binary layout

Extracted from `firmware/Transit_2025/KK21-14D003-AH.VBF` (strategy) and `LK41-14D007-AH` (calibration):

| Block | Flash addr | Size | Contents |
|---|---|---|---|
| strategy (block 0) | `0x01000000` | 1,048,560 B | Main application code + data |
| RAM init (block 1) | `0x10000400` | 3,072 B | Initial RAM image copied on boot |
| EPS core (block 2) | `0x20FF0000` | 327,680 B | Low-level motor / safety code |
| calibration | `0x00FD0000` | 65,520 B | 65,520-byte cal table (what we patch) |
| SBL | — | ~64 KB | Secondary bootloader (not shipped in cal/strategy VBFs) |

Strategy binary is a mixed code + data blob — no ELF section headers. Function pointer table at file offset `0x0E2B0` is the primary recovery handhold (BE32 pointers into `0x0100xxxx`).

## CPU

Renesas V850E2M (RH850 family). Little-endian. 32-bit, 16-bit halfword instructions with 32-bit extended encodings. Uses:
- `sp` (r3) — stack pointer
- `gp` (r4) — **scratch on Transit** (despite the name — do not assume it's a global cal pointer)
- `tp` (r5) — scratch / function arg
- `ep` (r30) — element pointer, often base for per-CPU state struct
- `lp` (r31) — link register (return address)
- `CTBP` — CALLT table base, used for compact calls to common helpers

**Calibration addressing — unresolved.** No `movhi 0x00FD` pairs appear in strategy. Cal base `0x00FD0000` appears exactly once as a literal (at flash `0x0100D7A3`, inside what looks like an MPU descriptor). Cal is probably accessed via a data-space mirror address not yet identified, OR via the SBL pre-loading cal contents into a RAM shadow. Static RE of cal-read sites is blocked until this is solved.

## CAN RX dispatch

**CAN ID table** at file `0x2BE0..0x2CF0`: array of 8-byte records:

```
struct CanRxEntry {
    uint16_t can_id;      // big-endian standard ID
    uint8_t  flags;       // 0x01 typical
    uint8_t  mailbox_slot;
    uint16_t size_enc;    // 0x0108 (11-bit), 0x0308 (29-bit), etc.
    uint16_t pad;         // 0
};
```

**Function pointer table** at file `0x316C..0x31D0`: array of BE32 function pointers, indexed by `(mailbox_slot - 9)`.

### Full decoded map (Transit 2025 AH)

| CAN ID | Slot | Handler fn | Purpose (from DBC) |
|---|---|---|---|
| `0x07D` | 33 | — | PSCM proprietary |
| `0x076` | 35 | — | PSCM proprietary |
| `0x077` | 34 | — | PSCM proprietary |
| `0x083` | 32 | `0x01090150` | EPAS_INFO |
| `0x167` | 31 | `0x0108FA2C` | Steering angle sensor |
| `0x202` | 30 | `0x0108F53E` | ABS status |
| **`0x213`** | 29 | **`0x0108F094`** | **DesiredTorqBrk (IPMA target torque)** |
| `0x216` | 28 | `0x0108EA8A` | — |
| `0x217` | 27 | `0x0108E716` | — |
| `0x263` | 26 | `0x0108E3A2` | — |
| **`0x3A8`** | 25 | **`0x0108E02E`** | **APA command** |
| `0x3B3` | 24 | `0x0108D9E0` | — |
| **`0x3CA`** | 23 | **`0x0108D684`** | **Lane_Assist_Data1 (LKA cmd from IPMA)** |
| `0x40A..0x431` | 16–22 | 0x0108BD04..0x0108D310 | Powertrain / body |
| `0x4B0` | 15 | `0x0108C180` | BrakeSpeed wheel data |
| `0x60A..0x63C` | 11–14 | 0x0108BE22..0x0108C2A8 | Powertrain |
| `0x730` | 10 | `0x0108BF42` | **UDS diag request** |
| `0x7DF` | 9 | `0x0108C17E` | UDS broadcast request |
| `0x63D..0x738` | 52–57 | — | Extended IDs (size `0x0308`) |

All handlers begin with identical 16-byte prologue `18 21 06 D0 1B 01 09 10 00 80 DD 01 70 c8 e0 02` — compiler-emitted template (PREPARE + register save + mailbox buffer load).

## CAN TX — what PSCM sends

From DBC (`opendbc/ford_lincoln_base_pt.dbc`), PSCM is the sender of:

| ID | Name | Cycle | Key signals |
|---|---|---|---|
| `0x082` | EPAS_INFO | 10 ms | Column torque, EPS failure, hands-on detection |
| `0x130` | EPAS_INFO_2 | 10 ms | (probably — needs confirmation) |
| `0x3CC` | Lane_Assist_Data3_FD1 | **30 ms** | **`LatCtlLim_D_Stat` (cap reached flag), `LatCtlCpblty_D_Stat`, `LsmcBrk_Tq_Rq` (ABS yaw assist torque)** |

The `0x3CC` frame is the primary observable the LKA control loop writes into. Its packing function is the **fastest path to the torque-cap logic**: the code that sets `LatCtlLim_D_Stat = 2 (LimitReached)` is called from the same cycle that clips motor torque.

## AUTOSAR BSW substrate

Strategy is built on AUTOSAR 4.x BSW (Com / CanIf / EcuM / RTE). Reference source at `reference/autoas/` (parai/as). BSW state lives in a fixed structure near `0x40010100`:

```
0x40010100: Com/CanIf states (u32 0x00030003)
0x4001010E: CanIf = 0x03 STARTED
0x40010140: EcuM = 0x02 RUN
0x40010170: main loop = 0x03 RUNNING
```

Per repo `docs/emulator-notes.md` — required for emulator bringup.

## Calibration regions (partial)

Cal base `0x00FD0000`, total 65,520 B, BE throughout.

| Offset | Contents | Status |
|---|---|---|
| `+0x02C4..02E0` | APA speed table `[0, 0.3, 1.1, 1.8, 2.5, 3.2, 4.6, 8.0]` kph | Known, patchable |
| `+0x0280..04A0` | **LKA torque + speed scheduling** — 7 tables (fine/mild/std/aggressive Nm curves, 3× speed-bp copies) | Identified 2026-04-12; see `calibration-map.md` |
| `+0x06B0..06C2` | u16 LKA lockout timer table (10s main @ `+0x06B6`) | **Patched → zero in `LKA_NO_LOCKOUT.VBF`** |
| `+0xF188` | Strategy PN ASCII `LK41-14D007-AH` | DID read |

## Reverse engineering status

**Solved:**
- ✅ VBF format, LZSS decompression, CRC16/32 recomputation — all tooling in `tools/`
- ✅ LKA 10s lockout timer — found, flashed, driver-confirmed
- ✅ CAN RX dispatch map — complete for Transit AH
- ✅ LKA torque table region in cal — narrowed to `+0x0280..+0x04A0`
- ✅ Standalone torque curves identified: `+0x0344` (mild), `+0x0384` (aggressive), `+0x03C4` (standard, matches Escape exactly)

**Outstanding:**
- ❌ Which torque curve LKA actively reads at runtime (blocked on cal addressing mode)
- ❌ Where min-speed floor (~10 m/s from drive data) is encoded
- ❌ Driver-override torque threshold (~0.7–1.5 Nm observed)
- ❌ Exact cal→RAM mirror address (data-space view of cal)
- ❌ LCA strategy-level gate (why AS-built reverts on power cycle despite cal data filled)

**Promising next moves (icanhack VW method):**
1. Decompile the `0x3CC` TX packer — find the function that writes the `LatCtlLim_D_Stat` bits. Trace back for the comparator that decides "cap reached."
2. Decompile `0x3CA` RX handler @ `0x0108D684` — find the RAM addresses it writes `LaRefAng_No_Req` / `LkaActvStats_D2_Req` into, then find consumers of those RAM locations; one is the torque applier.
3. Grep disasm for float constant `0x41200000` (10.0f), `0x40E00000` (7.0f) — candidate min-speed and max-Nm immediates.
4. Consider athrill dynamic trace for the 0x3CA → torque-applier → 0x213 pipeline with cal-read logging enabled.

## Tooling cache

Bulk outputs on disk (regenerate via Ghidra scripts in `/tmp/pscm/*.java`):
- `/tmp/pscm/decompiled/` — 2,738 `.c` files per function
- `/tmp/pscm/disasm/` — 2,738 `.asm` files per function
- `/tmp/pscm/transit_{AH,AM,AL}_blk*.bin` — extracted strategy blocks
- `/tmp/pscm/Transit_AH.bin` — extracted calibration

Ghidra 12.0.4 project at `~/.ghidra/…/PSCM/` with GhidraMCP plugin (built from source against 12.0.4, patches at `/tmp/GhidraMCP/`).
