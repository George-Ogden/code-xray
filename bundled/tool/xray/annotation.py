from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, TypeAlias

from .utils import LineNumber, Serializable

Timestamp: TypeAlias = int


@dataclass
class Position(Serializable):
    line: LineNumber
    character: int

    def __lt__(self, other: Position) -> bool:
        return (self.line, self.character) < (other.line, other.character)


@dataclass
class Annotation(Serializable):
    timestamp: Timestamp
    position: Position
    summary: str
    description: str

    def __lt__(self, other: Annotation) -> bool:
        return self.position < other.position


class Annotations(Serializable):
    def __init__(self):
        self._annotations: Dict[LineNumber, List[Annotation]] = defaultdict(list)

    def __iadd__(self, annotation: Annotation):
        """Add another annotation (in place)."""
        self._annotations[annotation.position.line].append(annotation)
        return self

    @property
    def line_count(self) -> int:
        return len(self._annotations)

    def to_json(self) -> Dict[str, Any]:
        return {
            line.zero: [annotation.to_json() for annotation in sorted(annotations)]
            for line, annotations in self._annotations.items()
        }
