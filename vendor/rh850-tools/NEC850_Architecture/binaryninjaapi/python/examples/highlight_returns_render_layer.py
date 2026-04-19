from typing import List, Optional

import binaryninja
from binaryninja import RenderLayer, InstructionTextToken, \
    InstructionTextTokenType, HighlightColor, ThemeColor
from binaryninjaui import getThemeColor


"""
Render Layer that highlights all lines in Linear View that have a return statement
"""


class HighlightReturnsLayer(RenderLayer):
    name = "Highlight Returns"

    # Highlighting in all ILs includes handling both normal blocks (up to MLIL) and HLIL bodies,
    # since HLIL is special and gets its own handler.
    def apply_to_high_level_il_body(
            self,
            function: 'binaryninja.Function',
            lines: List['binaryninja.LinearDisassemblyLine']
    ):
        ret_color = getThemeColor(ThemeColor.GraphExitNodeIndicatorColor)
        noret_color = getThemeColor(ThemeColor.GraphExitNoreturnNodeIndicatorColor)
        ret_highlight = HighlightColor(red=ret_color.red(), green=ret_color.green(), blue=ret_color.blue())
        noret_highlight = HighlightColor(red=noret_color.red(), green=noret_color.green(), blue=noret_color.blue())

        # Basic check: if the line has a keyword token which is "return" or "noreturn"
        for i, line in enumerate(lines):
            if any(token.type == InstructionTextTokenType.KeywordToken and token.text.startswith("return") for token in line.contents.tokens):
                line.contents.highlight = ret_highlight
            elif any(token.type == InstructionTextTokenType.KeywordToken and token.text == "noreturn" for token in line.contents.tokens):
                line.contents.highlight = noret_highlight
        return lines

    # Applies to MLIL and lower
    def apply_to_block(
            self,
            block: 'binaryninja.BasicBlock',
            lines: List['binaryninja.DisassemblyTextLine']
    ):
        ret_color = getThemeColor(ThemeColor.GraphExitNodeIndicatorColor)
        noret_color = getThemeColor(ThemeColor.GraphExitNoreturnNodeIndicatorColor)
        ret_highlight = HighlightColor(red=ret_color.red(), green=ret_color.green(), blue=ret_color.blue())
        noret_highlight = HighlightColor(red=noret_color.red(), green=noret_color.green(), blue=noret_color.blue())

        # Basic check: if the line has a keyword token which is "return" or "noreturn"
        for i, line in enumerate(lines):
            if any(token.type == InstructionTextTokenType.KeywordToken and token.text.startswith("return") for token in line.tokens):
                line.highlight = ret_highlight
            elif any(token.type == InstructionTextTokenType.KeywordToken and token.text == "noreturn" for token in line.tokens):
                line.highlight = noret_highlight
        return lines

    def apply_to_flow_graph(self, graph: 'binaryninja.FlowGraph'):
        # Ignore flow graphs, as this Render Layer should only apply to Linear View.
        pass


HighlightReturnsLayer.register()
