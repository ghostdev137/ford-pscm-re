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

Plain-language summary:

- [cal_plain_language_map.md](/Users/rossfisher/ford-pscm-re/analysis/f150/cal_plain_language_map.md) — quick EPS-role map for the major timer, gate, torque, and authority families
- [eps_dbc_message_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_dbc_message_trace.md) — canonical message-level map for F-150 `LKA`, `LCA/BlueCruise`, `APA`, and shared PSCM feedback frames

Current DBC-to-firmware message split is strongest at:

- `0x3CA` for direct `LKA`
- `0x3A8` for `APA`
- `0x3D3` as the current best-fit primary `LCA / BlueCruise` command PDU in this exact `f150_pscm_full.elf` image, with `0x3D6` still present but much thinner in raw binary evidence
- `0x3D7` now has a best-current periodic shared-supervisor consumer path `FUN_100586d0 -> FUN_1005ea9c -> FUN_1005e5fc`, which normalizes four object-like sideband channels into shared lateral state and writes three gp-backed halfword shims later reused by the `LCA / BlueCruise` locals (`FUN_10096f70/78/80`)
- `0x3CC` now has a pinned low-flash TX descriptor slot in the same contiguous list as `0x082` and `0x417`, but its exact PSCM packer is still open

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
| +0x07ADC | 0x101D7ADC | 10 27 | u16_LE = 10000 | Mixed EPS supervisor record; `10000` word is part of the LKA-adjacent timing neighborhood | REFINED |
| +0x07ADE | 0x101D7ADE | 10 27 | u16_LE = 10000 | Sibling `10000` word in the same mixed supervisor record | REFINED |
| +0x00114 | 0x101D0114 | 00 00 20 41 | float32 = 10.0 | LKA min speed (10.0 m/s) | CONFIRMED |
| +0x00120 | 0x101D0120 | 00 00 20 41 | float32 = 10.0 | LCA min speed (10.0 m/s) | CONFIRMED |
| +0x00144 | 0x101D0144 | 00 00 00 41 | float32 = 8.0 | APA max speed (8.0 kph) | CONFIRMED |
| +0x00140 | 0x101D0140 | 00 00 00 3F | float32 = 0.5 | APA min speed (0.5 kph) | CONFIRMED |
| +0x07E64 | 0x101D7E64 | 10 27 | u16_LE = 10000 | Sibling supervisor timer neighborhood, likely ESA/TJA-side | REFINED |
| +0x000C4 | 0x101D00C4 | 00 00 20 41 | float32 = 10.0 | LDW gate | CONFIRMED |

### Timer / supervisor context (0x7ADC / 0x7ADE)

Bytes at cal+0x07ADC: `10 27 10 27 DC 05 2C 01 01 01 03 00`
- +0x07ADC = 10000 (still part of the proven LKA-adjacent timing neighborhood)
- +0x07ADE = 10000 (same mixed record)
- +0x07AE0 = 1500 (related param)
- +0x07AE2 = 300 (related param)
- +0x07AE4/+0x07AE5 = `0x01/0x01` (now the best current fit for the directly proven byte-scaled `*10000 ms` substate timers)

ESA/TJA context at 0x7E64: `10 27 2C 01 DC 05 00 00`
- +0x07E64 = 10000 (timer)
- +0x07E66 = 300
- +0x07E68 = 1500

See also:

- [lka_timer_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/lka_timer_ghidra_trace.md)
- [eps_supervisor_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_supervisor_ghidra_trace.md)
- [eps_curve_family_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_curve_family_ghidra_trace.md)
- [eps_mode_separation_ghidra_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_mode_separation_ghidra_trace.md)

The live F-150 code path is more nuanced than a single naked `10000 ms` scalar. Ghidra now proves:

- a smaller 4-state helper with one fixed 10-second window
- two byte-scaled `*10000 ms` per-substate timers
- a separate packed debounce/persistence record for watchdog-style latch timing
- a mixed float/int supervisor record that best matches the `0x07ADC` neighborhood
- neighboring interpolation records that shape limiter, filter, and state-selection behavior

New `ctx + 0x68` refinement from the same supervisor family:

- `FUN_100a92ba` uses mid-record fields as continuous-control terms rather than timers
- the best-fit `0x07ADC`-relative values now line up with:
  - `+0x14 = 0.08726646` (`5 deg`)
  - `+0x18 = 0.17453292` (`10 deg`)
  - `+0x34 = 0.7`
  - `+0x44 = 0.008`
  - `+0x48 = 36.1111`
  - `+0x4c = 5.5556`
  - `+0x54 = 90.0`
  - `+0x5c = 1.2`
  - `+0x60 = 5.0`

That makes the `0x07D68..0x07E3F` neighborhood more defensible as a **continuous-control supervisor record** with angle-like thresholds, fallback magnitudes, and filter-shape terms, not just an unexplained float blob next to the timer words.

## Mirror-model refinement for unresolved cal blocks

The latest headless checks also tightened what **doesn't** work as a proof path.

Direct same-offset mirror checks now show:

- `fef20114`, `fef20140`, `fef20144`, `fef200c4`: no direct readers
- the broader `fef20100..fef2015c` neighborhood: no direct readers/writers
- `fef206ba`: no direct readers/writers

The `fef208xx` page does have many references, but the follow-on decompiles show it is a **live
runtime workspace**, not a passive same-offset calibration mirror:

- `FUN_101a5c4a` uses `DAT_fef20809/0b/0c/28/29...` as supervisor state
- `FUN_10180842` repacks `DAT_fef20800..0f` into another record
- `FUN_1017fda6`, `FUN_10180044`, `FUN_10180ca8`, `FUN_10181270` update `fef2081c/1e/30/54/78...`
  as mutable control variables

So for the still-open flash families:

- `cal+0x0100..0x015C`
- `cal+0x06BA`
- `cal+0x080C..0x0878`

the likely access path is now:

- copy into gp-backed records, or
- normalize into a context structure whose low offsets overlap dynamic runtime state

See [eps_envelope_threshold_trace.md](/Users/rossfisher/ford-pscm-re/analysis/f150/eps_envelope_threshold_trace.md).

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
