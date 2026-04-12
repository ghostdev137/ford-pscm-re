# Ford PSCM Firmware Reverse Engineering

Reverse engineering of the Ford Power Steering Control Module (PSCM) firmware used on the 2025 Transit and related platforms (Escape, F-150). Goal: unlock disabled driver-assist features (LKA lockout removal, APA high-speed, Lane Centering Assist) via targeted calibration/strategy patches.

> **Status:** `LKA_NO_LOCKOUT.VBF` successfully flashed via FORScan. APA and LCA patches built and ready. Full firmware docs, cal offsets, VBF tooling, and emulator notes below.

---

## Table of Contents
- [Hardware](#hardware)
- [Firmware Layout](#firmware-layout)
- [VBF Container Format](#vbf-container-format)
- [Calibration Map (PSCM)](#calibration-map-pscm)
- [Patches](#patches)
- [CAN / UDS Protocol](#can--uds-protocol)
- [Cross-Vehicle Comparison](#cross-vehicle-comparison)
- [Emulator (Athrill / autoas)](#emulator)
- [Flashing Workflow](#flashing)
- [Open Questions](#open-questions)
- [References](#references)

---

## Hardware

| Item | Value |
|---|---|
| Vendor | ThyssenKrupp Presta (TKP) EPS EPU |
| Platform ID | `TKP_INFO:35.13.8.0_FIH` |
| MCU | Renesas V850E2M / RH850 |
| Flash base | `0x00FD0000` (calibration) |
| Strategy base | `0x00F00000` approx. |
| RAM base | `0x40000000` (EP window at `0x40010100`) |
| ECU address | `0x730` (req) / `0x738` (resp) — ISO-15765 |
| Bus | MS-CAN (not HS-CAN — J2534/VCM-II required) |

## Firmware Layout

Each VBF typically contains 3 blocks:

| Block | Address | Purpose |
|---|---|---|
| block0 | strategy | Main application code (AUTOSAR + EPS strategy) |
| block1 | RAM init | Initialized data image copied to RAM on boot |
| block2 | EPS core | Low-level motor control / safety code |
| cal | `0x00FD0000` | 65,520 byte calibration table (this is what we patch) |
| SBL | — | Secondary Bootloader, delivered separately during flashing |

## VBF Container Format

```
header { ... } ;            # ASCII key=value block, terminated by '};'
for each block:
    u32 start_address        (big-endian)
    u32 length               (big-endian)
    u8  data[length]         # raw or LZSS (data_format_identifier=0x10)
    u16 crc16                # CRC16-CCITT on DECOMPRESSED data
u32 file_checksum            # CRC32 over all block data
```

Key header fields: `sw_part_number`, `sw_part_type`, `ecu_address=0x730`, `data_format_identifier` (`0x00` uncompressed / `0x10` LZSS), `file_checksum`.

- CRC16 = CRC16-CCITT over decompressed data.
- CRC32 = standard over the block data section.
- For uncompressed VBFs, CRC16 is on raw data.

## Calibration Map (PSCM)

Big-endian throughout. Offsets relative to `0x00FD0000`.

| Offset | Type | Field | Original | Patched | Confidence |
|---|---|---|---|---|---|
| `+0x02C4..02E0` | `float[]` | APA speed table (kph) | 4.6 / 8.0 cap | 50.0 / 200.0 | MEDIUM |
| `+0x02DC` | `float` | APA low-speed thresh | 4.6 | 50.0 | MEDIUM |
| `+0x02E0` | `float` | APA high-speed cap | 8.0 | 200.0 | MEDIUM |
| `+0x06B0..06C2` | `u16[]` | LKA lockout timer table (×10 ms) | various | all zero | HIGH |
| `+0x06B6` | `u16` | LKA main lockout timer | 0x03E8 (1000 = 10 s) | 0x0000 | **HIGH** |
| `+0xF188` DID | ASCII | Strategy PN | `LK41-14D007-AH` | — | — |
| `+0xF10A` DID | ASCII | Calibration PN | — | — | — |

GP-relative LCA data regions copied from Escape 2022 cal (`1FMCU9J98NUA09141`, LX6C PSCM, same platform & memory map):

`0x06C3, 0x06C8, 0x0E79, 0x0E82, 0x21BC, 0x2FCE, 0x327C, 0x33DD, 0x3AD1, 0x41AD, 0xFFDC` — total 4,460 bytes across 11 regions, populating all 12 GP-relative LCA offsets.

## Patches

| File | Changes | Status |
|---|---|---|
| `patched/LKA_NO_LOCKOUT.VBF` | Timer table `+0x06B0..06C2` zeroed (13 bytes) | **FLASHED ✓** |
| `patched/APA_HIGH_SPEED.VBF` | APA speed 50/200 kph | Ready |
| `patched/LCA_ENABLED.VBF` | Timer + 4.5 KB Escape LCA cal data | Ready (AS-built reverts on AM — likely strategy-level gate) |

All patched VBFs: CRC16 PASS, CRC32 PASS, 66,915 bytes, `data_format_identifier=0x00`, `ecu_address=0x00FD0000`.

## CAN / UDS Protocol

| CAN ID | Name | Purpose |
|---|---|---|
| `0x082` | EPAS_INFO | EPS status broadcast |
| `0x07E` | StePinion | Steering pinion angle |
| `0x091` | Yaw | Yaw rate |
| `0x213` | DesTorq | Desired torque (from IPMA) |
| `0x3A8` | APA | Active Park Assist cmd |
| `0x3CA` | LKA | Lane Keep Aid cmd |
| `0x3CC` | LKA_Stat | LKA status |
| `0x3D3` | LCA | Lane Centering Assist cmd |
| `0x415` | BrkSpeed | Brake + wheel speed |
| `0x730` | PSCM_Diag | UDS request |
| `0x738` | PSCM_Resp | UDS response |

UDS services used during RE:
- `0x10 0x03` — Extended diagnostic session
- `0x3E 0x00` — Tester Present
- `0x22 F188 / F10A` — Read strategy / cal PN
- `0x23 0x44 <addr32> <len32>` — ReadMemoryByAddress (dumps cal/RAM)

## Cross-Vehicle Comparison

| Vehicle | Strategy PN prefix | PSCM platform | LCA |
|---|---|---|---|
| 2025 Transit | `LK41` / `KK21` | TKP EPS EPU | **Disabled** |
| 2022 Escape | `LX6C` | TKP EPS EPU (same) | Enabled |
| 2022 F-150 | `ML34` / `ML3V` | different | Enabled |
| 2025 Transit IPMA | `NK3T` | — | Camera (Mobileye EyeQ3 + Mando LKAS) |

Escape & Transit share same PSCM memory map and 65,520-byte cal layout — this is what enables the cross-flash experiment.

## Emulator

`tools/v850/emu/athrill/` — TOPPERS Athrill2 V850E2M ISS, patched to:
- Suppress loader errors (missing DWARF/symbols in stripped Ford ELF)
- Load RAM segments directly from ELF
- Ignore undefined instruction exceptions (PC += 2 and continue)
- Track `cal_current_pc` for memory-access logging
- Inject AUTOSAR BSW state at EP-window addresses

BSW init values (derived from `reference/autoas/` source):

```c
bus_put_data32(0, 0x40010100, 0x00030003);  // Com/CanIf states
bus_put_data8 (0, 0x4001010E, 0x03);         // CanIf = STARTED
bus_put_data8 (0, 0x40010140, 0x02);         // EcuM = RUN
bus_put_data8 (0, 0x40010170, 0x03);         // main loop = RUNNING
```

**Blocker:** AUTOSAR COM is interrupt-driven. Sequential entry-by-entry execution in Athrill never reaches cal reads. Next step: wire autoas CAN socket simulator to Athrill's RS-CAN controller so BSW handles routing while the real firmware processes messages.

## Flashing

1. Put VCM-II (or TOPDON RLink X3 with Ford DLL) on OBD.
2. Open FORScan → Service → Module Programming → select **PSCM**.
3. Point at patched `.VBF`. FORScan handles SBL upload + erase + flash + activate.
4. Cycle ignition. Check for `P0600`/`C0051` DTCs.
5. Drive and test the feature.

> Only FORScan reliably routes UDS to `0x730` via the Ford J2534 stack.
> Direct ctypes calls to `RLink-FDRS.dll` (32-bit) only see `0x59E` — bus routing not set up without the Rlink Platform middleware.

## Open Questions

- LCA AS-built config reverts on power cycle even with cal data filled — strategy-level gate somewhere in block0?
- Removed code at `0x010E1000` (between AG→AH→AL→AM revisions): 80 EP-relative accesses, no cal reads, no CAN refs — **not** the LCA handler.
- `RJ6T` / `PZ11` firmware are IPMA, not PSCM — still hunting for shipped Escape PSCM binary for full diff.
- Can we bypass FORScan and drive the flash sequence directly via J2534?

## References

- [autoas/as](https://github.com/parai/as) — AUTOSAR 4.4 BSW reference
- [TOPPERS Athrill](https://github.com/toppers/athrill) — V850E2M ISS
- [icanhack.nl](https://icanhack.nl/) — Ford MS-CAN / UDS notes
- [openpilot comma.ai](https://github.com/commaai/openpilot) — LKAS architecture
- Ford FDSP: `www.fdspcl.dealerconnection.com` (requires dealer auth)
- VBF format: Volvo/Ford binary programming container (LZSS + CRC16-CCITT + CRC32)

---

**Disclaimer:** For research and personal-vehicle use only. Flashing modified firmware to a PSCM can disable power steering. Understand the risk before writing to your own ECU.
