from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional, Self, TypeAlias

from .annotation import Annotation
from .difference import Difference, NoDifference
from .utils import LineNumber, Position, Serializable

Timestamp: TypeAlias = Iterable[tuple[int, int]]


class Differences(Serializable):
    def __init__(self):
        self._differences: list[tuple[Position, Difference]] = []

    def add(self, position: Position, difference: Difference) -> Self:
        """Add another difference (in place)."""
        self._differences.append((position, difference))
        return self

    def to_annotations(self) -> ...:
        groups = self.group()

    def group(self) -> dict[Timestamp, dict[Position, list[Annotation]]]:
        @dataclass
        class Group:
            depth: int
            indent: int
            parent: Optional[Group] = None
            id: int = field(default_factory=itertools.count().__next__, init=False)
            multi_use: bool = field(default=False, init=False)

        annotations: dict[Timestamp, dict[Position, Iterable[Annotation]]] = defaultdict(dict)
        groups: dict[LineNumber, Group] = {}
        current_group = Group(-1, 0)
        timestamp = []
        last_visits: dict[LineNumber, Timestamp] = {}

        for position, difference in [
            (Position(LineNumber[1](0), 0), NoDifference())
        ] + self._differences:
            line_number = position.line
            indent = position.character
            while indent < current_group.indent:
                current_group = current_group.parent
                timestamp.pop(-1)

            if indent > current_group.indent:
                if line_number not in groups:
                    groups[line_number] = Group(current_group.depth + 1, indent, current_group)

                current_group = groups[line_number]
                timestamp.append((current_group.id, 0))
            elif line_number in last_visits and last_visits[line_number] == tuple(timestamp):
                group_id, timestamp_id = timestamp[-1]
                timestamp[-1] = (group_id, timestamp_id + 1)
                current_group.multi_use = True

            last_visits[line_number] = tuple(timestamp)
            annotations[tuple(timestamp)][position] = difference.to_annotations(position)

        multi_use_groups = [group.id for group in groups.values() if group.multi_use]

        compressed_annotations: dict[Timestamp, dict[Position, Iterable[Annotation]]] = defaultdict(
            dict
        )
        for timestamp, annotations in annotations.items():
            compressed_timestamp = tuple(
                (group_id, timestamp_id)
                for group_id, timestamp_id in timestamp
                if group_id in multi_use_groups
            )
            compressed_annotations[compressed_timestamp] |= annotations
        return compressed_annotations
