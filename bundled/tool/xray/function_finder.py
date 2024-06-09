from __future__ import annotations

import ast
from typing import Any, Optional

from .utils import LineNumber


class FunctionFinder(ast.NodeVisitor):
    """Find the function defined on the given line (1-based indexed)."""

    class FunctionNodeFoundException(Exception):
        def __init__(self, node: ast.FunctionDef):
            self.node = node

    def __init__(self, line_number: int):
        self.line_number = line_number

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if LineNumber[1](node.lineno) == self.line_number:
            raise FunctionFinder.FunctionNodeFoundException(node)

    def generic_visit(self, node: ast.AST) -> Any:
        try:
            if LineNumber[1](node.lineno) > self.line_number:
                return
            if LineNumber[1](node.end_lineno) < self.line_number:
                return
        except AttributeError:
            ...
        super().generic_visit(node)

    @classmethod
    def find_function(cls, source, line_number: LineNumber) -> Optional[str]:
        """Return the function name for the function defined in source on line `line_number`."""
        tree = ast.parse(source)

        name: Optional[str] = None
        try:
            FunctionFinder(line_number).visit(tree)
        except FunctionFinder.FunctionNodeFoundException as e:
            name = e.node.name

        return name
