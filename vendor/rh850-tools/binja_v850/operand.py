from . import enums
from .visitor import Visitable


## Operand

class Operand(Visitable):
    class Visitor(Visitable.Visitor):
        pass

    def __repr__(self):
        return "%s<%s>" % (self.__class__.__name__, self)


class BitInt(object):
    __slots__ = ("val", "width", "fmt", "signed")

    def __init__(self, val, width=32, signed=True):
        mask = (1 << width) - 1
        val = val & mask
        if signed:
            if val & (1 << (width - 1)):
                val = val - mask - 1
        self.width = width
        self.val = val
        self.fmt = "%%0%dx" % ((self.width + 3) / 4)
        self.signed = signed

    def __str__(self):
        return self.fmt % self.val

    def __int__(self):
        return self.val

    def __eq__(self, op):
        return int(self) == int(op)

    def __add__(self, other):
        width = self.width
        if isinstance(other, BitInt) and other.width > width:
            width = other.width
        return type(self)(self.val + int(other), width=width, signed=self.signed)


class Imm(Operand, BitInt):
    def __str__(self):
        return "%08x" % int(self)


class EnumOperand(Operand):
    __slots__ = ("val",)
    enum_class = NotImplemented

    def __init__(self, val):
        self.val = self.enum_class(val)

    def __str__(self):
        return self.val.name

    def __int__(self):
        return int(self.val)

    def __eq__(self, op):
        return int(self) == int(op)


class Reg(EnumOperand):
    enum_class = enums.REG


class SReg(Operand):
    def __init__(self, reg_id: int):
        self.reg_id = reg_id

    def __int__(self):
        return self.reg_id

    def __str__(self):
        return "sr%d" % self.reg_id


class Cond(EnumOperand):
    enum_class = enums.COND


class FCond(EnumOperand):
    enum_class = enums.FCOND


class Addressing(Operand):
    pass


class JumpAddress(Addressing):
    pass


class RelJump(JumpAddress, BitInt):
    def __str__(self):
        return "PC%s%d" % ("+" if int(self) >= 0 else "", int(self))


class RegJump(JumpAddress, EnumOperand):
    enum_class = enums.REG

    def __str__(self):
        return "[%s]" % self.val.name


class Displacement(Operand):
    __slots__ = ("disp", "base")

    def __init__(self, disp, base=0, width=32, signed=True):
        self.base = enums.REG(base)
        disp = BitInt(disp, width=width, signed=signed)
        if self.base == enums.REG.R0:
            disp = BitInt(int(disp), width=32, signed=False)
        self.disp = disp

    def __str__(self):
        if self.disp:
            return "%d[%s]" % (int(self.disp), self.base.name)
        else:
            return "[%s]" % self.base.name

    def __eq__(self, other):
        return self.disp == other.disp22 and self.base == other.base


class BasedJump(JumpAddress, Displacement):
    pass


class VecJump(JumpAddress, BitInt):
    def __init__(self, val, width=8):
        super(VecJump, self).__init__(val, width=width, signed=False)


class MemoryAddress(Addressing):
    pass


class RegMem(MemoryAddress, EnumOperand):
    enum_class = enums.REG

    def __str__(self):
        return "[%s]" % self.val.name


class ImmMem(MemoryAddress, BitInt):
    pass


class BasedMem(MemoryAddress, Displacement):
    pass


class EpBasedMem(BasedMem):
    def __init__(self, disp, width=7, signed=False):
        super(BasedMem, self).__init__(disp, enums.REG.EP, width=width, signed=signed)


class BitMem(MemoryAddress, Displacement):
    __slots__ = ("index", "disp", "base")

    def __init__(self, index, disp, base, width=32, signed=True):
        super(BitMem, self).__init__(disp, base, width, signed)
        self.index = index

    def __str__(self):
        return "#%d, %d[%s]" % (self.index, int(self.disp), self.base.name)


class RegList(Operand):
    def __init__(self, reg_list):
        self.reg_list = reg_list

    def __str__(self):
        return "[%s]" % (", ".join(r.name for r in self.reg_list))

    def __iter__(self):
        return iter(self.reg_list)

    def __contains__(self, reg):
        return reg in self.reg_list


class RegPair(Operand):
    def __init__(self, reg_hi, reg_lo=None):
        if reg_lo is None:
            rh = int(reg_hi)
            if rh % 2 == 0:
                reg_hi = enums.REG(rh + 1)
                reg_lo = enums.REG(rh)
            else:
                assert rh > 0
                reg_hi = enums.REG(rh)
                reg_lo = enums.REG(rh - 1)
        # assert int(reg_hi) == int(reg_lo) + 1, "reg_hi, reg_lo=%s, %s" % (reg_hi, reg_lo)
        self._regpair = (reg_hi, reg_lo)

    def __iter__(self):
        return iter(self._regpair)

    @property
    def reg_hi(self):
        return self._regpair[0]

    @property
    def reg_lo(self):
        return self._regpair[0]

    def __str__(self):
        return "%s || %s" % (self.reg_hi.name, self.reg_lo.name)


class RegRange(Operand):
    def __init__(self, rh, rt):
        assert int(rt) >= int(rh)
        self.start = enums.REG(rt)
        self.stop = enums.REG(rh)

    def __str__(self):
        return "%s-%s" % (self.start.name, self.stop.name)


class CacheOp(EnumOperand):
    cacheop_map = {
        0x0: enums.CACHEOP.CHBII,
        0x20: enums.CACHEOP.CIBII,
        0x40: enums.CACHEOP.CFALI,
        0x60: enums.CACHEOP.CISTI,
        0x61: enums.CACHEOP.CILDI,
        0x7e: enums.CACHEOP.CLL,
    }

    def __init__(self, cacheop):
        super(CacheOp, self).__init__(self.cacheop_map.get(cacheop, enums.CACHEOP.INVALID))


def __bool__(self):
    return self.val != enums.CACHEOP.INVALID


class PrefOp(EnumOperand):
    prefop_map = {
        0x0: enums.PREFOP.PREFI
    }

    def __init__(self, prefop):
        super(PrefOp, self).__init__(self.prefop_map.get(prefop, enums.PREFOP.INVALID))

    def __str__(self):
        return "%s" % self.prefop.name

    def __bool__(self):
        return self.val != enums.PREFOP.INVALID
