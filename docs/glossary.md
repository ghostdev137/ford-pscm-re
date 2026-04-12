---
title: Glossary
nav_order: 3
---

# Glossary

Short definitions of every acronym and term used in this repo.

## Vehicle / module names

| Term | Meaning |
|---|---|
| **PSCM** | Power Steering Control Module — the target of this project. Sits on the steering rack. |
| **IPMA** | Image Processing Module "A" — the forward-facing camera module. Sends LKA / LCA commands to the PSCM. On Transit this is `NK3T`. |
| **PAM** | Park Assist Module — the ultrasonic/parking controller. Sends `0x3A8` to the PSCM during APA maneuvers. |
| **PCM** | Powertrain Control Module — the engine ECU. `0x7E0` on HS-CAN. Not our concern. |
| **BdyCM** | Body Control Module — lights, doors, gateway. Bridges HS-CAN and MS-CAN. |
| **ABS** | Antilock Brake module — publishes `0x415` wheel speed, used by PSCM's APA speed gate. |
| **RCM** | Restraints Control Module — publishes `0x091` yaw rate. |
| **EPS** | Electric Power Steering — the physical motor + torque sensor stack. |
| **EPU** | ThyssenKrupp's EPS product line (Electric Power Unit). |

## Protocols / standards

| Term | Meaning |
|---|---|
| **CAN** | Controller Area Network — the message bus cars run on. |
| **HS-CAN** | High-Speed CAN, 500 kbps. Powertrain bus. Pins 6/14 on OBD-II. |
| **MS-CAN** | Medium-Speed CAN, 125–500 kbps depending on chassis. Body / chassis bus. Pins 3/11 or HS3 on Transit. PSCM lives here. |
| **ISO 15765** | Standard for segmented messages over CAN (a.k.a. CAN-TP / CAN Transport Protocol). Used by UDS. |
| **UDS** | Unified Diagnostic Services, ISO 14229. Client/server protocol over CAN for ECU communication. |
| **SID** | Service Identifier — a UDS command byte (e.g. `0x22`, `0x23`, `0x3E`). |
| **DID** | Data Identifier — a 16-bit tag for a piece of data readable via UDS `0x22`. E.g. `F188` = strategy PN. |
| **DTC** | Diagnostic Trouble Code — the P0xxx / C0xxx stuff. |
| **AUTOSAR** | Open automotive software architecture. The PSCM uses AUTOSAR 4.x BSW. |
| **BSW** | AUTOSAR Basic Software — reusable OS/driver/comm layer. |
| **PDU** | Protocol Data Unit — an AUTOSAR-internal unit of data routed between modules. |
| **SBL** | Secondary Bootloader — uploaded to RAM by FORScan before flash erase. |
| **J2534** | Standard API for pass-thru programming adapters (VCM-II, RLink, etc). |

## Firmware internals

| Term | Meaning |
|---|---|
| **VBF** | Versatile Binary Format — Ford/Volvo firmware file container. See [vbf-explained](vbf-explained.html). |
| **Block** | A contiguous chunk of binary inside a VBF, targeted at a specific flash address. |
| **block0** | Strategy — main application code. |
| **block1** | RAM init image — pre-initialized data copied to RAM on boot. |
| **block2** | EPS core — low-level motor control. |
| **Strategy** | Ford's high-level control code (when/how to steer). In block0 of the VBF. |
| **Calibration / cal** | Tables of numbers (thresholds, curves) that tune strategy. Stored separately at `0x00FD0000` on this platform. |
| **AS-built** | Non-volatile configuration bits set by the dealer when the car is built. Enable/disable optional features. |
| **GP-relative** | Global Pointer relative addressing — V850/RH850 feature where data is accessed as `GP + signed displacement`. |
| **EP-relative** | Element Pointer relative — similar but for a second data pointer, often used for stack-local or per-task data. |
| **EP window** | RAM region at `0x40010100+` holding AUTOSAR BSW state on this ECU. |

## Flashing / tooling

| Term | Meaning |
|---|---|
| **FORScan** | Windows app for Ford diagnostics and programming. |
| **FDRS** | Ford Diagnostic & Repair System — dealer-tier version of FORScan. |
| **VCM-II** | Ford's official J2534 adapter. |
| **RLink X3** | TOPDON's J2534 adapter, works with FORScan on Ford. |
| **STN2232 / ELM327** | Generic OBD-II Bluetooth dongles. Will NOT reach PSCM without MS-CAN support. |
| **CRC16-CCITT** | Polynomial `0x1021`, init `0xFFFF`. Used on VBF block data. |
| **CRC32** | Standard CRC32. Used on whole-file VBF checksum. |
| **LZSS** | Lempel-Ziv-Storer-Szymanski compression. Used in VBFs with `data_format_identifier=0x10`. |

## Features

| Term | Meaning |
|---|---|
| **LKA** | Lane Keep Aid — tug you back when drifting. Active only briefly. |
| **LDW** | Lane Departure Warning — alerts without steering. Precursor to LKA. |
| **LCA** | Lane Centering Assist — continuous lane keeping. What we want. |
| **TJA** | Traffic Jam Assist — low-speed LCA variant. Same code path on this platform. |
| **APA** | Active Park Assist — auto-parks the vehicle. |
| **DesTorq** | "Desired Torque" — the `0x213` CAN message carrying the torque command the PSCM should apply. |
| **ESA** | Evasive Steering Assist — augments driver avoidance input. |

## Parts numbers / platforms

| Term | Meaning |
|---|---|
| **LK41 / KK21** | 2025 Transit PSCM / strategy prefixes. |
| **RK31** | 2026 Transit PSCM (new platform). |
| **LX6C** | 2022 Escape PSCM (our LCA donor). |
| **PZ11** | 2024 Escape PSCM. |
| **ML34 / ML3V** | 2022 F-150 PSCM (different platform). |
| **NK3T** | 2025 Transit IPMA (camera module). |
| **TKP_INFO** | ThyssenKrupp Presta platform identifier string in the cal. |
