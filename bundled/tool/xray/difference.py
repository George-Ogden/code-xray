from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from typing import ClassVar, Iterable, Optional, Self

from .annotation import Annotation
from .utils import renamable


@dataclass(repr=False)
class Difference:
    MAX_LEN: ClassVar[int] = 30  # Maximum length of represented value.

    def __add__(self, other: Difference) -> Difference:
        match self, other:
            case NoDifference(), NoDifference():
                return NoDifference()
            case (NoDifference(), x) | (x, NoDifference()):
                return x
            case CompoundDifference(), CompoundDifference():
                return CompoundDifference(self.differences + other.differences)
            case (CompoundDifference(d), x) | (x, CompoundDifference(d)):
                return CompoundDifference(d + [x])
            case x, y:
                return CompoundDifference([x, y])

    def replace(self, **kwargs: any) -> Self:
        return (type(self))(**{k: kwargs.get(k, getattr(self, k)) for k in self.__match_args__})

    def add_prefix(self, prefix: str, value: Optional[any] = None) -> Self:
        return self.rename(r"^", prefix)

    def rename(self, pattern: str, replacement: str) -> Self:
        return self

    def __iter__(self) -> Iterable[Difference]:
        yield self

    def __repr__(self) -> str:
        return ""

    def __bool__(self) -> bool:
        return True

    def __eq__(self, other: object) -> bool:
        if type(self) != type(other):
            return False
        return vars(self.replace(history=None)) == vars(other.replace(history=None))

    @classmethod
    def repr(cls, obj: any) -> str:
        """Display a truncated version of the object."""
        representation = repr(obj)
        if len(representation) > cls.MAX_LEN:
            representation = representation[: cls.MAX_LEN - 2] + ".."
        return representation

    @property
    def summary(self) -> str:
        """Inline display."""
        return repr(self)

    @property
    def description(self) -> str:
        """Hover display."""
        return self.summary

    def to_annotations(self) -> Iterable[list[Annotation]]:
        """Convert to an annotation."""
        for difference in self:
            yield difference.to_annotation()

    def to_annotation(self) -> list[Annotation]:
        """Convert to an annotation."""
        return []

    def limit(self, name: str) -> str:
        if len(name) > self.MAX_LEN:
            return name[: self.MAX_LEN - 3] + ".." + name[-1]
        return name

    @classmethod
    def difference(cls, a: any, b: any) -> Difference:
        """Calculate the difference between two objects of (almost) any type."""
        try:
            # Two objects are identical.
            if a is b or a == b:
                return NoDifference()
        except ValueError:
            # Equivalent to failing.
            ...
        # Object has changed.
        if type(a) != type(b):
            return Edit("", a, b)  # Empty string represents no path to object.

        # Cases based on type (use isinstance to allow subtype matching e.g. defaultdict).
        elif isinstance(a, list):
            return cls.list_difference(a, b)
        elif isinstance(a, set):
            difference = cls.set_difference(a, b)
            if isinstance(difference, CompoundDifference):
                return Edit("", a, b)
            else:
                return difference
        elif isinstance(a, dict):
            return cls.dict_difference(a, b)
        else:
            return cls.object_difference(a, b)

    @classmethod
    def list_difference(cls, a: list[any], b: list[any]):
        """Calculate the difference between two lists."""
        # Return an edit distance (up to 1) or Edit.
        if abs(len(a) - len(b)) >= 2:
            return Edit("", a, b)
        # ? Not sure it needs to be this complicated.
        # Use 1-based indexing for table.
        difference_table = {(0, 0): NoDifference()}
        if len(b) > 0:
            difference_table[0, 1] = Add("[0]", b[0])
        if len(a) > 0:
            difference_table[1, 0] = Delete("[0]", a[0])

        for i in range(1, len(a) + 1):
            for j in range(max(i - 1, 1), min(i + 2, len(b) + 1)):
                difference = Difference.difference(a[i - 1], b[j - 1])
                if isinstance(difference, NoDifference):
                    difference_table[i, j] = difference_table[i - 1, j - 1]
                else:
                    edition = difference_table[i - 1, j - 1] + difference.add_prefix(
                        f"[{i-1}]", a[i - 1]
                    )
                    editions = [edition]
                    if (i, j - 1) in difference_table:
                        addition = difference_table[i, j - 1] + Add(f"[{j-1}]", b[j - 1])
                        editions.append(addition)
                    if (i - 1, j) in difference_table:
                        deletion = difference_table[i - 1, j] + Delete(f"[{i-1}]", a[i - 1])
                        editions.append(deletion)
                    short_editions = [
                        edit for edit in editions if not isinstance(edit, CompoundDifference)
                    ]
                    if len(short_editions) > 0:
                        difference_table[i, j] = short_editions[0]
                    else:
                        difference_table[i, j] = editions[0]
        if isinstance(difference_table[len(a), len(b)], CompoundDifference):
            return Edit("", a, b)
        else:
            return difference_table[len(a), len(b)]

    @classmethod
    def set_difference(cls, a: set[any], b: set[any]) -> Difference:
        """Calculate the difference between two sets."""
        left_difference = a.difference(b)
        right_difference = b.difference(a)
        differences = [Delete(".item", x) for x in left_difference] + [
            Add(".item", x) for x in right_difference
        ]
        return sum(differences, start=NoDifference())

    @classmethod
    def dict_difference(cls, a: dict[any, any], b: dict[any, any]) -> Difference:
        """Calculate the differences between two dictionaries."""
        a_keys = set(a.keys())
        b_keys = set(b.keys())
        key_difference = cls.set_difference(a_keys, b_keys)
        differences = []
        for difference in key_difference:
            key = difference.value
            match difference:
                case Add():
                    differences.append(Add(name=f"[{key!r}]", value=b[key]))
                case Delete():
                    differences.append(Delete(name=f"[{key!r}]", value=a[key]))

        for key in a_keys.intersection(b_keys):
            differences.append(
                cls.difference(a[key], b[key]).add_prefix(f"[{key!r}]", value=b[key])
            )
        return sum(differences, start=NoDifference())

    @classmethod
    def object_difference(cls, a: any, b: any) -> Difference:
        try:
            difference = cls.dict_difference(vars(a), vars(b))
        except TypeError:
            if a == b:
                return NoDifference()
            else:
                return Edit("", a, b)
        if isinstance(difference, CompoundDifference):
            return Edit("", a, b)
        else:
            return difference.rename(r"^\['([a-z0-9_]+)'\]", r".\1")


class VariableDifference(Difference):
    """Specific difference for variables."""

    name: str
    value: any
    history: list[tuple[str, any]]

    def add_prefix(self, prefix: str, value: any) -> Self:
        self.history.append(("", value))
        return super().add_prefix(prefix)

    def rename(self, pattern: str, replacement: str) -> Self:
        return self.replace(
            name=re.sub(pattern, replacement, self.name),
            history=[(re.sub(pattern, replacement, k), v) for k, v in self.history],
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(
                    self,
                ),
                ((k, v) for k, v in vars(self.replace(history=None)).items()),
            )
        )

    def to_annotation(self) -> Iterable[Annotation]:
        name_prefix = ""
        name_annotations = []
        for key, value in itertools.chain(reversed(self.history), [(self.name, self.value)]):
            assert key.startswith(name_prefix)
            subkey = key[len(name_prefix) :]
            name_annotations.append(Annotation(text=subkey, hover=repr(value)))
            name_prefix = key
        equals = Annotation(" = ")
        value = Annotation(self.limit(repr(self.value)), repr(self.value))
        return name_annotations + [equals, value]


@dataclass(repr=False, unsafe_hash=False)
class NoDifference(VariableDifference):
    history: list[tuple[str, any]] = field(default_factory=list)

    def __iter__(self) -> Iterable[Difference]:
        yield from []

    def __bool__(self) -> bool:
        return False

    def rename(self, pattern: str, replacement: str) -> Self:
        return self

    __hash__ = VariableDifference.__hash__
    __eq__ = Difference.__eq__


@dataclass(repr=False)
class Edit(VariableDifference):
    name: str
    old: any
    new: any
    history: list[tuple[str, any]] = field(default_factory=list)

    @property
    def value(self) -> any:
        return self.new

    def __repr__(self) -> str:
        return f"{self.name} = {self.repr(self.new)}"

    __hash__ = VariableDifference.__hash__
    __eq__ = Difference.__eq__


@dataclass(repr=False, unsafe_hash=False)
class Add(VariableDifference):
    name: str
    value: any
    history: list[tuple[str, any]] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"{self.name} = {self.repr(self.value)}"

    __hash__ = VariableDifference.__hash__
    __eq__ = Difference.__eq__


@dataclass(repr=False)
class Delete(VariableDifference):
    name: str
    value: any
    history: list[tuple[str, any]] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"del {self.name}"

    __hash__ = VariableDifference.__hash__
    __eq__ = Difference.__eq__


@dataclass(repr=False)
class CompoundDifference(Difference):
    differences: list[Difference]

    def __eq__(self, other: CompoundDifference) -> bool:
        if not isinstance(other, CompoundDifference):
            return False
        return len(self.differences) == len(other.differences) and set(self.differences) == set(
            other.differences
        )

    def add_prefix(self, prefix: str, value: any) -> Self:
        return CompoundDifference(
            [difference.add_prefix(prefix, value) for difference in self.differences]
        )

    def __iter__(self) -> Iterable[Difference]:
        yield from itertools.chain(*self.differences)

    def rename(self, pattern: str, replacement: str) -> Self:
        return CompoundDifference(
            [difference.rename(pattern, replacement) for difference in self.differences]
        )

    def __repr__(self) -> str:
        return ", ".join(repr(difference) for difference in self.differences if repr(difference))

    def __bool__(self) -> bool:
        return any(self)


@renamable
class KeywordDifference(Difference):
    keyword: str
    value: any

    @property
    def description(self) -> str:
        return f"{self.KeywordDifference.keyword} {self.KeywordDifference.value!r}"

    def to_annotation(self) -> Iterable[Annotation]:
        return [
            Annotation(f"{self.KeywordDifference.keyword} "),
            Annotation(
                self.limit(repr(self.KeywordDifference.value)), repr(self.KeywordDifference.value)
            ),
        ]


@dataclass(repr=False)
class Return(KeywordDifference[dict(keyword='"return"')]):
    value: any

    def __repr__(self) -> str:
        return f"return {self.repr(self.value)}"


@dataclass(repr=False)
class Exception_(KeywordDifference[dict(keyword='"raise"', value="exception")]):
    exception: Exception

    def __repr__(self) -> str:
        return f"raise {self.repr(self.exception)}"
