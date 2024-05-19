import ast
from typing import Optional

from pygls.workspace import text_document


class FunctionNodeFoundException(Exception):
    def __init__(self, node: ast.FunctionDef):
        self.node = node


class FunctionFinder(ast.NodeVisitor):
    """Find the function defined on the given line (1-based indexed)."""

    def __init__(self, lineno: int):
        self.lineno = lineno

    def visit_FunctionDef(self, node):
        if node.lineno == self.lineno:
            raise FunctionNodeFoundException(node)


def find_function(filepath: str, lineno: int) -> Optional[str]:
    """Return the function name for the function defined in `filename` on line `lineno` (0-indexed)."""
    document = text_document.TextDocument(filepath)
    source = document.source
    tree = ast.parse(source)

    name: Optional[str] = None
    try:
        FunctionFinder(lineno=lineno + 1).visit(tree)
    except FunctionNodeFoundException as e:
        name = e.node.name

    return name
