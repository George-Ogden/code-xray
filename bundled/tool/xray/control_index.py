from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Optional, TypeAlias

from .utils import LineNumber


@dataclass
class ControlNode:
    parent: Optional[ControlNode]
    line_number: LineNumber


ControlIndex: TypeAlias = dict[LineNumber, ControlNode]


class ControlIndexBuilder:
    def __init__(self, root: ast.FunctionDef):
        self.index: ControlIndex = {}
        self.control_root = ControlNode(parent=None, line_number=LineNumber[1](root.lineno))
        self.ast_root = root

    def visit(self, ast_node: Optional[ast.AST] = None, control_node: Optional[ControlNode] = None):
        """Visit a node to update the index based on the node's position."""
        if ast_node is None and control_node is None:
            ast_node = self.ast_root
            control_node = self.control_root

        try:
            line_number = LineNumber[1](ast_node.lineno)
        except AttributeError:
            return
        target = None

        # Consider all nodes that loop.
        match ast_node:
            case ast.comprehension() | ast.For() | ast.AsyncFor():
                target = ast_node.target
            case ast.While():
                target = ast_node.test
        # This means the node loops.
        if target is not None:
            control_node = ControlNode(
                parent=control_node, line_number=LineNumber[1](target.lineno)
            )

        # Update index.
        self.index[line_number] = control_node

        # Iterate over the children of the current node.
        for node in ast.iter_child_nodes(ast_node):
            self.visit(node, control_node)

    @classmethod
    def build_index(cls, node: ast.FunctionDef) -> ControlIndex:
        """Build the index from line numbers to source numbers."""
        builder = ControlIndexBuilder(node)
        builder.visit()
        return builder.index
