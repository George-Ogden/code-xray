from __future__ import annotations

import ast
from typing import Any, Optional

from pygls.workspace import text_document


class FunctionFinder(ast.NodeVisitor):
    """Find the function defined on the given line (1-based indexed)."""

    class FunctionNodeFoundException(Exception):
        def __init__(self, node: ast.FunctionDef):
            self.node = node

    def __init__(self, lineno: int):
        self.lineno = lineno

    def visit_FunctionDef(self, node):
        if node.lineno == self.lineno:
            raise FunctionFinder.FunctionNodeFoundException(node)

    def generic_visit(self, node: ast.AST) -> Any:
        try:
            if node.lineno > self.lineno:
                return
            if node.end_lineno < self.lineno:
                return
        except AttributeError:
            ...
        super().generic_visit(node)

    @classmethod
    def find_function(cls, filepath: str, lineno: int) -> Optional[str]:
        """Return the function name for the function defined in `filename` on line `lineno` (0-indexed)."""
        document = text_document.TextDocument(filepath)
        source = document.source
        tree = ast.parse(source)

        name: Optional[str] = None
        try:
            FunctionFinder(lineno=lineno + 1).visit(tree)
        except FunctionFinder.FunctionNodeFoundException as e:
            name = e.node.name

        return name
