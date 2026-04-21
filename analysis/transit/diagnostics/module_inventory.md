# 2025 Transit Custom 320 LWB — FDRS VIN-Session Module Inventory

Per-module diagnostic specs extracted from a FDRS VIN-session dump covering
22 ECUs on the vehicle. Every file is Ford CANdelaStudio MDX XML format
(directly parsable with standard XML tools).

Source folder: `firmware/Transit_2025/diagnostics/`

## Module table

| CAN ID | Module | Size | DIDs | Routines | DTCs | Role |
|---|---|---|---|---|---|---|
| `0x6F0` | BCMC | 370K | 98 | 15 | 29 | Body Control Module "C" |
| `0x706` | **IPMA** | 2.0 MB | 322 | 42 | 123 | **Image Processing Module A (camera — sends LKA cmd 0x3CA to PSCM)** |
| `0x716` | GWM | 2.9 MB | 209 | 13 | 32 | Gateway Module A (network bridge) |
| `0x720` | IPC | 945K | 181 | 16 | 58 | Instrument Panel Cluster |
| `0x724` | **SCCM** | 459K | 82 | 10 | 43 | **Steering Column Control Module (torque-sensor-adjacent)** |
| `0x725` | WACM | 338K | 84 | 8 | 7 | Wireless Accessory Charging |
| `0x726` | BCM | 4.3 MB | 682 | 58 | 272 | Body Control Module (vehicle-level config) |
| `0x727` | ACM | 1.1 MB | 228 | 18 | 38 | Audio Front Control |
| **`0x730`** | **PSCM** | **514K** | **106** | **10** | **50** | **Power Steering Control Module (our main target)** |
| `0x733` | HVAC | 761K | 127 | 15 | 53 | HVAC Control |
| `0x737` | RCM | 1.6 MB | 186 | 9 | 150 | Restraints Control (seatbelt / hands-on signals) |
| `0x751` | RTM | 367K | 101 | 19 | 6 | Radio Transceiver |
| `0x754` | TCU | 1.4 MB | 113 | 8 | 43 | Telematic Control Unit |
| `0x760` | ABS/SOBDMC | 2.3 MB | 310 | 17 | 396 | **ABS Control (vehicle speed + lateral-accel feeds)** |
| `0x764` | CCM | 268K | 57 | 7 | 10 | Cruise Control |
| `0x7C4` | SODL | 217K | 54 | 8 | 18 | Side Obstacle Detection - Left |
| `0x7C6` | SODR | 217K | 54 | 8 | 18 | Side Obstacle Detection - Right |
| `0x7C7` | ACCM | 162K | 40 | 7 | 10 | Air Conditioning Control |
| `0x7D0` | APIM | 2.8 MB | 206 | 20 | 46 | Accessory Protocol Interface (SYNC) |
| `0x7E0` | PCM | 2.3 MB | 310 | 17 | 396 | **Engine / Powertrain Control** |
| `0x7E2` | SOBDM | 2.3 MB | 310 | 17 | 396 | Secondary OBD Control "C" |
| `0x7E4` | BECM | 3.3 MB | 296 | 14 | 173 | Battery Energy Control |
| `0x7E6` | SOBDMC | 2.3 MB | 310 | 17 | 396 | Secondary OBD Control (mirror) |

## Most LKA-relevant neighbors

Beyond `0x730 PSCM`, these modules shape the LKA command/feedback chain:

### `0x706 IPMA` — camera (sender of `0x3CA Lane_Assist_Data1`)

322 DIDs including writable customer-side settings at security_03:

| DID | Role |
|---|---|
| `0x41FA` | Lane Assist Switch Status (live readable) |
| `0xDE20` | **Lane Assist Customer Settings** (writable) |
| `0xDE25` | **Highway Assist Customer** (writable — BlueCruise-class) |
| `0x42DB` | Pre Collision Assist Switch Status |
| `0xDE0B/C/D/F/10/16` | Park Assist / Vehicle / Misc config blocks |

IPMA also exposes dev routines: `0xFD47 Aurix XCP Password`, `0xFD48 Treerunner XCP Password`, `0xFD49 HSM Control` — confirms multi-MCU architecture (Aurix + Treerunner) with XCP password gating.

### `0x724 SCCM` — steering column

82 DIDs. Directly upstream of PSCM for handwheel position/torque sensing.
Worth grepping for torque-sensor-related DIDs to understand what the PSCM
receives from the column module specifically.

### `0x760 ABS`

310 DIDs, 396 DTCs. Provides vehicle-speed and lateral-acceleration signals
that PSCM uses for speed-gated LKA behavior (`cal+0x0690` min-speed comparison).

### `0x726 BCM`

Vehicle-level feature configuration. 682 DIDs. Many `0xDEnn` config DIDs
exist here too — BCM/IPMA cross-check may determine which LKA-class
features are enabled at the vehicle level before the PSCM even sees a
command.

## Top-level artifacts

- `firmware/Transit_2025/diagnostics/<CAN>_<MODULE>.xml` — source XML specs
- `analysis/transit/diagnostics/module_inventory.json` — programmatic per-module summary
- `analysis/transit/diagnostics/transit_pscm_dids.json` — PSCM DID detail (106 entries)
- `analysis/transit/diagnostics/README.md` — PSCM-specific deep dive

## Sourcing

Folder originally at `~/Downloads/2025_TRANSIT CUSTOM 320 LWB_WF0RXXTA8HSR88240/`.
Pulled from FDRS during a per-VIN diagnostic session; FDRS downloads the
relevant module MDX for the connected vehicle automatically. This is
Transit Custom (European/global-market) 320 LWB — mechanically similar
to the North American Transit 2025 our repo primarily targets.

Some platform differences may exist between Transit Custom (EU) and
Transit (NA), but the PSCM/IPMA architecture is shared.
