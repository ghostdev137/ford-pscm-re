---
title: Emulator Notes
nav_order: 30
---

# PSCM Emulator Notes (Athrill2 + autoas)

## Stack

- **[Athrill2](https://github.com/toppers/athrill)** — TOPPERS V850E2M ISS, C, single-stepping CPU emulator with bus+MPU abstraction.
- **[autoas/as](https://github.com/parai/as)** — AUTOSAR 4.4 BSW open-source implementation (EcuM, CanIf, Com, PduR, CanTp, Dcm, NvM, ComM, CanSM) with a UNIX-socket CAN simulator.

## Patches applied to Athrill

See `tools/athrill_apply_patches.py`.

- **`loader.c`** — tolerate missing DWARF/symbol sections (stripped Ford ELF), fall back to `mpu_get_pointer` when ROM region isn't mapped yet.
- **`main.c`** — inject `ford_setup_cpu()` before `do_cui()` to seed AUTOSAR state.
- **`cpuemu.c`** — replace `Exception!!` + `exit(1)` with `PC += 2` so unknown ops don't kill the sim.
- **`cpu_config.c`** — suppress decode-error spam; expose `cal_current_pc` for every dispatched instruction.
- **`bus.c`** — add `cal_log_pc[]` / `cal_log_addr[]` ring buffer for calibration-access tracing.
- **`mpu.c`**, **`elf_section.c`**, **`elf_dwarf_line.c`** — silence non-fatal warnings.

## BSW init values (EP window at `0x40010100`)

Derived by reading autoas source and matching the layout Ford's ELF expects:

```c
bus_put_data32(0, 0x40010100, 0x00030003);  // Com + CanIf states
bus_put_data8 (0, 0x4001010E, 0x03);        // CanIf = STARTED
bus_put_data8 (0, 0x40010140, 0x02);        // EcuM = RUN
bus_put_data8 (0, 0x40010170, 0x03);        // main loop = RUNNING
```

## What works

- Boot reaches main loop.
- 118 function entry points each execute up to ~18k clocks.
- Up to 122,000 unique instruction addresses covered from strategy entries.

## What doesn't work

- **Zero calibration reads observed.** AUTOSAR COM indirection (event-driven PDU routing) means the code path from "CAN frame arrived" to "read cal value and compute torque" only runs when an interrupt delivers a CanIf PDU, which sequential execution can't simulate.
- Integration with autoas CAN-socket simulator is not wired up. That is the next step: let autoas handle BSW init + PDU routing while Athrill runs the Ford strategy code on real messages.

## Future work

1. Wire autoas CAN socket to Athrill's RS-CAN peripheral registers.
2. Have autoas inject APA / LKA / BrakeSpeed / Yaw CAN frames at 10 ms tick.
3. Let the Ford ISR fire, COM route the PDU to the strategy, and watch cal reads light up.
4. With cal reads working, we can fuzz strategy inputs to find the LCA gate.
