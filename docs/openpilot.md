---
title: Notes for openpilot
nav_order: 14
---

# Notes for openpilot / comma.ai community

If you are coming here to build a Ford Transit openpilot port, this is the short version.

## TL;DR

1. **Flash [`LKA_FULL_AUTHORITY.VBF`](../firmware/patched/LKA_FULL_AUTHORITY.VBF)** — removes the 10-second lockout, lowers the min-speed floor to ~11 kph, and raises torque authority to F-150 BlueCruise levels (3.5 Nm at 70 kph, peak 6.5 Nm). Drive-confirmed +184% torque median vs stock.
2. **Drive `0x213 DesTorq` on MS-CAN** continuously. The PSCM accepts it as a torque command. With the lockout removed, the authority window stays open indefinitely.
3. You do **not** need to enable Ford LCA to do lane centering. Ford's LCA state machine is bypassed when you drive `0x213` directly.

## What the PSCM expects

The stock IPMA (`NK3T`) sends `0x3CA LKA` and `0x213 DesTorq` at 20 ms / 10 ms intervals. When it sends a nonzero torque in `0x213` while `0x3CA` indicates LKA active, the PSCM applies the torque through the EPS motor stage — **subject to the LKA lockout timer**.

Without the lockout patch, you get one 10-ms pulse of steering then 10 seconds of nothing. With the patch, continuous.

## Safety checks that **remain** after the patch

These are enforced in the EPS core (block2), which we do not modify:
- **Driver torque override** — push against the wheel, system yields.
- **Hands-off detection** — `0x082 EPAS_INFO` reports hands-on/off to the IPMA.
- **Max torque limit** — `0x213` values above a cal-defined cap are clipped.
- **Minimum speed floor** (~40 kph on stock, may be lower with APA patch).
- **Steering rate limits** — prevents sudden large commanded inputs.

These are the checks that keep the system from yanking the wheel. They are not affected by the LKA patch.

## CAN wiring

- MS-CAN is on HS3 (pins 12/13 on the OBD-II connector on Transit) — **not** pins 6/14 which are HS-CAN.
- You need a Panda or equivalent wired to HS3.
- Gateway isolation: the Transit BdyCM / gateway does not forward MS-CAN traffic to HS-CAN by default. You will see `0x730` PSCM diag on MS-CAN only.

## DBC starting points

Messages you will want in your DBC:

| ID | Name | Direction relative to your tool |
|---|---|---|
| `0x213` | DesTorq | TX — the torque command |
| `0x3CA` | LKA | TX — assert "LKA active" so PSCM accepts `0x213` |
| `0x082` | EPAS_INFO | RX — actual torque, hands-on/off, fault flags |
| `0x07E` | StePinion | RX — steering angle feedback |
| `0x091` | Yaw | RX — yaw rate |
| `0x415` | BrkSpeed | RX — wheel speed |

See [can-ids.html](can-ids.html) for the full catalog.

## Failure modes to watch for

- **IPMA fighting you** — the stock IPMA will also be sending `0x213`. Either (a) intercept and block it at your Panda, or (b) disable the IPMA from the MS-CAN bus. Method (a) is cleaner.
- **DTC storm** — the PSCM sets a "DesTorq plausibility" DTC if your values jump around. Rate-limit your command to <~50 Nm/s.
- **Lockout partial** — if you see intermittent 10-s dropouts anyway, the flash didn't take. Re-read cal `+0x06B0..06C2` via UDS and verify zeros.

## What you don't need

- Don't need to enable Ford LCA.
- Don't need to raise the APA speed cap (that's a different, unrelated feature).
- Don't need to modify the IPMA firmware.
- Don't need to patch the strategy code — only the calibration byte table.

## If you want to help

Open RE questions we'd love help on:
- **AS-built revert root cause.** Why does the PSCM revert AS-built bits after a cold boot when LCA is enabled? Suspected to be a VIN/vehicle-code check in strategy block.
- **Full cal map.** ~60% of the 65,520-byte cal is undocumented. Contributions welcome in [docs/calibration-map.md](https://github.com/ghostdev137/ford-pscm-re/blob/main/docs/calibration-map.md).
- **Emulator completion.** Athrill + autoas integration needs a CAN socket bridge. See [simulator.html](simulator.html).

File issues / PRs at <https://github.com/ghostdev137/ford-pscm-re>.
