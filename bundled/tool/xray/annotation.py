import copy
from dataclasses import dataclass
from typing import Optional, TypeAlias, Union

from .utils import Serializable


@dataclass
class AnnotationPart(Serializable):
    """Subpart of an annotation with text and a tooltip."""

    text: str
    hover: Optional[str] = None

    def to_json(self) -> dict[str, any]:
        inset_copy = copy.copy(self)
        if self.hover is None:
            del inset_copy.hover
        return super(type(self), inset_copy).to_json()


Annotation: TypeAlias = list[AnnotationPart]
Annotations: TypeAlias = dict[str, Union["Annotations", list[Annotation]]]
