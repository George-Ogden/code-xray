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

    class FunctionAnalyzedException(Exception): ...

    def __init__(self, line_number: LineNumber):
        self.line_number = line_number
        # Leave end line number until it is computed.
        self.end_line_number: Optional[LineNumber] = None
        # Map from start lines to end lines.
        self.index = LineIndex()

    def generic_visit(self, node: ast.AST):
        try:
            start_line_number = LineNumber[1](node.lineno)
            # Ignore lines after the end of the function.
            if start_line_number > self.end_lineno:
                return
            # Ignore lines before the start of the function.
            end_line_number = LineNumber[1](node.end_lineno)
            if end_line_number < self.line_number:
                return
            match node:
                case (
                    ast.AsyncFor()
                    | ast.AsyncFunctionDef()
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
        except AttributeError:
            ...
        super().generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if LineNumber[1](node.lineno) == self.line_number:
            # If this is the function, update the end line number, visit then finish (raise an exception).
            self.end_lineno = LineNumber[1](node.end_lineno)
            super().generic_visit(node)
            raise LineIndexBuilder.FunctionAnalyzedException(node)

    @classmethod
    def build_index(cls, source: str, line_number: LineNumber) -> LineIndex:
        """Build the index from line numbers to source numbers."""
        tree = ast.parse(source)

        finder = LineIndexBuilder(line_number=line_number)
        try:
            finder.visit(tree)
        except LineIndexBuilder.FunctionAnalyzedException:
            ...
        return finder.index
