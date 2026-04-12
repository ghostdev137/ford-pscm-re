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

| Patch | Status |
|---|---|
| [LKA 10-s lockout removal](lka.html) | ✅ **Flashed, working** |
| [APA high-speed unlock](apa.html) | Built, not yet road-tested |
| [LCA enable](lca.html) | Cal done, AS-built reverts — help wanted |

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

See [Notes for openpilot](openpilot.html). TL;DR: flash [`LKA_NO_LOCKOUT.VBF`](https://github.com/ghostdev137/ford-pscm-re/blob/main/firmware/patched/LKA_NO_LOCKOUT.VBF), drive `0x213 DesTorq` continuously on MS-CAN. Don't bother enabling Ford LCA.

## Reference

- [Calibration map](calibration-map.html) — known fields in the 65,520-byte cal.
- [CAN / UDS reference](can-ids.html) — message catalog and UDS commands.
- [VBF format spec](vbf-format.html) — terse format reference.
- [Vehicles](vehicles/) — per-vehicle PSCM docs.
- [Emulator notes](emulator-notes.html) — Athrill + autoas integration.

## Repository layout

```
ford-pscm-re/
├── firmware/
│   ├── Transit_2025/   ← our primary target (KK21 / LK41)
│   ├── Transit_2026/   ← new platform (RK31) — mostly unmapped
│   ├── Escape_2022/    ← LCA donor (LX6C) — same platform as Transit
│   ├── Escape_2024/    ← newer Escape (PZ11)
│   ├── F150_2022/      ← different platform (ML34/ML3V) — reference only
│   └── patched/        ← our modified VBFs ready to flash
├── simulator/
│   └── athrill/        ← V850E2M emulator with Ford patches
├── tools/              ← VBF parsing, decompilation, UDS harness, etc.
└── docs/               ← you are here
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
