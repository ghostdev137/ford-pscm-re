---
title: 2021 F-150 Lariat 502A BlueCruise
parent: Vehicles
nav_order: 6
---

# 2021 Ford F-150 Lariat 502A — BlueCruise

Donor firmware set from a 2021 F-150 Lariat 502A with BlueCruise. Same `ML34` /
`ML3V` PSCM platform family as the [2022 F-150](f150-2022.html) set, but with
the newer `EDL` calibration and the fully lifted combined ELF already in this repo.

This page used to describe the F-150 work as an early TODO. That is no longer
accurate: the 2021 BlueCruise PSCM has now been fully reverse-engineered at the
calibration / strategy / message-map level, and patched cal VBFs have already
been built.

## Identity

| Field | Value |
|---|---|
| Vehicle | 2021 F-150 Lariat, 502A package, BlueCruise-equipped |
| PSCM strategy prefix | `ML3V-14D003-*` |
| PSCM cal prefix | `ML34-14D007-*` |
| PSCM supplementary prefix | `ML34-14D004-*` |
| PSCM SBL prefix | `ML34-14D005-*` |
| Vehicle data bus | **CAN FD** (bit-rate-switched CAN, higher bandwidth) |
| UDS diagnostic bus | Classical CAN, `0x730` request / `0x738` response |
| Platform compatibility with Transit | ❌ Not compatible — different vendor, different cal layout |

## Files in this repo

`firmware/F150_2021_Lariat_BlueCruise/`:

| File | `sw_part_type` | Role | Size |
|---|---|---|---|
| `ML3V-14D003-BD.VBF` | `EXE` | Strategy — block0 | 1.5 MB |
| `ML34-14D004-EP.VBF` | `DATA` | Supplementary / secondary data | 66 KB |
| `ML34-14D005-AB.VBF` | `SBL` | Secondary Bootloader | 10 KB |
| `ML34-14D007-EDL.VBF` | `DATA` | Calibration | 197 KB |

## What is now confirmed

All four files:
- use `frame_format = CAN_STANDARD` and `ecu_address = 0x730` on the UDS flash path
- run on a Renesas **RH850** target
- use a little-endian calibration layout at `0x101D0000`

The key 2021 F-150 calibration gates are no longer guesses:

| Cal offset | Value | Meaning |
|---|---|---|
| `+0x0114` | `10.0` float32 LE | LKA minimum engage speed |
| `+0x0120` | `10.0` float32 LE | LCA / BlueCruise minimum engage speed |
| `+0x0140` | `0.5` float32 LE | APA minimum engage speed |
| `+0x0144` | `8.0` float32 LE | APA maximum engage speed |
| `+0x07ADC` | `10000` u16 LE | LKA supervisor timer neighborhood |
| `+0x07ADE` | `10000` u16 LE | sibling LKA supervisor timer word |
| `+0x07E64` | `10000` u16 LE | ESA / TJA-side supervisor timer neighborhood |

The current message split is also much tighter:

- `0x3CA` = direct `LKA`
- `0x3A8` = `APA`
- `0x3D3` = best-current primary `LCA / BlueCruise` command PDU in this exact image
- `0x3D7` = object / ESA sideband path feeding the shared lateral supervisor
- `0x3CC` = PSCM feedback / availability TX slot, packer still not fully isolated

See:
- [F-150 flash verdict](../analysis/f150/index.html)

Deeper repo notes live under `analysis/f150/`, especially:
- `verdict.md`
- `eps_dbc_message_trace.md`
- `cal_plain_language_map.md`

## Patch set

Patched calibration VBFs already exist under `firmware/patched/F150_Lariat_BlueCruise/`.
The narrowest first-flash candidate remains `LKA_LOCKOUT_ONLY.VBF`, with broader
variants for the LKA minimum-speed gate and APA envelopes also built.

The current repo verdict is:

- CRC32 recomputation is understood and implemented
- no in-firmware cal RSA/SHA verification path has been found
- remaining risk is cold-boot mask-ROM behavior, not flash-time rejection by the strategy/SBL path

## CAN FD note

The 2021+ F-150 uses CAN FD on its chassis/ADAS bus. This matters if you're doing openpilot-style integration — a classical CAN Panda won't interoperate with the ADAS bus at full bandwidth. Use a CAN FD-capable interface (comma black panda supports CAN FD, OpenDBC has F-150 definitions).

The UDS flashing path is still classical CAN, so FORScan with a VCM-II or RLink will flash this module fine.

## Status

**Fully RE'd at the current repo level.** Strategy / cal / SBL findings are written
up, patched VBFs are built, and the remaining open work is narrower follow-up:
exact `0x3CC` packer proof, exact `0x3D3` vs `0x3D6` dispatcher boundary proof, and
real-world flash / drive validation.

## See also

- [2022 F-150](f150-2022.html) — older revisions of the same platform.
- [Per-file catalog entry](../per-file-catalog.html#2021-f-150-lariat-502a--bluecruise-firmwaref150_2021_lariat_bluecruise)
- [LKA on Transit](../lka.html) — for contrast on how Ford tunes LKA differently per vehicle.
