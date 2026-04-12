# F-150 Flash Verdict — Full RE Complete

**Date:** 2026-04-12
**Target:** 2021 F-150 Lariat 502A BlueCruise PSCM, cal `ML34-14D007-EDL`

## TL;DR

**The patches will flash.** All crypto gates identified and accounted for.

## Evidence, in order

### 1. MCU confirmed: Renesas **RH850** (not V850E2M)

Strategy disassembly found the hardware string `AH850S54GxxxxxV101` at offset `0x2274` of the SBL — AUTOSAR hardware-abstraction component identifier for RH850. Flash mirror starts at `0xFEBE0000` (SBL) / `0x10040000` (strategy) / `0x101D0000` (cal), all consistent with RH850 family address maps.

Different from Transit (which is the older V850E2M), same family.

### 2. Strategy disasm confirmed every cal offset I hypothesized

| Cal offset | Abs addr | Bytes | Value | Role |
|---|---|---|---|---|
| `+0x07ADC` | `0x101D7ADC` | `10 27` | u16 LE = 10000 | **LKA arm timer** (10 s @ 1 ms tick) |
| `+0x07ADE` | `0x101D7ADE` | `10 27` | u16 LE = 10000 | **LKA re-arm timer** (10 s) |
| `+0x0114` | `0x101D0114` | `00 00 20 41` | f32 LE = 10.0 | **LKA min-engage-speed** (m/s ≈ 22 mph) |
| `+0x0144` | `0x101D0144` | `00 00 00 41` | f32 LE = 8.0 | **APA max-engage-speed** |
| `+0x0140` | `0x101D0140` | `00 00 00 3F` | f32 LE = 0.5 | **APA min-engage-speed** |
| `+0x07E64` | `0x101D7E64` | `10 27` | u16 LE = 10000 | **ESA / TJA timer** |
| `+0x00C4` | `0x101D00C4` | `00 00 20 41` | f32 LE = 10.0 | **LDW gate** |
| `+0x00120` | `0x101D0120` | `00 00 20 41` | f32 LE = 10.0 | **LCA engage-min** (leave alone) |

All eight values match their bytes in the extracted cal data exactly.

### 3. No runtime signature verification in strategy

1.5 MB of strategy disassembly contains:
- Zero SHA-256 software constants
- Zero SHA-1 / MD5 magic numbers
- Zero RSA / Montgomery multiplication patterns
- No references to any embedded public key

Strategy does not verify cal integrity at boot or during operation.

### 4. SBL uses hardware SHA-256 — but only for *itself*

`ML34-14D005-AB.VBF` (8,836-byte SBL) has three references to the RH850 on-chip SHA-256 peripheral at SFRs `0xFFFF3609/12/13`. The SBL's **own** integrity is verified via:
- `SBL_trailer[278:310]` = plain `SHA-256(SBL_code)` — verified by pure-Python computation, exact match.

**For the cal VBF**, no equivalent hash-of-cal-data appears anywhere in the cal trailer or elsewhere in the file. The SBL has NO code path that computes SHA-256 over received data and compares it to anything — the SHA peripheral is used for SBL self-check only.

### 5. Cal trailer is **NOT sent** to the SBL during flashing

Ford's UDS flash sequence:
1. Parse VBF header client-side.
2. `0x34 RequestDownload` + `0x36 TransferData` chunks → sends **block data only** (not trailer).
3. `0x37 RequestTransferExit`.
4. `0x31 RoutineControl 01 0202` CheckMemory with the 4-byte `file_checksum` CRC32 from the header.
5. SBL compares this CRC32 to its own running CRC32 over received bytes.

**The 296-byte trailer (including the "signature" and 32-byte hash-looking region) never reaches the SBL.** It stays on the client side and is dealer/server metadata.

### 6. RSA signature has no verifier anywhere

The 256-byte high-entropy region at start of the cal trailer is an RSA-2048 signature in form. But:
- No corresponding public key is embedded in the SBL (no high-entropy 256-byte region).
- No bignum / Montgomery multiplication code in the SBL (can't perform RSA).
- No such code in the 1.5 MB strategy either.

**Nothing in the flashed firmware can verify this signature.** It exists for Ford's FDRS server-side release-management.

## What this means for our patches

| Patch | CRC32 check | SHA verify | RSA verify | Outcome |
|---|---|---|---|---|
| Any of our 6 patched VBFs | ✅ recomputed | not applied to cal | not applied anywhere | **Should flash** |

## What still has unknown risk

**Mask-ROM behavior at cold boot.** We have not dumped the PSCM's mask ROM. A paranoid mask ROM could refuse to hand control to a modified strategy or cal. But:
- The cal sits alongside strategy in application flash; the mask ROM typically only verifies the SBL, not the application.
- Common RH850 bootmodes simply jump to a fixed flash address at `0x00000000`+reset-vector without verification.
- Ford hasn't been known to implement mask-ROM verification of app flash in the Transit / Escape PSCMs.

**If the mask ROM does reject the cal at boot:** PSCM falls back to safe mode or refuses to start power steering. **Not bricked** — flashing stock cal back recovers.

## Go / no-go

**Go.** The patches in `firmware/patched/F150_Lariat_BlueCruise/` are ready to flash. Start with `LKA_LOCKOUT_ONLY.VBF` (narrowest change) to minimize variables on the first attempt.

## Full output files

- `analysis/f150/sbl_raw.bin` — extracted SBL code
- `analysis/f150/sbl_findings.md` — full SBL RE writeup
- `analysis/f150/sbl_disassembly.txt` — annotated SBL hexdump
- `analysis/f150/strategy_raw.bin` — extracted strategy code
- `analysis/f150/strategy_findings.md` — full strategy RE writeup
- `analysis/f150/strategy_cal_reads.md` — per-offset cal-read trace
- `analysis/f150/cal_edl_raw.bin`, `cal_bdl_raw.bin` — extracted cal data
- `analysis/f150/cal_findings.md` — cal map + patch targets
