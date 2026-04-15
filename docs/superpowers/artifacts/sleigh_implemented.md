# SLEIGH baseline — implemented V850/RH850 instruction catalog

Source tree: `vendor/ghidra_v850_working/data/languages/`
Branch: `transit-rh850-extension` @ `e85ee05`

Each constructor is tagged:
- **real** — semantic p-code body present
- **unimpl** — SLEIGH `unimpl` keyword; instruction parses/disassembles but emits no p-code (decompiler gap)
- **stub** — body present but only bookkeeping / `TODO` / incomplete semantics

No `halt_baddata()` uses were found in any `.sinc` file. Sub-tables (`cc0003`, `DispList*`, `PrepList*`, `bins_*`, `buildPopSp`, `buildPushSp`, `rXX`, `reg4`, `R0004`, `R1115`, `R2731`) are helpers, not emitted instructions, and are omitted from the per-instruction tables.

## Arithmetic (ADD/SUB/MUL/DIV/CMP/SAT*/MAC)

| Mnemonic | Form | Opcode bits | Status | File:Line |
|---|---|---|---|---|
| mov | reg1, reg2 | op0510=0x00 | real | v850_arithmetic.sinc:11 |
| divh | reg1, reg2 | op0510=0x02 | real | v850_arithmetic.sinc:16 |
| satsubr | reg1, reg2 | op0510=0x04 | real | v850_arithmetic.sinc:34 |
| satsub | reg1, reg2 | op0510=0x05 | real | v850_arithmetic.sinc:42 |
| satadd | reg1, reg2 | op0510=0x06 | real | v850_arithmetic.sinc:50 |
| mulh | reg1, reg2 | op0510=0x07 | real | v850_arithmetic.sinc:59 |
| subr | reg1, reg2 | op0510=0x0C | real | v850_arithmetic.sinc:66 |
| sub | reg1, reg2 | op0510=0x0D | real | v850_arithmetic.sinc:72 |
| add | reg1, reg2 | op0510=0x0E | real | v850_arithmetic.sinc:78 |
| cmp | reg1, reg2 | op0510=0x0F | real | v850_arithmetic.sinc:84 |
| mov | imm5, reg2 | op0510=0x10 | real | v850_arithmetic.sinc:89 |
| satadd | imm5, reg2 | op0510=0x11 | real | v850_arithmetic.sinc:94 |
| add | imm5, reg2 | op0510=0x12 | real | v850_arithmetic.sinc:103 |
| cmp | imm5, reg2 | op0510=0x13 | real | v850_arithmetic.sinc:110 |
| mulh | imm5, reg2 | op0510=0x17 | real | v850_arithmetic.sinc:115 |
| addi | imm16, reg1, reg2 | op0510=0x30 | real | v850_arithmetic.sinc:120 |
| mov | imm32, reg1 | op0515=0x031 | real | v850_arithmetic.sinc:126 |
| movea | imm16, reg1, reg2 | op0510=0x31 | real | v850_arithmetic.sinc:131 |
| movhi | imm16, reg1, reg2 | op0510=0x32 | real | v850_arithmetic.sinc:135 |
| satsubi | imm16, reg1, reg2 | op0510=0x33 | real | v850_arithmetic.sinc:140 |
| mulhi | imm16, reg1, reg2 | op0510=0x37 | real | v850_arithmetic.sinc:148 |
| mul | reg1, reg2, reg3 | op0510=0x3F; op1626=0x220 | real | v850_arithmetic.sinc:153 |
| mulu | reg1, reg2, reg3 | op0510=0x3F; op1626=0x222 | real | v850_arithmetic.sinc:159 |
| mul | imm9, reg2, reg3 | op0510=0x3F; op2226=9,op1617=0 | real | v850_arithmetic.sinc:165 |
| mulu | imm9, reg2, reg3 | op0510=0x3F; op2226=9,op1617=2 | real | v850_arithmetic.sinc:172 |
| divh | reg1, reg2, reg3 | op0510=0x3F; op1626=0x280 | real | v850_arithmetic.sinc:179 |
| divhu | reg1, reg2, reg3 | op0510=0x3F; op1626=0x282 | real | v850_arithmetic.sinc:189 |
| div | reg1, reg2, reg3 | op0510=0x3F; op1626=0x2C0 | real | v850_arithmetic.sinc:199 |
| div (divq) | reg1, reg2, reg3 | op0510=0x3F; op1626=0x2FC | real | v850_arithmetic.sinc:208 |
| divu | reg1, reg2, reg3 | op0510=0x3F; op1626=0x2C2 | real | v850_arithmetic.sinc:217 |
| divqu | reg1, reg2, reg3 | op0510=0x3F; op1626=0x2FE | real | v850_arithmetic.sinc:226 |
| satsub | reg1, reg2, reg3 | op0510=0x3F; op1626=0x39A | real | v850_arithmetic.sinc:236 |
| satadd | reg1, reg2, reg3 | op0510=0x3F; op1626=0x3BA | real | v850_arithmetic.sinc:245 |
| mac | reg1, reg2, reg3, reg4 | op0510=0x3F; op2126=0x1E,op1616=0 | real | v850_arithmetic.sinc:254 |
| macu | reg1, reg2, reg3, reg4 | op0510=0x3F; op2126=0x1F,op1616=0 | real | v850_arithmetic.sinc:258 |
| setf^cond | cond, reg2 | op0410=0x7E; op1631=0 | real | v850_cond.sinc:52 |
| sasf^cond | cond, reg2 | op0410=0x7E; op1631=0x0200 | real | v850_cond.sinc:56 |
| cmov^cond | cond, imm5, reg2, reg3 | op0510=0x3F; op2126=0x18 | real | v850_cond.sinc:61 |
| cmov^cond | cond, reg1, reg2, reg3 | op0510=0x3F; op2126=0x19 | real | v850_cond.sinc:70 |
| sbf^cond | cond, reg1, reg2, reg3 | op0510=0x3F; op2126=0x1C | real | v850_cond.sinc:80 |
| adf^cond | cond, reg1, reg2, reg3 | op0510=0x3F; op2126=0x1D | real | v850_cond.sinc:90 |

## Logical (AND/OR/XOR/NOT/TST + shift/rotate, SXB/SXH/ZXB/ZXH)

| Mnemonic | Form | Opcode bits | Status | File:Line |
|---|---|---|---|---|
| not | reg1, reg2 | op0510=0x01 | real | v850_logical.sinc:7 |
| or | reg1, reg2 | op0510=0x08 | real | v850_logical.sinc:13 |
| xor | reg1, reg2 | op0510=0x09 | real | v850_logical.sinc:18 |
| and | reg1, reg2 | op0510=0x0A | real | v850_logical.sinc:23 |
| tst | reg1, reg2 | op0510=0x0B | real | v850_logical.sinc:28 |
| ori | imm16, reg1, reg2 | op0510=0x34 | real | v850_logical.sinc:33 |
| xori | imm16, reg1, reg2 | op0510=0x35 | real | v850_logical.sinc:38 |
| andi | imm16, reg1, reg2 | op0510=0x36 | real | v850_logical.sinc:43 |
| zxb | reg1 | op0515=0x004 | real | v850_data_manipulation.sinc:7 |
| sxb | reg1 | op0515=0x005 | real | v850_data_manipulation.sinc:11 |
| zxh | reg1 | op0515=0x006 | real | v850_data_manipulation.sinc:15 |
| sxh | reg1 | op0515=0x007 | real | v850_data_manipulation.sinc:19 |
| shr | imm5, reg2 | op0510=0x14 | real | v850_data_manipulation.sinc:52 |
| sar | imm5, reg2 | op0510=0x15 | real | v850_data_manipulation.sinc:56 |
| shl | imm5, reg2 | op0510=0x16 | real | v850_data_manipulation.sinc:60 |
| shr | reg1, reg2 | op0510=0x3F; op1631=0x80 | real | v850_data_manipulation.sinc:65 |
| shr | reg1, reg2, reg3 | op0510=0x3F; op1626=0x82 | real | v850_data_manipulation.sinc:69 |
| sar | reg1, reg2 | op0510=0x3F; op1631=0xA0 | real | v850_data_manipulation.sinc:73 |
| sar | reg1, reg2, reg3 | op0510=0x3F; op1626=0xA2 | real | v850_data_manipulation.sinc:77 |
| shl | reg1, reg2 | op0510=0x3F; op1631=0xC0 | real | v850_data_manipulation.sinc:81 |
| shl | reg1, reg2, reg3 | op0510=0x3F; op1626=0xC2 | real | v850_data_manipulation.sinc:85 |
| rotl | reg1, reg2, reg3 | op0510=0x3F; op1626=0x0C6 | real | v850e3.sinc:486 |
| rotl | imm5, reg2, reg3 | op0510=0x3F; op1626=0x0C4 | real | v850e3.sinc:489 |

## Bit manipulation (BSW/BSH/HSW/HSH, SET1/CLR1/NOT1/TST1, SCH0/SCH1, BINS)

| Mnemonic | Form | Opcode bits | Status | File:Line |
|---|---|---|---|---|
| bsw | reg2, reg3 | op0010=0x7E0; op1626=0x340 | real | v850_data_manipulation.sinc:90 |
| bsh | reg2, reg3 | op0010=0x7E0; op1626=0x342 | real | v850_data_manipulation.sinc:100 |
| hsw | reg2, reg3 | op0010=0x7E0; op1626=0x344 | real | v850_data_manipulation.sinc:110 |
| hsh | reg2, reg3 | op0010=0x7E0; op1626=0x346 | real | v850_data_manipulation.sinc:119 |
| sch0r | reg2, reg3 | op0010=0x7E0; op1626=0x360 | real | v850_data_manipulation.sinc:146 |
| sch1r | reg2, reg3 | op0010=0x7E0; op1626=0x362 | real | v850_data_manipulation.sinc:154 |
| sch0l | reg2, reg3 | op0010=0x7E0; op1626=0x364 | real | v850_data_manipulation.sinc:162 |
| sch1l | reg2, reg3 | op0010=0x7E0; op1626=0x366 | real | v850_data_manipulation.sinc:170 |
| set1 | bit3, disp16[reg1] | op0510=0x3E; op1415=0 | real | v850_logical.sinc:49 |
| not1 | bit3, disp16[reg1] | op0510=0x3E; op1415=1 | real | v850_logical.sinc:56 |
| clr1 | bit3, disp16[reg1] | op0510=0x3E; op1415=2 | real | v850_logical.sinc:63 |
| tst1 | bit3, disp16[reg1] | op0510=0x3E; op1415=3 | real | v850_logical.sinc:70 |
| set1 | reg2, [reg1] | op0510=0x3F; op1631=0xE0 | real | v850_logical.sinc:77 |
| not1 | reg2, [reg1] | op0510=0x3F; op1631=0xE2 | real | v850_logical.sinc:83 |
| clr1 | reg2, [reg1] | op0510=0x3F; op1631=0xE4 | real | v850_logical.sinc:89 |
| tst1 | reg2, [reg1] | op0510=0x3F; op1631=0xE6 | real | v850_logical.sinc:95 |
| bins | reg1, pos, width, reg2 | op0510=0x3F; op2026∈{0x09,0x0B,0x0D}, op1616=0 | real | v850e3.sinc:509 |

## Load / Store (LD/ST/SLD/SST/PREPARE/DISPOSE, plus RH850 extensions)

| Mnemonic | Form | Opcode bits | Status | File:Line |
|---|---|---|---|---|
| sld.bu | disp4[ep], reg2 | op0410=0x06 | real | v850_load_store.sinc:8 |
| sld.hu | disp5[ep], reg2 | op0410=0x07 | real | v850_load_store.sinc:14 |
| sld.b | disp7[ep], reg2 | op0710=0x06 | real | v850_load_store.sinc:21 |
| sst.b | disp7[ep], reg2 | op0710=0x07 | real | v850_load_store.sinc:26 |
| sld.h | disp8[ep], reg2 | op0710=0x08 | real | v850_load_store.sinc:31 |
| sst.h | disp8[ep], reg2 | op0710=0x09 | real | v850_load_store.sinc:37 |
| sld.w | disp8[ep], reg2 | op0710=0x0A,op0000=0 | real | v850_load_store.sinc:43 |
| sst.w | disp8[ep], reg2 | op0710=0x0A,op0000=1 | real | v850_load_store.sinc:49 |
| ld.b | disp16[reg1], reg2 | op0510=0x38 | real | v850_load_store.sinc:56 |
| ld.h | disp16[reg1], reg2 | op0510=0x39; op1616=0 | real | v850_load_store.sinc:61 |
| ld.w | disp16[reg1], reg2 | op0510=0x39; op1616=1 | real | v850_load_store.sinc:66 |
| st.b | reg2, disp16[reg1] | op0510=0x3A | real | v850_load_store.sinc:72 |
| st.h | reg2, disp16[reg1] | op0510=0x3B; op1616=0 | real | v850_load_store.sinc:77 |
| st.w | reg2, disp16[reg1] | op0510=0x3B; op1616=1 | real | v850_load_store.sinc:82 |
| ld.b | disp23[reg1], reg3 | op0515=0x03C; op1619=5 | real | v850_load_store.sinc:89 |
| ld.h | disp23[reg1], reg3 | op0515=0x03C; op1620=7 | real | v850_load_store.sinc:95 |
| ld.w | disp23[reg1], reg3 | op0515=0x03C; op1620=9 | real | v850_load_store.sinc:101 |
| st.b | reg3, disp23[reg1] | op0515=0x03C; op1619=0xD | real | v850_load_store.sinc:107 |
| st.w | reg3, disp23[reg1] | op0515=0x03C; op1620=0xF | real | v850_load_store.sinc:113 |
| ld.bu | disp23[reg1], reg3 | op0515=0x03D; op1619=5 | real | v850_load_store.sinc:119 |
| ld.hu | disp23[reg1], reg3 | op0515=0x03D; op1619=7 | real | v850_load_store.sinc:125 |
| st.h | reg3, disp23[reg1] | op0515=0x03D; op1620=0xD | real | v850_load_store.sinc:131 |
| ld.bu | disp16[reg1], reg2 | op0610=0x1E; op1616=1 | real | v850_load_store.sinc:138 |
| ld.hu | disp16[reg1], reg2 | op0510=0x3F; op1616=1 | real | v850_load_store.sinc:145 |
| st.dw | reg3pair, disp23[reg1] | op0515=0x3D; op1620=0xF | real | v850e3.sinc:204 |
| ld.dw | disp23[reg1], reg3pair | op0515=0x03d; op1620=0x09 | real | v850e3.sinc:212 |
| ldl.w | [reg1], reg3 | op0515=0x03F; op1626=0x378 | stub (no link-tracking) | v850e3.sinc:285 |
| stc.w | reg3, [reg1] | op0515=0x03F; op1626=0x37A | stub (no link-check) | v850e3.sinc:292 |
| ld.b | [reg1]+, reg3 | op0515=0x0BF; op1626=0x370 | real | v850e3.sinc:303 |
| ld.b | [reg1]-, reg3 | op0515=0x13F; op1626=0x370 | real | v850e3.sinc:308 |
| ld.h | [reg1]+, reg3 | op0515=0x0BF; op1626=0x374 | real | v850e3.sinc:313 |
| ld.h | [reg1]-, reg3 | op0515=0x13F; op1626=0x374 | real | v850e3.sinc:318 |
| ld.bu | [reg1]+, reg3 | op0515=0x0FF; op1626=0x370 | real | v850e3.sinc:323 |
| ld.bu | [reg1]-, reg3 | op0515=0x17F; op1626=0x370 | real | v850e3.sinc:328 |
| ld.hu | [reg1]+, reg3 | op0515=0x0FF; op1626=0x374 | real | v850e3.sinc:333 |
| ld.hu | [reg1]-, reg3 | op0515=0x17F; op1626=0x374 | real | v850e3.sinc:338 |
| ld.w | [reg1]+, reg3 | op0515=0x0BF; op1626=0x378 | real | v850e3.sinc:343 |
| ld.w | [reg1]-, reg3 | op0515=0x13F; op1626=0x378 | real | v850e3.sinc:348 |
| st.b | reg3, [reg1]+ | op0515=0x0BF; op1626=0x372 | real | v850e3.sinc:354 |
| st.b | reg3, [reg1]- | op0515=0x13F; op1626=0x372 | real | v850e3.sinc:359 |
| st.h | reg3, [reg1]+ | op0515=0x0BF; op1626=0x376 | real | v850e3.sinc:364 |
| st.h | reg3, [reg1]- | op0515=0x13F; op1626=0x376 | real | v850e3.sinc:369 |
| st.w | reg3, [reg1]+ | op0515=0x0BF; op1626=0x37A | real | v850e3.sinc:374 |
| st.w | reg3, [reg1]- | op0515=0x13F; op1626=0x37A | real | v850e3.sinc:379 |
| popsp | rh, rt | op0515=0x33F; op1626=0x160 | real | v850e3.sinc:436 |
| pushsp | rh, rt | op0515=0x23F; op1626=0x160 | real | v850e3.sinc:462 |
| dispose | imm5, list12 | prep0615=0x19; prep1620=0 | real | v850_func.sinc:90 |
| dispose | imm5, list12, [reg1] | prep0615=0x19 | real | v850_func.sinc:96 |
| prepare | list12, imm5 | prep0615=0x1E; prep1620=0x01 | real | v850_func.sinc:155 |
| prepare | list12, imm5, sp | prep0615=0x1E; prep1620=0x03 | real | v850_func.sinc:160 |
| prepare | list12, imm5, imm16(lo) | prep0615=0x1E; prep1620=0x0B | real | v850_func.sinc:166 |
| prepare | list12, imm5, imm16(hi) | prep0615=0x1E; prep1620=0x13 | real | v850_func.sinc:172 |
| prepare | list12, imm5, imm32 | prep0615=0x1E; prep1620=0x1B | real | v850_func.sinc:178 |

## Control flow (Bcond, JR, JARL, JMP, RETI, EIRET, FERET, CTRET, TRAP, SYSCALL, HALT, LOOP, SWITCH, FETRAP, CALLT, DI/EI, NOP, SYNC*)

| Mnemonic | Form | Opcode bits | Status | File:Line |
|---|---|---|---|---|
| b^cond | disp9 | op0710=0xB | real | v850_cond.sinc:44 |
| br | disp9 | op0710=0xB; op0003=0x5 | real | v850_cond.sinc:47 |
| jmp | [reg1] (ret form, r31) | op0515=0x003; reg=31 | real | v850_func.sinc:7 |
| jmp | [reg1] | op0515=0x003; reg!=31 | real | v850_func.sinc:11 |
| jr | disp32 | op0015=0x02E0 | real | v850_func.sinc:17 |
| jarl | disp32, reg1 | op0515=0x017 | real | v850_func.sinc:23 |
| jmp | disp32[reg1] | op0515=0x037 | real | v850_func.sinc:30 |
| jr | disp22 | op0615=0x1E | real | v850_func.sinc:36 |
| jarl | disp22, reg2 | op0610=0x1E | real | v850_func.sinc:43 |
| jarl | [reg1], reg3 | op0515=0x63f; op1626=0x160 | real | v850e3.sinc:220 |
| b^cond | disp17 | op0515=0x03F | real | v850e3.sinc:227 |
| br | disp17 | op0515=0x03F; op0003=0x5 | real | v850e3.sinc:230 |
| loop | reg1, disp16 | op0515=0x037; op1616=1 | real | v850e3.sinc:237 |
| switch | reg1 | op0515=0x002 | real | v850_special.sinc:31 |
| fetrap | vector4 | op0010=0x040 | real | v850_special.sinc:39 |
| callt | imm6 | op0615=0x008 | real | v850_special.sinc:53 |
| trap | imm5 | op0515=0x3F; op1631=0x0100 | real | v850_special.sinc:85 |
| halt | - | op0515=0x3F; op1631=0x0120 | real | v850_special.sinc:101 |
| reti | - | op0515=0x3F; op1631=0x0140 | real | v850_special.sinc:105 |
| ctret | - | op0515=0x3F; op1631=0x0144 | real | v850_special.sinc:119 |
| eiret | - | op0515=0x3F; op1631=0x0148 | real | v850_special.sinc:125 |
| feret | - | op0515=0x3F; op1631=0x014A | real | v850_special.sinc:131 |
| di | - | op0015=0x07E0; op1631=0x0160 | real | v850_special.sinc:138 |
| ei | - | op0015=0x87E0; op1631=0x0160 | real | v850_special.sinc:143 |
| syscall | vector8 | op0515=0x6BF; op1626=0x160 | real | v850_special.sinc:149 |
| nop | - | op0015=0x0000 | real | v850_special.sinc:10 |
| synce | - | op0015=0x001D | real | v850_special.sinc:15 |
| syncm | - | op0015=0x001E | real | v850_special.sinc:19 |
| syncp | - | op0015=0x001F | real | v850_special.sinc:23 |
| synci | - | op0015=0x001C | real | v850e3.sinc:528 |
| snooze | - | op0015=0x0FE0; op1631=0x0120 | real | v850e3.sinc:523 |
| rie | (16-bit) | op0015=0x0040 | unimpl | v850_special.sinc:28 |
| rie | (32-bit) | op0410=0x7F; op1631=0 | unimpl | v850_special.sinc:63 |

## System / special-register (LDSR/STSR/selID, CAXI, LDL.W/STC.W, MPU/cache/TLB/guest)

| Mnemonic | Form | Opcode bits | Status | File:Line |
|---|---|---|---|---|
| ldsr | reg2, regID | op0510=0x3F; op1631=0x20 | real | v850_special.sinc:66 |
| stsr | regID, reg2 | op0510=0x3F; op1631=0x40 | real | v850_special.sinc:70 |
| caxi | [reg1], reg2, reg3 | op0510=0x3F; op1626=0xEE | real | v850_special.sinc:75 |
| stsr | regID, reg2, selID(1..15, skip 8) | op0510=0x3F; op1626=0x40 | real | v850e3.sinc:251-264 |
| ldsr | reg2, regID, selID(1..15, skip 8) | op0510=0x3F; op1626=0x20 | real | v850e3.sinc:267-280 |
| cache | cacheop, reg1 | op0510=0x3F; op1315=0x7; op1626=0x160 | unimpl | v850e3.sinc:536 |
| dbcp | - | op0015=0xE840 | unimpl | v850e3.sinc:539 |
| dbhvtrap | - | op0015=0xE040 | unimpl | v850e3.sinc:541 |
| dbpush | reg1, reg3 | op0515=0x2FF; op1626=0x160 | unimpl | v850e3.sinc:543 |
| dbtag | imm10 | op0515=0x67F; op1626=0x160 | unimpl | v850e3.sinc:545 |
| dst | - | op0015=0x07E0; op1631=0x0134 | unimpl | v850e3.sinc:548 |
| est | - | op0015=0x07E0; op1631=0x0132 | unimpl | v850e3.sinc:550 |
| hvcall | vector8 | op0515=0x6BF; op1624=0x160,op3030=1 | unimpl | v850e3.sinc:553 |
| hvtrap | imm5 | op0515=0x03F; op1631=0x0110 | unimpl | v850e3.sinc:555 |
| ldtc.gr | reg1, reg2 | op0510=0x3F; op1631=0x0032 | unimpl | v850e3.sinc:558 |
| ldtc.sr | reg1, SR[2], selID(0..7) | op1626=0x030 | unimpl (8 entries) | v850e3.sinc:561-569 |
| ldtc.vr | reg1, VR2 | op0515=0x03F; op1631=0x0832 | unimpl | v850e3.sinc:572 |
| ldtc.pc | reg1 | op0515=0x03F; op1631=0xF832 | unimpl | v850e3.sinc:575 |
| ldvc.sr | reg1, SR[2], selID(0..7) | op1626=0x034 | unimpl (8 entries) | v850e3.sinc:578-586 |
| pref | prefop, reg1 | op0515=0x6FF; op1626=0x160 | unimpl | v850e3.sinc:589 |
| sttc.gr | reg1, reg2 | op0515=0x03F; op1631=0x0052 | unimpl | v850e3.sinc:592 |
| sttc.sr | SR1, reg2, selID(0..31) | op1626=0x050 | unimpl (33 entries, 0..31) | v850e3.sinc:595-629 |
| sttc.vr | VR1, reg2 | op0515=0x03F; op1631=0x0852 | unimpl | v850e3.sinc:632 |
| sttc.pc | reg2 | op0515=0x03F; op1631=0xF852 | unimpl | v850e3.sinc:635 |
| stvc.sr | SR1, reg2, selID(0..31) | op1626=0x054 | unimpl (33 entries, 0..31) | v850e3.sinc:638-670 |
| tlbai | - | op0015=0x87E0; op1631=0x8960 | unimpl | v850e3.sinc:674 |
| tlbr | - | op0015=0x87E0; op1631=0xE960 | unimpl | v850e3.sinc:676 |
| tlbs | - | op0015=0x87E0; op1631=0xC160 | unimpl | v850e3.sinc:678 |
| tlbvi | - | op0015=0x87E0; op1631=0x8160 | unimpl | v850e3.sinc:680 |
| tlbw | - | op0015=0x87E0; op1631=0xE160 | unimpl | v850e3.sinc:682 |

Notes on `ldsr`/`stsr` selID: entries are only emitted for selIDs 1,2,3,4,5,6,7,9,10,11,12,13,14,15. **selID 8 and 0 are not handled** in the selID form (selID 0 is the no-selID form covered by the simple `ldsr/stsr` at v850_special.sinc). **No `setpsw` / `clrpsw` / `cll` constructor exists** in any `.sinc` (both are RH850 G4MH instructions missing from this baseline).

## FPU (F.S / F.D + conversions, compares, fused-MAC, half-precision)

| Mnemonic | Form | Opcode (op2126,op1620 unless noted) | Status | File:Line |
|---|---|---|---|---|
| absf.d | reg2pair, reg3pair | 0x22, 0b11000; op0004=0 | real | v850_float.sinc:2 |
| absf.s | reg2, reg3 | 0x22, 0b01000; op0004=0 | real | v850_float.sinc:7 |
| addf.d | reg1pair, reg2pair, reg3pair | 0x23, 0b10000 | real | v850_float.sinc:12 |
| addf.s | reg1, reg2, reg3 | 0x23, 0b00000 | real | v850_float.sinc:17 |
| ceilf.dl | reg2pair, reg3pair | 0x22, 0b10100; op0004=0b00010 | real | v850_float.sinc:22 |
| ceilf.dul | reg2pair, reg3pair | 0x22, 0b10100; op0004=0b10010 | real | v850_float.sinc:28 |
| ceilf.duw | reg2pair, reg3 | 0x22, 0b10000; op0004=0b10010 | real | v850_float.sinc:34 |
| ceilf.dw | reg2pair, reg3 | 0x22, 0b10000; op0004=0b00010 | real | v850_float.sinc:39 |
| ceilf.sl | reg2, reg3pair | 0x22, 0b00100; op0004=0b00010 | real | v850_float.sinc:44 |
| ceilf.sul | reg2, reg3pair | 0x22, 0b00100; op0004=0b10010 | real | v850_float.sinc:50 |
| ceilf.sul (labelled .SUW) | reg2, reg3 | 0x22, 0b00000; op0004=0b10010 | real | v850_float.sinc:56 |
| ceilf.sw | reg2, reg3 | 0x22, 0b00000; op0004=0b00010 | real | v850_float.sinc:61 |
| cmovf.d | fcbit, reg1, reg2, reg3pair | 0x20, op2020=1 | real | v850_float.sinc:67 |
| cmovf.s | fcbit, reg1, reg2, reg3 | 0x20, op2020=0 | real | v850_float.sinc:73 |
| cmpf.d | fcond, reg2pair, reg1pair, fcbit | 0x21, op2020=1 | real | v850_float.sinc:88 |
| cmpf.s | fcond, reg2, reg1, fcbit | 0x21, op2020=0 | real | v850_float.sinc:98 |
| cvtf.dl | reg2pair, reg3pair | 0x22, 0b10100; op0004=0b00100 | real | v850_float.sinc:109 |
| cvtf.ds | reg2pair, reg3 | 0x22, 0b10010; op0004=0b00011 | real | v850_float.sinc:114 |
| cvtf.dul | reg2pair, reg3pair | 0x22, 0b10100; op0004=0b10100 | real | v850_float.sinc:119 |
| cvtf.duw | reg2pair, reg3 | 0x22, 0b10000; op0004=0b10100 | real | v850_float.sinc:124 |
| cvtf.sw (labelled .DW) | reg2pair, reg3 | 0x22, 0b10000; op0004=0b00100 | real | v850_float.sinc:129 |
| cvtf.ls (labelled .LD) | reg2pair, reg3pair | 0x22, 0b10010; op0004=0b00001 | real | v850_float.sinc:134 |
| cvtf.ls | reg2pair, reg3 | 0x22, 0b00010; op0004=0b00001 | real | v850_float.sinc:139 |
| cvtf.sd | reg2, reg3pair | 0x22, 0b10010; op0004=0b00010 | real | v850_float.sinc:144 |
| cvtf.sl | reg2, reg3pair | 0x22, 0b00100; op0004=0b00100 | real | v850_float.sinc:149 |
| cvtf.sul | reg2, reg3pair | 0x22, 0b00100; op0004=0b10100 | real | v850_float.sinc:154 |
| cvtf.suw | reg2, reg3 | 0x22, 0b00000; op0004=0b10100 | real | v850_float.sinc:159 |
| cvtf.sw | reg2, reg3 | 0x22, 0b00000; op0004=0b00100 | real | v850_float.sinc:164 |
| cvtf.uls (labelled .ULD) | reg2pair, reg3pair | 0x22, 0b10010; op0004=0b10001 | real | v850_float.sinc:169 |
| cvtf.uls | reg2pair, reg3 | 0x22, 0b00010; op0004=0b10001 | real | v850_float.sinc:174 |
| cvtf.uwd | reg2, reg3pair | 0x22, 0b10010; op0004=0b10000 | real | v850_float.sinc:179 |
| cvtf.uws | reg2, reg3 | 0x22, 0b00010; op0004=0b10000 | real | v850_float.sinc:184 |
| cvtf.wd | reg2, reg3pair | 0x22, 0b10010; op0004=0b00000 | real | v850_float.sinc:189 |
| cvtf.ws | reg2, reg3 | 0x22, 0b00010; op0004=0b00000 | real | v850_float.sinc:194 |
| divf.s (labelled .D) | reg1pair, reg2pair, reg3pair | 0x23, 0b11110 | real | v850_float.sinc:199 |
| divf.s | reg1, reg2, reg3 | 0x23, 0b01110 | real | v850_float.sinc:204 |
| floorf.dl | reg2pair, reg3pair | 0x22, 0b10100; op0004=0b00011 | real | v850_float.sinc:209 |
| floorf.dul | reg2pair, reg3pair | 0x22, 0b10100; op0004=0b10011 | real | v850_float.sinc:215 |
| floorf.duw | reg2, reg3 | 0x22, 0b10000; op0004=0b10011 | real | v850_float.sinc:222 |
| floorf.dw | reg2, reg3 | 0x22, 0b10000; op0004=0b00011 | real | v850_float.sinc:228 |
| floorf.sl | reg2, reg3pair | 0x22, 0b00100; op0004=0b00011 | real | v850_float.sinc:233 |
| floorf.sul | reg2, reg3pair | 0x22, 0b00100; op0004=0b10011 | real | v850_float.sinc:239 |
| floorf.suw | reg2, reg3 | 0x22, 0b00000; op0004=0b10011 | real | v850_float.sinc:245 |
| floorf.suw (labelled .SW) | reg2, reg3 | 0x22, 0b00000; op0004=0b00011 | real | v850_float.sinc:250 |
| maddf.s | reg1, reg2, reg3, reg4 | op2426=0b101, op2122=0b00 | real | v850_float.sinc:255 |
| maxf.d | reg1pair, reg2pair, reg3pair | 0x23, 0b11000 | real | v850_float.sinc:260 |
| maxf.s | reg1, reg2, reg3 | 0x23, 0b01000 | real | v850_float.sinc:267 |
| minf.d | reg1pair, reg2pair, reg3pair | 0x23, 0b11010 | real | v850_float.sinc:274 |
| minf.s | reg1, reg2, reg3 | 0x23, 0b01010 | real | v850_float.sinc:281 |
| msubf.s | reg1, reg2, reg3, reg4 | op2426=0b101, op2122=0b01 | real | v850_float.sinc:288 |
| mulf.d | reg1, reg2, reg3pair | 0x23, 0b10100 | real | v850_float.sinc:294 |
| mulf.s | reg1, reg2, reg3 | 0x23, 0b00100 | real | v850_float.sinc:299 |
| negf.d | reg2pair, reg3pair | 0x22, 0b11000; op0004=0b00001 | real | v850_float.sinc:304 |
| negf.s | reg2, reg3 | 0x22, 0b01000; op0004=0b00001 | real | v850_float.sinc:309 |
| nmaddf.s | reg1, reg2, reg3, reg4 | op2426=0b101, op2122=0b10 | real | v850_float.sinc:314 |
| nmsubf.s | reg1, reg2, reg3, reg4 | op2426=0b101, op2122=0b11 | real | v850_float.sinc:319 |
| recipf.d | reg2pair, reg3pair | 0x22, 0b11110; op0004=0b00001 | real | v850_float.sinc:324 |
| recipf.s | reg2, reg3 | 0x22, 0b01110; op0004=0b00001 | real | v850_float.sinc:329 |
| rsqrtf.d | reg2pair, reg3pair | 0x22, 0b11110; op0004=0b00010 | real | v850_float.sinc:334 |
| rsqrtf.s | reg2, reg3 | 0x22, 0b01110; op0004=0b00010 | real | v850_float.sinc:339 |
| sqrtf.d | reg2pair, reg3pair | 0x22, 0b11110; op0004=0b00000 | real | v850_float.sinc:344 |
| sqrtf.s | reg2, reg3 | 0x22, 0b01110; op0004=0b00000 | real | v850_float.sinc:349 |
| subf.d | reg1pair, reg2pair, reg3pair | 0x23, 0b10010 | real | v850_float.sinc:355 |
| subf.s | reg1, reg2, reg3 | 0x23, 0b00010 | real | v850_float.sinc:360 |
| trfsr | fcbit | 0x20, op2020=0; op1115=0 | real | v850_float.sinc:365 |
| trncf.dl | reg2pair, reg3pair | 0x22, 0b10100; op0004=0b00001 | real | v850_float.sinc:371 |
| trncf.dul | reg2pair, reg3pair | 0x22, 0b10100; op0004=0b10001 | real | v850_float.sinc:376 |
| trncf.duw | reg2pair, reg3 | 0x22, 0b10000; op0004=0b10001 | real | v850_float.sinc:381 |
| trncf.dw | reg2pair, reg3 | 0x22, 0b10000; op0004=0b00001 | real | v850_float.sinc:386 |
| trncf.sl | reg2, reg3pair | 0x22, 0b00100; op0004=0b00001 | real | v850_float.sinc:391 |
| trncf.sul | reg2, reg3pair | 0x22, 0b00100; op0004=0b10001 | real | v850_float.sinc:396 |
| trncf.suw | reg2, reg3 | 0x22, 0b00000; op0004=0b10001 | real | v850_float.sinc:401 |
| trncf.sw | reg2, reg3 | 0x22, 0b00000; op0004=0b00001 | real | v850_float.sinc:406 |
| cvtf.hs | reg2, reg3 | op0010=0x7E2; op1626=0x442 | real | v850e3.sinc:690 |
| cvtf.sh | reg2, reg3 | op0010=0x7E3; op1626=0x442 | real | v850e3.sinc:699 |
| fmaf.s | reg1, reg2, reg3 | op0510=0x03F; op1626=0x4E0 | real | v850e3.sinc:708 |
| fmsf.s | reg1, reg2, reg3 | op0510=0x03F; op1626=0x4E2 | real | v850e3.sinc:718 |
| fnmaf.s | reg1, reg2, reg3 | op0510=0x03F; op1626=0x4E4 | real | v850e3.sinc:727 |
| fnmsf.s | reg1, reg2, reg3 | op0510=0x03F; op1626=0x4E6 | real | v850e3.sinc:737 |

## DSP / MAC

See `mac` / `macu` in the Arithmetic table (v850_arithmetic.sinc:254, 258). No other DSP-specific opcodes (MUL.HB, DSP saturating variants, vector VR ops) have constructors beyond the VR-register definitions themselves; the G4MH/G4MH2 FXU (`fxu*`) and vector (`vr*`) instruction classes are absent.

## Other

- `cc0003` / `cc1720` (16 condition codes) — helper tables (v850_cond.sinc:7-40)
- `addr9 / addr22 / addr32 / addr32abs / addr17b / addr16loop` — address computation helpers (v850_common.sinc:270-284)
- `R0004 / R1115 / R2731` — r0-zero-folding reg tables (v850_common.sinc:313-320)
- `DispList*` / `PrepList*` / `rXX` / `buildPopSp` / `buildPushSp` — register-list builders for PREPARE/DISPOSE/POPSP/PUSHSP
- `bins_pos / bins_width` — bitfield operand sub-tables (v850e3.sinc:497-507)

## Summary

### Counts per category (status: real / unimpl / stub)

| Category | Real | Unimpl | Stub | Total |
|---|---:|---:|---:|---:|
| Arithmetic (incl. cond-arith sbf/adf/cmov/setf/sasf) | 40 | 0 | 0 | 40 |
| Logical + shift/rotate + SXB/SXH/ZXB/ZXH | 23 | 0 | 0 | 23 |
| Bit manipulation (BSW/HSW/SCH*/SET1/CLR1/NOT1/TST1/BINS) | 17 | 0 | 0 | 17 |
| Load / Store (incl. LD.DW, ST.DW, pre/post-inc/dec, PREPARE/DISPOSE, POPSP/PUSHSP) | 50 | 0 | 2 (ldl.w, stc.w) | 52 |
| Control flow (Bcond/JR/JARL/JMP/RETI/EIRET/FERET/CTRET/TRAP/SYSCALL/HALT/LOOP/CALLT/FETRAP/SWITCH/NOP/SYNC*/DI/EI/SNOOZE) | 29 | 2 (rie ×2) | 0 | 31 |
| System / special-register (LDSR/STSR/CAXI + selID + MPU/cache/TLB/guest/debug) | 31 | 61 | 0 | 92 |
| FPU (all F.S/F.D + conversions + compares + fused-MAC + half-precision) | 80 | 0 | 0 | 80 |
| DSP / MAC | 2 | 0 | 0 | 2 |
| Other (helpers only) | — | — | — | — |
| **TOTAL** | **272** | **63** | **2** | **337** |

### Surprises / notes

- **No `setpsw` / `clrpsw`**: the G4MH PSW flag-manipulation instructions are completely absent (not even as `unimpl`). Any binary using them will be disassembled as undefined.
- **No `cll` (cancel load-link)**: absent, even though `ldl.w` / `stc.w` are stubbed in.
- **`ldl.w` / `stc.w`** are semantic stubs — they read/write memory but don't model the link register / atomic success flag. Functional for straight-line decompilation but unsound for concurrent semantics.
- **`halt_baddata()` is not used anywhere** in the `.sinc` tree — so there are no explicit "known-opcode but safe-to-halt" stubs. Unknown opcodes fall through to Ghidra's default "bad instruction" handling.
- **FPU coverage is very dense** (80 real constructors). The only FPU gaps are the FXU (`fxu*`) and any G4MH2-specific extensions beyond half-precision and fused-MAC.
- **MPU/cache/TLB/guest-mode/debug block is essentially a parser-only layer**: 61 `unimpl` entries covering `ldtc.*`, `ldvc.*`, `sttc.*`, `stvc.*`, `cache`, `pref`, `tlb*`, `hv*`, `db*`, `dst`, `est`. The cost of bringing these up to "real" is mechanical but large.
- **`sttc.sr` / `stvc.sr` have selID 0..31 entries**, but `ldtc.sr` / `ldvc.sr` only cover selID 0..7 — asymmetric and probably intentional (store is 32 to match reg-field width; load side never got extended). Worth flagging for Phase 2.
- **selID 8 is missing from `ldsr`/`stsr`** selID-bearing forms. Baseline has no register bank attached for selID 8 (the FXU set is at selID 10), so selID-8 `ldsr/stsr` will not disassemble.
- **No VR (vector register) ops** beyond the `vr0..vr31` register definition and the unimpl `ldtc.vr` / `sttc.vr`.
- **Duplicate / mis-labelled float constructors** in `v850_float.sinc` (e.g. two `cvtf.ls`, two `divf.s`, `ceilf.sul` reused for SUW, `floorf.suw` reused for SW, `cvtf.sw` named but comment says DW). These compile fine (distinct patterns) but the disassembly mnemonic is wrong in several cases — flag for Phase 3 cleanup.

### Files inspected

- `v850_common.sinc` (321 lines) — register/token/attach/macro definitions only; no constructors.
- `v850_cond.sinc` (99 lines)
- `v850_arithmetic.sinc` (261 lines)
- `v850_logical.sinc` (100 lines)
- `v850_data_manipulation.sinc` (178 lines)
- `v850_load_store.sinc` (151 lines)
- `v850_func.sinc` (186 lines)
- `v850_special.sinc` (163 lines)
- `v850_float.sinc` (409 lines)
- `v850e3.sinc` (749 lines)

All files parsed successfully; no `v850_system.sinc` exists in the tree.
