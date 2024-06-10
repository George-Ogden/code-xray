from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Optional

from .utils import Position, Serializable


@dataclass
class Annotation(Serializable):
    position: Position
    summary: str
    description: str

    def __lt__(self, other: Annotation) -> bool:
        return self.position < other.position


@dataclass
class InsetComponent(Serializable):
    text: str
    hover: Optional[str] = None

    def to_json(self) -> dict[str, any]:
        inset_copy = copy.copy(self)
        if self.hover is None:
            del inset_copy.hover
        return super(type(self), inset_copy).to_json()


class Annotations(Serializable):
    def __init__(self):
        self._annotations: list[Annotation] = []

    def __iadd__(self, annotation: Annotation):
        """Add another annotation (in place)."""
        self._annotations.append(annotation)
        return self

    @property
    def line_count(self) -> int:
        return len(self._annotations)

    def to_json(self) -> dict[str, any]:
        return {
            line.zero: [annotation.to_json() for annotation in sorted(annotations)]
            for line, annotations in self._annotations.items()
        }
