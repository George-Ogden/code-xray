from __future__ import annotations

import abc
from typing import Any, ClassVar, Self, Type


class LineNumber:
    """Class for representing line numbers (zero or one-indexed)."""

    _type: ClassVar[int]
    _value: int

    def __init__(self, value: int):
        self._value = value

    @property
    @abc.abstractmethod
    def zero(self) -> int: ...

    @property
    @abc.abstractmethod
    def one(self) -> int: ...

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"({self._type}){self._value}"

    def __add__(self, other: int) -> Self:
        return (type(self))(self._value + other)

    def __class_getitem__(cls, idx: int) -> Type[LineNumber]:
        if not (idx is 0 or idx is 1):
            raise ValueError("Index must be zero or 1.")
        cls = (LineNumber0, LineNumber1)[idx]
        cls.__class_getitem__ = cls.__derived_class_getitem__
        return cls

    @classmethod
    def __derived_class_getitem__(cls, *args: Any) -> None:
        raise TypeError(f"{cls.__name__} does not support further specialization.")


class LineNumber0(LineNumber):
    _type = 0

    @property
    def zero(self) -> int:
        return self._value

    @property
    def one(self) -> int:
        return self._value + 1


class LineNumber1(LineNumber):
    _type = 1

    @property
    def zero(self) -> int:
        return self._value - 1

    @property
    def one(self) -> int:
        return self._value
