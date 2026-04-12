---
title: PSCM Architecture
nav_order: 6
---

# PSCM Firmware Architecture

## Hardware

- **MCU:** Renesas V850E2M / RH850 (32-bit, single-core, ~100 MHz)
- **EPS vendor:** ThyssenKrupp Presta (EPU variant)
- **Platform marker (readable via UDS):** `TKP_INFO:35.13.8.0_FIH`
- **Flash size:** ~1 MB (application) + separate bootloader region
- **RAM:** tens of KB, EP-window-addressed at `0x40000000+`

## Memory map (Transit `LK41-14D007-AH`)

| Region | Address | Purpose |
|---|---|---|
| Vectors / boot | `0x00000000` | Reset vector, exception table, boot ROM check |
| Strategy (block0) | ~`0x00F00000` | AUTOSAR BSW + Ford strategy code |
| Strategy continued | `0x010E1000` area | EPS lateral control, LKA/LCA/APA handlers |
| EPS core (block2) | separate | Low-level motor control loop (separate safety rating) |
| Calibration | `0x00FD0000`–`0x00FDFFF0` | 65,520 bytes, our patch target |
| RAM (EP window) | `0x40000000`+ | AUTOSAR BSW state, stacks, heap |
| Peripherals | `0xFF000000`+ | CAN, SPI, ADC, timers |

## Block structure in the VBF

Each programming-session flash delivers 3 blocks:

1. **block0 — strategy.** Main application image. Contains AUTOSAR BSW (EcuM, Com, CanIf, PduR, CanTp, Dcm, NvM, ComM, CanSM) and Ford's EPS strategy (LKA, APA, LCA handlers, steering math, fault detection).
2. **block1 — RAM init image.** Pre-initialized data copied into RAM on boot. AUTOSAR `.data` segment basically.
3. **block2 — EPS core.** Separately-certified low-level motor control. We don't touch this — it runs the inner current/torque loop at high rate and contains functional-safety code.

Plus the **calibration partition** (`14D007`) as a separate VBF and the **SBL** (`14D005`) as another separate VBF. SBL is uploaded to RAM by FORScan before erasing application flash.

## AUTOSAR layer

Ford uses AUTOSAR 4.x. BSW modules observed in binary (by strings + call patterns):

| Module | Role |
|---|---|
| EcuM | ECU state machine (STARTUP / RUN / SHUTDOWN) |
| Com | Signal routing between PDUs and application |
| CanIf | CAN driver interface, HW filter config |
| PduR | PDU router (Com ↔ CanTp ↔ CanIf) |
| CanTp | ISO-15765 transport (segmented UDS) |
| Dcm | Diagnostic Communication Manager (implements UDS services) |
| NvM | Non-volatile data manager (AS-built, learned values) |
| ComM | Communication state manager (wake/sleep) |
| CanSM | CAN state manager |

Initialization values for these modules (what our emulator has to fake):

```c
// EP window base 0x40010100
0x40010100 u32 = 0x00030003  // Com + CanIf states
0x4001010E u8  = 0x03        // CanIf = STARTED
0x40010140 u8  = 0x02        // EcuM = RUN
0x40010170 u8  = 0x03        // main loop = RUNNING
```

(Derived by reading `autoas/as` source and matching the address layout the Ford binary expects.)

## Strategy layer (Ford code)

The strategy implements:
- **LKA:** reads `0x3CA` (LKA command from IPMA), applies torque through EPS core, maintains lockout timers from cal `+0x06B0`.
- **APA:** reads `0x3A8` (PAM angle command), gates on speed from `0x415`, only applies below cal `+0x02E0` threshold.
- **LCA:** reads `0x3D3` (LCA command), applies continuous centering torque. **Gated by cal presence + AS-built + unknown third check on Transit.**
- **DesTorq path:** `0x213` is an openpilot-friendly interface — direct torque command that goes through the same output stage as LKA/LCA/APA. Subject to LKA authority window (which we opened up).

Entry points & MainFunctions run on 1 ms / 10 ms / 100 ms ticks via the OS scheduler.

## Calibration structure

65,520 bytes, lives at `0x00FD0000`. Contents include:
- Float lookup tables (speed, angle, torque curves)
- u16 timer arrays (lockouts, debounces)
- u8 enable flags
- String identifiers (strategy PN, cal PN, TKP_INFO) readable as DIDs

A full field-by-field map is a long-term RE project. Our current annotations live in [calibration-map.html](calibration-map.html).

## What we don't touch

- **EPS core block.** Runs the inner motor-control loop, has safety certification. Modifying it can cause unintended steering torque.
- **Bootloader.** On-chip, not in our VBFs.
- **Vectors / exception handlers.** Same.
