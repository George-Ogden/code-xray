from __future__ import annotations

from dataclasses import dataclass

from .line_number import LineNumber, Serializable


@dataclass(unsafe_hash=True)
class Position(Serializable):
    """Utility for representing a position in a document."""

    line: LineNumber
    character: int
    _instruction: int = 0
