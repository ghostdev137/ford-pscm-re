---
title: Home
nav_order: 1
---

# Ford PSCM Firmware Reverse Engineering

Unlock driver-assist features Ford disables in firmware on the 2025 Transit — and map the same module across Escape, F-150, and 2026 Transit.

## Who is this for?

- **Transit owners** who want continuous lane-keep or highway APA.
- **openpilot / comma.ai developers** porting lateral control to the Transit.
- **Automotive reverse engineers** interested in the TKP EPS / V850E2M PSCM platform.
- **Curious people** who've never touched firmware before — start with [Getting Started](getting-started.html).

## Current status

| Item | Status |
|---|---|
| [LKA lockout removal + full authority](lka.html) | ✅ **Flashed, drive-confirmed** — torque median +184% |
| [APA high-speed / standstill](apa.html) | Built, not yet road-tested |
| [LCA enable](lca.html) | Cal done, AS-built reverts — help wanted |
| Ghidra decompiler (RH850 patch) | ✅ 42% → 90% clean on Transit firmware |
| F-150 cal RE | ✅ All offsets confirmed, patched VBFs built — pending test-flash |

## Learning path

If you're new, read in this order:

1. **[Getting Started](getting-started.html)** — what a PSCM is, what you need, what the simplest thing to try is.
2. **[Glossary](glossary.html)** — all the acronyms.
3. **[VBF Files Explained](vbf-explained.html)** — what's actually inside a Ford firmware file.
4. **[Per-File VBF Catalog](per-file-catalog.html)** — every file in the repo, what it is, where it flashes.
5. **[PSCM Architecture](architecture.html)** — how the module is laid out internally.
6. Pick a feature: **[LKA](lka.html)**, **[LCA](lca.html)**, or **[APA](apa.html)**.
7. **[Flashing Guide](flashing.html)** — when you're ready to write to the vehicle.

## For openpilot developers specifically

See [Notes for openpilot](openpilot.html). TL;DR: flash [`LKA_FULL_AUTHORITY.VBF`](../firmware/patched/LKA_FULL_AUTHORITY.VBF), drive `0x213 DesTorq` continuously on MS-CAN. Don't bother enabling Ford LCA.

## Reference

- [Calibration map](calibration-map.html) — known cal fields and patch targets.
- [VBF patches](vbf-patches.html) — what each patched VBF changes and why.
- [CAN / UDS reference](can-ids.html) — message catalog and UDS commands.
- [PSCM Architecture](architecture.html) — MCU, memory map, CAN dispatch.
- [Decompiler setup](decompiler.html) — Ghidra + RH850 patch, scripts, AI pipeline.
- [Simulator](simulator.html) — Athrill status and limitations.
- [VBF format spec](vbf-format.html) — terse format reference.
- [Transit torque arbitration map](transit-arbiter-map.html) — arbiter entry points, Q15 scaling, TAUB writes.
- [Transit LCA hunt (0x3CC / 0x3D6)](transit-lca-hunt.html) — PDU-table gate blocking LCA.
- [Vehicles](vehicles/) — per-vehicle PSCM docs.

## Repository layout

```
ford-pscm-re/
├── firmware/
│   ├── Transit_2025/              ← primary target (KK21 / LK41)
│   ├── Transit_2026/              ← new platform (RK31) — unmapped
│   ├── Escape_2022/               ← LCA donor (LX6C) — same platform as Transit
│   ├── Escape_2024/               ← newer Escape (PZ11)
│   ├── F150_2022/                 ← different platform (ML34/ML3V) — reference
│   ├── F150_2021_Lariat_BlueCruise/  ← BlueCruise donor for torque curves
│   └── patched/                   ← modified VBFs ready to flash
├── analysis/
│   ├── transit/                   ← APA gate analysis, CAN dispatch
│   └── f150/                      ← F-150 cal RE, flash verdict
├── simulator/
│   └── athrill/                   ← V850E2M emulator with Ford patches
├── tools/
│   ├── ghidra_v850_patched/       ← forked SLEIGH: 42%→90% on Transit
│   ├── scripts/                   ← Ghidra headless scripts
│   ├── pipeline/                  ← AI annotation client
│   └── *.py                       ← VBF tooling, UDS harness
└── docs/
    ├── archive/                   ← superseded docs (kept for history)
    └── ...
```

## Contributing

Issues and PRs welcome at <https://github.com/ghostdev137/ford-pscm-re>. High-value contributions:

- Drive the patched firmware and report what happens.
- Help chase the LCA AS-built revert.
- Fill in undocumented regions of the calibration map.
- Port the patches to 2026 Transit (`RK31`).
- Help with the emulator — AUTOSAR CAN socket bridge is the blocker.

## Safety

Modified PSCM firmware can disable power steering. **I have bricked one PSCM doing this work.** Don't flash anything until you've read the [Flashing Guide](flashing.html) and you have a recovery plan (donor module, dealer nearby, or friend with a tow rig). Never flash somebody else's vehicle without consent.
