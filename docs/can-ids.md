---
title: CAN / UDS Reference
---

# CAN / UDS Reference — Transit PSCM

The PSCM is on the **MS-CAN** bus (medium-speed, 125 kbps on some chassis, 500 kbps on Transit). This is **not** the HS-CAN bus that most OBD tools default to. You need either:

- Ford VCM-II with the J2534 stack
- TOPDON RLink X3 with the FDRS DLL (`C:\Program Files\TOPDON\J2534\FORD\RLink-FDRS.dll`)
- A CAN interface physically wired into the HS3/HS4 gateway

Generic ELM327 on COM port will only see HS-CAN (PCM at `0x7E0`). You will not reach the PSCM from a generic dongle.

## CAN message catalog (observed)

| CAN ID | Name | Period | DLC | Sender | Notes |
|---|---|---|---|---|---|
| `0x07E` | StePinion | 10 ms | 8 | PSCM | Steering pinion angle |
| `0x082` | EPAS_INFO | 10 ms | 8 | PSCM | EPS status, APA/LKA active bits |
| `0x091` | Yaw | 10 ms | 8 | RCM | Yaw rate + lateral accel |
| `0x213` | DesTorq | 10 ms | 8 | IPMA | **Desired steering torque** — openpilot entry point |
| `0x3A8` | APA | 50 ms | 8 | PAM | Desired steering angle (parking) |
| `0x3CA` | LKA | 20 ms | 8 | IPMA | LKA torque command |
| `0x3CC` | LKA_Stat | 100 ms | 8 | PSCM | LKA state feedback |
| `0x3D3` | LCA | 20 ms | 8 | IPMA | Lane Centering command (absent on Transit) |
| `0x415` | BrkSpeed | 20 ms | 8 | ABS | 4-wheel speed + service brake |
| `0x730` | PSCM_Diag | — | 8 | Tester | UDS request to PSCM |
| `0x738` | PSCM_Resp | — | 8 | PSCM | UDS response |
| `0x59E` | — | — | — | Gateway | Visible via TOPDON without routing; diagnostic echo |

## UDS commands used

All examples on PSCM (`0x730` req, `0x738` resp). ISO-15765 handles flow-control (FC) automatically.

### Session / presence

```
# Tester Present (no response suppressed)
730  02 3E 00                    →  738  01 7E 00

# Extended Session
730  02 10 03                    →  738  06 50 03 00 32 01 F4
```

### Read DIDs

```
# Strategy part number (DID F188)
730  03 22 F1 88                 →  738  1x xx 62 F1 88 4C 4B 34 31 ...   = "LK41-14D007-AH"

# Calibration part number (DID F10A)
730  03 22 F1 0A                 →  738  1x xx 62 F1 0A ...

# ECU serial number (DID F18C)
730  03 22 F1 8C                 →  ...
```

### Read memory by address

Service `0x23` with the format byte `0x44` (addr size 4, len size 4):

```
# Read 20 bytes at 0x00FD06B0 (LKA timer table)
730  10 0A 23 44 00 FD 06 B0 00 14
738  30 00 00                    (flow control — continue)
730  21 ...                      (next consecutive frame if request spans frames)
738  21 62 ... (response with 20 bytes)
```

### Write memory by address (dangerous — used by SBL during flashing only)

`0x3D` with format byte `0x44`. Normally gated behind security access (`0x27`) and only available in programming session.

## UDS service codes referenced

| SID | Name | Used |
|---|---|---|
| `0x10` | DiagnosticSessionControl | default/extended/programming |
| `0x11` | ECUReset | — |
| `0x22` | ReadDataByIdentifier | dump PN / cal ID |
| `0x23` | ReadMemoryByAddress | dump cal/RAM |
| `0x27` | SecurityAccess | unlock for flashing |
| `0x2E` | WriteDataByIdentifier | AS-built writes |
| `0x31` | RoutineControl | erase, checksum-check |
| `0x34`/`0x36`/`0x37` | RequestDownload / TransferData / RequestTransferExit | flash sequence |
| `0x3D` | WriteMemoryByAddress | SBL writes |
| `0x3E` | TesterPresent | keep session alive |

See `tools/pscm_test32.py` and `tools/pscm_ram_dump.py` for working Python implementations.

## TOPDON RLink routing caveat

Direct ctypes calls to `RLink-FDRS.dll` from Python see only CAN ID `0x59E`. FORScan using the **same adapter** sees the full bus.

Root cause (suspected): the Ford J2534 DLL requires the **RLink Platform middleware** service (started when you open the RLink desktop app) to set up MS-CAN ↔ HS-CAN routing in the adapter firmware. Without it, the DLL opens a passthru channel that only the gateway's diagnostic echo reaches.

Workaround: use VCM-II, or proxy via FORScan, or wire directly to the MS-CAN pair.
