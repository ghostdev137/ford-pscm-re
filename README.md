# Ford PSCM Firmware Reverse Engineering

Reverse engineering of the Ford Power Steering Control Module (PSCM) firmware across **2025 Transit**, **2022/2024 Escape**, and **2022/2021 F-150**. Primary goals: unlock disabled driver-assist features on Transit (LKA authority expansion, APA standstill, Lane Centering) via calibration patches, and document the platform fully so others can port the work.

> **Status (2026-04-13):** `LKA_FULL_AUTHORITY.VBF` flashed and drive-confirmed — column torque median +184% vs stock. Ghidra decompiler patched to 90% clean-decompile on Transit firmware. F-150 and Transit remain distinct V850-family targets; in this Ghidra setup the F-150 full ELF also lifts best under `v850e3`.

---

## What works today

| Patch | File | Status |
|---|---|---|
| LKA lockout removal | `LKA_NO_LOCKOUT.VBF` | Flashed, confirmed |
| LKA full authority (F-150 BlueCruise envelope) | `LKA_FULL_AUTHORITY.VBF` | **Flashed, drive-confirmed** — torque median 0.44 → 1.25 Nm (+184%) |
| LKA + APA high-speed | `LKA_NO_LOCKOUT_APA_HIGH_SPEED.VBF` | Ready |
| LKA + APA standstill | `LKA_APA_STANDSTILL.VBF` | Ready |
| LCA enable attempt | `LCA_ENABLED.VBF` | Cal works, AS-built reverts on power cycle |

All patched VBFs are in `firmware/patched/`. Flash with FORScan → PSCM → Module Programming → Load from file.

---

## Hardware

| Item | Transit 2025 | F-150 2022/2021 |
|---|---|---|
| Vendor | ThyssenKrupp Presta (TKP) EPU | Different vendor |
| MCU | Renesas **RH850** (V850-family, extended ops) | Renesas **V850-family** (`v850e3` gives the best full-ELF lift in this repo) |
| Endianness | Little-endian | Little-endian |
| Cal base | `0x00FD0000` (65,520 B, big-endian tables) | `0x101D0000` (195,584 B, little-endian tables) |
| ECU address | `0x730` (req) / `0x738` (resp) | `0x730` / `0x738` |
| Bus | MS-CAN | CAN FD (UDS over classical CAN) |

Transit and 2022 Escape share the same PSCM platform (`TKP_INFO:35.13.8.0_FIH`), same 65,520-byte cal layout. F-150 is a completely different platform — not cross-compatible.

---

## Repository layout

```
ford-pscm-re/
├── firmware/
│   ├── Transit_2025/       ← primary target (KK21 / LK41)
│   ├── Transit_2026/       ← new platform (RK31) — unmapped
│   ├── Escape_2022/        ← LCA cal donor (LX6C) — same platform as Transit
│   ├── Escape_2024/        ← newer Escape (PZ11)
│   ├── F150_2022/          ← different platform (ML34/ML3V) — reference
│   ├── F150_2021_Lariat_BlueCruise/  ← BlueCruise donor for torque curves
│   └── patched/            ← modified VBFs ready to flash
├── analysis/
│   ├── transit/            ← APA gate analysis, CAN dispatch map
│   └── f150/               ← F-150 cal RE, SBL/strategy findings, flash verdict
├── simulator/
│   └── athrill/            ← V850E2M emulator (Transit executes, limited by SP/GP)
├── tools/
│   ├── ghidra_v850_patched/  ← forked SLEIGH: 42% → 90% clean-decompile on Transit
│   ├── scripts/              ← Ghidra headless scripts (ProbeWithSeed, DumpDecomps, etc.)
│   ├── pipeline/             ← annotate.py: OpenAI-compatible client → GLM-4.7-Flash
│   └── *.py                  ← VBF tooling, UDS harness, etc.
└── docs/                   ← reference docs
```

---

## Reproducing the key results

### 1. Verify the LKA_FULL_AUTHORITY patch
```bash
python tools/vbf_decompress.py firmware/patched/LKA_FULL_AUTHORITY.VBF
# Expect: CRC16 PASS, CRC32 PASS, addr=0x00FD0000
```
Flash via FORScan. Read cal `+0x03C4` (32 bytes) via UDS to confirm the new torque curve is live:
```
req  0x730  10 12 23 44 00 FD 03 C4 00 20
resp 0x738  63 <32 bytes>
# Decoded as 8 BE float32: [0, 0.7, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5] Nm
```

### 2. Run Ghidra decompiler at 90%
```bash
# Install patched SLEIGH:
cp -r tools/ghidra_v850_patched ~/Library/ghidra/ghidra_<VERSION>_PUBLIC/Extensions/ghidra_v850
$(brew --prefix)/Cellar/ghidra/*/libexec/support/sleigh tools/ghidra_v850_patched/data/languages/v850e3.slaspec

# Headless decompile probe (requires transit_AH_blk0_0x01000000.bin extracted first):
$(brew --prefix)/Cellar/ghidra/*/libexec/support/analyzeHeadless /tmp/proj TestRun \
  -import /tmp/pscm/transit_AH_blk0_0x01000000.bin \
  -loader BinaryLoader -loader-baseAddr 0x01000000 \
  -processor "v850e3:LE:32:default" \
  -scriptPath tools/scripts \
  -postScript ProbeWithSeed.java -deleteProject \
  2>&1 | grep RESULT
# Expect: 90/100 clean
```

### 3. AI-annotate decompile output
```bash
# Dumps all clean decompiles to decompiles_clean/<addr>.c, then annotates:
python tools/pipeline/annotate.py \
  --input /tmp/pscm/decompiled/ \
  --endpoint http://100.69.219.3:8000/v1 \
  --model glm-4-flash
```

---

## Open questions

1. **LCA AS-built revert** — after filling LCA cal data from Escape, AS-built enable bits revert on power cycle. Suspected strategy-level VIN/vehicle-code check in block0.
2. **Cal addressing mode** — no `movhi 0x00FD` in Transit strategy. Cal is probably accessed via a data-space mirror address. Finding it unlocks static tracing of all cal reads.
3. **CAN 0x3CA vs 0x3A8 dispatch** — 178 raw-byte hits for 0x3A8 in Transit firmware vs 1 for 0x3CA, but 0x3CA is confirmed to work (LKA patches prove it). Likely matched via lookup table, not literal compare.
4. **Angle limit 5.86°** — `LaRefAng_No_Req` DBC 12-bit signed scale-0.05 artifact, not a PSCM firmware clamp. Could be changed by rescaling in opendbc.
5. **F-150 BlueCruise flash** — patched VBFs have valid CRC32. SBL confirmed no crypto verification of cal. Unknown: mask ROM boot behavior. Test on donor/bench module first.

---

## Quick links

**New here?** → [docs/getting-started.md](docs/getting-started.md) → [docs/glossary.md](docs/glossary.md)

**Flashing?** → [docs/vbf-patches.md](docs/vbf-patches.md) · [docs/flashing.md](docs/flashing.md)

**RE work?** → [docs/architecture.md](docs/architecture.md) · [docs/decompiler.md](docs/decompiler.md) · [docs/calibration-map.md](docs/calibration-map.md)

**openpilot?** → [docs/openpilot.md](docs/openpilot.md) — TL;DR: flash `LKA_FULL_AUTHORITY.VBF`, drive `0x213 DesTorq` on MS-CAN.

**CAN/UDS?** → [docs/can-ids.md](docs/can-ids.md)

**Emulator?** → [docs/simulator.md](docs/simulator.md)

---

**Disclaimer:** For research and personal-vehicle use only. Flashing modified firmware to a PSCM can disable power steering. One PSCM was bricked during this project. Understand the risk before writing to your own ECU.
