---
title: Flashing Guide
nav_order: 13
---

# Flashing the PSCM

> **Warning:** A failed flash can brick the PSCM and disable power steering. **This has happened to me.** Have a donor PSCM on hand, or be prepared to tow the vehicle to a dealer for recovery, before you flash anything.

## Hardware

- **Ford VCM-II** (genuine or clone — clones work with FORScan), or
- **TOPDON RLink X3** with the Ford-specific driver (RLink-FDRS.dll)
- Reliable 12 V supply — a battery maintainer during the flash is strongly recommended
- Laptop running FORScan 2.x (Extended license required for programming)

## Step-by-step

1. **Verify the base firmware.** The patched VBF is built from `LK41-14D007-AH`. If your Transit is running a different cal revision, re-derive the patch against your revision — do not flash a mismatched cal.

   Read cal PN via UDS:
   ```
   730  03 22 F1 0A  →  738  1x xx 62 F1 0A 4C 4B 34 31 2D 31 34 44 30 30 37 2D 41 48
                                       L  K  4  1  -  1  4  D  0  0  7  -  A  H
   ```

2. **Battery maintainer ON.** 13.5–14.0 V during flashing.

3. **FORScan** → open vehicle → **Service Procedures** → **Module Programming** → **PSCM — Power Steering Control Module**.

4. Choose **"Load from file"** when prompted. Select the patched VBF (e.g. `LKA_NO_LOCKOUT.VBF` from `firmware/patched/`).

5. FORScan will:
   - Switch PSCM to programming session (`0x10 0x02`).
   - Security access (`0x27`) — uses Ford seed/key algorithm.
   - Upload the SBL (secondary bootloader).
   - Erase target blocks.
   - Stream the data blocks with `0x34 / 0x36 / 0x37`.
   - Request checksum (`0x31 RoutineControl`) — this is where a bad CRC fails.
   - Activate (`0x11 ECUReset`).

6. Cycle ignition. Check for DTCs in FORScan: `P0600` (lost comms) or `C0051` (steering angle) are the two most common failure modes.

7. Drive and test.

## Recovery

If the flash fails mid-sequence, FORScan usually offers a retry. The SBL will still be resident and the module is still in programming session — do **not** power-cycle. Just retry.

If you have power-cycled and the module now reports no response to UDS, you will need:
- Another diagnostic tool that can reach SBL (FDRS at a dealer, or a direct CAN-H/L connection bypassing the gateway).
- Or swap the PSCM module.

## Programming session quirks

- The PSCM checks a security counter in NVM. Too many failed `0x27` attempts will lock the module for 10 minutes.
- Programming session times out after ~10 s without activity — keep `0x3E Tester Present` going if you are driving the sequence manually.

## Why not drive the flash manually?

You can — the sequence is not secret. But you will need:
- Working Ford seed/key (PSCM uses a variant; leaked implementations exist)
- The SBL file (part of every VBF set — `14D005` is usually the EPS SBL)
- Careful implementation of the 0x34/0x36/0x37 block transfer with correct padding

Not worth the effort unless FORScan doesn't support your scenario.

## Which patched file to flash

| Goal | File | Risk |
|---|---|---|
| Remove LKA lockout only (minimal diff) | `LKA_NO_LOCKOUT.VBF` | Low |
| **Recommended: full authority (lockout + min-speed + torque)** | **`LKA_FULL_AUTHORITY.VBF`** | **Low — drive-confirmed** |
| Raise APA speed ceiling (+ LKA lockout) | `LKA_NO_LOCKOUT_APA_HIGH_SPEED.VBF` | Medium — APA at speed untested |
| APA from true standstill | `LKA_APA_STANDSTILL.VBF` | Medium — standstill path untested |
| Attempt LCA enable | `LCA_ENABLED.VBF` | Medium — AS-built reverts, not bricking |

See [docs/vbf-patches.md](vbf-patches.html) for the full description of each patch.
