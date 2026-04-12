---
title: Ford PSCM Firmware Reverse Engineering
---

# Ford PSCM Firmware Reverse Engineering

Unlocking driver-assist features on the 2025 Ford Transit by patching the Power Steering Control Module (PSCM) firmware.

## Status

| Feature | Patch | Status |
|---|---|---|
| LKA 10-second lockout | `LKA_NO_LOCKOUT.VBF` | **Flashed ✓** |
| APA high-speed (50/200 kph) | `APA_HIGH_SPEED.VBF` | Ready |
| Lane Centering Assist | `LCA_ENABLED.VBF` | Flashed, AS-built reverts (strategy gate suspected) |

## Docs

- [VBF container format](vbf-format.html)
- [Calibration map](calibration-map.html)
- [Emulator notes (Athrill + autoas)](emulator-notes.html)
- [Full README on GitHub](https://github.com/ghostdev137/ford-pscm-re)

## Repo layout

```
firmware/
  Transit_2025/   KK21-* (AG→AL) and LK41-* (AD→AH) PSCM firmware revisions
  Transit_2026/   RK31-* PSCM (new platform)
  Escape_2022/    LX6C-* (same PSCM platform as Transit — source for LCA cal data)
  Escape_2024/    PZ11-* PSCM
  F150_2022/      ML34/ML3V-* PSCM (different platform, reference only)
  patched/        Our modified VBFs ready to flash
simulator/
  athrill/        TOPPERS Athrill2 V850E2M ISS with Ford-specific patches
tools/
  pscm_test32.py          32-bit J2534 harness for TOPDON RLink
  ford_download.py        FDRS download URL extraction
  vbf_decompress.py       VBF LZSS decompressor
  decompile_block0.py     V850E2M disassembly helpers
  ...
```

## Hardware under test

- 2025 Ford Transit, PSCM: ThyssenKrupp Presta EPS EPU
- Strategy PN: `LK41-14D007-AH`
- MCU: Renesas V850E2M / RH850
- Bus: MS-CAN `0x730`/`0x738`, requires VCM-II or TOPDON RLink X3 J2534

## Quick links — patches

- [Calibration offsets table](calibration-map.html#lka-lockout-timer-table--0x06b0--0x06c2)
- [APA speed floats](calibration-map.html#apa-active-park-assist-speed-table--0x02c4--0x02e0)

---

*For research only. Modifying PSCM firmware can disable power steering — flash at your own risk.*
