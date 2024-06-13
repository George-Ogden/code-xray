from __future__ import annotations

import ast
import re
from typing import TypeAlias

from .utils import LineNumber

IndentIndex: TypeAlias = dict[LineNumber, int]


class IndentIndexBuilder:
    def __init__(self, source: str):
        self.original_source_lines = source.splitlines()
        self.original_tree = ast.parse(source)
        modified_source = ast.unparse(self.original_tree)
        self.modified_source_lines = modified_source.splitlines()
        self.modified_source_lines.append("")
        self.modified_tree = ast.parse(modified_source)

        self.index: IndentIndex = {}

    def visit(self, original_node: ast.AST, modified_node: ast.AST):
        """Visit a node to update the index based on the node's position."""
        # Handle special cases.
        self.detect_hidden_block(original_node, modified_node, "orelse", "el(se|if)")
        self.detect_hidden_block(original_node, modified_node, "finalbody", "finally")

        # Deal with line number on current node.
        try:
            original_line_number = LineNumber[1](original_node.lineno)
            modified_line_number = LineNumber[1](modified_node.lineno)
        except AttributeError:
            ...
        else:
            self.index[original_line_number] = max(
                self.count_spaces(modified_line_number), self.count_spaces(modified_line_number + 1)
            )

        # Iterate over the fields for the current node.
        for original_child, modified_child in zip(
            ast.iter_child_nodes(original_node), ast.iter_child_nodes(modified_node)
        ):
            self.visit(original_child, modified_child)

    def detect_hidden_block(
        self, original_node: ast.AST, modified_node: ast.AST, key: str, prefix: str
    ):
        """
        Add a line to the index that is not allocated its own node in an AST.
        Currently, that appears as "else" in if/try/for/while and final in try.
        """
        if hasattr(original_node, key) and len(getattr(original_node, key)) > 0:
            original_block = getattr(original_node, key)[0]
            modified_block = getattr(modified_node, key)[0]

            original_line_number = LineNumber[1](original_block.lineno)
            modified_line_number = LineNumber[1](modified_block.lineno)
            pattern = rf"^ *{prefix}"
            spaces = self.count_spaces(modified_line_number)

            if re.match(pattern, self.original_source_lines[original_line_number.zero]):
                self.index[original_line_number] = spaces
            elif re.match(pattern, self.original_source_lines[(original_line_number - 1).zero]):
                self.index[original_line_number - 1] = spaces
            else:
                raise SyntaxError(f"Block `{key}` not found in the original source code.")

    def count_spaces(self, line_number: LineNumber) -> int:
        """Count the number of spaces at the start of the line in modified source."""
        line = self.modified_source_lines[line_number.zero]
        space = re.match(r"^ *", line).group(0)
        return len(space)

    @classmethod
    def build_index(cls, source: str):
        """Build the index from line numbers to source numbers."""
        builder = IndentIndexBuilder(source)
        builder.visit(builder.original_tree, builder.modified_tree)
        return builder.index
