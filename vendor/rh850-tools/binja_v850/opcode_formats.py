from .enums import *


def bitfield(hi, lo=0, ret_type=int):
    assert hi >= lo >= 0
    bits = hi - lo + 1
    mask = (1 << bits) - 1

    def getter(self):
        return ret_type((int(self) >> lo) & mask)

    def mk(meth):
        prop = property(fget=getter, doc=getattr(meth, "__doc__", None))
        return prop

    return mk


def list12(l12: int):
    reg_list = map(REG, [30, 31, 29, 28, 23, 22, 21, 20, 27, 26, 25, 24])
    l = []
    for i, r in enumerate(reg_list):
        if l12 & (1 << i):
            l.append(r)
    l.sort()
    return l


class Format(int):
    def __getitem__(self, key):
        if isinstance(key, slice):
            assert key.step is None
            hi = key.start
            lo = 0 if key.stop is None else key.stop
        elif isinstance(key, int):
            hi = key
            lo = key
        else:
            raise IndexError(key)

        assert hi >= lo >= 0
        bits = hi - lo + 1
        mask = (1 << bits) - 1
        return (int(self) >> lo) & mask

    @bitfield(hi=15, lo=11)
    def hi5(self):
        pass

    @bitfield(hi=4, lo=0)
    def lo5(self):
        pass

    @bitfield(hi=10, lo=7)
    def opcode_hi(self):
        """the upper 4 bit of opcode"""
        pass

    @bitfield(hi=6, lo=5)
    def opcode_lo(self):
        """lower part of opcode"""
        pass

    opcode_lo_width = 2

    @property
    def opcode(self):
        return self.opcode_hi << self.opcode_lo_width | self.opcode_lo

    @bitfield(hi=26, lo=26, ret_type=bool)
    def is_fp(self):
        pass

    @bitfield(hi=25, lo=23)
    def ext_opcode_hi(self):
        pass

    @bitfield(hi=22, lo=21)
    def ext_opcode_lo(self):
        pass

    @property
    def ext_opcode(self):
        return self.ext_opcode_hi << 2 | self.ext_opcode_lo

    @bitfield(hi=31, lo=27)
    def ext_hi5(self):
        pass

    @bitfield(hi=20, lo=16)
    def ext_lo5(self):
        pass

    @bitfield(hi=4, lo=4)
    def bit4(self):
        pass

    @bitfield(hi=16, lo=16)
    def bit16(self):
        pass


class FormatI(Format):
    @bitfield(hi=4, lo=0, ret_type=REG)
    def reg1(self):
        pass

    @bitfield(hi=15, lo=11, ret_type=REG)
    def reg2(self):
        pass


class FormatII(Format):
    @bitfield(hi=4, lo=0, ret_type=REG)
    def imm(self):
        pass

    @bitfield(hi=15, lo=11, ret_type=REG)
    def reg2(self):
        pass


class FormatIII(Format):
    @bitfield(hi=3, lo=0, ret_type=COND)
    def cond(self):
        pass

    @bitfield(hi=6, lo=4)
    def _disp_lo(self):
        pass

    @bitfield(hi=15, lo=11)
    def _disp_hi(self):
        pass

    @property
    def disp9(self):
        return (self._disp_hi << 4) | (self._disp_lo << 1)


class FormatIV7(Format):
    @bitfield(hi=15, lo=11, ret_type=REG)
    def reg2(self):
        pass

    @bitfield(hi=6, lo=1)
    def disp6(self):
        pass

    @bitfield(hi=0, lo=0)
    def sub_opcode(self):
        pass

    @bitfield(hi=6, lo=0)
    def disp7(self):
        pass


class FormatIV4(Format):
    @bitfield(hi=15, lo=11, ret_type=REG)
    def reg2(self):
        pass

    @bitfield(hi=6, lo=4)
    def opcode_lo(self):
        pass

    opcode_lo_width = 3

    @bitfield(hi=3, lo=0)
    def disp(self):
        pass


class FormatV(Format):
    @bitfield(hi=15, lo=11, ret_type=REG)
    def reg2(self):
        pass

    @bitfield(hi=6, lo=6)
    def opcode_lo(self):
        pass

    opcode_lo_width = 1

    @bitfield(hi=5, lo=0)
    def _disp_hi(self):
        pass

    @bitfield(hi=31, lo=16)
    def _disp_lo(self):
        pass

    @property
    def disp22(self):
        return self._disp_hi << 16 | self._disp_lo


class FormatVI(FormatI):
    @bitfield(hi=31, lo=16)
    def _imm_lo(self):
        pass

    @bitfield(hi=47, lo=32)
    def _imm_hi(self):
        pass

    @property
    def imm16(self):
        return self._imm_lo

    @property
    def imm32(self):
        return self._imm_hi << 16 | self._imm_lo


class FormatVII(FormatI):
    @bitfield(hi=32, lo=17)
    def disp15(self):
        pass

    @bitfield(hi=16, lo=16)
    def sub_opcode(self):
        pass

    @bitfield(hi=32, lo=16)
    def disp16(self):
        pass


class FormatVIII(Format):
    @bitfield(hi=15, lo=14)
    def sub_opcode(self):
        pass

    @bitfield(hi=13, lo=11)
    def bit(self):
        pass

    @bitfield(hi=4, lo=0, ret_type=REG)
    def reg1(self):
        pass

    @bitfield(hi=31, lo=16)
    def disp16(self):
        pass


class FormatIX(FormatI):
    @bitfield(hi=31, lo=17)
    def sub_opcode(self):
        pass


class FormatX(Format):
    @bitfield(hi=31, lo=17)
    def sub_opcode(self):
        pass


class FormatXI(FormatI):
    @bitfield(hi=31, lo=27, ret_type=REG)
    def reg3(self):
        pass

    @bitfield(hi=26, lo=17)
    def sub_opcode(self):
        pass


class FormatXII(Format):
    @bitfield(hi=15, lo=11, ret_type=REG)
    def reg2(self):
        pass

    @bitfield(hi=31, lo=27, ret_type=REG)
    def reg3(self):
        pass

    @bitfield(hi=31, lo=17)
    def sub_opcode(self):
        pass

    @bitfield(hi=22, lo=18)
    def _imm_hi(self):
        pass

    @property
    def imm10(self):
        return self._imm_hi << 5 | self.lo5


class FormatXIII(Format):
    @bitfield(hi=4, lo=1)
    def imm5(self):
        pass

    @bitfield(hi=0, lo=0)
    def _list12_0(self):
        pass

    @bitfield(hi=31, lo=21)
    def _list12(self):
        pass

    @property
    def reg_list(self):
        return list12(self._list12 << 1 | self._list12_0)

    @bitfield(hi=20, lo=16, ret_type=REG)
    def reg2(self):
        pass

    @bitfield(hi=47, lo=32)
    def _imm16_lo(self):
        pass

    @bitfield(hi=63, lo=48)
    def _imm16_hi(self):
        pass

    @property
    def imm16(self):
        return self._imm16_lo

    @property
    def imm32(self):
        return self._imm16_hi << 16 | self._imm16_lo


class FormatXIV(Format):
    @bitfield(hi=4, lo=0, ret_type=REG)
    def reg1(self):
        pass

    @bitfield(hi=31, lo=27, ret_type=REG)
    def reg3(self):
        pass

    @bitfield(hi=19, lo=16)
    def sub_opcode(self):
        pass

    @bitfield(hi=26, lo=20)
    def _disp_lo(self):
        pass

    @bitfield(hi=47, lo=32)
    def _disp_hi(self):
        pass

    @property
    def disp23(self):
        return self._disp_hi << 7 | self._disp_lo


class FormatF(Format):
    @bitfield(hi=4, lo=0, ret_type=REG)
    def reg1(self):
        pass

    @bitfield(hi=20, lo=16, ret_type=REG)
    def reg2(self):
        pass

    @bitfield(hi=31, lo=27, ret_type=REG)
    def reg3(self):
        pass

    @bitfield(hi=25, lo=23)
    def category(self):
        pass

    @bitfield(hi=22, lo=21)
    def fp_type(self):
        pass

    @bitfield(hi=20, lo=17)
    def fp_subop(self):
        pass
