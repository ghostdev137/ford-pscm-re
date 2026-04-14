from typing import Optional, Tuple, List

import binaryninja as bn

from .opcode_table import decode
from .enums import MNEM, REG, SREG_V850, SREG_V850E2M, SREG_V850ES, SREG_RH850, USER_FLAG, COND, Subarch
from .operand import *
from .lifter import choose_lifter, V850Lifter


class OperandToText(Operand.Visitor):
    def __init__(self, addr):
        self.addr = addr

    def visit_Operand(self, op):
        return [bn.InstructionTextToken(bn.InstructionTextTokenType.TextToken, "%s<%s>" % (type(op).__name__, op))]

    def visit_EnumOperand(self, op):
        return [bn.InstructionTextToken(bn.InstructionTextTokenType.RegisterToken, "%s" % (op.val.name.lower()))]

    def visit_Imm(self, op):
        return [bn.InstructionTextToken(bn.InstructionTextTokenType.IntegerToken, op.fmt % int(op))]

    def visit_RelJump(self, op):
        return [
            bn.InstructionTextToken(bn.InstructionTextTokenType.PossibleAddressToken, "%.8x" % (int(op + self.addr)))]

    def visit_RegJump(self, op):
        return [bn.InstructionTextToken(bn.InstructionTextTokenType.BeginMemoryOperandToken, "["),
                bn.InstructionTextToken(bn.InstructionTextTokenType.RegisterToken, "%s" % op.val.name.lower()),
                bn.InstructionTextToken(bn.InstructionTextTokenType.EndMemoryOperandToken, "]"),
                ]

    def visit_VecJump(self, op):
        return [bn.InstructionTextToken(bn.InstructionTextTokenType.TextToken, "vector:"),
                bn.InstructionTextToken(bn.InstructionTextTokenType.IntegerToken, "%d" % int(op)),
                ]

    def visit_RegMem(self, op):
        return [bn.InstructionTextToken(bn.InstructionTextTokenType.BeginMemoryOperandToken, "["),
                bn.InstructionTextToken(bn.InstructionTextTokenType.RegisterToken, "%s" % op.val.name.lower()),
                bn.InstructionTextToken(bn.InstructionTextTokenType.EndMemoryOperandToken, "]"),
                ]

    def visit_Displacement(self, op):
        if op.base == REG.R0:
            token_type = bn.InstructionTextTokenType.PossibleAddressToken
        else:
            token_type = bn.InstructionTextTokenType.IntegerToken
        ret = []
        if op.base == REG.R0 or int(op.disp) != 0:
            ret += [bn.InstructionTextToken(token_type, op.disp.fmt % int(op.disp))]
        if op.base != REG.R0:
            ret += [bn.InstructionTextToken(bn.InstructionTextTokenType.BeginMemoryOperandToken, "["),
                    bn.InstructionTextToken(bn.InstructionTextTokenType.RegisterToken, "%s" % op.base.name.lower()),
                    bn.InstructionTextToken(bn.InstructionTextTokenType.OperandSeparatorToken, "]")]
        return ret

    def visit_BitMem(self, op):
        ret = [bn.InstructionTextToken(bn.InstructionTextTokenType.IntegerToken, "#%d" % op.index),
               bn.InstructionTextToken(bn.InstructionTextTokenType.OperandSeparatorToken, ", ")]
        ret += self.visit_Displacement(op)
        return ret

    def visit_RegList(self, op):
        ret = [bn.InstructionTextToken(bn.InstructionTextTokenType.TextToken, "[")]
        first = True
        for reg in op:
            if not first:
                ret.append(bn.InstructionTextToken(bn.InstructionTextTokenType.TextToken, ", "))
            else:
                first = False
            ret.append(bn.InstructionTextToken(bn.InstructionTextTokenType.RegisterToken, "%s" % reg.name.lower()))
        ret.append(bn.InstructionTextToken(bn.InstructionTextTokenType.TextToken, "]"))
        return ret

    def visit_RegPair(self, op, addr):
        return [bn.InstructionTextToken(bn.InstructionTextTokenType.RegisterToken, op.reg_hi),
                bn.InstructionTextToken(bn.InstructionTextTokenType.OperandSeparatorToken, " || "),
                bn.InstructionTextToken(bn.InstructionTextTokenType.RegisterToken, op.reg_lo),
                ]

    def visit_RegRange(self, op, addr):
        return [bn.InstructionTextToken(bn.InstructionTextTokenType.RegisterToken, op.reg_hi),
                bn.InstructionTextToken(bn.InstructionTextTokenType.OperandSeparatorToken, "-"),
                bn.InstructionTextToken(bn.InstructionTextTokenType.RegisterToken, op.reg_lo)
                ]


v850_gpregs = {
    "r%d" % i: bn.RegisterInfo("r%d" % i, 4) for i in range(32)
}
v850_gpregs.update(dict(sp=bn.RegisterInfo("r3", 4),
                        gp=bn.RegisterInfo("r4", 4),
                        tp=bn.RegisterInfo("r5", 4),
                        ep=bn.RegisterInfo("r30", 4),
                        lp=bn.RegisterInfo("r31", 4),
                        pc=bn.RegisterInfo("pc", 4),
                        ))

v850_regs = dict(v850_gpregs)
v850_regs.update(
    {sr.name.lower(): bn.RegisterInfo(sr.name.lower(), 4) for sr in SREG_V850}
)


class V850Architecture(bn.Architecture):
    name = 'v850'
    address_size = 4
    default_int_size = 4
    instr_alignment = 2
    max_instr_length = 8
    stack_pointer = "sp"
    link_reg = "lp"
    regs = v850_regs
    flags = ["z", "s", "ov", "cy", "sat"]
    flag_write_types = ["zsov", "nosat", "*"]
    flags_written_by_flag_write_type = {
        "zsov": ["z", "s", "ov"],
        "nosat": ["z", "s", "ov", "cy"],
        "*": ["z", "s", "ov", "cy", "sat"]
    }
    flag_roles = {
        "z": bn.FlagRole.ZeroFlagRole,
        "s": bn.FlagRole.NegativeSignFlagRole,
        "ov": bn.FlagRole.OverflowFlagRole,
        "cy": bn.FlagRole.CarryFlagRole,
        "sat": bn.FlagRole.SpecialFlagRole
    }
    flags_required_for_flag_condition = {
        bn.LowLevelILFlagCondition.LLFC_SGE: ["s", "ov"],
        bn.LowLevelILFlagCondition.LLFC_SGT: ["z", "s", "ov"],
        bn.LowLevelILFlagCondition.LLFC_SLE: ["z", "s", "ov"],
        bn.LowLevelILFlagCondition.LLFC_SLT: ["s", "ov"],
        bn.LowLevelILFlagCondition.LLFC_UGT: ["z", "cy"],
        bn.LowLevelILFlagCondition.LLFC_ULT: ["cy"],
        bn.LowLevelILFlagCondition.LLFC_ULE: ["z", "cy"],
        bn.LowLevelILFlagCondition.LLFC_UGE: ["cy"],
        bn.LowLevelILFlagCondition.LLFC_E: ["z"],
        bn.LowLevelILFlagCondition.LLFC_NE: ["z"],
        bn.LowLevelILFlagCondition.LLFC_NEG: ["s"],
        bn.LowLevelILFlagCondition.LLFC_O: ["ov"],
    }

    def get_instruction_info(self, data: bytes, addr: int) -> Optional[bn.InstructionInfo]:
        subarch = Subarch[self.name.upper()]
        mnem, operands, length = decode(data, subarch=subarch)
        if mnem == MNEM.INVALID_CODE or mnem == MNEM.UNDEF_CODE:
            return None
        info = bn.InstructionInfo()
        info.length = length * 2
        if mnem == MNEM.JMP:
            op = operands[0]
            if isinstance(op, RegJump):
                if op.val == REG.R0:
                    info.add_branch(bn.BranchType.UnconditionalBranch, 0)
                elif op.val == REG.LP:
                    info.add_branch(bn.BranchType.FunctionReturn)
                else:
                    info.add_branch(bn.BranchType.UnresolvedBranch)
            elif isinstance(op, BasedJump):
                if op.base == REG.R0:
                    info.add_branch(bn.BranchType.UnconditionalBranch, int(op.disp))
                else:
                    info.add_branch(bn.BranchType.UnresolvedBranch)
        elif mnem == MNEM.JR:
            op = operands[0]
            if isinstance(op, RelJump):
                info.add_branch(bn.BranchType.UnconditionalBranch, addr + int(op))
        elif mnem == MNEM.JARL:
            op = operands[0]
            if isinstance(op, RelJump):
                if operands[1].val == REG.LP:
                    info.add_branch(bn.BranchType.CallDestination, addr + int(op))
                else:
                    info.add_branch(bn.BranchType.UnconditionalBranch, addr + int(op))
        elif mnem == MNEM.B:
            op = operands[1]
            if isinstance(op, RelJump):
                info.add_branch(bn.BranchType.TrueBranch, addr + int(op))
                if operands[0].val != COND.R:
                    info.add_branch(bn.BranchType.FalseBranch, addr + length * 2)
        elif mnem == MNEM.SWITCH:
            info.add_branch(bn.BranchType.UserDefinedBranch)
        elif mnem == MNEM.CALLT:
            info.add_branch(bn.BranchType.UserDefinedBranch)
        elif mnem == MNEM.SYSCALL:
            info.add_branch(bn.BranchType.SystemCall)
        elif mnem in [MNEM.DBTRAP, MNEM.TRAP, MNEM.FETRAP, MNEM.RIE, MNEM.HALT]:
            info.add_branch(bn.BranchType.ExceptionBranch)
        elif mnem in [MNEM.RETI, MNEM.DBRET, MNEM.FERET, MNEM.EIRET, MNEM.CTRET]:
            info.add_branch(bn.BranchType.FunctionReturn)
        elif mnem == MNEM.DISPOSE:
            if len(operands) == 3:
                if operands[2].val == REG.LP:
                    info.add_branch(bn.BranchType.FunctionReturn)
                else:
                    info.add_branch(bn.BranchType.UnresolvedBranch)
        return info

    def get_instruction_text(self, data: bytes, addr: int) -> Tuple[List['bn.function.InstructionTextToken'], int]:
        subarch = Subarch[self.name.upper()]
        mnem, operands, length = decode(data, subarch=subarch)
        mnemonic = mnem.name.replace("_", ".").lower()
        if mnemonic == "b":
            cond = operands.pop(0)
            mnemonic += cond.val.name.lower()
        ret = [bn.InstructionTextToken(bn.InstructionTextTokenType.InstructionToken, "%s " % mnemonic)]
        first = True
        vis = OperandToText(addr)
        for op in operands:
            if first:
                first = False
            else:
                ret.append(bn.InstructionTextToken(bn.InstructionTextTokenType.OperandSeparatorToken, ", "))
            ret += op.accept(vis)
        return ret, length * 2

    def get_instruction_low_level_il(self, data: bytes, addr: int, il: 'bn.lowlevelil.LowLevelILFunction') -> int:
        subarch = Subarch[self.name.upper()]
        mnem, operands, length = decode(data, subarch=subarch)
        if mnem == MNEM.INVALID_CODE or mnem == MNEM.UNDEF_CODE:
            return None
        lifter = choose_lifter(subarch)(self)
        if not lifter.process_instruction(mnem, operands, length, addr, il):
            return length * 2


v850es_regs = dict(v850_gpregs)
v850es_regs.update(
    {sr.name.lower(): bn.RegisterInfo(sr.name.lower(), 4) for sr in SREG_V850ES}
)

v850es_intrinsics = {
    'bsh': bn.IntrinsicInfo([bn.IntrinsicInput(bn.Type.int(4), "src")], [bn.Type.int(4)]),
    'bsw': bn.IntrinsicInfo([bn.IntrinsicInput(bn.Type.int(4), "src")], [bn.Type.int(4)]),
    'hsw': bn.IntrinsicInfo([bn.IntrinsicInput(bn.Type.int(4), "src")], [bn.Type.int(4)])
}


class V850ESArchitecture(V850Architecture):
    name = 'v850es'
    regs = v850es_regs
    intrinsics = v850es_intrinsics


v850e2_regs = dict(v850_gpregs)
v850e2_regs.update(
    {sr.name.lower(): bn.RegisterInfo(sr.name.lower(), 4) for sr in SREG_V850E2M}
)

v850e2m_intrinsics = dict(v850es_intrinsics)
v850e2m_intrinsics.update(
    {
        'sch0l': bn.IntrinsicInfo([bn.IntrinsicInput(bn.Type.int(4), "src")], [bn.Type.int(4)]),
        'sch0r': bn.IntrinsicInfo([bn.IntrinsicInput(bn.Type.int(4), "src")], [bn.Type.int(4)]),
        'sch1l': bn.IntrinsicInfo([bn.IntrinsicInput(bn.Type.int(4), "src")], [bn.Type.int(4)]),
        'sch1r': bn.IntrinsicInfo([bn.IntrinsicInput(bn.Type.int(4), "src")], [bn.Type.int(4)]),
        'ldsr': bn.IntrinsicInfo([bn.IntrinsicInput(bn.Type.int(4), "reg"), bn.IntrinsicInput(bn.Type.int(1), "regID"),
                                  bn.IntrinsicInput(bn.Type.int(4), "bsel")], []),
        'stsr': bn.IntrinsicInfo([bn.IntrinsicInput(bn.Type.int(1), "regID"),
                                  bn.IntrinsicInput(bn.Type.int(4), "bsel")], [bn.Type.int(4)]),
    }
)


class V850E2MArchitecture(V850Architecture):
    name = 'v850e2m'
    regs = v850e2_regs
    intrinsics = v850e2m_intrinsics


rh850_regs = dict(v850_gpregs)
rh850_regs.update(
    {sr.name.lower(): bn.RegisterInfo(sr.name.lower(), 4) for sr in SREG_RH850}
)


class RH850Architecture(V850E2MArchitecture):
    name = 'rh850'
    regs = rh850_regs
