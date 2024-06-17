from __future__ import annotations

from dataclasses import dataclass

from .line_number import LineNumber, Serializable


@dataclass
class Position(Serializable):
    """Utility for representing a position in a document."""

    line: LineNumber
    character: int

    def __lt__(self, other: Position) -> bool:
        return (self.line, self.character) < (other.line, other.character)

    def __hash__(self) -> int:
        return hash((self.line, self.character))
