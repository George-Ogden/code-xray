from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from typing import ClassVar, Iterable, Self

from .annotation import Annotation, Position, Timestamp
from .utils import renamable


@dataclass(frozen=True, repr=False)
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

    def add_prefix(self, prefix: str) -> Self:
        return self

    def rename(self, pattern: str, replacement: str) -> Self:
        return self

    def __iter__(self) -> Iterable[Difference]:
        yield self

    def __repr__(self) -> str:
        return ""

    def __bool__(self) -> bool:
        return True

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
        return ""

    def to_annotations(self, timestamp: Timestamp, position: Position) -> Iterable[Annotation]:
        """Convert to an annotation."""
        for difference in self:
            yield Annotation(
                timestamp=timestamp,
                position=position,
                summary=difference.summary,
                description=difference.description,
            )

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
                    edition = difference_table[i - 1, j - 1] + difference.add_prefix(f"[{i-1}]")
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
    def set_difference(cls, a: Set[any], b: Set[any]) -> Difference:
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
            differences.append(cls.difference(a[key], b[key]).add_prefix(f"[{key!r}]"))
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


@dataclass(frozen=True, repr=False)
class NoDifference(Difference):
    def __iter__(self) -> Iterable[Difference]:
        yield from []

    def __bool__(self) -> bool:
        return False


@dataclass(frozen=True, repr=False)
class Edit(VariableDifference):
    name: str
    old: any
    new: any

    def add_prefix(self, prefix: str) -> Self:
        return Edit(name=prefix + self.name, old=self.old, new=self.new)

    def rename(self, pattern: str, replacement: str) -> Self:
        return Edit(name=re.sub(pattern, replacement, self.name), old=self.old, new=self.new)

    def __repr__(self) -> str:
        return f"{self.name} = {self.repr(self.new)}"


@dataclass(frozen=True, repr=False)
class Add(VariableDifference):
    name: str
    value: any

    def add_prefix(self, prefix: str) -> Self:
        return Add(name=prefix + self.name, value=self.value)

    def rename(self, pattern: str, replacement: str) -> Self:
        return Add(name=re.sub(pattern, replacement, self.name), value=self.value)

    def __repr__(self) -> str:
        return f"{self.name} = {self.repr(self.value)}"


@dataclass(frozen=True, repr=False)
class Delete(VariableDifference):
    name: str
    value: any

    def add_prefix(self, prefix: str) -> Self:
        return Delete(name=prefix + self.name, value=self.value)

    def rename(self, pattern: str, replacement: str) -> Self:
        return Delete(name=re.sub(pattern, replacement, self.name), value=self.value)

    def __repr__(self) -> str:
        return f"del {self.name}"


@dataclass(frozen=True, repr=False)
class CompoundDifference(Difference):
    differences: list[Difference]

    def __eq__(self, other: CompoundDifference) -> bool:
        if not isinstance(other, CompoundDifference):
            return False
        return len(self.differences) == len(other.differences) and set(self.differences) == set(
            other.differences
        )

    def add_prefix(self, prefix: str) -> Self:
        return CompoundDifference(
            [difference.add_prefix(prefix) for difference in self.differences]
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


@dataclass(frozen=True, repr=False)
class Return(KeywordDifference[dict(keyword='"return"')]):
    value: any

    def __repr__(self) -> str:
        return f"return {self.repr(self.value)}"


@dataclass(frozen=True, repr=False)
class Exception_(KeywordDifference[dict(keyword='"raise"', value="exception")]):
    exception: Exception

    def __repr__(self) -> str:
        return f"raise {self.repr(self.exception)}"
