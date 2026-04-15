# Phase 1b — Transit PSCM truncating opcodes

Source: Ghidra 12.0.4 headless with stock `esaulenka/ghidra_v850` (v850e3) SLEIGH.
Binary: `/Users/rossfisher/Desktop/Transit_2025_PSCM_dump/transit_pscm.elf`
Seed: 2,730 function-entry addresses from `/tmp/pscm/entries.json`, auto-analysis followed.

## Summary

- Total functions seeded / created: 2,730 / 2177
- Total instructions disassembled: 46,659
- Bad-instruction bookmarks: 926
- Distinct byte patterns: 267
- Functions affected (contain >=1 bad insn): 815 (37.4%)

### By category (weighted by frequency)

- ctrlflow: 662
- loadstore: 141
- other: 122
- fpu: 1

## Worklist (frequency-sorted)

| bytes (LE) | count | mnemonic guess | category | manual pg | funcs | sample | notes |
|---|---|---|---|---|---|---|---|
| `E0 02 50 63` | 280 | jr disp32 | ctrlflow | ~240 (JR) | 280 | 010279e6 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 1C 63` | 147 | jr disp32 | ctrlflow | ~240 (JR) | 147 | 01027192 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `00 00 00 00` | 42 | padding | other | - | 42 | 0100222c | 0x00/0xFF fill between functions |
| `E0 02 30 0C` | 40 | jr disp32 | ctrlflow | ~240 (JR) | 40 | 01087cbc | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 58 67` | 31 | jr disp32 | ctrlflow | ~240 (JR) | 31 | 01021810 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `FF FF FF FF` | 25 | padding | other | - | 25 | 01000040 | 0x00/0xFF fill between functions |
| `E0 02 30 67` | 22 | jr disp32 | ctrlflow | ~240 (JR) | 22 | 01021892 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 48 10` | 11 | jr disp32 | ctrlflow | ~240 (JR) | 11 | 01089e14 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `8C FF 1A F7` | 8 | ld/st disp23 | loadstore | ~250 | 4 | 0108666c | should be impl |
| `A8 07 E4 54` | 6 | ld/st disp23 | loadstore | ~250 | 6 | 0108cf94 | should be impl |
| `A8 07 E6 44` | 5 | ld/st disp23 | loadstore | ~250 | 5 | 0108ce5e | should be impl |
| `E0 02 4A 33` | 4 | jr disp32 | ctrlflow | ~240 (JR) | 3 | 010c82f6 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 2A 03` | 4 | jr disp32 | ctrlflow | ~240 (JR) | 4 | 01096e62 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 48 00` | 4 | jr disp32 | ctrlflow | ~240 (JR) | 4 | 01098de4 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 30 06` | 3 | jr disp32 | ctrlflow | ~240 (JR) | 3 | 010c4338 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 4A 43` | 3 | jr disp32 | ctrlflow | ~240 (JR) | 3 | 01088c28 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 07 E4 1D` | 3 | ld/st disp23 | loadstore | ~250 | 3 | 0108d364 | should be impl |
| `E0 02 1C E7` | 3 | jr disp32 | ctrlflow | ~240 (JR) | 3 | 01097402 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `9F FF 48 04` | 3 | ld/st disp23 | loadstore | ~250 | 1 | 010c1ace | should be impl |
| `E0 02 1C 9D` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 01025b38 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E1 02 50 8C` | 2 | UNKNOWN | other | - | 1 | 0104fd28 | op0510=0x17 op0515=0x017 op1626=0x450 op2126=0x22 |
| `A0 5F 50 D2` | 2 | ld/st disp23 | loadstore | ~250 | 1 | 010a3ad6 | should be impl |
| `A8 FF 7C E7` | 2 | ld/st disp23 | loadstore | ~250 | 2 | 010c42d4 | should be impl |
| `E0 02 48 0D` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 01068fbc | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 50 0D` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 01074042 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 48 1E` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 0107710e | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 07 7A 11` | 2 | ld/st disp23 | loadstore | ~250 | 1 | 01080112 | should be impl |
| `E0 02 34 A8` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 010876ae | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `85 1F 20 07` | 2 | ld/st disp23 | loadstore | ~250 | 1 | 010b8428 | should be impl |
| `AC FF E2 07` | 2 | ld/st disp23 | loadstore | ~250 | 2 | 0108845a | should be impl |
| `E0 02 30 0B` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 010884ec | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 07 E4 1C` | 2 | ld/st disp23 | loadstore | ~250 | 2 | 01088e46 | should be impl |
| `91 0F 90 7F` | 2 | ld/st disp23 | loadstore | ~250 | 1 | 01088d76 | should be impl |
| `E0 02 50 09` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 0108b860 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 54 0B` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 0108b91c | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 50 0A` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 0108bc22 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 2E 10` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 0108be32 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 07 E4 19` | 2 | ld/st disp23 | loadstore | ~250 | 2 | 0108e096 | should be impl |
| `E0 02 48 17` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 0109ab3a | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 58 07` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 0109d1fc | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E2 02 48 10` | 2 | UNKNOWN | other | - | 2 | 0109d28e | op0510=0x17 op0515=0x017 op1626=0x048 op2126=0x02 |
| `E0 02 50 0C` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 0109d3ac | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 7A 12` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 010a0850 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E2 02 48 2F` | 2 | UNKNOWN | other | - | 2 | 010a6d40 | op0510=0x17 op0515=0x017 op1626=0x748 op2126=0x3a |
| `E0 02 58 84` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 010a0bbc | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E6 02 48 1E` | 2 | UNKNOWN | other | - | 2 | 010a715a | op0510=0x17 op0515=0x017 op1626=0x648 op2126=0x32 |
| `A8 FF E2 16` | 2 | ld/st disp23 | loadstore | ~250 | 2 | 010ae62e | should be impl |
| `E0 02 70 E8` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 010bbfa8 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 70 A8` | 2 | jr disp32 | ctrlflow | ~240 (JR) | 2 | 010d043e | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 FF 48 8C` | 2 | ld/st disp23 | loadstore | ~250 | 1 | 010c1b6e | should be impl |
| `9F FF 48 0D` | 2 | ld/st disp23 | loadstore | ~250 | 1 | 010c1ae0 | should be impl |
| `84 FF 7C E6` | 2 | ld/st disp23 | loadstore | ~250 | 1 | 010e192e | should be impl |
| `E2 02 48 30` | 2 | UNKNOWN | other | - | 2 | 010e5278 | op0510=0x17 op0515=0x017 op1626=0x048 op2126=0x02 |
| `54 4B 50 5F` | 1 | UNKNOWN | other | - | 1 | 01002028 | op0510=0x1a op0515=0x25a op1626=0x750 op2126=0x3a |
| `FF 07 01 05` | 1 | UNKNOWN (op0510=0x3F ext) | other | - | 1 | 01003212 | op1626=0x501 op2126=0x28 |
| `B7 17 42 14` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010054be | should be impl |
| `F3 2F A0 08` | 1 | extended-impl | other | - | 1 | 01007882 | op1626 in impl set — why bad? |
| `AC AF 40 00` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010073b6 | should be impl |
| `AC AF A0 08` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010073aa | should be impl |
| `B5 2F 40 00` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01007432 | should be impl |
| `B5 2F A0 08` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01007426 | should be impl |
| `BD AF 40 00` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010074ae | should be impl |
| `BD AF A0 08` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010074a2 | should be impl |
| `E0 02 38 08` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010d7290 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 7C 06` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010d7ae0 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `92 CF 40 00` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010072be | should be impl |
| `92 CF A0 08` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010072b2 | should be impl |
| `9B 4F 40 00` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0100733a | should be impl |
| `9B 4F A0 08` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0100732e | should be impl |
| `E5 02 48 23` | 1 | UNKNOWN | other | - | 1 | 01077214 | op0510=0x17 op0515=0x017 op1626=0x348 op2126=0x1a |
| `F5 AF A0 08` | 1 | extended-impl | other | - | 1 | 010079f6 | op1626 in impl set — why bad? |
| `A1 1F A0 08` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0100797a | should be impl |
| `A1 1F 50 80` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01007986 | should be impl |
| `FA AF A0 08` | 1 | extended-impl | other | - | 1 | 01007a72 | op1626 in impl set — why bad? |
| `42 61 63 6B` | 1 | UNKNOWN | other | - | 1 | 01008b98 | op0510=0x0a op0515=0x30a op1626=0x363 op2126=0x1b |
| `00 00 00 01` | 1 | UNKNOWN | other | - | 1 | 01009658 | op0510=0x00 op0515=0x000 op1626=0x100 op2126=0x08 |
| `AC CF 02 00` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0100d562 | should be impl |
| `00 26 00 00` | 1 | UNKNOWN | other | - | 1 | 010104fe | op0510=0x30 op0515=0x130 op1626=0x000 op2126=0x00 |
| `A1 8F 50 80` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0101ceba | should be impl |
| `A1 97 50 80` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0101ced6 | should be impl |
| `A1 87 50 80` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0101d03e | should be impl |
| `E0 02 18 89` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0102015c | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 54 6C` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01021b06 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E1 02 6C 27` | 1 | UNKNOWN | other | - | 1 | 0102484c | op0510=0x17 op0515=0x017 op1626=0x76c op2126=0x3b |
| `E0 02 50 1F` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01025b1c | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 70 A2` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01025b64 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 70 07` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010283f6 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `3A 06 7D 87` | 1 | UNKNOWN | other | - | 1 | 0102e826 | op0510=0x31 op0515=0x031 op1626=0x77d op2126=0x3b |
| `E0 02 30 E7` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01030022 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E1 02 1C 63` | 1 | UNKNOWN | other | - | 1 | 0102ffca | op0510=0x17 op0515=0x017 op1626=0x31c op2126=0x18 |
| `E1 02 50 E7` | 1 | UNKNOWN | other | - | 1 | 0102ffd6 | op0510=0x17 op0515=0x017 op1626=0x750 op2126=0x3a |
| `E0 02 2A 06` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0103090c | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 1E 73` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01030b08 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 7C 6A` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01033432 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `AB 3F 10 69` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01040084 | should be impl |
| `AB 3F 02 33` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010431f6 | should be impl |
| `E2 02 48 00` | 1 | UNKNOWN | other | - | 1 | 010404ae | op0510=0x17 op0515=0x017 op1626=0x048 op2126=0x02 |
| `E0 02 10 03` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01043138 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 54 EC` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01047186 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 54 0D` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01055d6a | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 34 0D` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01050026 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `50 AD 38 24` | 1 | UNKNOWN | other | - | 1 | 010503ac | op0510=0x2a op0515=0x56a op1626=0x438 op2126=0x21 |
| `E0 02 7C 00` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01050724 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 20 05` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010a3b00 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `B0 5F 44 D6` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010a3ae2 | should be impl |
| `90 0F 78 00` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010533fc | should be impl |
| `E6 02 48 13` | 1 | UNKNOWN | other | - | 1 | 010533f2 | op0510=0x17 op0515=0x017 op1626=0x348 op2126=0x1a |
| `E0 02 50 E6` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01053f02 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 1F E6 18` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0105e638 | should be impl |
| `A8 FF E6 2F` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0105e67e | should be impl |
| `E2 02 48 1D` | 1 | UNKNOWN | other | - | 1 | 01068fa2 | op0510=0x17 op0515=0x017 op1626=0x548 op2126=0x2a |
| `E4 96 10 0C` | 1 | UNKNOWN | other | - | 1 | 01061632 | op0510=0x37 op0515=0x4b7 op1626=0x410 op2126=0x20 |
| `99 BF 2A 3F` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01061128 | should be impl |
| `E2 02 48 1F` | 1 | UNKNOWN | other | - | 1 | 0106579e | op0510=0x17 op0515=0x017 op1626=0x748 op2126=0x3a |
| `A0 67 5C 01` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0106e8ec | should be impl |
| `A1 77 54 81` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0106e8f8 | should be impl |
| `54 06 E0 24` | 1 | UNKNOWN | other | - | 1 | 01073c82 | op0510=0x32 op0515=0x032 op1626=0x4e0 op2126=0x27 |
| `E0 02 68 64` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01073cfa | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 54 06` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01073c80 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 36 24` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01073cd6 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 C7 E8 02` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01073cc4 | should be impl |
| `E1 02 7C 97` | 1 | UNKNOWN | other | - | 1 | 01076a5e | op0510=0x17 op0515=0x017 op1626=0x77c op2126=0x3b |
| `90 67 E8 03` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010771c2 | should be impl |
| `A8 07 1C C6` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010772c8 | should be impl |
| `A8 07 E2 28` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01077700 | should be impl |
| `A8 07 E2 0B` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01077e00 | should be impl |
| `A8 07 E2 07` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01077ef4 | should be impl |
| `91 07 50 E9` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01077fb8 | should be impl |
| `E0 02 68 75` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0106d512 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E5 0B E0 47` | 1 | UNKNOWN | other | - | 1 | 01078cb4 | op0510=0x1f op0515=0x05f op1626=0x7e0 op2126=0x3f |
| `E1 02 5C E5` | 1 | UNKNOWN | other | - | 1 | 0107ba1e | op0510=0x17 op0515=0x017 op1626=0x55c op2126=0x2a |
| `E8 02 48 26` | 1 | UNKNOWN | other | - | 1 | 0107ba30 | op0510=0x17 op0515=0x017 op1626=0x648 op2126=0x32 |
| `E0 02 80 03` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0108b442 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `B1 0F 58 0C` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0108b41c | should be impl |
| `E1 02 54 AC` | 1 | UNKNOWN | other | - | 1 | 0107a80a | op0510=0x17 op0515=0x017 op1626=0x454 op2126=0x22 |
| `E1 02 48 40` | 1 | UNKNOWN | other | - | 1 | 0107a81e | op0510=0x17 op0515=0x017 op1626=0x048 op2126=0x02 |
| `E1 02 48 4D` | 1 | UNKNOWN | other | - | 1 | 0107a8ec | op0510=0x17 op0515=0x017 op1626=0x548 op2126=0x2a |
| `71 7F 7F F0` | 1 | UNKNOWN | other | - | 1 | 0107afee | op0510=0x3b op0515=0x3fb op1626=0x07f op2126=0x03 |
| `A8 07 E2 08` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0107ee08 | should be impl |
| `AF FF E6 0B` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01080086 | should be impl |
| `B6 1F AE 51` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0108002e | should be impl |
| `E0 02 50 C6` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0108032e | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 64 00` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01081008 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 7C 09` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01082f0a | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `52 A6 50 E1` | 1 | UNKNOWN | other | - | 1 | 010848de | op0510=0x32 op0515=0x532 op1626=0x150 op2126=0x0a |
| `58 AD 51 1A` | 1 | UNKNOWN | other | - | 1 | 01084c2e | op0510=0x2a op0515=0x56a op1626=0x251 op2126=0x12 |
| `E0 02 30 9B` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010866f2 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 1C C6` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01086832 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 58 E7` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010869e2 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 30 A6` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01086c54 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 58 8C` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01086e5a | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 48 1F` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01087144 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 1C 7D` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01087164 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 48 04` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01087236 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 58 A5` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010d2220 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `AE FF E2 16` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0108749c | should be impl |
| `E0 02 70 80` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010c7bd8 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `8A DF E8 4A` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01087ab4 | should be impl |
| `8B E7 E8 4C` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010879ac | should be impl |
| `8B 4F 48 63` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01087a44 | should be impl |
| `9F 7F 6C 13` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01087d72 | should be impl |
| `90 0F 48 03` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010881e8 | should be impl |
| `E0 02 50 0B` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010880d8 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `92 7F 74 E8` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010884ba | should be impl |
| `A8 07 E4 1A` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01088ed4 | should be impl |
| `89 0C 2A 00` | 1 | UNKNOWN | other | - | 1 | 01089c30 | op0510=0x24 op0515=0x064 op1626=0x02a op2126=0x01 |
| `A8 07 E4 06` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01094004 | should be impl |
| `A8 07 E4 28` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0108c450 | should be impl |
| `E0 02 22 00` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0108c6ac | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 07 E6 41` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0108da2c | should be impl |
| `A8 07 E4 55` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0108db54 | should be impl |
| `A8 07 E4 18` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0108f13c | should be impl |
| `A8 07 E4 20` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0108f2ce | should be impl |
| `A8 07 E4 56` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0108f362 | should be impl |
| `A8 07 E6 3E` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0108f4f4 | should be impl |
| `E0 02 50 E5` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0109142a | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E4 02 2C 06` | 1 | UNKNOWN | other | - | 1 | 01091096 | op0510=0x17 op0515=0x017 op1626=0x62c op2126=0x31 |
| `E0 02 70 0B` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010959ea | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 1C AC` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01095d84 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A3 67 68 1B` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0109622c | should be impl |
| `48 3F 31 7D` | 1 | UNKNOWN | other | - | 1 | 010960c0 | op0510=0x3a op0515=0x1fa op1626=0x531 op2126=0x29 |
| `A4 D7 E8 0A` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010960bc | should be impl |
| `A6 1F 30 1D` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01095f6c | should be impl |
| `E0 02 48 0B` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01096414 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 30 1F` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01094f66 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 1E D6` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010974c0 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `8D 67 34 77` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 01097408 | should be impl |
| `8C FF 7C E7` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0109882a | should be impl |
| `E0 02 50 08` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 01090ae6 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 27 E0 5F` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0109ac86 | should be impl |
| `8C FF 1A 31` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0109ad48 | should be impl |
| `8C FF 20 7B` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0109b852 | should be impl |
| `E0 02 48 26` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0109c1f2 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 50 A5` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0109c33c | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 1C A5` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0109c48e | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 FF E2 21` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0109c488 | should be impl |
| `AC CF 1A F7` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0109bf48 | should be impl |
| `E0 02 58 89` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 0109c4f6 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 FF E2 13` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0109d316 | should be impl |
| `A8 FF 00 CF` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 0109d32a | should be impl |
| `E0 02 30 AC` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010a8cfc | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 7C C3` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010a3e0c | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E6 02 48 1F` | 1 | UNKNOWN | other | - | 1 | 010a6cee | op0510=0x17 op0515=0x017 op1626=0x748 op2126=0x3a |
| `E2 02 48 2E` | 1 | UNKNOWN | other | - | 1 | 010a6f9e | op0510=0x17 op0515=0x017 op1626=0x648 op2126=0x32 |
| `E0 02 90 0F` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010a10a2 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 0F E6 0B` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010a783a | should be impl |
| `E8 02 4A 23` | 1 | UNKNOWN | other | - | 1 | 010ae658 | op0510=0x17 op0515=0x017 op1626=0x34a op2126=0x1a |
| `E0 02 50 E7` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010af4f6 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 30 FB` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010afd3a | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 FF E2 1E` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010afe70 | should be impl |
| `E0 02 58 C5` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010b049e | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `00 07 48 13` | 1 | UNKNOWN | other | - | 1 | 010b2c26 | op0510=0x38 op0515=0x038 op1626=0x348 op2126=0x1a |
| `01 39 18 0B` | 1 | UNKNOWN | other | - | 1 | 010b2be8 | op0510=0x08 op0515=0x1c8 op1626=0x318 op2126=0x18 |
| `A8 FF E6 05` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010b2c1c | should be impl |
| `A2 6F B8 61` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010b9880 | should be impl |
| `E0 02 50 FE` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010bc7da | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `86 0F 2A 0C` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010bd2d4 | should be impl |
| `79 FF 0D E1` | 1 | UNKNOWN | other | - | 1 | 010bd494 | op0510=0x3b op0515=0x7fb op1626=0x10d op2126=0x08 |
| `A8 FF E6 CD` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010bd490 | should be impl |
| `A8 FF E2 12` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010bd67e | should be impl |
| `A8 FF 36 09` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010bdaca | should be impl |
| `E0 02 30 A7` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010bf244 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 30 DA` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010bf926 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 18 C7` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010bf92e | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 58 E4` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010bfada | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `9C 07 2A A3` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010bfcc2 | should be impl |
| `AB 27 7C 9B` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010bfc80 | should be impl |
| `B7 2E 5F E4` | 1 | UNKNOWN | other | - | 1 | 010c00e4 | op0510=0x35 op0515=0x175 op1626=0x45f op2126=0x22 |
| `E0 02 30 1E` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010c84c2 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 30 8C` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010c014e | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 58 0A` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010c00b4 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A0 3F E8 16` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c0074 | should be impl |
| `A0 7F E8 36` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c0034 | should be impl |
| `A7 57 E8 28` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c0050 | should be impl |
| `A7 9F E8 4C` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c0008 | should be impl |
| `E2 02 48 15` | 1 | UNKNOWN | other | - | 1 | 010c011c | op0510=0x17 op0515=0x017 op1626=0x548 op2126=0x2a |
| `E0 02 48 16` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010c103a | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `95 F7 4A 33` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c1020 | should be impl |
| `E0 02 30 AA` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010c1528 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 30 C8` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010c153c | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `71 E6 9F FF` | 1 | UNKNOWN | other | - | 1 | 010c1b10 | op0510=0x33 op0515=0x733 op1626=0x79f op2126=0x3c |
| `51 7F 00 4C` | 1 | UNKNOWN | other | - | 1 | 010c1c2a | op0510=0x3a op0515=0x3fa op1626=0x400 op2126=0x20 |
| `89 57 48 20` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c1c0a | should be impl |
| `9F FF 02 E4` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c1ac4 | should be impl |
| `E0 02 34 A6` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010c41fe | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `A8 07 E2 0E` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c525e | should be impl |
| `A8 07 E2 49` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c5276 | should be impl |
| `B3 DF E8 21` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c51b4 | should be impl |
| `A1 67 BA 01` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c54f8 | should be impl |
| `87 07 9E 51` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c7394 | should be impl |
| `86 57 9C 01` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010c7388 | should be impl |
| `E0 02 70 08` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010ca20a | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 10 1A` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010cc2dc | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 12 CA` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010cceac | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 48 03` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010cd29c | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 70 00` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010cd3fa | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 18 0A` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010ce22e | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 0C 07` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010d8348 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 30 08` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010d8e28 | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `E0 02 58 0C` | 1 | jr disp32 | ctrlflow | ~240 (JR) | 1 | 010d8efe | first halfword=0x02E0 is canonical jr disp32; stock SLEIGH may reject due to 6-byte alignment issue or disp low halfword collision |
| `7C 06 40 40` | 1 | UNKNOWN | other | - | 1 | 010e1af4 | op0510=0x33 op0515=0x033 op1626=0x040 op2126=0x02 |
| `84 FF 06 67` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010e1a0a | should be impl |
| `84 FF 7C 85` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010e1a72 | should be impl |
| `84 FF 7C 64` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010e1cdc | should be impl |
| `8C FF E2 96` | 1 | ld/st disp23 | loadstore | ~250 | 1 | 010e1d30 | should be impl |
| `E1 02 E8 00` | 1 | UNKNOWN | other | - | 1 | 010e32e6 | op0510=0x17 op0515=0x017 op1626=0x0e8 op2126=0x07 |
| `E6 1F 50 9C` | 1 | fpu F:I variant | fpu | ~313-360 | 1 | 010e5794 | FPU sub-op not in impl set |

## Notes

- Error type is **"Bad Instruction"** (Ghidra bookmark category), which is stock SLEIGH raising `unknown-instruction`. There are no `halt_baddata` stubs in stock `esaulenka/ghidra_v850`, so this is the expected truncation surface.
- **By far the most common (461 of 927)** are variants of `E0 02 XX XX` — first halfword = 0x02E0, i.e. `jr disp32` or `jarl disp32, r0`. Stock SLEIGH's constructor for `jr disp32` requires specific disp32 alignment; many instances look like legitimate 6-byte jr/jarl that the disassembler fails mid-decode (likely alignment/halfword-boundary edge case in stock). **These are the single highest-leverage fix in Phase 2.**
- Patterns starting with `A8 07`, `8C FF`, `9F FF` etc. are `op0510=0x3F` extended-family sub-ops missing from stock.
- Patterns `00 00 00 00` / `FF FF FF FF` (67 total) are inter-function padding that the disassembler walked into when a jump target/return was not recognised; these are not real instructions but count as truncation.
