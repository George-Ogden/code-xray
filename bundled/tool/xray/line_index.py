from __future__ import annotations

import ast
from typing import Optional

from .utils import LineNumber


class LineIndex(dict[LineNumber, LineNumber]):
    """Index to map the start of definitions to the end of definitions on each line."""

    def update(self, start_line_number: LineNumber, end_line_number: LineNumber):
        """Update the index with a new node in the ast."""
        if start_line_number not in self or end_line_number > self[start_line_number]:
            self[start_line_number] = end_line_number


class LineIndexBuilder(ast.NodeVisitor):
    """Compute an index to store a map from to last lines of definitions in a file."""

    def __init__(self, node: ast.FunctionDef):
        # Map from start lines to end lines.
        self.index = LineIndex()
        self.root = node

    def visit(self, node: Optional[ast.AST] = None):
        if node is None:
            # The root is the only function definition to not visit.
            for child in ast.iter_child_nodes(self.root):
                super().visit(child)
        else:
            super().visit(node)

    def generic_visit(self, node: ast.AST):
        try:
            start_line_number = LineNumber[1](node.lineno)
            end_line_number = LineNumber[1](node.end_lineno)
        except AttributeError:
            ...
        else:
            match node:
                case (
                    ast.AsyncFor()
                    | ast.AsyncWith()
                    | ast.For()
                    | ast.If()
                    | ast.IfExp()
                    | ast.Match()
                    | ast.Try()
                    | ast.TryStar()
                    | ast.While()
                    | ast.With()
                ):
                    # Ignore multiline definitions.
                    ...
                case _:
                    # We must be in range so update the index.
                    self.index.update(start_line_number, end_line_number)
        super().generic_visit(node)

    @classmethod
    def build_index(cls, node: ast.FunctionDef) -> LineIndex:
        """Build the index from line numbers to source numbers."""
        finder = LineIndexBuilder(node)
        finder.visit()
        return finder.index
