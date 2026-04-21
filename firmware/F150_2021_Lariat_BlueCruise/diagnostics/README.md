# F-150 2021 PSCM Diagnostic Specification (MDX)

Ford CANdelaStudio diagnostic database for the 2021 F-150 PSCM, covering
UDS DIDs, routines, sessions, security levels, memory map, and DTCs.

## Source

- **File:** `DSML34-3F964-AE.mdx`
- **Part number:** DS-ML34-3F964-AE
- **ECU name:** Power Steering Control Module
- **Platform prefix:** ML34 (F-150 2021 Lariat, matches repo firmware `ML34-14D007-EDL`, `ML34-14D005-AB`, `ML3V-14D003-BD`)
- **Created:** 2021-02-16 by Ford Motor Company
- **CANdela template:** Ford 4.12.0b
- **Rack vendor:** Nexteer (per DTC `NTC` prefix references)

## Contents

- 74 DIDs (`IdentifierByService`)
- 6 Routines (`RoutineControl`)
- 48 DTCs (mostly steering/torque/communication faults)
- 5 Sessions (Ford standard: default, extended, programming)
- 4 Security levels (`security_level_2` gates most writes)
- 8 Memory areas covering strategy, 2 cal partitions, SBL

## Memory map (from MDX) — matches RE findings byte-for-byte

| MDX name | Absolute base | Contents | Size |
|---|---|---|---|
| Strategy | `0x10040000` | `ML3V-14D003-BD` | 1,527 KB |
| Strategy Validity | `0x101BFC00` | trailer | 0x12C |
| Calibration 1 | `0x101C0000` | `ML34-14D004-EP` (supplementary) | 64 KB |
| Calibration 1 Validity | `0x101CFC00` | trailer | 0x12C |
| **Calibration 2** | **`0x101D0000`** | **`ML34-14D007-EDL`** (main cal, our patch target) | 192 KB |
| Calibration 2 Validity | `0x101FFC00` | trailer | 0x12C |
| Secondary Bootloader | `0xFEBE0000` | `ML34-14D005-AB` | 8,836 B |

Independent corroboration of the map in `analysis/f150/verdict.md`.

## Derived JSON

Structured extracts of DID metadata are in
`analysis/f150/diagnostics/ml34_dids.json` (name, number, size,
readable/writable, security level, sub-fields, units, resolution, enum
values). Used by `tools/panda_pscm_live_dids.py` (pending) and any
future on-car polling script.

## Why this matters to our patches

- **DID `0x330C`** (Steering Shaft Torque Sensor #2, units=Nm,
  resolution=1/10, offset=-12.7) is the driver-input torque signal the
  override state machine reads. Used to validate the `cal+0x29D4 / +0x29E0`
  override-threshold hypothesis on-car.
- **DID `0xEE05`** (Final Motor Torque, units=Nm) validates the
  `cal+0x03C4..+0x03E3` torque-authority patch — directly measurable.
- **DID `0xEE07`** (EPS System State) exposes the Normal/Limited-Assist
  transition that fires when override yields — observable event that
  distinguishes our patch's effect from stock.
- **DID `0xEE42`** (Active Features) has a dedicated LKA Feature State
  byte with PASSIVE/ACTIVE/LOCKED states — **LOCKED is probably what the
  10-s lockout timer triggers**, and our `LKA_NO_LOCKOUT` patch prevents.
- **DID `0xEE20`** (LoA Fault Reporting) captures the 8 newest
  Limitation-of-Availability DTCs — read this after any LKA drop to see
  which fault condition the rack reported.

## Cross-platform note

The `DSSZ1C-3F964-AB.MDX` in `firmware/_other_platforms/diagnostics/` is
for a different Ford platform (2024-era; possibly Explorer or
Super-Duty). DID numbers largely overlap with F-150 conventions
(`0x330C`, `0x3020`, `0xEE05`, `0xEE07` all present) but absolute
memory addresses and the enum content differ. Don't assume offsets
transfer between platforms.

## Transit MDX status

**Not yet acquired.** The Transit PSCM's diagnostic spec would be named
`DSLK41-3F964-*.mdx` or `DSKK21-3F964-*.mdx`. If found in a Ford FDRS
installation, add it to `firmware/Transit_2025/diagnostics/` and update
`analysis/transit/driver_override_patch_candidates.md` with the real
live-readable torque DID.
