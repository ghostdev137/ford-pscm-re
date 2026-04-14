from .opcode_formats import Format, FormatI, FormatII, FormatIII, FormatIV7, FormatIV4, FormatV, FormatF
from .opcode_formats import FormatVI, FormatVII, FormatVIII, FormatIX, FormatX, FormatXI, FormatXII, FormatXIII
from .opcode_formats import FormatXIV
from .enums import MNEM, REG as REG, Subarch, check_subarch
from .operand import *


def bs2int(bs: bytes, endianess=0) -> int:
    bs = (bs + b"\x00" * 8)[:8]
    indices = range(8)
    if not endianess:
        indices = reversed(indices)
    r = 0
    for i in indices:
        r <<= 8
        r |= bs[i]
    return r


def invalid(size=1):
    def f(cxt, fmt: Format):
        return MNEM.INVALID_CODE, [], size

    return f


def undef(size=1):
    def f(cxt, fmt: Format):
        return MNEM.UNDEF_CODE, [], size

    return f


class DecoderContext(object):
    def __init__(self, subarch=Subarch.V850E2M, **kw):
        self.subarch = subarch

    def check_mnem(self, mnem):
        return check_subarch(self.subarch, mnem)


def subtable00(cxt: DecoderContext, fmt: Format):
    """ MOV R,r | NOP | SYNCE | SYNCM | SYNCP """
    if fmt.hi5:
        return MNEM.MOV, [Reg(fmt.lo5), Reg(fmt.hi5)], 1
    else:
        if fmt.lo5 == 0:
            return MNEM.NOP, [], 1
        elif fmt.lo5 == 0x1c:
            return MNEM.SYNCI, [], 1
        elif fmt.lo5 == 0x1d:
            return MNEM.SYNCE, [], 1
        elif fmt.lo5 == 0x1e:
            return MNEM.SYNCM, [], 1
        elif fmt.lo5 == 0x1f:
            return MNEM.SYNCP, [], 1
    return MNEM.INVALID_CODE, [], 1


def subtable01(cxt: DecoderContext, fmt: Format):
    """ NOT """
    return MNEM.NOT, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


def subtable02(cxt: DecoderContext, fmt: Format):
    """ DIVH | SWITCH | DBTRAP | RIE """
    if fmt.lo5 and fmt.hi5:
        return MNEM.DIVH, [Reg(fmt.lo5), Reg(fmt.hi5)], 1
    elif fmt.lo5 and not fmt.hi5:
        return MNEM.SWITCH, [Reg(fmt.lo5)], 1
    elif not fmt.lo5 and fmt.hi5 == 0x1f:
        return MNEM.DBTRAP, [], 1
    elif not fmt.lo5 and not fmt.hi5:
        return MNEM.RIE, [], 1
    elif not fmt.lo5 and fmt.hi5 <= 0x0f:
        return MNEM.FETRAP, [VecJump(fmt.hi5, width=4)], 1
    return MNEM.INVALID_CODE, [], 1


def subtable03(cxt: DecoderContext, fmt: Format):
    """ JMP | SLD.BU | SLD.HU """
    if not fmt.hi5:
        return MNEM.JMP, [RegJump(fmt.lo5)], 1
    else:
        disp4 = fmt[3:0]
        if fmt.bit4:
            mnem = MNEM.SLD_HU
        else:
            mnem = MNEM.SLD_BU
        return mnem, [EpBasedMem(disp4, width=4, signed=False), Reg(fmt.hi5)], 1


subtable0 = [
    subtable00,
    subtable01,
    subtable02,
    subtable03
]


def subtable10(cxt: DecoderContext, fmt: Format):
    """ SATSUBR | ZXB """
    if not fmt.hi5:
        return MNEM.ZXB, [Reg(fmt.lo5)], 1
    else:
        return MNEM.SATSUBR, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


def subtable11(cxt: DecoderContext, fmt: Format):
    """ SATSUB | SXB """
    if not fmt.hi5:
        return MNEM.SXB, [Reg(fmt.lo5)], 1
    else:
        return MNEM.SATSUB, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


def subtable12(cxt: DecoderContext, fmt: Format):
    """ SATADD | ZXH """
    if not fmt.hi5:
        return MNEM.ZXH, [Reg(fmt.lo5)], 1
    else:
        return MNEM.SATADD, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


def subtable13(cxt: DecoderContext, fmt: Format):
    """ MULH | SXH """
    if not fmt.hi5:
        return MNEM.SXH, [Reg(fmt.lo5)], 1
    else:
        return MNEM.MULH, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


subtable1 = [
    subtable10,
    subtable11,
    subtable12,
    subtable13
]


def subtable20(cxt: DecoderContext, fmt: Format):
    """ OR """
    return MNEM.OR, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


def subtable21(cxt: DecoderContext, fmt: Format):
    """ XOR """
    return MNEM.XOR, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


def subtable22(cxt: DecoderContext, fmt: Format):
    """ AND """
    return MNEM.AND, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


def subtable23(cxt: DecoderContext, fmt: Format):
    """ TST """
    return MNEM.TST, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


subtable2 = [
    subtable20,
    subtable21,
    subtable22,
    subtable23
]


def subtable30(cxt: DecoderContext, fmt: Format):
    """ SUBR """
    return MNEM.SUBR, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


def subtable31(cxt: DecoderContext, fmt: Format):
    """ SUB """
    return MNEM.SUB, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


def subtable32(cxt: DecoderContext, fmt: Format):
    """ ADD """
    return MNEM.ADD, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


def subtable33(cxt: DecoderContext, fmt: Format):
    """ CMP """
    return MNEM.CMP, [Reg(fmt.lo5), Reg(fmt.hi5)], 1


subtable3 = [
    subtable30,
    subtable31,
    subtable32,
    subtable33
]


def subtable40(cxt: DecoderContext, fmt: Format):
    """ MOV | CALLT """
    if fmt.hi5:
        return MNEM.MOV, [Imm(fmt.lo5, width=5, signed=True), Reg(fmt.hi5)], 1
    else:
        return MNEM.CALLT, [Imm(fmt[5:0], width=6, signed=False)], 1


def subtable41(cxt: DecoderContext, fmt: Format):
    """ SATADD | CALLT """
    if fmt.hi5:
        return MNEM.SATADD, [Imm(fmt.lo5, width=5, signed=True), Reg(fmt.hi5)], 1
    else:
        return MNEM.CALLT, [Imm(fmt[5:0], width=6, signed=False)], 1


def subtable42(cxt: DecoderContext, fmt: Format):
    """ ADD """
    return MNEM.ADD, [Imm(fmt.lo5, width=5, signed=True), Reg(fmt.hi5)], 1


def subtable43(cxt: DecoderContext, fmt: Format):
    """ CMP """
    return MNEM.CMP, [Imm(fmt.lo5, width=5, signed=True), Reg(fmt.hi5)], 1


subtable4 = [
    subtable40,
    subtable41,
    subtable42,
    subtable43
]


def subtable50(cxt: DecoderContext, fmt: Format):
    """ SHR """
    return MNEM.SHR, [Imm(fmt.lo5, width=5, signed=False), Reg(fmt.hi5)], 1


def subtable51(cxt: DecoderContext, fmt: Format):
    """ SAR """
    return MNEM.SAR, [Imm(fmt.lo5, width=5, signed=False), Reg(fmt.hi5)], 1


def subtable52(cxt: DecoderContext, fmt: Format):
    """ SHL """
    return MNEM.SHL, [Imm(fmt.lo5, width=5, signed=False), Reg(fmt.hi5)], 1


def subtable53(cxt: DecoderContext, fmt: Format):
    """ MULH | JR | JARL """
    if fmt.hi5:
        return MNEM.MULH, [Imm(fmt.lo5, width=5, signed=True), Reg(fmt.hi5)], 1
    else:
        fmt = FormatVI(fmt)
        operands = [RelJump(fmt.imm32, width=32, signed=True)]
        if fmt.lo5:
            mnem = MNEM.JARL
            operands += [Reg(fmt.reg1)]
        else:
            mnem = MNEM.JR
        return mnem, operands, 3


subtable5 = [
    subtable50,
    subtable51,
    subtable52,
    subtable53
]


def subtable6(cxt: DecoderContext, fmt: Format):
    """ SLD.B """
    fmt = FormatIV7(fmt)
    return MNEM.SLD_B, [EpBasedMem(fmt.disp7, width=7, signed=False), Reg(fmt.reg2)], 1


def subtable7(cxt: DecoderContext, fmt: Format):
    """ SST.B """
    fmt = FormatIV7(fmt)
    return MNEM.SST_B, [Reg(fmt.reg2), EpBasedMem(fmt.disp7, width=7, signed=False)], 1


def subtable8(cxt: DecoderContext, fmt: Format):
    """ SLD.H """
    fmt = FormatIV7(fmt)
    return MNEM.SLD_B, [EpBasedMem(fmt.disp7, width=7, signed=False), Reg(fmt.reg2)], 1


def subtable9(cxt: DecoderContext, fmt: Format):
    """ SST.H """
    fmt = FormatIV7(fmt)
    return MNEM.SST_B, [Reg(fmt.reg2), EpBasedMem(fmt.disp7, width=7, signed=False)], 1


def subtableA(cxt: DecoderContext, fmt: Format):
    fmt = FormatIV7(fmt)
    if fmt.sub_opcode:
        mnem = MNEM.SST_W
    else:
        mnem = MNEM.SLD_W
    disp8 = fmt.disp6 << 2
    return mnem, [EpBasedMem(disp8, width=8, signed=False), Reg(fmt.reg2)], 1


def subtableB(cxt: DecoderContext, fmt: Format):
    fmt = FormatIII(fmt)
    return MNEM.B, [Cond(fmt.cond), RelJump(fmt.disp9, width=9, signed=True)], 1


def subtableC0(cxt: DecoderContext, fmt: Format):
    """ ADDI """
    fmt = FormatVI(fmt)
    return MNEM.ADDI, [Imm(fmt.imm16, width=16, signed=True), Reg(fmt.reg1), Reg(fmt.reg2)], 2


def subtableC1(cxt: DecoderContext, fmt: Format):
    """ MOVEA | MOV """
    fmt = FormatVI(fmt)
    if fmt.hi5:
        return MNEM.MOVEA, [Imm(fmt.imm16, width=16, signed=True), Reg(fmt.reg1), Reg(fmt.reg2)], 2
    else:
        return MNEM.MOV, [Imm(fmt.imm32, width=32, signed=False), Reg(fmt.reg1)], 3


def subtableC2(cxt: DecoderContext, fmt: Format):
    """ MOVHI | DISPOSE """
    if fmt.hi5:
        fmt = FormatVI(fmt)
        return MNEM.MOVHI, [Imm(fmt.imm16, width=16, signed=False), Reg(fmt.reg1), Reg(fmt.reg2)], 2
    else:
        fmt = FormatXIII(fmt)
        operands = [Imm(fmt.imm5, width=5, signed=False), RegList(fmt.reg_list)]
        if fmt.reg2.value:
            operands += [Reg(fmt.reg2)]
        return MNEM.DISPOSE, operands, 2


def subtableC3(cxt: DecoderContext, fmt: Format):
    """ SATSUBI | DISPOSE """
    if fmt.hi5:
        fmt = FormatVI(fmt)
        return MNEM.SATSUBI, [Imm(fmt.imm16, width=16, signed=True), Reg(fmt.reg1), Reg(fmt.reg2)], 2
    else:
        fmt = FormatXIII(fmt)
        operands = [Imm(fmt.imm5, width=5, signed=False), RegList(fmt.reg_list)]
        if fmt.reg2.value:
            operands += [Reg(fmt.reg2)]
        return MNEM.DISPOSE, operands, 2


subtableC = [
    subtableC0,
    subtableC1,
    subtableC2,
    subtableC3,
]


def subtableD0(cxt: DecoderContext, fmt: Format):
    """ ORI """
    fmt = FormatVI(fmt)
    return MNEM.ORI, [Imm(fmt.imm16, width=16, signed=False), Reg(fmt.reg1), Reg(fmt.reg2)], 2


def subtableD1(cxt: DecoderContext, fmt: Format):
    """ XORI """
    fmt = FormatVI(fmt)
    return MNEM.XORI, [Imm(fmt.imm16, width=16, signed=False), Reg(fmt.reg1), Reg(fmt.reg2)], 2


def subtableD2(cxt: DecoderContext, fmt: Format):
    """ ANDI """
    fmt = FormatVI(fmt)
    return MNEM.ANDI, [Imm(fmt.imm16, width=16, signed=False), Reg(fmt.reg1), Reg(fmt.reg2)], 2


def subtableD3(cxt: DecoderContext, fmt: Format):
    """ MULHI | JMP | LOOP """
    fmt = FormatVI(fmt)
    if fmt.hi5:
        return MNEM.MULHI, [Imm(fmt.imm16, width=16, signed=False), Reg(fmt.reg1), Reg(fmt.reg2)], 2
    elif fmt[16] == 0:
        return MNEM.JMP, [BasedJump(fmt.imm32, fmt.reg1, width=32, signed=True)], 3
    else:
        fmt = FormatVII(fmt)
        disp16 = fmt[31:17] << 1
        return MNEM.LOOP, [Reg(fmt.reg1), Imm(disp16, width=16, signed=False)], 2


subtableD = [
    subtableD0,
    subtableD1,
    subtableD2,
    subtableD3,
]


def subtableE0(cxt: DecoderContext, fmt: Format):
    """ LD.B """
    fmt = FormatVII(fmt)
    return MNEM.LD_B, [BasedMem(fmt.disp16, fmt.reg1, width=16, signed=True), Reg(fmt.reg2)], 2


def subtableE1(cxt: DecoderContext, fmt: Format):
    """ LD.H | LD.W """
    fmt = FormatVII(fmt)
    if fmt.sub_opcode:
        mnem = MNEM.LD_W
    else:
        mnem = MNEM.LD_H
    return mnem, [BasedMem(fmt.disp15 << 1, fmt.reg1, width=16, signed=True), Reg(fmt.reg2)], 2


def subtableE2(cxt: DecoderContext, fmt: Format):
    """ ST.B """
    fmt = FormatVII(fmt)
    return MNEM.ST_B, [Reg(fmt.reg2), BasedMem(fmt.disp16, fmt.reg1, width=16, signed=True)], 2


def subtableE3(cxt: DecoderContext, fmt: Format):
    """ ST.H | ST.W """
    fmt = FormatVII(fmt)
    if fmt.sub_opcode:
        mnem = MNEM.ST_W
    else:
        mnem = MNEM.ST_H
    return mnem, [Reg(fmt.reg2), BasedMem(fmt.disp15 << 1, fmt.reg1, width=16, signed=True)], 2


subtableE = [
    subtableE0,
    subtableE1,
    subtableE2,
    subtableE3,
]


def subtableF0(cxt: DecoderContext, fmt: Format):
    """ JR | JARL | LD.BU | PREPARE | LD.B | LD.H | ST.B | ST.W """
    if fmt.bit16:
        if fmt.hi5:
            fmt = FormatVII(fmt)
            disp16 = fmt.disp15 << 1 | fmt[5]
            return MNEM.LD_BU, [BasedMem(disp16, fmt.reg1, width=16, signed=True), Reg(fmt.reg2)], 2
        else:
            sub_opcode = fmt[18:17]
            if sub_opcode == 1 or (sub_opcode == 0 and fmt[20:19] == 0):
                fmt = FormatXIII(fmt)
                f = fmt[20:19]
                operands = [RegList(fmt.reg_list), Imm(fmt.imm5, width=5, signed=False)]
                size = 2
                if f == 0:
                    operands.append(Reg(REG.SP))
                elif f == 1:
                    operands.append(Imm(fmt.imm16, width=16, signed=True))
                elif f == 2:
                    operands.append(Imm(fmt.imm16 << 16, width=32, signed=False))
                elif f == 3:
                    operands.append(Imm(fmt.imm32, width=32))
                    size = 3
                return MNEM.PREPARE, operands, size
            else:
                fmt = FormatXIV(fmt)
                size = 3
                if fmt.sub_opcode == 5:
                    mnem = MNEM.LD_B
                    operands = [BasedMem(fmt.disp23, fmt.reg1, width=23, signed=True), Reg(fmt.reg3)]
                elif fmt.sub_opcode == 7 and fmt[20] == 0:
                    mnem = MNEM.LD_H
                    operands = [BasedMem(fmt.disp23, fmt.reg1, width=23, signed=True), Reg(fmt.reg3)]
                elif fmt.sub_opcode == 9 and fmt[20] == 0:
                    mnem = MNEM.LD_W
                    operands = [BasedMem(fmt.disp23, fmt.reg1, width=23, signed=True), Reg(fmt.reg3)]
                elif fmt.sub_opcode == 13:
                    mnem = MNEM.ST_B
                    operands = [Reg(fmt.reg3), BasedMem(fmt.disp23, fmt.reg1, width=23, signed=True)]
                elif fmt.sub_opcode == 15:
                    mnem = MNEM.ST_W
                    operands = [Reg(fmt.reg3), BasedMem(fmt.disp23, fmt.reg1, width=23, signed=True)]
                else:
                    mnem = MNEM.INVALID_CODE
                    operands = []
                    size = 2
                return mnem, operands, size
    else:
        fmt = FormatV(fmt)
        if fmt.hi5:
            return MNEM.JARL, [RelJump(fmt.disp22, width=22, signed=True), Reg(fmt.reg2)], 2
        else:
            return MNEM.JR, [RelJump(fmt.disp22, width=22, signed=True)], 2


def subtableF1(cxt: DecoderContext, fmt: Format):
    """ JR | JARL | LD.BU | PREPARE | LD.HU | ST.H """
    if fmt.bit16:
        if fmt.hi5:
            fmt = FormatVII(fmt)
            disp16 = fmt.disp15 << 1 | fmt[5]
            return MNEM.LD_BU, [BasedMem(disp16, fmt.reg1, width=16, signed=True), Reg(fmt.reg2)], 2
        else:
            sub_opcode = fmt[18:17]
            if sub_opcode == 1 or (sub_opcode == 0 and fmt[20:19] == 0):
                fmt = FormatXIII(fmt)
                f = fmt[20:19]
                operands = [RegList(fmt.reg_list), Imm(fmt.imm5, width=5, signed=False)]
                size = 2
                if f == 0:
                    operands.append(Reg(REG.SP))
                elif f == 1:
                    operands.append(Imm(fmt.imm16, width=16, signed=True))
                elif f == 2:
                    operands.append(Imm(fmt.imm16 << 16, width=32, signed=False))
                elif f == 3:
                    operands.append(Imm(fmt.imm32, width=32))
                    size = 3
                return MNEM.PREPARE, operands, size
            else:
                fmt = FormatXIV(fmt)
                size = 3
                if fmt.sub_opcode == 5:
                    mnem = MNEM.LD_BU
                    operands = [BasedMem(fmt.disp23, fmt.reg1, width=23, signed=True), Reg(fmt.reg3)]
                elif fmt.sub_opcode == 7 and fmt[20] == 0:
                    mnem = MNEM.LD_HU
                    operands = [BasedMem(fmt.disp23, fmt.reg1, width=23, signed=True), Reg(fmt.reg3)]
                elif fmt.sub_opcode == 13 and fmt[20] == 0:
                    mnem = MNEM.ST_H
                    operands = [Reg(fmt.reg3), BasedMem(fmt.disp23, fmt.reg1, width=23, signed=True)]
                else:
                    mnem = MNEM.INVALID_CODE
                    operands = []
                    size = 2
                return mnem, operands, size
    else:
        fmt = FormatV(fmt)
        if fmt.hi5:
            return MNEM.JARL, [RelJump(fmt.disp22, width=22, signed=True), Reg(fmt.reg2)], 2
        else:
            return MNEM.JR, [RelJump(fmt.disp22, width=22, signed=True)], 2


def subtableF2(cxt: DecoderContext, fmt: Format):
    """ SET1 | NOT1 | CLR1 | TST1 """
    fmt = FormatVIII(fmt)
    mnems = [MNEM.SET1, MNEM.NOT1, MNEM.CLR1, MNEM.TST1]
    mnem = mnems[fmt.sub_opcode]
    return mnem, [BitMem(fmt.bit, fmt.disp16, fmt.reg1, width=16, signed=True)], 2


def subtableF3(cxt: DecoderContext, fmt: Format):
    """ LD.HU | undef | extended """
    if fmt.bit16:
        if fmt.hi5:
            fmt = FormatVII(fmt)
            return MNEM.LD_HU, [BasedMem(fmt.disp15 << 1, width=16, signed=True), Reg(fmt.reg2)], 2
        else:
            return MNEM.INVALID_CODE, [], 2
    else:
        return decode_ext(cxt, fmt)


subtableF = [
    subtableF0,
    subtableF1,
    subtableF2,
    subtableF3
]


def ext_subtable00(cxt: DecoderContext, fmt: Format):
    """ SETF | RIE """
    if fmt.ext_hi5 == 0 and fmt.ext_lo5 == 0:
        if fmt[4] == 0:
            fmt = FormatIX(fmt)
            return MNEM.SETF, [Cond(fmt.lo5), Reg(fmt.hi5)], 2
        else:
            return MNEM.RIE, [], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable01(cxt: DecoderContext, fmt: Format):
    """ LDSR """
    if fmt.ext_lo5 == 0:
        if fmt.ext_hi5 == 0:
            return MNEM.LDSR, [Reg(fmt.lo5), SReg(fmt.hi5)], 2
        elif cxt.subarch.value >= Subarch.RH850:
            return MNEM.LDSR, [Reg(fmt.lo5), SReg(fmt.hi5), Imm(fmt.ext_hi5, width=5, signed=False)], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable02(cxt: DecoderContext, fmt: Format):
    """ STSR """
    if fmt.ext_lo5 == 0:
        if fmt.ext_hi5 == 0:
            return MNEM.STSR, [SReg(fmt.lo5), Reg(fmt.hi5)], 2
        elif cxt.subarch.value >= Subarch.RH850:
            return MNEM.STSR, [SReg(fmt.lo5), Reg(fmt.hi5), Imm(fmt.ext_hi5, width=5, signed=False)], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable03(cxt: DecoderContext, fmt: Format):
    """ """
    return MNEM.UNDEF_CODE, [], 2


ext_subtable0 = [
    ext_subtable00,
    ext_subtable01,
    ext_subtable02,
    ext_subtable03
]


def ext_subtable10(cxt: DecoderContext, fmt: Format):
    """ SHR | BINS """
    fmt = FormatIX(fmt)
    if fmt.ext_hi5 == 0 and fmt.ext_lo5 == 0:
        return MNEM.SHR, [Reg(fmt.lo5), Reg(fmt.hi5)], 2
    elif fmt.ext_lo5 == 0x2:
        return MNEM.SHR, [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.ext_hi5)], 2
    elif fmt[20]:
        msb = fmt.ext_hi5 >> 1
        lsb = fmt[27] << 3 | fmt[19:17]
        msb += 16
        lsb += 16
        pos = lsb
        wid = msb - pos + 1
        return MNEM.BINS, [Reg(fmt.lo5), Imm(wid, width=5, signed=False), Imm(pos, width=5, signed=False),
                           Reg(fmt.hi5)], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable11(cxt: DecoderContext, fmt: Format):
    """ SAR | BINS """
    fmt = FormatIX(fmt)
    if fmt.ext_hi5 == 0 and fmt.ext_lo5 == 0:
        return MNEM.SAR, [Reg(fmt.lo5), Reg(fmt.hi5)], 2
    elif fmt.ext_lo5 == 0x2:
        return MNEM.SAR, [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.ext_hi5)], 2
    elif fmt[20]:
        msb = fmt.ext_hi5 >> 1
        lsb = fmt[27] << 3 | fmt[19:17]
        msb += 16
        pos = lsb
        wid = msb - pos + 1
        return MNEM.BINS, [Reg(fmt.lo5), Imm(wid, width=5, signed=False), Imm(pos, width=5, signed=False),
                           Reg(fmt.hi5)], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable12(cxt: DecoderContext, fmt: Format):
    """ SHL | BINS """
    fmt = FormatIX(fmt)
    if fmt.ext_hi5 == 0 and fmt.ext_lo5 == 0:
        return MNEM.SHL, [Reg(fmt.lo5), Reg(fmt.hi5)], 2
    elif fmt.ext_lo5 == 0x2:
        return MNEM.SHL, [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.ext_hi5)], 2
    elif fmt.ext_lo5 == 0x4 or fmt.ext_lo5 == 0x6:
        if fmt.ext_lo5 == 0x4:
            operands = [Imm(fmt.lo5, width=5, signed=False)]
        else:
            operands = [Reg(fmt.lo5)]
        operands += [Reg(fmt.reg2), Reg(fmt.ext_hi5)]
        return MNEM.ROTL, operands, 2
    elif fmt[20]:
        msb = fmt.ext_hi5 >> 1
        lsb = fmt[27] << 3 | fmt[19:17]
        pos = lsb
        wid = msb - pos + 1
        return MNEM.BINS, [Reg(fmt.lo5), Imm(wid, width=5, signed=False), Imm(pos, width=5, signed=False),
                           Reg(fmt.hi5)], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable13(cxt: DecoderContext, fmt: Format):
    """ SET1 | NOT1 | CLR1 | TST1 | CAXI """
    if fmt.ext_hi5 == 0 and fmt[20:19] == 0:
        ff = fmt[18:17]
        mnem = [MNEM.SET1, MNEM.NOT1, MNEM.CLR1, MNEM.TST1][ff]
        return mnem, [Reg(fmt.hi5), RegMem(fmt.lo5)], 2
    elif fmt.ext_lo5 == 0xe:
        fmt = FormatXI(fmt)
        return MNEM.CAXI, [RegMem(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)], 2
    return MNEM.INVALID_CODE, [], 2


ext_subtable1 = [
    ext_subtable10,
    ext_subtable11,
    ext_subtable12,
    ext_subtable13
]


def ext_subtable20(cxt: DecoderContext, fmt: Format):
    """ TRAP """
    if fmt.hi5 == 0 and fmt.ext_hi5 == 0 and fmt.ext_lo5 == 0:
        return MNEM.TRAP, [VecJump(fmt.lo5, width=5)], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable21(cxt: DecoderContext, fmt: Format):
    """ HALT """
    if fmt.hi5 == 0 and fmt.lo5 == 0 and fmt.ext_hi5 == 0 and fmt.ext_lo5 == 0:
        return MNEM.HALT, [], 2
    elif fmt.hi5 == 1 and fmt.lo5 == 0 and fmt.ext_hi5 == 0 and fmt.ext_lo5 == 0:
        return MNEM.SNOOZE, [], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable22(cxt: DecoderContext, fmt: Format):
    """ RETI | CTRET | DBRET | EIRET | FERET | undef """
    if fmt.hi5 == 0 and fmt.lo5 == 0 and fmt.ext_hi5 == 0 and fmt[20:19] == 0:
        ff = fmt[18:17]
        mnem = [MNEM.RETI, MNEM.UNDEF_CODE, MNEM.CTRET, MNEM.DBRET][ff]
        return mnem, [], 2
    elif fmt.hi5 == 0 and fmt.lo5 == 0 and fmt.ext_hi5 == 0 and fmt[20:19] == 1:
        ff = fmt[18:17]
        mnem = [MNEM.EIRET, MNEM.FERET, MNEM.UNDEF_CODE, MNEM.UNDEF_CODE][ff]
        return mnem, [], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable23(cxt: DecoderContext, fmt: Format):
    """ EI | DI | SYSCALL | CLL | PUSHSP | POPSP | undef """
    if fmt.lo5 == 0 and fmt.ext_hi5 == 0 and fmt.ext_lo5 == 0:
        ff_hi = fmt[15:14]
        ff_lo = fmt[13:11]
        mnem = [[MNEM.DI] + [MNEM.UNDEF_CODE] * 3,
                [MNEM.UNDEF_CODE] * 4,
                [MNEM.EI] + [MNEM.UNDEF_CODE] * 3,
                [MNEM.UNDEF_CODE] * 4,
                ][ff_hi][ff_lo]
        return mnem, [], 2
    elif fmt.hi5 == 0x1a and fmt[31:30] == 0 and fmt.ext_lo5 == 0:
        fmt = FormatX(fmt)
        vector8 = fmt[29:27] << 5 | fmt.lo5
        return MNEM.SYSCALL, [VecJump(vector8, width=8)], 2
    elif fmt.hi5 == 0x1f and fmt.lo5 == 0x1f and fmt.ext_hi5 == 0x1e and fmt.ext_lo5 == 0:
        return MNEM.CLL, [], 2
    elif fmt[15:13] == 0x6 and fmt.ext_lo5 == 0:
        prefop = PrefOp(fmt.ext_hi5)
        if prefop:
            return MNEM.PREF, [prefop, RegMem(fmt.lo5)], 2
    elif fmt[15:13] == 0x7 and fmt.ext_lo5 == 0:
        cacheop = CacheOp(fmt[12:11] << 5 | fmt.ext_hi5)
        if cacheop:
            return MNEM.CACHE, [cacheop, RegMem(fmt.lo5)], 2
    elif fmt.hi5 == 0x8 and fmt.ext_lo5 == 0:
        fmt = FormatXI(fmt)
        return MNEM.PUSHSP, [RegRange(fmt.reg1, fmt.reg3)], 2
    elif fmt.hi5 == 0xc and fmt.ext_lo5 == 0:
        fmt = FormatXI(fmt)
        return MNEM.POPSP, [RegRange(fmt.reg1, fmt.reg3)], 2
    return MNEM.INVALID_CODE, [], 2


ext_subtable2 = [
    ext_subtable20,
    ext_subtable21,
    ext_subtable22,
    ext_subtable23
]

ext_subtable3 = undef(2)


def ext_subtable40(cxt: DecoderContext, fmt: Format):
    """ SASF """
    if fmt[4] == 0 and fmt.ext_hi5 == 0 and fmt.ext_lo5 == 0:
        return MNEM.SASF, [Cond(fmt.lo5), Reg(fmt.hi5)], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable41(cxt: DecoderContext, fmt: Format):
    """ MUL | MULU """
    if fmt.ext_lo5 == 0:
        fmt = FormatXI(fmt)
        return MNEM.MUL, [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable42(cxt: DecoderContext, fmt: Format):
    """ MUL | MULU """
    if fmt[17] == 0:
        mnem = MNEM.MUL
    else:
        mnem = MNEM.MULU
    fmt = FormatXII(fmt)
    imm9 = fmt.imm10 & 0x1ff
    return mnem, [Imm(imm9, width=9, signed=False), Reg(fmt.reg2), Reg(fmt.reg3)], 2


ext_subtable43 = ext_subtable42
# def ext_subtable43(fmt: Format):
#    """ MUL | MULU """
#    return MNEM.INVALID_CODE, [], 2


ext_subtable4 = [
    ext_subtable40,
    ext_subtable41,
    ext_subtable42,
    ext_subtable43
]


def ext_subtable50(cxt: DecoderContext, fmt: Format):
    """ DIVH | DIVHU """
    if fmt[20:18] == 0:
        if fmt[17] == 0:
            mnem = MNEM.DIVH
        else:
            mnem = MNEM.DIVHU
        fmt = FormatXI(fmt)
        return mnem, [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)], 2
    return MNEM.INVALID_CODE, [], 2


ext_subtable51 = undef(2)


def ext_subtable52(cxt: DecoderContext, fmt: Format):
    """ DIV | DIVU """
    if fmt[20:18] == 0:
        if fmt[17] == 0:
            mnem = MNEM.DIV
        else:
            mnem = MNEM.DIVU
        fmt = FormatXI(fmt)
        return mnem, [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable53(cxt: DecoderContext, fmt: Format):
    """ DIVQ | DIVQU """
    if fmt[20:18] == 7:
        if fmt[17] == 0:
            mnem = MNEM.DIVQ
        else:
            mnem = MNEM.DIVQU
        fmt = FormatXI(fmt)
        return mnem, [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)], 2
    return MNEM.INVALID_CODE, [], 2


ext_subtable5 = [
    ext_subtable50,
    ext_subtable51,
    ext_subtable52,
    ext_subtable53
]


def ext_subtable60(cxt: DecoderContext, fmt: Format):
    """ CMOV """
    fmt = FormatXII(fmt)
    cond = fmt.ext_lo5 >> 1
    return MNEM.CMOV, [Cond(cond), Imm(fmt.lo5, width=5, signed=True), Reg(fmt.reg2), Reg(fmt.reg3)], 2


def ext_subtable61(cxt: DecoderContext, fmt: Format):
    """ CMOV """
    fmt = FormatXI(fmt)
    cond = fmt.ext_lo5 >> 1
    return MNEM.CMOV, [Cond(cond), Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)], 2


def ext_subtable62(cxt: DecoderContext, fmt: Format):
    """ BSW | BSH | HSW | HSH """
    if fmt.lo5 == 0:
        fmt = FormatXII(fmt)
        ff = fmt[18:17]
        mnem = [MNEM.BSW, MNEM.BSH, MNEM.HSW, MNEM.HSH][ff]
        operands = [Reg(fmt.reg2), Reg(fmt.reg3)]
        return mnem, operands, 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable63(cxt: DecoderContext, fmt: Format):
    """ SCH0R | SCH1R | SCH0L | SCH1L | LDL_W """
    if fmt.lo5 == 0 and fmt[20:19] == 0:
        fmt = FormatIX(fmt)
        ff = fmt[18:17]
        mnem = [MNEM.SCH0R, MNEM.SCH1R, MNEM.SCH0L, MNEM.SCH1L]
        return mnem, [Reg(fmt.reg2), Reg(fmt.ext_hi5)], 2
    elif fmt.hi5 == 0 and fmt.ext_lo5 == 0x18:
        fmt = FormatVII(fmt)
        return MNEM.LDL_W, [RegMem(fmt.reg1), Reg(fmt.ext_hi5)], 2
    elif fmt.hi5 == 0 and fmt.ext_lo5 == 0x1a:
        fmt = FormatVII(fmt)
        return MNEM.STC_W, [Reg(fmt.ext_hi5), RegMem(fmt.reg1)], 2
    return MNEM.INVALID_CODE, [], 2


ext_subtable6 = [
    ext_subtable60,
    ext_subtable61,
    ext_subtable62,
    ext_subtable63
]


def ext_subtable70(cxt: DecoderContext, fmt: Format):
    """ SBF | SATSUB """
    fmt = FormatXI(fmt)
    if fmt.ext_lo5 == 0x1a:
        return MNEM.SATSUB, [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)], 2
    else:
        cond = fmt.ext_lo5 >> 1
        return MNEM.SBF, [Cond(cond), Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)], 2


def ext_subtable71(cxt: DecoderContext, fmt: Format):
    """ ADF | SATADD """
    fmt = FormatXI(fmt)
    if fmt.ext_lo5 == 0x1a:
        return MNEM.SATADD, [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)], 2
    else:
        cond = fmt.ext_lo5 >> 1
        return MNEM.ADF, [Cond(cond), Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)], 2


def ext_subtable72(cxt: DecoderContext, fmt: Format):
    """ MAC """
    if fmt[27] == 0:
        fmt = FormatXI(fmt)
        return MNEM.MAC, [Reg(fmt.reg1), Reg(fmt.reg2), RegPair(fmt.reg3), RegPair(fmt.ext_lo5)], 2
    return MNEM.INVALID_CODE, [], 2


def ext_subtable73(cxt: DecoderContext, fmt: Format):
    """ MACU """
    if fmt[27] == 0:
        fmt = FormatXI(fmt)
        return MNEM.MACU, [Reg(fmt.reg1), Reg(fmt.reg2), RegPair(fmt.reg3), RegPair(fmt.ext_lo5)], 2
    return MNEM.INVALID_CODE, [], 2


ext_subtable7 = [
    ext_subtable70,
    ext_subtable71,
    ext_subtable72,
    ext_subtable73
]

ext_table = [
    ext_subtable0,
    ext_subtable1,
    ext_subtable2,
    ext_subtable3,
    ext_subtable4,
    ext_subtable5,
    ext_subtable6,
    ext_subtable7,
]


def decode_ext(cxt: DecoderContext, fmt: Format):
    if fmt.is_fp:
        return decode_fp(cxt, fmt)
    else:
        ext_tbl = ext_table[fmt.ext_opcode_hi]
        if type(ext_tbl) is list:
            ext_tbl = ext_tbl[fmt.ext_opcode_lo]
        return ext_tbl(cxt, fmt)


def fp_type00(cxt: DecoderContext, fmt: FormatF):
    """CMOVF.D | CMOVF.S"""
    mnem = MNEM.INVALID_CODE
    operands = []
    fcbit = fmt[19:17]
    if fmt.reg3 != REG.R0:
        operands = [Imm(fcbit, width=3, signed=False)]
        if fmt[20] == 0:
            mnem = MNEM.CMOVF_S
            operands += [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)]
        elif fmt[11] == 0 and fmt[0] == 0 and fmt[27] == 0:
            mnem = MNEM.CMOVF_D
            operands += [RegPair(fmt.reg1), RegPair(fmt.reg2), RegPair(fmt.reg3)]
        else:  # INVALID
            operands = []
    elif fmt.hi5 == 0 and fmt.lo5 == 0 and fmt[20] == 0:
        mnem = MNEM.TRFSR
        operands = [Imm(fcbit, width=3, signed=False)]
    return mnem, operands, 2


def fp_type01(cxt: DecoderContext, fmt: FormatF):
    """ CMPF.D | CMPF.S """
    fcbit = fmt[19:17]
    operands = [FCond(fmt[30:27])]
    if fmt[31] == 0 and fmt[20] == 0:
        mnem = MNEM.CMOVF_S
        operands += [Reg(fmt.reg2), Reg(fmt.reg1)]
        if fcbit:
            operands.append(Imm(fcbit, width=3, signed=False))
    elif fmt[31] == 0 and fmt[11] == 0 and fmt[0] == 0:
        mnem = MNEM.CMOVF_D
        operands += [RegPair(fmt.reg1), RegPair(fmt.reg2)]
        if fcbit:
            operands.append(Imm(fcbit, width=4, signed=False))
    else:
        mnem = MNEM.INVALID_CODE
        operands = []
    return mnem, operands, 2


def fp_type02_0(cxt: DecoderContext, fmt: FormatF):
    """ ABFS_{D,S} | CVTF.{WD, WS, UWD, UWS} | SQRT.{D,S} """
    # 11 27 4   0 20   16
    #  0  0 00000  11000   ABSF_D
    #  r  w 00000  01000   ABSF_S
    #  r  w 10000  10010   CVTF.UWD
    #  r  w 10000  00010   CVTF.UWS
    #  r  0 00000  10010   CVTF.WD
    #  r  w 00000  00010   CVTF.WS
    #  0  0 00000  11110   SQRTF.D
    #  r  w 00000  01110   SQRTF.S
    subop = fmt[19:17]
    if subop == 0x1:  # CVTF
        mnem = [[MNEM.CVTF_WS, MNEM.CVTF_UWS],
                [MNEM.CVTF_WD, MNEM.CVTF_UWD],
                ][fmt[20]][fmt[4]]
        if mnem != MNEM.CVTF_WD or fmt[27] == 0:
            return mnem
    elif subop == 0x4:
        mnem, b11, b27 = [(MNEM.ABSF_S, True, True), (MNEM.ABSF_D, False, False)][fmt[20]]
        if fmt[4] == 0 and (b11 or fmt[11] == 0) and (b27 or fmt[27] == 0):
            return mnem
    elif subop == 0x7:
        mnem, b11, b27 = [(MNEM.SQRTF_S, True, True), (MNEM.SQRT_D, False, False)][fmt[20]]
        if fmt[4] == 0 and (b11 or fmt[11] == 0) and (b27 or fmt[27] == 0):
            return mnem


def fp_type02_1(cxt: DecoderContext, fmt: FormatF):
    """ CVTF.{LD, LS, ULD, ULS} | NEGF.{D,S} | RECIPF.{D,S} | TRNCF.{DL, DUL, DUW, DW, SL, SUL, SUW, SW} """
    # 11 27 4   0 20   16
    #  0  0 00001  10010   CVTF.LD
    #  0  w 00001  00010   CVTF.LS
    #  0  0 10001  10010   CVTF.ULD
    #  0  w 10001  00010   CVTF.ULS
    #  0  0 00001  11000   NEGF.D
    #  r  w 00001  01000   NEGF.S
    #  0  0 00001  11110   RECIPF.D
    #  r  w 00001  01110   RECIPF.S
    #  0  0 00001  10100   TRNCF.DL
    #  0  0 10001  10100   TRNCF.DUL
    #  0  w 10001  10000   TRNCF.DUW
    #  0  w 00001  10000   TRNCF.DW
    #  r  0 00001  00100   TRNCF.SL
    #  r  0 10001  00100   TRNCF.SUL
    #  r  w 10001  00000   TRNCF.SUW
    #  r  w 00001  00000   TRNCF.SW
    subop = fmt[19:17]
    if subop == 0 or subop == 2:
        # TRNCF
        sel = fmt[4] << 2 | fmt[20] << 1 | fmt[18]
        mnem, b11, b27 = [(MNEM.TRNCF_SW, True, True), (MNEM.TRNCF_SL, True, False),
                          (MNEM.TRNCF_DW, False, True), (MNEM.TRNCF_DL, False, False),
                          (MNEM.TRNCF_SUW, True, True), (MNEM.TRNCF_SUL, True, False),
                          (MNEM.TRNCF_DUW, False, True), (MNEM.TRNCF_DUL, False, False)][sel]
        if (b11 or fmt[11] == 0) and (b27 or fmt[27] == 0):
            return mnem
    elif subop == 1:
        # CVTF
        sel = fmt[4] << 1 | fmt[20]
        mnem, b11, b27 = [(MNEM.CVTF_LS, False, True), (MNEM.CVTF_LD, False, False),
                          (MNEM.CVTF_ULS, False, True), (MNEM.CVTF_ULD, False, False)][sel]
        if (b11 or fmt[11] == 0) and (b27 or fmt[27] == 0):
            return mnem
    elif subop == 4:
        mnem, b11, b27 = [(MNEM.NEGF_S, True, True), (MNEM.NEGF_D, False, False)][fmt[20]]
        if fmt[4] == 0 and (b11 or fmt[11] == 0) and (b27 or fmt[27] == 0):
            return mnem
    elif subop == 7:
        mnem, b11, b27 = [(MNEM.RECIPF_S, True, True), (MNEM.RECIPF_D, False, False)][fmt[20]]
        if fmt[4] == 0 and (b11 or fmt[11] == 0) and (b27 or fmt[27] == 0):
            return mnem


def fp_type02_2(cxt: DecoderContext, fmt: FormatF):
    """ CEILF.{DL, DUL, DUW, DW, SL, SUL, SUW, SW} | CVTF.{SD, HS} | RSQRTF.{D,S} """
    # 11 27 4   0 20   16
    #  0  0 00010  10100   CEILF.DL
    #  0  0 10010  10100   CEILF.DUL
    #  0  w 10010  10000   CEILF.DUW
    #  0  w 00010  10000   CEILF.DW
    #  r  0 00010  00100   CEILF.SL
    #  r  0 10010  00100   CEILF.SUL
    #  r  w 10010  00000   CEILF.SUW
    #  r  w 00010  00000   CEILF.SW
    #  r  0 00010  10010   CVTF.SD
    #  0  0 00010  11110   RSQRTF.D
    #  r  w 00010  01110   RSQRTF.S
    #  r  w 00010  00010   CVTF.HS

    subop = fmt[19:17]
    if subop == 0 or subop == 2:
        # CEILF
        sel = fmt[4] << 2 | fmt[20] << 1 | fmt[18]
        mnem, b11, b27 = [(MNEM.CEILF_SW, True, True), (MNEM.CEILF_SL, True, False),
                          (MNEM.CEILF_DW, False, True), (MNEM.CEILF_DL, False, False),
                          (MNEM.CEILF_SUW, True, True), (MNEM.CEILF_SUL, True, False),
                          (MNEM.CEILF_DUW, False, True), (MNEM.CEILF_DUL, False, False)][sel]
        if (b11 or fmt[11] == 0) and (b27 or fmt[27] == 0):
            return mnem
    elif subop == 1:
        # CVTF
        if fmt[27] == 0 and fmt[4] == 0 and fmt[20] == 1:
            return MNEM.CVTF_SD
        elif fmt[4] == 0 and fmt[20] == 0:
            return MNEM.CVTF_HS
    elif subop == 7:
        mnem, b11, b27 = [(MNEM.RSQRTF_S, True, True), (MNEM.RSQRT_D, False, False)][fmt[20]]
        if fmt[4] == 0 and (b11 or fmt[11] == 0) and (b27 or fmt[27] == 0):
            return mnem


def fp_type02_3(cxt: DecoderContext, fmt: FormatF):
    """ CVTF.DS | FLOORF.{DL, DUL, DUW, DW, SL, SUL, SUW, SW} """
    # 11 27 4   0 20   16
    #  0  w 00011  10010   CVTF.DS
    #  0  0 00011  10100   FLOORF.DL
    #  0  0 10011  10100   FLOORF.DUL
    #  0  w 10011  10000   FLOORF.DUW
    #  0  w 00011  10000   FLOORF.DW
    #  r  0 00011  00100   FLOORF.SL
    #  r  0 10011  00100   FLOORF.SUL
    #  r  w 10011  00000   FLOORF.SUW
    #  r  w 00011  00000   FLOORF.SW
    #  r  w 00011  00010   CVTF.SH

    subop = fmt[19:17]
    if subop == 0 or subop == 2:
        # FLOORF
        sel = fmt[4] << 2 | fmt[20] << 1 | fmt[18]
        mnem, b11, b27 = [(MNEM.FLOORF_SW, True, True), (MNEM.FLOOR_SL, True, False),
                          (MNEM.FLOORF_DW, False, True), (MNEM.FLOORF_DL, False, False),
                          (MNEM.FLOORF_SUW, True, True), (MNEM.FLOOR_SUL, True, False),
                          (MNEM.FLOORF_DUW, False, True), (MNEM.FLOOR_DUL, False, False)][sel]
        if (b11 or fmt[11] == 0) and (b27 or fmt[27] == 0):
            return mnem
    elif subop == 1:
        # CVTF
        if fmt[11] == 0 and fmt[4] == 0 and fmt[20] == 1:
            return MNEM.CVTF_DS
        elif fmt[4] == 0 and fmt[20] == 0:
            return MNEM.CVTF_SH

def fp_type02_4(cxt: DecoderContext, fmt: FormatF):
    """ CVTF.{DL, DUL, DUW, DW, SL, SUL, SUW, SW} """
    # 11 27 4   0 20   16
    #  0  0 00100  10100   CVTF.DL
    #  0  0 10100  10100   CVTF.DUL
    #  0  w 10100  10000   CVTF.DUW
    #  0  w 00100  10000   CVTF.DW
    #  r  0 00100  00100   CVTF.SL
    #  r  0 10100  00100   CVTF.SUL
    #  r  w 10100  00000   CVTF.SUW
    #  r  w 00100  00000   CVTF.SW
    subop = fmt[19:17]
    if subop == 0 or subop == 2:
        # CVTF
        sel = fmt[4] << 2 | fmt[20] << 1 | fmt[18]
        mnem, b11, b27 = [(MNEM.CVTF_SW, True, True), (MNEM.CVTF_SL, True, False),
                          (MNEM.CVTF_DW, False, True), (MNEM.CVTF_DL, False, False),
                          (MNEM.CVTF_SUW, True, True), (MNEM.CVTF_SUL, True, False),
                          (MNEM.CVTF_DUW, False, True), (MNEM.CVTF_DUL, False, False)][sel]
        if (b11 or fmt[11] == 0) and (b27 or fmt[27] == 0):
            return mnem


def fp_type02(cxt: DecoderContext, fmt: FormatF):
    """  FP-mnem reg2, reg3 """
    operands = [Reg(fmt.reg2), Reg(fmt.reg3)]
    # 11 27 4   0 20   16
    #  0  0 00000  11000   ABSF_D
    #  r  w 00000  01000   ABSF_S
    #  0  0 00010  10100   CEILF.DL
    #  0  0 10010  10100   CEILF.DUL
    #  0  w 10010  10000   CEILF.DUW
    #  0  w 00010  10000   CEILF.DW
    #  r  0 00010  00100   CEILF.SL
    #  r  0 10010  00100   CEILF.SUL
    #  r  w 10010  00000   CEILF.SUW
    #  r  w 00010  00000   CEILF.SW

    #  0  0 00100  10100   CVTF.DL
    #  0  w 00011  10010   CVTF.DS
    #  0  0 10100  10100   CVTF.DUL
    #  0  w 10100  10000   CVTF.DUW
    #  0  w 00100  10000   CVTF.DW
    #  0  0 00001  10010   CVTF.LD
    #  0  w 00001  00010   CVTF.LS
    #  r  0 00010  10010   CVTF.SD
    #  r  0 00100  00100   CVTF.SL
    #  r  0 10100  00100   CVTF.SUL
    #  r  w 10100  00000   CVTF.SUW
    #  r  w 00100  00000   CVTF.SW
    #  0  0 10001  10010   CVTF.ULD
    #  0  w 10001  00010   CVTF.ULS
    #  r  w 10000  10010   CVTF.UWD
    #  r  w 10000  00010   CVTF.UWS
    #  r  0 00000  10010   CVTF.WD
    #  r  w 00000  00010   CVTF.WS

    #  0  0 00011  10100   FLOORF.DL
    #  0  0 10011  10100   FLOORF.DUL
    #  0  w 10011  10000   FLOORF.DUW
    #  0  w 00011  10000   FLOORF.DW
    #  r  0 00011  00100   FLOORF.SL
    #  r  0 10011  00100   FLOORF.SUL
    #  r  w 10011  00000   FLOORF.SUW
    #  r  w 00011  00000   FLOORF.SW

    #  0  0 00001  11000   NEGF.D
    #  r  w 00001  01000   NEGF.S

    #  0  0 00001  11110   RECIPF.D
    #  r  w 00001  01110   RECIPF.S

    #  0  0 00010  11110   RSQRTF.D
    #  r  w 00010  01110   RSQRTF.S

    #  0  0 00000  11110   SQRTF.D
    #  r  w 00000  01110   SQRTF.S

    #  0  0 00001  10100   TRNCF.DL
    #  0  0 10001  10100   TRNCF.DUL
    #  0  w 10001  10000   TRNCF.DUW
    #  0  w 00001  10000   TRNCF.DW
    #  r  0 00001  00100   TRNCF.SL
    #  r  0 10001  00100   TRNCF.SUL
    #  r  w 10001  00000   TRNCF.SUW
    #  r  w 00001  00000   TRNCF.SW

    #  r  w 00010  00010   CVTF.HS
    #  r  w 00011  00010   CVTF.SH

    subop = fmt[3:0]  # [4:0]?
    fp_type02_subtables = [
        fp_type02_0,
        fp_type02_1,
        fp_type02_2,
        fp_type02_3,
        fp_type02_4,
        None,
        None,
        None,
    ]
    tbl = fp_type02_subtables[subop]
    if tbl is not None:
        mnem = tbl(cxt, fmt)
        if mnem is not None:
            return mnem, operands, 2
    return MNEM.INVALID_CODE, [], 2


# mnem reg1, reg2, reg3
def fp_type03(cxt: DecoderContext, fmt: FormatF):
    operands = [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)]
    # 11  0 27 20   16
    #  0  0  0  10000  ADDF.D
    #  r  R  w  00000  ADDF.S
    #  0  0  0  11110  DIVF.D
    #  r  R  w  01110  DIVF.S
    #  0  0  0  11000  MAXF.D
    #  r  R  w  01000  MAXF.S
    #  0  0  0  11010  MINF.D
    #  r  R  w  01010  MINF.S
    #  0  0  0  10100  MULF.D
    #  r  R  w  00100  MULF.S
    #  0  0  0  10010  SUBF.D
    #  r  R  w  00010  SUBF.S
    subop = fmt[19:17]
    opname = ["ADD", "SUB", "MUL", None, "MAX", "MIN", None, "DIV"][subop]
    sd = ["S" , "D"][fmt[20]]
    if opname:
        mnem = MNEM["%sF_%s" %(opname, sd)]
        if fmt[20] == 0 or (fmt[11] == 0 and fmt[27] == 0 and fmt[0] == 0):
            return mnem, operands, 2
    return MNEM.INVALID_CODE, [], 2

fp_category0 = [
    fp_type00,
    fp_type01,
    fp_type02,
    fp_type03,
]


def fp_category1(cxt: DecoderContext, fmt: FormatF):
    """ FMAF.S | FMSF.S | FNMAF.S | FNMSF.S """
    if fmt.fp_type == 3 and fmt[20: 19] == 0:
        # F[N]M{A,S}F.S
        operands = [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3)]
        subop = fmt[18:17]
        mnem = [MNEM.FMAF_S, MNEM.FMSF_S, MNEM.FNMAF_S, MNEM.FNMSF_S][subop]
        return mnem, operands, 2
    return MNEM.INVALID_CODE, [], 2

def fp_category2_3(cxt:DecoderContext, fmt: FormatF):
    """ MADDF_S | MSUB_F | NMADDF_S | NMSUBF_S """
    reg4 = fmt.ext_lo5 | fmt[23]
    operands = [Reg(fmt.reg1), Reg(fmt.reg2), Reg(fmt.reg3), Reg(reg4)]
    subop = fmt[22:21]
    mnem = [MNEM.MADDF_S, MNEM.MSUBF_S, MNEM.NMADDF_S, MNEM.NMSUBF_S][subop]
    return mnem, operands, 2

fp_category2 = fp_category2_3
fp_category3 = fp_category2_3

fp_category4 = undef(2)
fp_category5 = undef(2)
fp_category6 = undef(2)
fp_category7 = undef(2)


fp_category = [
    fp_category0,
    fp_category1,
    fp_category2,  # MADDF.S, MSUBF.S, NMADDF.S NMADDF.S
    fp_category3,  # MADDF.S, MSUBF.S, NMADDF.S NMADDF.S
    fp_category4,
    fp_category5,
    fp_category6,
    fp_category7,
]


def decode_fp(cxt: DecoderContext, fmt: Format):
    fmt = FormatF(fmt)
    tbl = fp_category[fmt.category]
    if type(tbl) is list:
        tbl = tbl[fmt.fp_type]
        if type(tbl) is list:
            tbl = tbl[fmt.fp_subop]
    return tbl(cxt, fmt)


decode_table = [
    subtable0,
    subtable1,
    subtable2,
    subtable3,
    subtable4,
    subtable5,
    subtable6,
    subtable7,
    subtable8,
    subtable9,
    subtableA,
    subtableB,
    subtableC,
    subtableD,
    subtableE,
    subtableF
]


def decode(bs, subarch=Subarch.V850E2M, **kw):
    code = bs2int(bs)
    fmt = Format(code)
    cxt = DecoderContext(subarch=subarch, **kw)
    tbl = decode_table[fmt.opcode_hi]
    if type(tbl) is list:
        tbl = tbl[fmt.opcode_lo]
    mnem, operands, length = tbl(cxt, fmt)
    assert isinstance(mnem, MNEM), "%s" % mnem
    if not cxt.check_mnem(mnem):
        mnem = MNEM.INVALID_CODE
        operands = []
    return mnem, operands, length
