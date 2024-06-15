from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Optional, TypeVar, Union

from .utils import Serializable


@dataclass
class Annotation(Serializable):
    text: str
    hover: Optional[str] = None

    def to_json(self) -> dict[str, any]:
        inset_copy = copy.copy(self)
        if self.hover is None:
            del inset_copy.hover
        return super(type(self), inset_copy).to_json()


Annotations: TypeVar = dict[str, Union["Annotations", list[list[Annotation]]]]
