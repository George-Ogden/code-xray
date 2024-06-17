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
    """Build an index used to decide the control flow of a program."""

    def __init__(self, root: ast.FunctionDef):
        self.index: ControlIndex = {}
        self.control_root = ControlNode(parent=None, line_number=LineNumber[1](root.lineno))
        self.ast_root = root

    def visit(self, ast_node: Optional[ast.AST] = None, control_node: Optional[ControlNode] = None):
        """Visit a node to update the index based on the node's position."""
        if ast_node is None and control_node is None:
            ast_node = self.ast_root
            control_node = self.control_root

        target = None

        # Consider all nodes that loop.
        try:
            # Generators are a special case.
            target = ast_node.generators[0].target
        except AttributeError:
            match ast_node:
                case ast.For() | ast.AsyncFor():
                    target = ast_node.target
                case ast.While():
                    target = ast_node.test

        # This means the node loops.
        if target is not None:
            control_node = ControlNode(
                parent=control_node, line_number=LineNumber[1](target.lineno)
            )

        # Update index.
        try:
            self.index[LineNumber[1](ast_node.lineno)] = control_node
            self.index[LineNumber[1](ast_node.end_lineno)] = control_node
        except AttributeError:
            ...

        # Iterate over the children of the current node.
        for node in ast.iter_child_nodes(ast_node):
            self.visit(node, control_node)

    @classmethod
    def build_index(cls, node: ast.FunctionDef) -> ControlIndex:
        """Build the index from line numbers to source numbers."""
        builder = ControlIndexBuilder(node)
        builder.visit()
        # Handle edge case for root header.
        header_start_line_number = LineNumber[1](node.lineno)
        header_end_line_number = max(
            header_start_line_number, LineNumber[1](node.body[0].lineno) - 1
        )
        if not header_end_line_number in builder.index:
            builder.index[header_end_line_number] = builder.control_root
        return builder.index
