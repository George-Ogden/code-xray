from __future__ import annotations

from typing import Any


class GenericClass:
    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __eq__(self, other: GenericClass) -> bool:
        return vars(self) == vars(other)

    def __repr__(self) -> str:
        return str(vars(self))
