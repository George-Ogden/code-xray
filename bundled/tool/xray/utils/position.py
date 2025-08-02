from __future__ import annotations

from dataclasses import dataclass

from .line_number import LineNumber, Serializable


@dataclass(unsafe_hash=True)
class Position(Serializable):
    """Utility for representing a position in a document."""

    line: LineNumber
    character: int
    _instruction: int = 0
    _original_line: LineNumber = None

    def __post_init__(self):
        if self._original_line is None:
            self._original_line = self.line
