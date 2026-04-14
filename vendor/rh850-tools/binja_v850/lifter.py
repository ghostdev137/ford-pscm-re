import binaryninja as bn
from .enums import MNEM, REG, COND, Subarch, SREG_V850, SREG_V850ES, SREG_V850E2M, SREG_RH850
from .operand import Operand, RegJump, Reg, RegPair, RegList


def reg(r, il: bn.LowLevelILFunction):
    return il.reg(4, r.name.lower())


class OperandGet(Operand.Visitor):
    def __init__(self, addr):
        self.addr = addr

    def visit_Reg(self, op, il: bn.LowLevelILFunction, size=4):
        if op.val == REG.R0:
            return il.const(size, 0)
        r = reg(op.val, il)
        if size < 4:
            r = il.low_part(size, r)
        return r

    def visit_Imm(self, op, il: bn.LowLevelILFunction, size=4):
        return il.const(size, int(op))

    def visit_RegMem(self, op, il: bn.LowLevelILFunction, size=4):
        base = reg(op.val, il)
        return il.load(size, base)

    def visit_Displacement(self, op, il: bn.LowLevelILFunction, size=4):
        base = reg(op.base, il)
        disp = il.const(4, int(op.disp))
        return il.load(size, il.add(4, base, disp))


class OperandDest(Operand.Visitor):
    def __init__(self, addr):
        self.addr = addr

    def visit_Operand(self, op, il: bn.LowLevelILFunction, length, size=4):
        pass

    def visit_RelJump(self, op, il: bn.LowLevelILFunction, length, size=4):
        return il.const(4, self.addr + int(op))

    def visit_RegJump(self, op, il: bn.LowLevelILFunction, length, size=4):
        assert size == 4
        if op.val == REG.R0:
            return il.const(size, 0)
        return reg(op.val, il)

    def visit_BasedJump(self, op, il: bn.LowLevelILFunction, length, size=4):
        assert size == 4
        if op.base == REG.R0:
            return il.const(size, int(op.disp))
        else:
            return il.add(4, reg(op.base, il), il.const(4, int(op.disp)))


class OperandSet(Operand.Visitor):
    def __init__(self, addr):
        self.addr = addr

    def visit_Operand(self, op, il: bn.LowLevelILFunction, val, size=4):
        pass

    def visit_Reg(self, op, il: bn.LowLevelILFunction, val, size=4):
        if op.val != REG.R0:
            ex = il.set_reg(size, op.val.name.lower(), val)
        else:
            assert size == 4
            ex = val
        il.append(ex)
        return il

    def visit_RegPair(self, op: RegPair, il: bn.LowLevelILFunction, val, size=8):
        ex = il.set_reg_split(size, op.reg_hi.name.lower(), op.reg_lo.name.lower(), val)
        il.append(ex)
        return il

    def visit_Displacement(self, op, il: bn.LowLevelILFunction, val, size=4):
        base = reg(op.base, il)
        disp = il.const(4, int(op.disp))
        addr = il.add(4, base, disp)
        ex = il.store(size, addr, val)
        il.append(ex)
        return il


class SysRegLifterBase(object):
    def get_sysreg(self, rID, bsel=None):
        pass

    def ldsr(self, val, sreg, il):
        pass

    def stsr(self, sreg, reg, il):
        pass


class LifterBase(object):
    def __init__(self, arch=None):
        if arch is None:
            arch = bn.Architecture["v850"]
        self.arch = arch

    def ldsr(self, val, sreg, il):
        pass

    def stsr(self, sreg, reg, il):
        pass

    def process_instruction(self, mnem: MNEM, operands, length: int, addr: int, il: bn.LowLevelILFunction):
        name = mnem.name.split("_")[0]
        meth = getattr(self, "lift_" + name, self.lift_Default)
        return meth(mnem, operands, length, addr, il)

    def lift_Default(self, mnem: MNEM, operands, length: int, addr: int, il: bn.LowLevelILFunction):
        il.append(il.unimplemented())


def il_if_then(il: bn.LowLevelILFunction, cond, then_):
    t = bn.LowLevelILLabel()
    e = bn.LowLevelILLabel()
    il.append(il.if_expr(cond, t, e))
    il.mark_label(t)
    then_(il)
    il.append(il.goto(e))
    il.mark_label(e)


def il_if_then_else(il: bn.LowLevelILFunction, cond, then_, else_):
    t = bn.LowLevelILLabel()
    f = bn.LowLevelILLabel()
    e = bn.LowLevelILLabel()
    il.append(il.if_expr(cond, t, f))
    il.mark_label(t)
    then_(il)
    il.append(il.goto(e))
    il.mark_label(f)
    else_(il)
    il.append(il.goto(e))
    il.mark_label(e)


class V850Lifter(LifterBase):
    sysreg = SREG_V850

    def get_sysreg(self, rID, ldsr=False):
        if ldsr and rID == 4:
            return None
        try:
            return self.sysreg(rID)
        except ValueError:
            pass

    def ldsr(self, reg, regid, il):
        sr = self.get_sysreg(regid, ldsr=True)
        if sr and regid != 4:
            ex = il.set_reg(4, sr.name.lower(), reg)
            il.append(ex)

    def stsr(self, regid, reg, il):
        sr = self.get_sysreg(regid)
        if sr:
            ex = il.set_reg(4, reg, il.reg(4, sr.name.lower()))
            il.append(ex)

    def lift_ADD(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val0 = src.accept(getter, il, size=4)
        val1 = dst.accept(getter, il, size=4)
        exp = il.add(4, val0, val1, flags="nosat")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_ADDI(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src0, src1, dst = operands
        getter = OperandGet(addr)
        val0 = src0.accept(getter, il, size=4)
        val1 = src1.accept(getter, il, size=4)
        exp = il.add(4, val0, val1, flags="nosat")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_AND(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val0 = src.accept(getter, il, size=4)
        val1 = dst.accept(getter, il, size=4)
        exp = il.and_expr(4, val0, val1, flags="zsov")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_ANDI(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src0, src1, dst = operands
        getter = OperandGet(addr)
        val0 = src0.accept(getter, il, size=4)
        val1 = src1.accept(getter, il, size=4)
        exp = il.and_expr(4, val0, val1, flags="zsov")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    cond_il = {
        COND.V: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_O),
        COND.L: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_ULT),
        COND.Z: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_E),
        COND.NH: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_ULE),
        COND.N: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_NEG),
        COND.LT: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_SLT),
        COND.LE: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_SLE),
        COND.NV: lambda il: il.not_expr(0, il.flag_condition(bn.LowLevelILFlagCondition.LLFC_O)),
        COND.NL: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_UGE),
        COND.NZ: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_NE),
        COND.H: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_UGT),
        COND.P: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_POS),
        COND.SA: lambda il: il.flag("sat"),
        COND.GE: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_SGE),
        COND.GT: lambda il: il.flag_condition(bn.LowLevelILFlagCondition.LLFC_SGT),
    }
    def lift_B(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        cond, disp = operands
        dest = addr + int(disp)
        tgt = il.get_label_for_address(self.arch, dest)
        flt = il.get_label_for_address(self.arch, addr + length * 2)
        if cond.val == COND.R:
            if tgt:
                ex = il.goto(tgt)
            else:
                ex = il.jump(il.const_pointer(4, dest))
            il.append(ex)
        else:
            c = self.cond_il[cond.val](il)
            if tgt:
                t = tgt
            else:
                t = bn.LowLevelILLabel()
            if flt:
                f = flt
            else:
                f = bn.LowLevelILLabel()
            ex = il.if_expr(c, t, f)
            il.append(ex)
            if not tgt:
                il.mark_label(t)
                ex = il.jump(il.const_pointer(4, dest))
                il.append(ex)
            if not flt:
                il.mark_label(f)

    def bit1op(self, mnem, operands, length, addr, il: bn.LowLevelILFunction, binop):
        getter = OperandGet(addr)
        setter = OperandSet(addr)
        dst = operands[-1]
        b = dst.accept(getter, il, size=1)
        # assert hasattr(dst, "index"), (b,type(dst))
        if len(operands) == 1:
            index = il.const(1, int(dst.index))
        else:
            r = operands[0].accept(getter, il, size=1)
            index = il.and_expr(1, r, il.const(1, 0x7))
        sht = il.shift_left(1, il.const(1, 1), index)
        z = il.compare_equal(1, il.and_expr(1, b, sht), il.const(1, 0))
        il.append(il.set_flag("z", z))
        if binop is not None:
            val = binop(b, sht, il)
            dst.accept(setter, il, val, size=1)

    def lift_CLR1(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        def clr1(old_b, sht, il: bn.LowLevelILFunction):
            return il.and_expr(1, old_b, il.neg_expr(1, sht))

        return self.bit1op(mnem, operands, length, addr, il, clr1)

    def lift_CMP(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val0 = src.accept(getter, il, size=4)
        val1 = dst.accept(getter, il, size=4)
        exp = il.sub(4, val1, val0, flags="nosat")
        il.append(exp)

    def lift_DISPOSE(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        imm, list12 = operands[:2]
        # list12 : RegList
        ret = None
        if len(operands) == 3:
            ret = operands[2]
        il.append(il.set_reg(4, "sp", il.add(4, il.reg(4, "sp"), il.const(4, int(imm)))))
        for r in reversed(list12.reg_list):
            il.append(il.set_reg(4, r.name.lower(), il.pop(4)))

        if ret:
            r = reg(ret.val, il)
            if ret.val == REG.LP:
                il.append(il.ret(r))
            else:
                il.append(il.jump(r))

    def lift_JARL(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        dst, ret = operands
        setter = OperandSet(addr)
        destvis = OperandDest(addr)
        dest = dst.accept(destvis, il, length)
        ret.accept(setter, il, il.const(4, addr + length * 2))
        if ret.val == REG.LP:
            ex = il.call(dest)
        else:
            ex = il.jump(dest)
        il.append(ex)

    def lift_JMP(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        dst, = operands
        destvis = OperandDest(addr)
        dest = dst.accept(destvis, il, length)
        assert dest is not None, dst
        if isinstance(dst, RegJump) and dst.val == REG.LP:
            ex = il.ret(dest)
        else:
            ex = il.jump(dest)
        il.append(ex)

    def lift_JR(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        dst, = operands
        destvis = OperandDest(addr)
        dest = dst.accept(destvis, il, length)
        ex = il.jump(dest)
        il.append(ex)

    def lift_LD(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        post = mnem.name.split("_")[1]
        size, signed = {
            "B": (1, True),
            "BU": (1, False),
            "H": (2, True),
            "HU": (2, False),
            "W": (4, True),
        }[post]
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=size)
        if size < 4:
            if signed:
                val = il.sign_extend(4, val)
            else:
                val = il.zero_extend(4, val)
        setter = OperandSet(addr)
        dst.accept(setter, il, val, 4)

    def lift_LDSR(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        reg, sreg = operands
        reg = il.reg(4, reg.val.name.lower())
        self.ldsr(reg, int(sreg), il)

    def lift_MOV(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        setter = OperandSet(addr)
        dst.accept(setter, il, val, size=4)

    def lift_MOVEA(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        imm, src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        setter = OperandSet(addr)
        dst.accept(setter, il, il.add(4, val, il.const(4, int(imm))), size=4)

    def lift_MOVHI(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        imm, src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        setter = OperandSet(addr)
        dst.accept(setter, il, il.add(4, val, il.const(4, int(imm) << 16)), size=4)

    def lift_MUL(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src0, src1, dst = operands
        assert isinstance(src1, Reg) and isinstance(dst, Reg)
        tgt = RegPair(dst.val, src1.val)
        getter = OperandGet(addr)
        setter = OperandSet(addr)
        val0 = src0.accept(getter, il, size=4)
        val1 = src1.accept(getter, il, size=4)
        tgt.accept(setter, il, il.mult(8, val0, val1), size=8)

    def lift_MULH(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        setter = OperandSet(addr)
        val0 = src.accept(getter, il, size=2)
        val1 = dst.accept(getter, il, size=2)
        dst.accept(setter, il, il.mult(4, val0, val1), size=4)

    def lift_MULHI(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        imm, src, dst = operands
        getter = OperandGet(addr)
        setter = OperandSet(addr)
        val0 = imm.accept(getter, il, size=2)
        val1 = src.accept(getter, il, size=2)
        dst.accept(setter, il, il.mult(4, val0, val1), size=4)

    lift_MULU = lift_MUL

    def lift_NOP(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        pass

    def lift_NOT(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        exp = il.not_expr(4, val, flags="zsov")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_NOT1(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        def not1(old_b, sht, il: bn.LowLevelILFunction):
            i = il.and_expr(1, old_b, sht)
            xi = il.neg_expr(1, il.xor_expr(1, i, i))
            return il.or_expr(1, old_b, xi)

        return self.bit1op(mnem, operands, length, addr, il, not1)

    def lift_OR(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val0 = src.accept(getter, il, size=4)
        val1 = dst.accept(getter, il, size=4)
        exp = il.or_expr(4, val0, val1, flags="zsov")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_ORI(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src0, src1, dst = operands
        getter = OperandGet(addr)
        val0 = src0.accept(getter, il, size=4)
        val1 = src1.accept(getter, il, size=4)
        exp = il.or_expr(4, val0, val1, flags="zsov")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_PREPARE(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        list12, imm = operands[:2]
        ep = None
        if len(operands) == 3:
            ep = operands[2]
        for r in list12:
            il.append(il.push(4, reg(r, il)))
        il.append(il.set_reg(4, "sp", il.sub(4, il.reg(4, "sp"), il.const(4, int(imm)))))
        if ep:
            getter = OperandGet(addr)
            val = ep.accept(getter, il, size=4)
            il.append(il.set_reg(4, "ep", val))

    def lift_SAR(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        sft, src = operands[:2]
        if len(operands) == 3:
            dst = operands[2]
        else:
            dst = src
        getter = OperandGet(addr)
        val0 = sft.accept(getter, il, size=4)
        val1 = src.accept(getter, il, size=4)

        if isinstance(sft, Reg):
            val0 = il.and_expr(4, val0, il.const(4, 0x1f))
        exp = il.arith_shift_right(4, val1, val0, flags="nosat")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_SET1(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        def set1(old_b, sht, il: bn.LowLevelILFunction):
            return il.or_expr(1, old_b, sht)

        return self.bit1op(mnem, operands, length, addr, il, set1)

    def lift_SETF(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        cccc, reg = operands
        c = self.cond_il[cccc.val](il)
        setter = OperandSet(addr)
        def t(il):
            reg.accept(setter, il, il.const(4,1))
        def f(il):
            reg.accept(setter, il, il.const(4, 0))
        il_if_then_else(il, c, t, f)

    def lift_SHL(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        sft, src = operands[:2]
        if len(operands) == 3:
            dst = operands[2]
        else:
            dst = src
        getter = OperandGet(addr)
        val0 = sft.accept(getter, il, size=4)
        val1 = src.accept(getter, il, size=4)

        if isinstance(sft, Reg):
            val0 = il.and_expr(4, val0, il.const(4, 0x1f))
        exp = il.shift_left(4, val1, val0, flags="nosat")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_SHR(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        sft, src = operands[:2]
        if len(operands) == 3:
            dst = operands[2]
        else:
            dst = src
        getter = OperandGet(addr)
        val0 = sft.accept(getter, il, size=4)
        val1 = src.accept(getter, il, size=4)

        if isinstance(sft, Reg):
            val0 = il.and_expr(4, val0, il.const(4, 0x1f))
        exp = il.logical_shift_right(4, val1, val0, flags="nosat")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    lift_SLD = lift_LD

    def lift_ST(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        post = mnem.name.split("_")[1]
        size, signed = {
            "B": (1, True),
            "BU": (1, False),
            "H": (2, True),
            "HU": (2, False),
            "W": (4, True),
        }[post]
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=size)
        setter = OperandSet(addr)
        dst.accept(setter, il, val, size)

    lift_SST = lift_ST

    def lift_SUB(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val0 = src.accept(getter, il, size=4)
        val1 = dst.accept(getter, il, size=4)
        exp = il.sub(4, val1, val0, flags="nosat")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_STSR(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        sreg, reg = operands
        reg = reg.val.name.lower()
        self.stsr(int(sreg), reg, il)

    def lift_SUBR(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val0 = src.accept(getter, il, size=4)
        val1 = dst.accept(getter, il, size=4)
        exp = il.sub(4, val0, val1, flags="nosat")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_SWITCH(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        r = operands[0]
        assert isinstance(r, Reg)
        r = reg(r.val, il)
        npc = il.const(4, addr + length * 2)
        adr = il.add(4, npc, il.shift_left(4, r, il.const(4, 1)))
        tbl = il.shift_left(4, il.sign_extend(4, il.load(2, adr)), il.const(4, 1))
        dest = il.add(4, npc, tbl)
        il.append(il.jump(dest))

    def lift_SXB(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        dst = operands[0]
        getter = OperandGet(addr)
        setter = OperandSet(addr)
        val = dst.accept(getter, il, size=1)
        dst.accept(setter, il, il.sign_extend(4, val), size=4)

    def lift_SXH(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        dst = operands[0]
        getter = OperandGet(addr)
        setter = OperandSet(addr)
        val = dst.accept(getter, il, size=2)
        dst.accept(setter, il, il.sign_extend(4, val), size=4)

    def lift_TRAP(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        vec = operands[0]
        il.append(il.trap(int(vec)))

    def lift_TST(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val0 = src.accept(getter, il, size=4)
        val1 = dst.accept(getter, il, size=4)
        exp = il.and_expr(4, val0, val1, flags="zsov")
        il.append(exp)

    def lift_TST1(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        return self.bit1op(mnem, operands, length, addr, il, None)

    def lift_XOR(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val0 = src.accept(getter, il, size=4)
        val1 = dst.accept(getter, il, size=4)
        exp = il.xor_expr(4, val0, val1, flags="zsov")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_XORI(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src0, src1, dst = operands
        getter = OperandGet(addr)
        val0 = src0.accept(getter, il, size=4)
        val1 = src1.accept(getter, il, size=4)
        exp = il.xor_expr(4, val0, val1, flags="zsov")
        setter = OperandSet(addr)
        dst.accept(setter, il, exp, size=4)

    def lift_ZXB(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        dst = operands[0]
        getter = OperandGet(addr)
        setter = OperandSet(addr)
        val = dst.accept(getter, il, size=1)
        dst.accept(setter, il, il.zero_extend(4, val), size=4)

    def lift_ZXH(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        dst = operands[0]
        getter = OperandGet(addr)
        setter = OperandSet(addr)
        val = dst.accept(getter, il, size=2)
        dst.accept(setter, il, il.zero_extend(4, val), size=4)


class V850ESLifter(V850Lifter):
    sysreg = SREG_V850ES

    def get_sysreg(self, rID, ldsr=False):
        if ldsr and rID in [4, 21]:
            return None
        try:
            return self.sysreg(rID)
        except ValueError:
            pass

    def lift_BSH(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        ex = il.intrinsic([il.reg(4, dst.val.name.lower())], "bsh", [val])
        il.append(ex)

    def lift_BSW(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        ex = il.intrinsic([il.reg(4, dst.val.name.lower())], "bsw", [val])
        il.append(ex)

    def lift_CALLT(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        imm = operands[0]
        # ctpc <- PC + 2
        e = il.set_reg(4, "ctpc", il.const_pointer(4, addr + length * 2))
        il.append(e)
        # ctpsw <- PSW
        e = il.set_reg(4, "ctpsw", il.reg(4, "psw"))
        il.append(e)
        # adr <- ctbp + imm << 1
        adr = il.add(4, il.reg(4, "ctbp"), il.const(4, int(imm) << 1))
        ld = il.load(2, adr)
        e = il.jump(il.add(4, il.reg(4, "ctbp"), il.zero_extend(4, ld)))
        il.append(e)

    def lift_CMOV(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        cccc, op1, reg2, reg3 = operands
        getter = OperandGet(addr)
        setter = OperandSet(addr)
        c = self.cond_il[cccc.val](il)
        il_if_then_else(il, c, lambda il: reg3.accept(setter, il, op1.accept(getter, il, size=4),size=4)
                        , lambda il: reg3.accept(setter, il, reg2.accept(getter, il, size=4), size=4))

    def lift_CTRET(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        e = il.set_reg(4, "psw", il.reg(4, "ctpsw"))
        il.append(e)
        e = il.ret(il.reg(4, "ctpc"))
        il.append(e)

    def lift_HSW(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        ex = il.intrinsic([il.reg(4, dst.val.name.lower())], "hsw", [val])
        il.append(ex)


class V850E2Lifter(V850ESLifter):
    sysreg = SREG_V850E2M

    def ldsr(self, val, rid, il: bn.LowLevelILFunction):
        if 28 <= rid < 32:
            sr = self.sysreg(rid)
            ex = il.set_reg(4, sr.name.lower(), val)
            il.append(ex)
        else:
            bsel = il.reg(4, "bsel")
            ex = il.intrinsic([], "ldsr", [val, il.const(1, rid), bsel])
            il.append(ex)

    def stsr(self, rid, reg, il: bn.LowLevelILFunction):
        if 28 <= rid < 32:
            sr = self.sysreg(rid)
            ex = il.set_reg(4, reg, il.reg(4, sr.name.lower()))
            il.append(ex)
        else:
            bsel = il.reg(4, "bsel")
            ex = il.intrinsic([il.reg(4, reg)], "stsr", [il.const(1, rid), bsel])
            il.append(ex)

    def lift_HSW(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        ex = il.set_reg(4, dst.val.name.lower(), val)  # should set flags
        il.append(ex)

    def lift_RIE(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        il.set_reg(4, bn.RegisterName("fepc"), il.const(4, addr + 4))
        il.set_reg(4, bn.RegisterName("fepsw"), il.reg(4, bn.RegisterName("psw")))
        il.append(il.jump(il.const(4, 0x30)))

    def lift_SCH0L(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        ex = il.intrinsic([il.reg(4, dst.val.name.lower())], "sch0l", [val])
        il.append(ex)

    def lift_SCH0R(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        ex = il.intrinsic([il.reg(4, dst.val.name.lower())], "sch0r", [val])
        il.append(ex)

    def lift_SCH1L(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        ex = il.intrinsic([il.reg(4, dst.val.name.lower())], "sch1l", [val])
        il.append(ex)

    def lift_SCH1R(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        src, dst = operands
        getter = OperandGet(addr)
        val = src.accept(getter, il, size=4)
        ex = il.intrinsic([il.reg(4, dst.val.name.lower())], "sch1r", [val])
        il.append(ex)


class RH850Lifter(V850E2Lifter):
    sysreg = SREG_V850

    def lift_LDSR(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        reg, sreg = operands[:2]
        rID = int(sreg)
        if len(operands) == 3:
            sel = int(operands[2])
        else:
            sel = 0
        reg = il.reg(4, reg.val.name.lower())
        try:
            sr = self.sysreg(sel << 8 | rID)
            if sr != SREG_RH850.BSEL:
                il.append(il.set_reg(4, sr.name.lower(), reg))
        except ValueError:
            ex = il.intrinsic([], "ldsr", [reg, il.const(1, rID), sel])
            il.append(ex)

    def lift_STSR(self, mnem, operands, length, addr, il: bn.LowLevelILFunction):
        sreg, reg = operands
        rID = int(sreg)
        if len(operands) == 3:
            sel = int(operands[2])
        else:
            sel = 0
        reg = reg.val.name.lower()
        try:
            sr = self.sysreg(sel << 8 | rID)
            if sr == SREG_RH850.BSEL:
                sr = il.const(4, 0)
            else:
                sr = il.reg(4, sr.name.lower())
            il.append(il.set_reg(4, reg, sr))
        except ValueError:
            ex = il.intrinsic([il.reg(4, reg)], "stsr", [il.const(1, rID), sel])
            il.append(ex)


def choose_lifter(subarch: Subarch):
    if subarch.value < subarch.V850ES.value:
        return V850Lifter
    elif subarch.value < subarch.V850E2.value:
        return V850ESLifter
    elif subarch.value < subarch.RH850.value:
        return V850E2Lifter
