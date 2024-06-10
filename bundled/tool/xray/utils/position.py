from __future__ import annotations

from dataclasses import dataclass

from .line_number import LineNumber, Serializable


@dataclass
class Position(Serializable):
    line: LineNumber
    character: int

    def __lt__(self, other: Position) -> bool:
        return (self.line, self.character) < (other.line, other.character)
