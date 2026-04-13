---
title: Simulator (Athrill)
nav_order: 30
---

# Simulator — Athrill V850E2M

## Stack

- **[Athrill2](https://github.com/toppers/athrill)** — TOPPERS V850E2M instruction-set simulator (ISS), C, single-stepping CPU with bus + MPU abstraction.
- **[autoas/as](https://github.com/parai/as)** — AUTOSAR 4.4 BSW open-source reference (EcuM, CanIf, Com, PduR, CanTp, Dcm, NvM, ComM, CanSM) with a UNIX-socket CAN simulator.

Location: `simulator/athrill/`

## What works

Athrill builds with Ford patches applied (see `tools/athrill_apply_patches.py`). Both Transit and F-150 firmware load and execute without illegal-instruction errors — Athrill's V850E2M decoder handles the Transit's RH850 extended ops (or at least skips them without crashing).

- Transit firmware executes (PC advances, no fatal exceptions).
- F-150 firmware also loads and runs.

## What does not work

**PC-injection into CAN handlers crashes immediately.** When we try to jump execution directly into a known handler (e.g., the `0x3CA` LKA handler at `0x0108D684`), the CPU crashes because register state (SP, GP, EP) is wrong without real boot code. The function's prologue (`PREPARE` instruction) tries to write to garbage stack addresses.

The fundamental issue is that the Transit binary is a stripped flat blob with no ELF section headers. Athrill can load it at the right base address, but it has no startup sequence that would initialize SP/GP/EP to their real runtime values. Without real boot code, any non-trivial function entry crashes.

**Zero calibration reads observed** in straight sequential execution. AUTOSAR COM is interrupt-driven — the code path from "CAN frame arrived" → "read cal value → compute torque" only runs when an ISR delivers a PDU, which single-step sequential execution never triggers.

## Patches applied to Athrill

See `tools/athrill_apply_patches.py`:

- `loader.c` — tolerate missing DWARF/symbol sections, fall back to `mpu_get_pointer` when ROM not yet mapped.
- `main.c` — inject `ford_setup_cpu()` before `do_cui()` to seed AUTOSAR BSW state.
- `cpuemu.c` — replace `Exception!! + exit(1)` with `PC += 2` so unknown ops skip rather than kill the sim.
- `cpu_config.c` — suppress decode-error spam; expose `cal_current_pc`.
- `bus.c` — `cal_log_pc[]`/`cal_log_addr[]` ring buffer for tracing mem accesses.
- `mpu.c`, `elf_section.c`, `elf_dwarf_line.c` — silence non-fatal warnings.

## BSW init values (seeded by `ford_setup_cpu()`)

```c
bus_put_data32(0, 0x40010100, 0x00030003);  // Com + CanIf states
bus_put_data8 (0, 0x4001010E, 0x03);        // CanIf = STARTED
bus_put_data8 (0, 0x40010140, 0x02);        // EcuM = RUN
bus_put_data8 (0, 0x40010170, 0x03);        // main loop = RUNNING
```

## Why the 90% Ghidra static path is more productive than simulation

The sim's key blocker (SP/GP/EP wrong without boot code) cannot be fixed without either:
1. Reverse engineering the boot sequence completely to reproduce initial register state, or
2. Wiring autoas CAN socket to Athrill's RS-CAN peripheral so BSW fires real interrupts and sets up register state properly.

Option 2 is the right long-term path but significant integration work. In the meantime, the Ghidra 90%-clean-decompile corpus (`/tmp/pscm/decompiled/`) + AI annotation (`tools/pipeline/annotate.py`) is the productive static analysis route.

## If you want to push the sim further

1. Wire autoas CAN socket to Athrill's RS-CAN peripheral registers.
2. Inject APA / LKA / BrakeSpeed / Yaw CAN frames at 10 ms tick from autoas.
3. Let the Ford ISR fire, COM route the PDU, and watch cal reads appear in `cal_log_addr[]`.
4. With cal reads working, fuzz strategy inputs to find the LCA gate.
