from __future__ import annotations

import ast
import re
from typing import TypeAlias

from .utils import LineNumber

IndentIndex: TypeAlias = dict[LineNumber, int]


class IndentIndexBuilder:
    def __init__(self, source: str):
        self.original_tree = ast.parse(source)
        modified_source = ast.unparse(self.original_tree)
        self.modified_source_lines = modified_source.splitlines()
        self.modified_source_lines.append("")
        self.modified_tree = ast.parse(modified_source)

        self.index: IndentIndex = {}

    def visit(self, original_node: ast.AST, modified_node: ast.AST):
        try:
            original_line_number = LineNumber[1](original_node.lineno)
            modified_line_number = LineNumber[1](modified_node.lineno)
        except AttributeError:
            ...
        else:
            self.index[original_line_number] = max(
                self.count_spaces(modified_line_number), self.count_spaces(modified_line_number + 1)
            )
        for (_, original_value), (_, modified_value) in zip(
            ast.iter_fields(original_node), ast.iter_fields(modified_node)
        ):
            if isinstance(original_value, list):
                for original_item, modified_item in zip(original_value, modified_value):
                    if isinstance(original_item, ast.AST):
                        self.visit(original_item, modified_item)
            elif isinstance(original_value, ast.AST):
                self.visit(original_value, modified_value)

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
