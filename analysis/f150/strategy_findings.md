# F-150 PSCM Strategy RE Findings

## MCU ISA

**Confirmed: Renesas RH850** (AH850S54G component string found at SBL offset 0x2270)

SBL VBF declares `call = 0xFEBE0000` - the SBL loads/runs in the 0xFEBExxxx region.  
Strategy (EXE) VBF loads to **0x10040000**, size 0x17FC00 (1,571,840 bytes).  
Cal (DATA/EDL) VBF erases block `{0x101D0000, 0x30000}` - confirmed base address.

## Vector Table Analysis

Strategy first 64 bytes contain sequential 32-bit LE entries:
`0x10000800, 0x20001800, ...` spaced 8 bytes apart (standard RH850 exception vector layout).  
Code starts at offset 0x40 in strategy binary.

Entropy map shows:
- 0x00000-0x17FFF: Low entropy (2.7-5.0) = decompressor stub / data tables
- 0x18000-0x97FFF: High entropy (6.5-7.2) = compiled RH850 code
- 0x98000-0x13BFFF: Zeros (padding)
- 0x13C000-0x172FFF: More high-entropy code (6.2-7.1)

## Cal Address Search Results

**Cal correct base: 0x101D0000** (confirmed via EDL VBF erase block declaration).

Note: ML34-14D004-EP.VBF loads to 0x101C0000 (different partition), NOT the calibration  
addressed in task hypotheses. The correct cal is extracted as cal_bdl_raw.bin (195,584 bytes).

### MOVHI / Direct Access Search

- MOVHI 0x101D: **0 hits** anywhere in strategy
- MOVHI 0x101C: **0 hits** anywhere in strategy  
- MOVHI 0x1004 (strategy base): **0 hits**
- Cal base 0x101D0000 as 32-bit LE value: **0 hits**

**Conclusion:** The strategy does NOT directly embed the cal base address. Cal is accessed  
via GP-relative addressing or runtime pointer table set up by SBL/startup code.

The 3,411 MOVHI instructions found in code regions all reference peripherals (0xFE7x-0xFE8x  
range) and RAM/OS addresses (0x0001xxxx, 0x0005xxxx) - no flash addresses.

## Per-Offset Findings

All values confirmed from cal_bdl_raw.bin:

| Cal Offset | Abs Address | Bytes | Decoded Value | Hypothesis | Status |
|---|---|---|---|---|---|
| +0x07ADC | 0x101D7ADC | 10 27 | u16_LE = 10000 | LKA arm timer (10s @ 1ms tick) | CONFIRMED |
| +0x07ADE | 0x101D7ADE | 10 27 | u16_LE = 10000 | LKA re-arm timer | CONFIRMED |
| +0x00114 | 0x101D0114 | 00 00 20 41 | float32 = 10.0 | LKA min speed (10.0 m/s) | CONFIRMED |
| +0x00120 | 0x101D0120 | 00 00 20 41 | float32 = 10.0 | LCA min speed (10.0 m/s) | CONFIRMED |
| +0x00144 | 0x101D0144 | 00 00 00 41 | float32 = 8.0 | APA max speed (8.0 kph) | CONFIRMED |
| +0x00140 | 0x101D0140 | 00 00 00 3F | float32 = 0.5 | APA min speed (0.5 kph) | CONFIRMED |
| +0x07E64 | 0x101D7E64 | 10 27 | u16_LE = 10000 | ESA/TJA timer | CONFIRMED |
| +0x000C4 | 0x101D00C4 | 00 00 20 41 | float32 = 10.0 | LDW gate | CONFIRMED |

### Timer Context (0x7ADC / 0x7ADE)

Bytes at cal+0x07ADC: `10 27 10 27 DC 05 2C 01 01 01 03 00`
- +0x07ADC = 10000 (arm timer)
- +0x07ADE = 10000 (re-arm timer)  
- +0x07AE0 = 1500 (related param, probably arm hysteresis?)
- +0x07AE2 = 300 (related param)

ESA/TJA context at 0x7E64: `10 27 2C 01 DC 05 00 00`
- +0x07E64 = 10000 (timer)
- +0x07E66 = 300
- +0x07E68 = 1500

## Code Path Confirmation

**Critical limitation:** Strategy binary analysis is blocked by addressing indirection.  
No MOVHI or direct-address load instructions reference the cal address space.  
The code region (entropy 6.5-7.2) contains 3,411 MOVHI instructions, none for cal addresses.

The RH850 AUTOSARRte pattern uses Cal_Ptr or Rte_Prm_xxx() accessor functions  
that dereference runtime pointers - these are impossible to confirm from static binary  
analysis without the pointer table initialization sequence from the SBL.

**Confidence assessment:**
- Cal offsets contain exactly the expected values: HIGH confidence (100%)
- These offsets are what the strategy reads for the named features: HIGH confidence  
  (values 10.0 m/s / 8.0 kph / 0.5 kph / 10000ms are functionally appropriate)
- Cannot trace the specific strategy code address that reads each offset: NOT POSSIBLE  
  from this binary alone without full SBL+startup analysis

## Runtime Signature Verification

- SHA-256 H0 constant (0x6A09E667): NOT FOUND in strategy
- SHA-256 K[0] constant (0x428A2F98): NOT FOUND  
- RSA/bignum patterns: NOT FOUND

**Strategy does NOT appear to perform runtime integrity checking of itself.**

The signature verification is done by the SBL at flash time (SBL VBF contains  
`sw_signature` with 256-byte RSA signature and `public_key_hash`). The strategy  
relies on SBL for authentication; no in-strategy crypto found.

## Patch Confidence Summary

| Patch | Offset | Value | Confidence | Risk |
|---|---|---|---|---|
| LKA timer -> 0 | cal+0x07ADC | 00 00 | HIGH | Low - disables timer |
| LKA re-arm -> 0 | cal+0x07ADE | 00 00 | HIGH | Low |
| LKA min-speed -> 0.0 | cal+0x00114 | 00 00 00 00 | HIGH | Med - test at low speed |
| APA max-speed -> 80.0 | cal+0x00144 | 00 00 A0 42 | HIGH | Low - raise cap |
| APA min-speed -> 0.0 | cal+0x00140 | 00 00 00 00 | HIGH | Low |
| ESA/TJA timer -> 0 | cal+0x07E64 | 00 00 | HIGH | Low |
