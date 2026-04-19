import functools
import json
import math

from binaryninja import Workflow, Activity, AnalysisContext, ReportCollection, \
    FlowGraphReport, show_report_collection, DisassemblySettings, DisassemblyOption
from binaryninja.lowlevelil import *
from binaryninja.mediumlevelil import *

"""
This workflow copies every instruction in an IL function to a new IL function and then
verifies that they are exactly the same.
"""


def assert_llil_eq(old_insn: LowLevelILInstruction, new_insn: LowLevelILInstruction):
    """
    Make sure that these two instructions are the same (probably correct). Asserts otherwise.

    Note: This ignores when instructions reference other instructions by index directly
    as that IL indices are not guaranteed to be consistent. So things like goto/if/jump_to
    will check that the target of the branch is the same, but allow the target to have
    a different instruction index.
    """
    err_msg = (hex(old_insn.address), old_insn, new_insn)
    assert old_insn.operation == new_insn.operation, err_msg
    # assert old_insn.attributes == new_insn.attributes, err_msg
    assert old_insn.size == new_insn.size, err_msg
    assert old_insn.raw_flags == new_insn.raw_flags, err_msg
    assert old_insn.source_location == new_insn.source_location, err_msg
    assert len(old_insn.operands) == len(new_insn.operands), err_msg
    # Can't compare operands directly since IL expression indices might change when
    # copying an instruction to another function
    for i, (old_op, new_op) in enumerate(zip(old_insn.detailed_operands, new_insn.detailed_operands)):
        err_msg = (hex(old_insn.address), f'op {i}', old_insn, new_insn, old_op, new_op)
        assert old_op[0] == new_op[0], err_msg  # op name
        assert old_op[2] == new_op[2], err_msg  # op type

        op_type = old_op[2]
        if op_type == 'LowLevelILInstruction':
            assert_llil_eq(old_op[1], new_op[1])
        elif op_type == 'InstructionIndex' or \
                (old_insn.operation == LowLevelILOperation.LLIL_GOTO and old_op[0] == 'dest') or \
                (old_insn.operation == LowLevelILOperation.LLIL_IF and old_op[0] == 'true') or \
                (old_insn.operation == LowLevelILOperation.LLIL_IF and old_op[0] == 'false'):
            # These aren't consistent if the old function has instructions outside BBs
            # (they are not copied), so just make sure the target instruction looks the same
            assert old_insn.function[old_op[1]].operation == new_insn.function[new_op[1]].operation
        elif op_type in [
            'List[LowLevelILInstruction]',
            'List[\'LowLevelILInstruction\']'  # compat (ew)
        ]:
            for old_sub, new_sub in zip(old_op[1], new_op[1]):
                assert_llil_eq(old_sub, new_sub)
        elif op_type == 'float':
            if math.isnan(old_op[1]) and math.isnan(new_op[1]):
                # both nan so they will compare not equal
                pass
            else:
                assert old_op[1] == new_op[1], err_msg
        elif old_insn.operation == LowLevelILOperation.LLIL_JUMP_TO and old_op[0] == 'targets':
            for old_target, new_target in zip(sorted(old_op[1].items()), sorted(new_op[1].items())):
                assert old_target[0] == new_target[0], err_msg
                # Same as with instruction index
                assert_llil_eq(old_insn.function[old_target[1]], new_insn.function[new_target[1]])
        else:
            # TODO: Any other types of ops need special behavior?
            assert old_op[1] == new_op[1], err_msg


@functools.lru_cache(maxsize=8)
def get_mlil_maps(mlil: MediumLevelILFunction, builders: bool) -> Tuple[LLILSSAToMLILInstructionMapping, LLILSSAToMLILExpressionMapping]:
    instr_map = mlil._get_llil_ssa_to_mlil_instr_map(builders)
    expr_map = mlil._get_llil_ssa_to_mlil_expr_map(builders)
    return instr_map, expr_map


def assert_mlil_eq(old_insn: MediumLevelILInstruction, new_insn: MediumLevelILInstruction):
    """
    Make sure that these two instructions are the same (probably correct). Asserts otherwise.

    Note: This ignores when instructions reference other instructions by index directly
    as that IL indices are not guaranteed to be consistent. So things like goto/if/jump_to
    will check that the target of the branch is the same, but allow the target to have
    a different instruction index.
    """
    err_msg = (hex(old_insn.address), old_insn, new_insn)
    assert old_insn.operation == new_insn.operation, err_msg
    assert old_insn.attributes == new_insn.attributes, err_msg
    assert old_insn.size == new_insn.size, err_msg
    assert old_insn.source_location == new_insn.source_location, err_msg
    assert len(old_insn.operands) == len(new_insn.operands), err_msg
    # Type only applies once we've generated SSA form (probably not consistent)
    # assert old_insn.expr_type == new_insn.expr_type, f"{err_msg} {old_insn.expr_type} {new_insn.expr_type}"

    instr_map, expr_map = get_mlil_maps(new_insn.function, True)

    # Compare that the instruction's LLIL SSA map is the same as the old function
    if old_insn.instr_index is not None and old_insn.function.get_expr_index_for_instruction(old_insn.instr_index) == old_insn.expr_index:
        old_llil_ssa = old_insn.function.get_low_level_il_instruction_index(old_insn.instr_index)
        if old_llil_ssa is not None:
            assert [mlil for (llil, mlil) in instr_map.items() if llil == old_llil_ssa] == [new_insn.instr_index], err_msg
        else:
            assert [mlil for (llil, mlil) in instr_map.items() if llil == old_llil_ssa] == [], err_msg

    # Can't compare operands directly since IL expression indices might change when
    # copying an instruction to another function
    for i, (old_op, new_op) in enumerate(zip(old_insn.detailed_operands, new_insn.detailed_operands)):
        err_msg = (hex(old_insn.address), f'op {i}', old_insn, new_insn, old_op, new_op)
        assert old_op[0] == new_op[0], err_msg  # op name
        assert old_op[2] == new_op[2], err_msg  # op type

        op_type = old_op[2]
        if op_type == 'MediumLevelILInstruction':
            assert_mlil_eq(old_op[1], new_op[1])
        elif op_type == 'InstructionIndex' or \
                (old_insn.operation == MediumLevelILOperation.MLIL_GOTO and old_op[0] == 'dest') or \
                (old_insn.operation == MediumLevelILOperation.MLIL_IF and old_op[0] == 'true') or \
                (old_insn.operation == MediumLevelILOperation.MLIL_IF and old_op[0] == 'false'):
            # These aren't consistent if the old function has instructions outside BBs
            # (they are not copied), so just make sure the target instruction looks the same
            assert old_insn.function[old_op[1]].operation == new_insn.function[new_op[1]].operation
        elif op_type == 'List[MediumLevelILInstruction]':
            for old_sub, new_sub in zip(old_op[1], new_op[1]):
                assert_mlil_eq(old_sub, new_sub)
        elif op_type == 'float':
            if math.isnan(old_op[1]) and math.isnan(new_op[1]):
                # both nan so they will compare not equal
                pass
            else:
                assert old_op[1] == new_op[1], err_msg
        elif op_type == 'Variable':
            assert old_op[1].core_variable == new_op[1].core_variable, err_msg
        elif op_type == 'List[Variable]':
            for old_sub, new_sub in zip(old_op[1], new_op[1]):
                err_msg = (hex(old_insn.address), f'op {i}', old_insn, new_insn, old_op, new_op, old_sub, new_sub)
                assert old_sub.core_variable == new_sub.core_variable, err_msg
        elif op_type == 'SSAVariable':
            assert old_op[1].var.core_variable == new_op[1].var.core_variable, err_msg
            assert old_op[1].version == new_op[1].version, err_msg
        elif old_insn.operation == MediumLevelILOperation.MLIL_JUMP_TO and old_op[0] == 'targets':
            for old_target, new_target in zip(sorted(old_op[1].items()), sorted(new_op[1].items())):
                err_msg = (hex(old_insn.address), f'op {i}', old_insn, new_insn, old_op, new_op, old_target, new_target)
                assert old_target[0] == new_target[0], err_msg
                # Same as with instruction index
                assert_mlil_eq(old_insn.function[old_target[1]], new_insn.function[new_target[1]])
        else:
            # TODO: Any other types of ops need special behavior?
            assert old_op[1] == new_op[1], err_msg


def lil_action(context: AnalysisContext):
    def translate_instr(
            new_func: LowLevelILFunction,
            old_block: LowLevelILBasicBlock,
            old_instr: LowLevelILInstruction,
    ):
        # no-op copy
        return old_instr.copy_to(
            new_func,
            lambda sub_instr: translate_instr(new_func, old_block, sub_instr)
        )

    old_lil = context.lifted_il
    if old_lil is None:
        return
    new_lil = old_lil.translate(translate_instr)
    new_lil.finalize()

    if context.function.check_for_debug_report("copy_expr_test_lil"):
        # debug the test :)
        report = ReportCollection()
        settings = DisassemblySettings()
        settings.set_option(DisassemblyOption.ShowAddress, True)
        report.append(FlowGraphReport("old graph", old_lil.create_graph_immediate(settings)))
        report.append(FlowGraphReport("new graph", new_lil.create_graph_immediate(settings)))
        show_report_collection("copy expr test", report)

    # Check all BBs have all the same instructions
    # Technically, this misses any instructions outside a BB, but those are not
    # picked up by analysis anyway, and therefore don't matter.
    assert len(old_lil.basic_blocks) == len(new_lil.basic_blocks)
    for old_bb, new_bb in zip(old_lil.basic_blocks, new_lil.basic_blocks):
        assert len(old_bb) == len(new_bb)
        for old_insn, new_insn in zip(old_bb, new_bb):
            assert_llil_eq(old_insn, new_insn)


def llil_action(context: AnalysisContext):
    def translate_instr(
            new_func: LowLevelILFunction,
            old_block: LowLevelILBasicBlock,
            old_instr: LowLevelILInstruction,
    ):
        # no-op copy
        return old_instr.copy_to(
            new_func,
            lambda sub_instr: translate_instr(new_func, old_block, sub_instr)
        )

    old_llil = context.llil
    if old_llil is None:
        return
    new_llil = old_llil.translate(translate_instr)
    new_llil.finalize()
    new_llil.generate_ssa_form()

    if context.function.check_for_debug_report("copy_expr_test_llil"):
        # debug the test :)
        report = ReportCollection()
        settings = DisassemblySettings()
        settings.set_option(DisassemblyOption.ShowAddress, True)
        report.append(FlowGraphReport("old graph", old_llil.create_graph_immediate(settings)))
        report.append(FlowGraphReport("new graph", new_llil.create_graph_immediate(settings)))
        show_report_collection("copy expr test", report)

    # Check all BBs have all the same instructions
    # Technically, this misses any instructions outside a BB, but those are not
    # picked up by analysis anyway, and therefore don't matter.
    assert len(old_llil.basic_blocks) == len(new_llil.basic_blocks)
    for old_bb, new_bb in zip(old_llil.basic_blocks, new_llil.basic_blocks):
        assert len(old_bb) == len(new_bb)
        for old_insn, new_insn in zip(old_bb, new_bb):
            assert_llil_eq(old_insn, new_insn)


def mlil_action(context: AnalysisContext):
    def translate_instr(
            new_func: MediumLevelILFunction,
            old_block: MediumLevelILBasicBlock,
            old_instr: MediumLevelILInstruction,
    ):
        # no-op copy
        return old_instr.copy_to(
            new_func,
            lambda sub_instr: translate_instr(new_func, old_block, sub_instr)
        )

    old_mlil = context.mlil
    if old_mlil is None:
        return
    new_mlil = old_mlil.translate(translate_instr)
    new_mlil.finalize()
    new_mlil.generate_ssa_form()

    if context.function.check_for_debug_report("copy_expr_test_mlil"):
        # debug the test :)
        report = ReportCollection()
        settings = DisassemblySettings()
        settings.set_option(DisassemblyOption.ShowAddress, True)
        report.append(FlowGraphReport("old graph", old_mlil.create_graph_immediate(settings)))
        report.append(FlowGraphReport("new graph", new_mlil.create_graph_immediate(settings)))
        show_report_collection("copy expr test", report)

    # Check expr mappings are the same
    new_map = list(sorted(new_mlil._get_llil_ssa_to_mlil_expr_map(True), key=lambda o: (o.lower_index, o.higher_index)))
    old_map = list(sorted(old_mlil._get_llil_ssa_to_mlil_expr_map(False), key=lambda o: (o.lower_index, o.higher_index)))
    assert old_map == new_map

    # Check all BBs have all the same instructions
    # Technically, this misses any instructions outside a BB, but those are not
    # picked up by analysis anyway, and therefore don't matter.
    assert len(old_mlil.basic_blocks) == len(new_mlil.basic_blocks)
    for old_bb, new_bb in zip(old_mlil.basic_blocks, new_mlil.basic_blocks):
        assert len(old_bb) == len(new_bb)
        for old_insn, new_insn in zip(old_bb, new_bb):
            assert_mlil_eq(old_insn, new_insn)

    # Make sure mappings update correctly following set
    new_map = list(sorted(new_mlil._get_llil_ssa_to_mlil_expr_map(True), key=lambda o: (o.lower_index, o.higher_index)))
    context.mlil = new_mlil
    newer_map = list(sorted(context.mlil._get_llil_ssa_to_mlil_expr_map(False), key=lambda o: (o.lower_index, o.higher_index)))
    assert new_map == newer_map


wf = Workflow("core.function.metaAnalysis").clone("core.function.metaAnalysis")

# Define the custom activity configuration
wf.register_activity(Activity(
    configuration=json.dumps({
        "name": "extension.test_copy_expr.lil_action",
        "title": "Lifted IL copy_expr Test",
        "description": "Makes sure copy_expr works on Lifted IL functions.",
        "eligibility": {
            "auto": {
                "default": False
            }
        }
    }),
    action=lil_action
))
wf.register_activity(Activity(
    configuration=json.dumps({
        "name": "extension.test_copy_expr.llil_action",
        "title": "Low Level IL copy_expr Test",
        "description": "Makes sure copy_expr works on Low Level IL functions.",
        "eligibility": {
            "auto": {
                "default": False
            }
        }
    }),
    action=llil_action
))
wf.register_activity(Activity(
    configuration=json.dumps({
        "name": "extension.test_copy_expr.mlil_action",
        "title": "Medium Level IL copy_expr Test",
        "description": "Makes sure copy_expr works on Medium Level IL functions.",
        "eligibility": {
            "auto": {
                "default": False
            }
        }
    }),
    action=mlil_action
))
wf.insert("core.function.analyzeAndExpandFlags", ["extension.test_copy_expr.lil_action"])
wf.insert("core.function.generateMediumLevelIL", ["extension.test_copy_expr.llil_action"])
wf.insert("core.function.generateHighLevelIL", ["extension.test_copy_expr.mlil_action"])
# TODO: MLIL and higher
wf.register()
