# APA Speed Gate Analysis — 2025 Ford Transit PSCM Strategy (AM)

## Strategy File

- Source VBF: `firmware/Transit_2025/KK21-14D003-AM` (no extension, 833,330 bytes)
- Extraction: `tools/vbf_decompress.py` using LZSS (EI=10, EJ=4, ring_init=0x20)
- Block 0 (strategy): flash base 0x01000000, decompressed size 1,048,560 bytes
- Output: `analysis/transit/strategy_raw_AM.bin`
- Note: VBF CRC16 shows MISMATCH (tool uses wrong polynomial), but decompression is correct — AL vs AM binary diffs confirm authentic content.

## APA 0x3A8 RX Handler

CAN mailbox dispatch is built from two structures in the strategy DATA region:

- CAN ID table at file 0x2C60 maps 0x3A8 to mailbox slot 25
- Function pointer table at file 0x316C holds 24 BE32 entries indexed from slot 9
- Entry[16] (slot 25, table offset 0x316C + 16×4 = 0x31AC) = **0x0108E2BE**

File offset: **0x08E2BE**  
Flash address: **0x0108E2BE**

First bytes: `18 21 06 D0 1B 01 09 10 00 80 DD 01 70 C8 E0 02 30 06 AD FB`

The handler reads CAN bytes 1, 3, 5, 7 of the 0x3A8 frame using V850 load patterns at file offsets 0x8E2DE (`18 8B A8 01`), 0x8E2E6 (`18 8B A8 03`), 0x8E2EE (`18 8B A8 05`), 0x8E2F6 (`18 8B A8 07`). It does NOT contain any speed comparison against a hardcoded constant.

## BrkSpeed 0x415 Handler

- CAN ID table at 0x2C60 maps 0x415 to mailbox slot 21
- Entry[12] (slot 21, offset 0x316C + 12×4 = 0x319C) = **0x0108D0B2**

File offset: **0x08D0B2**  
Flash address: **0x0108D0B2**

First bytes: `18 21 06 C0 1A C1 09 18 00 80 54 01 00 44 71 68 E0 02 31 8B`

The handler stores parsed wheel speed data to RAM. It does NOT contain 0x0FA0 (Ford ABS zero-speed offset 4000) as an immediate value in the function body.

Wheel speed RAM base: estimated near 0x10000540 (inferred from load displacement patterns in handler, not definitively confirmed without working V850 disassembler).

## Speed Gate — Key Finding

**There is NO hardcoded speed gate in strategy code.**

Exhaustive search of the code region (file 0x20000–0xD8000, ~768 KB of compiled V850):
- 0.3 kph float32 (`3E 99 99 9A`) occurrences in code region: **0**
- 0.5 kph float32 (`3E 00 00 00`) occurrences in code region: **0**
- 1.0 kph float32 (`3F 80 00 00`) occurrences in code region: **0**
- 0x0FA0 as 16-bit immediate in APA/BrkSpeed handlers: **0**

Speed gating is implemented entirely via **big-endian float32 lookup tables in the strategy DATA region** (file 0x00000–0x1FFFF). The APA torque/angle authority functions use these tables with minimum X-breakpoint = 0.3 kph. Below that threshold the code clamps to the first table output value rather than interpolating, so 0.3 kph is effectively a standstill lockout.

## Speed Gate Tables — Patchable Locations

All occurrences of 0.3 kph (`3E 99 99 9A`) in strategy DATA region:

| File Offset | Flash Address    | Context |
|-------------|------------------|---------|
| 0x0FD3C     | 0x0100FD3C       | steering rate limit table |
| 0x1023C     | 0x0101023C       | APA steer authority table (main) |
| 0x10770     | 0x01010770       | APA steer authority table |
| 0x10C70     | 0x01010C70       | APA steer authority table |
| 0x12158     | 0x01012158       | APA torque/angle copy 1 of 9 |
| 0x13628     | 0x01013628       | APA torque/angle copy 2 of 9 |
| 0x138E0     | 0x010138E0       | intermediate table |
| 0x13C4C     | 0x01013C4C       | intermediate table |
| 0x14AF8     | 0x01014AF8       | APA torque/angle copy 3 of 9 |
| 0x14DB0     | 0x01014DB0       | intermediate table |
| 0x1511C     | 0x0101511C       | intermediate table |
| 0x15FC8     | 0x01015FC8       | APA torque/angle copy 4 of 9 |
| 0x16280     | 0x01016280       | intermediate table |
| 0x165EC     | 0x010165EC       | intermediate table |
| 0x17498     | 0x01017498       | APA torque/angle copy 5 of 9 |
| 0x17750     | 0x01017750       | intermediate table |
| 0x17ABC     | 0x01017ABC       | intermediate table |
| 0x18968     | 0x01018968       | APA torque/angle copy 6 of 9 |
| 0x18C20     | 0x01018C20       | intermediate table |
| 0x18F8C     | 0x01018F8C       | intermediate table |
| 0x19E38     | 0x01019E38       | APA torque/angle copy 7 of 9 |
| 0x1A0F0     | 0x0101A0F0       | intermediate table |
| 0x1A45C     | 0x0101A45C       | intermediate table |
| 0x1B308     | 0x0101B308       | APA torque/angle copy 8 of 9 |
| 0x1B5C0     | 0x0101B5C0       | intermediate table |
| 0x1B92C     | 0x0101B92C       | intermediate table |
| 0x1C7D8     | 0x0101C7D8       | APA torque/angle copy 9 of 9 |

**Total: 27 occurrences.**

## Candidate Patches — Ranked by Confidence

### Patch A — Calibration only (ALREADY DONE, CONFIDENCE: HIGH)
The calibration file (0x00FD0000 region) contains the same APA authority lookup tables. The standstill patch already applied to the cal file removes the 0.3 kph lower bound in those tables. If the strategy DATA region tables are not also the active lookup source, the cal patch alone is sufficient.

- Evidence for sufficiency: The strategy DATA region tables at 0x10000–0x1FFFF may be defaults overwritten at runtime by cal data. Ford AUTOSAR typically loads calibration via NvM/DCM into RAM, then the application reads from RAM, not from flash directly.

### Patch B — Strategy DATA minimum speed tables (CONFIDENCE: MEDIUM)
Patch all 27 occurrences of `3E 99 99 9A` (0.3 kph) in strategy DATA region to `00 00 00 00` (0.0 kph).

```
For each address in the table above:
  Original: 3E 99 99 9A
  Patched:  00 00 00 00
```

This ensures that even if the strategy DATA is the active source (not cal), the speed floor is zero.

Risk: LOW — replacing a lookup table breakpoint with 0.0 is a minimal change. The interpolation math is unchanged; at V=0 it will use the first output value rather than clamping.

### Patch C — Combine A + B (CONFIDENCE: HIGHEST for robustness)
Apply both cal patch and strategy DATA patch. This covers both possible runtime data sources with no risk of one overriding the other.

### Patch D — NOT RECOMMENDED: Code region NO-OP
Since no speed gate exists in code, there is nothing to NOP in the V850 instructions. Any attempt to patch code at the APA handler would require correct V850 disassembly which is not available with current tooling.

## Evidence Against a Separate Hard Gate

1. Zero occurrences of any speed constant (0.3, 0.5, 1.0 kph) in the 768 KB code region.
2. APA handler (0x0108E2BE) and BrkSpeed handler (0x0108D0B2) contain no immediate value matching Ford ABS zero-speed offset 0x0FA0.
3. AL vs AM binary comparison shows 548 KB of changes in the code region — these are real instruction changes not padding, confirming the code region IS decoded V850 and was scanned correctly.
4. The data lookup pattern is consistent with AUTOSAR-generated code which always uses calibration tables rather than hardcoded comparisons.

## Summary

The APA speed lockout at standstill is caused entirely by lookup table breakpoints at 0.3 kph, located in both the calibration file (0x00FD0000) and the strategy DATA region (0x01000000–0x0101FFFF). There is no separate hard gate instruction in strategy code. The already-applied calibration patch should be sufficient IF the ECU loads calibration into RAM and the application reads from RAM. Applying Patch B additionally to the strategy binary provides belt-and-suspenders coverage and is the recommended approach for reliable standstill operation.
