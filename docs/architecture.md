---
title: PSCM Architecture
nav_order: 6
---

# PSCM Firmware Architecture

## MCU platform — Transit vs F-150

| Vehicle | MCU | Ghidra treatment | Notes |
|---|---|---|---|
| 2025 Transit / 2022 Escape | Renesas **RH850** (V850-family, extended instruction set) | Use `v850e3:LE:32:default` from patched SLEIGH | Stock Ghidra 12 V850 spec decodes 0/48; our patch reaches 90/100 |
| 2022/2021 F-150 | Renesas **V850** (baseline) | Stock Ghidra V850 decodes it cleanly | Older-generation PSCM |

> **TriCore/Aurix was a false lead.** Earlier sessions saw peripherals named `LDRAM_13`/`SPRAM_13` and suspected Infineon TriCore. Those names appeared only because we loaded the binary as TC172x in Ghidra — they were not evidence. Both Transit and F-150 are confirmed Renesas V850-family.

Both are 32-bit little-endian cores. The Transit's RH850 adds extended 32-bit instruction encodings not present in baseline V850 — that is why the stock Ghidra V850 spec fails on Transit but decodes F-150 correctly.

## Transit hardware identity

- **EPS vendor:** ThyssenKrupp Presta (EPU variant)
- **Platform marker (readable via UDS):** `TKP_INFO:35.13.8.0_FIH`
- **Flash size:** ~1 MB (application) + separate bootloader region
- **RAM:** EP-window-addressed at `0x40000000+`

The same `TKP_INFO` string appears in 2022 Escape firmware — confirming both vehicles share the same PSCM silicon and memory map. F-150 does NOT have this string; it is a different vendor.

## Memory map (Transit `LK41-14D007-AH`)

| Region | Address | Purpose |
|---|---|---|
| Vectors / boot | `0x00000000` | Reset vector, exception table |
| Strategy (block0) | `0x01000000` | AUTOSAR BSW + Ford strategy code (1,048,560 B) |
| RAM init (block1) | `0x10000400` | Initial data image copied to RAM on boot |
| Calibration | `0x00FD0000`–`0x00FDFFF0` | 65,520 bytes, big-endian tables — our patch target |
| RAM (EP window) | `0x40010100`+ | AUTOSAR BSW state, stacks |
| Peripherals | `0xFF000000`+ | CAN, SPI, ADC, timers |

## Memory map (F-150 Lariat BlueCruise `ML34-14D007-EDL`)

| Region | Address | Notes |
|---|---|---|
| Strategy | `0x10040000` | 1,571,840 B |
| Calibration | `0x101D0000` | 195,584 B, **little-endian** tables |
| SBL | `0xFEBE0000` | Uploaded to RAM during flashing |

F-150 cal is little-endian — different from Transit/Escape big-endian. Do not cross-apply offsets.

## Block structure (Transit VBF)

| Block | Flash addr | Size | Contents |
|---|---|---|---|
| strategy (block 0) | `0x01000000` | 1,048,560 B | Main application: AUTOSAR BSW + Ford strategy |
| RAM init (block 1) | `0x10000400` | 3,072 B | `.data` segment |
| calibration | `0x00FD0000` | 65,520 B | Cal table (what we patch) |
| SBL | (RAM only) | ~64 KB | Secondary bootloader — not stored in flash |

> There is no separate "EPS core block2" for this platform. Earlier docs were wrong about this. The `-14D005-*` VBF has `sw_part_type = SBL` — it is the secondary bootloader, uploaded to RAM during flashing and never persisted. Motor control code lives inside block0 alongside the strategy.

## CAN RX dispatch (Transit 2025 AH)

CAN ID table at file offset `0x2BE0`: array of 8-byte records mapping CAN ID → mailbox slot. Function pointer table at `0x316C`: array of BE32 pointers indexed by `(mailbox_slot - 9)`.

Key handlers:

| CAN ID | Slot | Handler | Purpose |
|---|---|---|---|
| `0x213` | 29 | `0x0108F094` | DesiredTorqBrk (IPMA torque command) |
| `0x3A8` | 25 | `0x0108E02E` | APA command from PAM |
| `0x3CA` | 23 | `0x0108D684` | LKA command from IPMA |
| `0x730` | 10 | `0x0108BF42` | UDS diagnostic request |

All handlers share identical 16-byte prologue (`18 21 06 D0 ...`) — compiler-emitted PREPARE + register save + mailbox buffer load.

## AUTOSAR layer

Ford uses AUTOSAR 4.x BSW. BSW state lives near `0x40010100`:

```c
0x40010100: Com/CanIf states  = 0x00030003
0x4001010E: CanIf             = 0x03 (STARTED)
0x40010140: EcuM              = 0x02 (RUN)
0x40010170: main loop         = 0x03 (RUNNING)
```

## Calibration addressing (unresolved)

No `movhi 0x00FD` pairs appear in Transit strategy code — the cal base address is never loaded as a literal. Cal is probably accessed via a data-space mirror address set up by the SBL or startup code. This blocks static tracing of which strategy functions read which cal offsets. Work-around: use Ghidra bulk decompile output in `/tmp/pscm/decompiled/` + AI annotation to infer cal consumers from variable naming patterns.

## Strategy features

| Feature | CAN in | CAN out | Cal region |
|---|---|---|---|
| LKA | `0x3CA` | `0x3CC` (status) | `+0x03C4` (torque curve), `+0x06B0` (lockout timers), `+0x0690` (min-speed) |
| APA | `0x3A8` | `0x082` (status) | `+0x02C4` (speed table) |
| LCA | `0x3D3` | `0x3CC` | `+0x06C3..0xFFDC` (11 regions, empty on Transit) |
| DesTorq | `0x213` | — | Subject to LKA authority window |

## What we do not modify

- **Boot vectors / exception handlers** — on-chip, not in our VBFs
- **Motor control code** (lives inside block0 but is the inner EPS safety loop) — touching it risks loss of power steering in hardware fault conditions
