from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional, Self, TypeAlias

from .annotation import Annotation
from .difference import Difference, NoDifference
from .utils import LineNumber, Position, Serializable

Timestamp: TypeAlias = Iterable[tuple[int, int]]
GroupedAnnotations: TypeAlias = dict[Timestamp, dict[Position, list[Annotation]]]


class Differences(Serializable):
    def __init__(self):
        self._differences: list[tuple[Position, Difference]] = []

    def add(self, position: Position, difference: Difference) -> Self:
        """Add another difference (in place)."""
        self._differences.append((position, difference))
        return self

    def to_annotations(self) -> ...:
        groups = self.group()

    def group(self) -> GroupedAnnotations:
        """Group annotation based on where they appear in the control flow."""

        @dataclass
        class Block:
            depth: int
            indent: int
            parent: Optional[Block] = None
            id: int = field(default_factory=itertools.count().__next__, init=False)
            multi_use: bool = field(default=False, init=False)

        annotations: GroupedAnnotations = defaultdict(dict)
        # Keep track of the different blocks and current block.
        blocks: dict[LineNumber, Block] = {}
        current_block = Block(-1, 0)
        timestamp = []
        last_visits: dict[LineNumber, Timestamp] = {}

        for position, difference in itertools.chain(
            [(Position(LineNumber[1](0), 0), NoDifference())], self._differences
        ):
            line_number = position.line
            indent = position.character
            # Pop blocks until the indents line up.
            while indent < current_block.indent:
                current_block = current_block.parent
                timestamp.pop(-1)

            if indent > current_block.indent:
                # Create a block if the line has not been visited.
                if line_number not in blocks:
                    blocks[line_number] = Block(current_block.depth + 1, indent, current_block)
                current_block = blocks[line_number]
                # Add a new block and a zero timestamp.
                timestamp.append((current_block.id, 0))
            elif line_number in last_visits and last_visits[line_number] == tuple(timestamp):
                # If we last visited this line in the same timestamp, increment.
                block_id, timestamp_id = timestamp[-1]
                timestamp[-1] = (block_id, timestamp_id + 1)
                current_block.multi_use = True

            last_visits[line_number] = tuple(timestamp)
            annotations[tuple(timestamp)][position] = difference.to_annotations(position)

        # Keep track of blocks within loops.
        multi_use_blocks = {block.id for block in blocks.values() if block.multi_use}

        compressed_annotations: GroupedAnnotations = defaultdict(dict)
        for timestamp, annotations in annotations.items():
            # Compress timestamps by removing unused blocks.
            compressed_timestamp = tuple(
                (block_id, timestamp_id)
                for block_id, timestamp_id in timestamp
                if block_id in multi_use_blocks
            )
            compressed_annotations[compressed_timestamp] |= annotations
        return compressed_annotations
