from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Optional

from .utils import LineNumber
from .utils.position import Position


@dataclass
class FunctionPosition:
    name: str
    line: LineNumber


class FunctionFinder(ast.NodeVisitor):
    """Find the function defined on the given line (1-based indexed)."""

    @dataclass
    class FunctionNodeFoundException(Exception):
        node: ast.FunctionDef
        name: str = None

        def __post_init__(self):
            if self.name is None:
                self.name = self.node.name

    def __init__(self, line_number: int):
        self.line_number = line_number

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        return self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        try:
            return self.generic_visit(node)
        except FunctionFinder.FunctionNodeFoundException as e:
            raise FunctionFinder.FunctionNodeFoundException(e.node, f"{node.name}.{e.name}")

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if LineNumber[1](node.lineno) <= self.line_number <= LineNumber[1](node.end_lineno):
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
    def find_function(cls, source, line_number: LineNumber) -> Optional[ast.FunctionDef]:
        """Return the ast node for the function defined in source on line `line_number`."""
        tree = ast.parse(source)

        node: Optional[ast.FunctionDef] = None
        try:
            FunctionFinder(line_number).visit(tree)
        except FunctionFinder.FunctionNodeFoundException as e:
            node = e.node

        return node

    @classmethod
    def get_function(cls, source, line_number: LineNumber) -> Optional[FunctionPosition]:
        """Return the function name for the function defined in source on line `line_number`."""
        tree = ast.parse(source)

        position: Optional[ast.FunctionDef] = None
        try:
            FunctionFinder(line_number).visit(tree)
        except FunctionFinder.FunctionNodeFoundException as e:
            position = FunctionPosition(name=e.name, line=LineNumber[1](e.node.lineno))

        return position

    @classmethod
    def find_all_functions(cls, source: str) -> list[Position]:
        lines = []
        i = LineNumber[0](0)
        while i < LineNumber[0](len(source.splitlines())):
            node = cls.find_function(source, i)
            if node:
                lines.append(LineNumber[1](node.lineno))
                i = LineNumber[1](node.end_lineno)
            i += 1
        return lines
