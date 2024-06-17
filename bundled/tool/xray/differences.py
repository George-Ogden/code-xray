from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import dataclass, field
from typing import ClassVar, Iterable, Optional, Self, TypeAlias

from .annotation import Annotation, Annotations
from .control_index import ControlIndex, ControlNode
from .difference import Difference
from .utils import LineNumber, Position, Serializable, recursive_defaultdict

Timestamp: TypeAlias = Iterable[tuple[int, int]]
GroupedAnnotations: TypeAlias = dict[Timestamp, dict[Position, list[Annotation]]]


@dataclass
class LineAnnotation(Serializable):
    position: Position
    annotations: list[list[Annotation]]


class Differences(Serializable):
    """Utility for grouping differences."""

    def __init__(self):
        self._differences: list[tuple[Position, Difference]] = []

    def add(self, position: Position, difference: Difference) -> Self:
        """Add another difference (in place)."""
        self._differences.append((position, difference))
        return self

    def to_annotations(self, control_index: ControlIndex) -> Annotations:
        groups = self.group(control_index)
        annotations = recursive_defaultdict()
        for timestamp, timestep_annotations in groups.items():
            # Create a slot based on the block and timestamps that contain this structure.
            slot = annotations
            for block_id, timestamp_id in timestamp:
                slot = slot[f"block_{block_id}"]
                slot = slot[f"timestamp_{timestamp_id}"]
            for position, line_annotations in timestep_annotations.items():
                # Store an annotation for the specific line.
                slot[f"line_{position.line.zero}"] = LineAnnotation(
                    position=position,
                    annotations=list(line_annotations),
                )
        return annotations.to_non_empty_dict()

    def group(self, control_index: ControlIndex) -> GroupedAnnotations:
        """Group annotation based on where they appear in the control flow."""

        @dataclass
        class Block:
            """Utility for storing blocks of code."""

            control_node: ControlNode
            time: int = 0
            id: int = field(default_factory=itertools.count().__next__, init=False)
            children: list[Block] = field(default_factory=list)

            @property
            def line_number(self) -> LineNumber:
                return self.control_node.line_number

            @property
            def parent(self) -> Optional[Block]:
                if self.is_root:
                    return None
                # Parent is decided by the control information.
                return Block[self.control_node.parent.line_number]

            def next(self):
                """Move to the next timestep."""
                self.time += 1
                for child in self.children:
                    child.reset()

            def reset(self):
                """Set the time to 0 for this block and all child blocks."""
                self.time = 0
                for child in self.children:
                    child.reset()

            @property
            def timestamp(self) -> tuple[tuple[int, int], ...]:
                """Recursively get the current timestamp as block and timestamp ids."""
                if self.is_root:
                    return ()
                return self.parent.timestamp + ((self.id, self.time),)

            @property
            def is_root(self) -> bool:
                return self.control_node.parent is None

            _blocks: ClassVar[dict[LineNumber, Block]] = {}

            def __class_getitem__(cls, line_number: LineNumber) -> Block:
                """Lookup a block based on the line number."""
                # Lookup the line number from the control information.
                line_number = control_index[line_number].line_number
                if line_number not in cls._blocks:
                    # Create the block if it does not exist.
                    parent = control_index[line_number]
                    block = Block(control_node=parent)

                    cls._blocks[line_number] = block
                    if block.parent:
                        # Add a double-link to the tree.
                        block.parent.children.append(block)
                return cls._blocks[line_number]

        annotations: GroupedAnnotations = defaultdict(dict)

        for position, difference in self._differences:
            line_number = position.line
            block = Block[line_number]

            if block.line_number == line_number and not block.is_root:
                # If we reach a line again, increment the timestamp.
                block.next()

            if (
                block.is_root
                and block.timestamp in annotations
                and position in annotations[block.timestamp]
            ):
                # Handle special case where a root line is repeated.
                annotations[block.timestamp][position] = itertools.chain(
                    annotations[block.timestamp][position], difference.to_annotations()
                )
            else:
                annotations[block.timestamp][position] = difference.to_annotations()

        return annotations
