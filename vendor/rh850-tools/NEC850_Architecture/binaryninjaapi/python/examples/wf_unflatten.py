import json
from binaryninja import Workflow, Activity, AnalysisContext, MediumLevelILBasicBlock, \
    MediumLevelILInstruction, ReportCollection, FlowGraphReport, show_report_collection, \
    FlowGraph, DisassemblySettings
from binaryninja.mediumlevelil import *
from binaryninja.enums import *


"""
This workflow reverses the control-flow flattening algorithm of Limoncello[1],
at least some of the time. It does this in a relatively simple manner:

1. Find "dispatcher blocks" which contain a MLIL_JUMP_TO whose targets all have the 
   dispatcher as a post-dominator (ie all targets must flow back to the dispatcher)
2. Walk backwards from all unconditional branches into the dispatcher until finding blocks
   with conditional branches and build a list of all unconditional continuation blocks
   for each block that flows into the dispatcher.
3. Copy those continuation blocks and the dispatcher into each block that calls them.
   This leaves you with a copy of the dispatcher block (and intermediate bookkeeping) in
   every path that would have normally flowed into the dispatcher.
4. Since each path now has its own copy of the dispatcher, use MLIL dataflow to solve for
   which branch of the dispatcher is taken at each copy. When a dispatcher with a solved
   target is encountered, rewrite it as an MLIL_GOTO with the target directly.

[1] https://github.com/jonpalmisc/limoncello
"""


def is_dispatcher(block: MediumLevelILBasicBlock) -> bool:
    """
    Determine if a block looks like a CFF dispatcher, i.e. all outgoing edges
    post-dominate it (or return)

    :param block: The block to check
    :return: True if it's a dispatcher
    """
    for ins in block:
        ins: MediumLevelILInstruction
        if ins.operation == MediumLevelILOperation.MLIL_JUMP_TO:
            for edge in block.outgoing_edges:
                out_block = edge.target
                # This is too trivial for fancier cases with multiple blocks that all lead
                # to a return, but whatever this is just a sample plugin
                if len(out_block.outgoing_edges) == 0:
                    continue
                if block not in out_block.post_dominators:
                    return False

            return True
    return False


def graph_pls(fn: MediumLevelILFunction) -> FlowGraph:
    # For ReportCollection, create graph with the settings I want
    settings = DisassemblySettings()
    settings.set_option(DisassemblyOption.ShowAddress, True)
    return fn.create_graph_immediate(settings=settings)


def rewrite_action(context: AnalysisContext, do_it: bool):
    # Main workflow action

    # =====================================================================
    # Custom debug report

    report = None
    if context.function.check_for_debug_report("unflatten"):
        report = ReportCollection()

    try:
        if report is not None:
            init_graph = graph_pls(context.mlil)
            report.append(FlowGraphReport("Initial", init_graph, context.view))

        # =====================================================================
        # Finding flattened control flow and resolving continuations

        # Look for dispatcher block
        dispatcher = None
        for block in context.mlil.basic_blocks:
            if is_dispatcher(block):
                dispatcher = block
                break

        if dispatcher is None:
            return

        if report is not None:
            init_graph = graph_pls(context.mlil)
            for node_index, node in enumerate(init_graph.nodes):
                if node.basic_block.start == dispatcher.start:
                    node.highlight = HighlightStandardColor.RedHighlightColor
                init_graph.replace(node_index, node)
            report.append(FlowGraphReport("Finding Dispatcher", init_graph, context.view))

        # Find blocks that flow directly into the dispatcher
        queue = []
        to_copy = {}
        for incoming in dispatcher.incoming_edges:
            if dispatcher in incoming.source.dominators:
                to_copy[incoming.source] = [dispatcher]
                queue.append(incoming.source)

        # For each of these, walk back along unconditional branch edges to find their
        # list of continuation blocks which will be copied at their end
        while len(queue) > 0:
            # This is a sort of backwards BFS
            top = queue.pop(0)
            any_conditional = False
            for incoming in top.incoming_edges:
                if incoming.type != BranchType.UnconditionalBranch:
                    any_conditional = True
            # Having any conditional branches ends the unconditional chain
            if not any_conditional:
                for incoming in top.incoming_edges:
                    if incoming.type == BranchType.UnconditionalBranch:
                        if incoming.source not in to_copy:
                            queue.append(incoming.source)
                        to_copy[incoming.source] = [top] + to_copy[top]
                to_copy[top] = []

        # Ignore empty continuation paths
        for bb in list(to_copy.keys()):
            if len(to_copy[bb]) == 0:
                to_copy.pop(bb)

        if report is not None:
            for block, path in to_copy.items():
                init_graph = graph_pls(context.mlil)
                for node_index, node in enumerate(init_graph.nodes):
                    if node.basic_block.start in [bb.start for bb in path]:
                        node.highlight = HighlightStandardColor.RedHighlightColor
                    if node.basic_block.start == block.start:
                        node.highlight = HighlightStandardColor.GreenHighlightColor
                    init_graph.replace(node_index, node)
                report.append(FlowGraphReport("  Blocks flowing into", init_graph, context.view))

        # =====================================================================
        # Modify the IL to copy the continuations into all the blocks calling the dispatcher

        # Make a new IL function and append the modified instructions to it
        old_mlil = context.mlil
        new_mlil = MediumLevelILFunction(old_mlil.arch, low_level_il=context.llil)
        new_mlil.prepare_to_copy_function(old_mlil)
        block_map_starts = {}

        # Copy all instructions in all blocks of the old version of the function
        for block in old_mlil.basic_blocks:
            new_mlil.prepare_to_copy_block(block)
            block_map_starts[block] = len(new_mlil)

            new_mlil.set_current_address(old_mlil[InstructionIndex(block.start)].address, block.arch)

            for instr_index in range(block.start, block.end):
                old_instr: MediumLevelILInstruction = old_mlil[InstructionIndex(instr_index)]

                # Copy continuation blocks to end of block calling dispatcher
                if block in to_copy:
                    path = to_copy[block]

                    if instr_index == block.end - 1:
                        # For every block in the continuation, copy it at the end of this block
                        for copy_block in path:
                            new_mlil.prepare_to_copy_block(copy_block)

                            # Skip the final instruction in the continuations because it is a MLIL_GOTO
                            end = copy_block.end - 1
                            if copy_block == dispatcher:
                                end = copy_block.end

                            for copy_block_instr_index in range(copy_block.start, end):
                                # Copy instructions as-is
                                copy_block_instr: MediumLevelILInstruction = old_mlil[InstructionIndex(copy_block_instr_index)]
                                new_mlil.set_current_address(copy_block_instr.address, copy_block.arch)
                                new_mlil.append(copy_block_instr.copy_to(new_mlil), ILSourceLocation.from_instruction(copy_block_instr))
                        continue

                # Otherwise, copy the instruction as-is
                new_mlil.set_current_address(old_instr.address, block.arch)
                new_mlil.append(old_instr.copy_to(new_mlil), ILSourceLocation.from_instruction(old_instr))

        # Generate blocks and SSA (for dataflow) for the next part
        new_mlil.finalize()
        new_mlil.generate_ssa_form()

        # Since we're constructing a new function twice, we need to commit the mappings
        # of the intermediate function before copying again so that mappings will resolve
        # all the way to the end (gross)
        # TODO: Construct from another function without needing this
        context.mlil = new_mlil

        if report is not None:
            newer_graph = graph_pls(new_mlil)
            report.append(FlowGraphReport("Swapped dispatch with jump_to", newer_graph, context.view))

        # =====================================================================
        # Now convert all MLIL_JUMP_TO with known dest to a jump

        # Maybe this should be a separate workflow action (so it can be composed)
        old_mlil = new_mlil
        new_mlil = MediumLevelILFunction(old_mlil.arch, low_level_il=context.llil)
        new_mlil.prepare_to_copy_function(old_mlil)

        for old_block in old_mlil.basic_blocks:
            new_mlil.prepare_to_copy_block(old_block)

            for instr_index in range(old_block.start, old_block.end):
                old_instr: MediumLevelILInstruction = old_mlil[InstructionIndex(instr_index)]
                new_mlil.set_current_address(old_instr.address, old_block.arch)

                # If we find a MLIL_JUMP_TO with a known constant dest, then rewrite it
                # to a MLIL_GOTO with the known dest filled in
                if old_instr.operation == MediumLevelILOperation.MLIL_JUMP_TO:
                    if old_instr.dest.value.type == RegisterValueType.ConstantPointerValue:
                        dest_value = old_instr.dest.value.value
                        if dest_value in old_instr.targets:
                            old_target_index = old_instr.targets[dest_value]
                            new_mlil.append(new_mlil.goto(new_mlil.get_label_for_source_instruction(old_target_index), ILSourceLocation.from_instruction(old_instr)), ILSourceLocation.from_instruction(old_instr))
                            continue

                # Otherwise, copy the instruction as-is
                new_mlil.append(old_instr.copy_to(new_mlil), ILSourceLocation.from_instruction(old_instr))

        new_mlil.finalize()
        new_mlil.generate_ssa_form()

        if report is not None:
            newer_graph = graph_pls(new_mlil)
            report.append(FlowGraphReport("Resolved constant jump_to's", newer_graph, context.view))

        # =====================================================================
        # And we're done

        if do_it:
            context.mlil = new_mlil
    finally:
        # Show debug report if requested, even on exception thrown
        if report is not None:
            show_report_collection("Unflatten Debug Report", report)


# Create and register the workflow for translating these instructions
wf = Workflow("core.function.metaAnalysis").clone("core.function.metaAnalysis")

# Define the custom activity configuration
wf.register_activity(Activity(
    configuration=json.dumps({
        "name": "extension.unflatten_limoncello.unflatten.dry_run",
        "title": "Unflatten (Limoncello) Dry Run",
        "description": "Detect and reverse Limoncello's Control Flow Flattening scheme.",
        "eligibility": {
            "auto": {
                "default": False
            }
        }
    }),
    action=lambda context: rewrite_action(context, False)
))
wf.register_activity(Activity(
    configuration=json.dumps({
        "name": "extension.unflatten_limoncello.unflatten",
        "title": "Unflatten (Limoncello)",
        "description": "Detect and reverse Limoncello's Control Flow Flattening scheme.",
        "eligibility": {
            "auto": {
                "default": False
            }
        }
    }),
    action=lambda context: rewrite_action(context, True)
))

wf.insert_after("core.function.generateMediumLevelIL",[
    "extension.unflatten_limoncello.unflatten.dry_run",
    "extension.unflatten_limoncello.unflatten"
])
wf.register()
