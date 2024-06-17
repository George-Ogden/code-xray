from typing import Any, Dict, List, Set

import pytest

from .conftest import GenericClass
from .difference import *


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (NoDifference(), NoDifference(), NoDifference()),
        (NoDifference(), Edit("name", "old", "new"), Edit("name", "old", "new")),
        (NoDifference(), Add("name", "value"), Add("name", "value")),
        (NoDifference(), Delete("name", "value"), Delete("name", "value")),
        (
            NoDifference(),
            CompoundDifference([Edit("name", "old", "new")]),
            CompoundDifference([Edit("name", "old", "new")]),
        ),
        (Edit("name", "old", "new"), NoDifference(), Edit("name", "old", "new")),
        (
            Edit("name1", "old1", "new1"),
            Edit("name2", "old2", "new2"),
            CompoundDifference([Edit("name1", "old1", "new1"), Edit("name2", "old2", "new2")]),
        ),
        (
            Edit("name", "old", "new"),
            Add("name", "value"),
            CompoundDifference([Edit("name", "old", "new"), Add("name", "value")]),
        ),
        (
            Edit("name", "old", "new"),
            Delete("name", "value"),
            CompoundDifference([Edit("name", "old", "new"), Delete("name", "value")]),
        ),
        (
            Edit("name", "old", "new"),
            CompoundDifference([Edit("name2", "old2", "new2")]),
            CompoundDifference([Edit("name", "old", "new"), Edit("name2", "old2", "new2")]),
        ),
        (Add("name", "value"), NoDifference(), Add("name", "value")),
        (
            Add("name", "value"),
            Edit("name", "old", "new"),
            CompoundDifference([Add("name", "value"), Edit("name", "old", "new")]),
        ),
        (
            Add("name1", "value1"),
            Add("name2", "value2"),
            CompoundDifference([Add("name1", "value1"), Add("name2", "value2")]),
        ),
        (
            Add("name", "value"),
            Delete("name", "value"),
            CompoundDifference([Add("name", "value"), Delete("name", "value")]),
        ),
        (
            Add("name", "value"),
            CompoundDifference([Edit("name", "old", "new")]),
            CompoundDifference([Add("name", "value"), Edit("name", "old", "new")]),
        ),
        (Delete("name", "value"), NoDifference(), Delete("name", "value")),
        (
            Delete("name", "value"),
            Edit("name", "old", "new"),
            CompoundDifference([Delete("name", "value"), Edit("name", "old", "new")]),
        ),
        (
            Delete("name", "value1"),
            Add("name2", "value2"),
            CompoundDifference([Delete("name", "value1"), Add("name2", "value2")]),
        ),
        (
            Delete("name", "value"),
            Delete("name", "value"),
            CompoundDifference([Delete("name", "value"), Delete("name", "value")]),
        ),
        (
            Delete("name", "value"),
            CompoundDifference([Edit("name", "old", "new")]),
            CompoundDifference([Delete("name", "value"), Edit("name", "old", "new")]),
        ),
        (
            CompoundDifference([Edit("name", "old", "new")]),
            NoDifference(),
            CompoundDifference([Edit("name", "old", "new")]),
        ),
        (
            CompoundDifference([Edit("name1", "old1", "new1")]),
            Edit("name2", "old2", "new2"),
            CompoundDifference([Edit("name1", "old1", "new1"), Edit("name2", "old2", "new2")]),
        ),
        (
            CompoundDifference([Edit("name", "old", "new")]),
            Add("name", "value"),
            CompoundDifference([Edit("name", "old", "new"), Add("name", "value")]),
        ),
        (
            CompoundDifference([Edit("name", "old", "new")]),
            Delete("name", "value"),
            CompoundDifference([Edit("name", "old", "new"), Delete("name", "value")]),
        ),
        (
            CompoundDifference([Edit("name", "old", "new")]),
            CompoundDifference([Edit("name2", "old2", "new2")]),
            CompoundDifference([Edit("name", "old", "new"), Edit("name2", "old2", "new2")]),
        ),
    ],
)
def test_difference_add(a, b, expected):
    assert a + b == expected


@pytest.mark.parametrize(
    "prefix, difference, expected",
    [
        ("prefix.", NoDifference(), NoDifference()),
        ("prefix.", Edit("name", "old", "new"), Edit("prefix.name", "old", "new")),
        ("prefix.", Add("name", "value"), Add("prefix.name", "value")),
        ("prefix.", Delete("name", "value"), Delete("prefix.name", "value")),
        (
            "prefix.",
            CompoundDifference([Edit("name1", "old1", "new1"), Add("name2", "value2")]),
            CompoundDifference(
                [Edit("prefix.name1", "old1", "new1"), Add("prefix.name2", "value2")]
            ),
        ),
    ],
)
def test_add_prefix(prefix: str, difference: Difference, expected: Difference):
    assert difference.add_prefix(prefix, None) == expected


@pytest.mark.parametrize(
    "difference, expected",
    [
        (NoDifference(), []),
        (Edit("name", "old", "new"), [Edit("name", "old", "new")]),
        (Add("name", "value"), [Add("name", "value")]),
        (Delete("name", "value"), [Delete("name", "value")]),
        (
            CompoundDifference([Edit("name1", "old1", "new1"), Add("name2", "value2")]),
            [Edit("name1", "old1", "new1"), Add("name2", "value2")],
        ),
    ],
)
def test_iter(difference: Difference, expected: List[Difference]):
    assert list(difference) == expected


@pytest.mark.parametrize(
    "a,b,difference",
    [
        ({0}, {0}, NoDifference()),
        ({1, 0}, {0, 1}, NoDifference()),
        ({1}, {0, 1}, Add(".item", 0)),
        ({1, 0}, {0}, Delete(".item", 1)),
        ({1}, {0}, CompoundDifference([Delete(".item", 1), Add(".item", 0)])),
        (
            {0, 1, 2, 3},
            {2, 3, 4},
            CompoundDifference([Delete(".item", 0), Delete(".item", 1), Add(".item", 4)]),
        ),
    ],
)
def test_set_difference(a: Set[Any], b: Set[Any], difference: Difference):
    assert Difference.set_difference(a, b) == difference


@pytest.mark.parametrize(
    "a,b,difference",
    [
        (0, 0, NoDifference()),
        (1.5, 1.5, NoDifference()),
        (0, 1, Edit("", 0, 1)),
        (1.5, -2.5, Edit("", 1.5, -2.5)),
    ],
)
def test_primitive_object_difference(a: Any, b: Any, difference: Difference):
    assert Difference.object_difference(a, b) == difference


@pytest.mark.parametrize(
    "a,b,difference",
    [
        ({0: 1}, {0: 1}, NoDifference()),
        ({1: 0}, {1: 1}, Edit("[1]", 0, 1)),
        ({"a": 0}, {"a": 1}, Edit("['a']", 0, 1)),
        ({1: 0}, {1: 0, 2: 3}, Add("[2]", 3)),
        ({1: 0}, {1: 0, "b": 3}, Add("['b']", 3)),
        (
            {"a": "a", "b": "b", "c": "c"},
            {"a": "a", "b": "c", "d": "e"},
            CompoundDifference([Edit("['b']", "b", "c"), Delete("['c']", "c"), Add("['d']", "e")]),
        ),
    ],
)
def test_non_recursive_dict_difference(
    a: Dict[Any, Any], b: Dict[Any, Any], difference: Difference
):
    assert Difference.dict_difference(a, b) == difference


@pytest.mark.parametrize(
    "a,b,difference",
    [
        (GenericClass(a=1), GenericClass(a=1), NoDifference()),
        (GenericClass(a=0), GenericClass(a=1), Edit(".a", 0, 1)),
        (GenericClass(a=0), GenericClass(a=0, b=3), Add(".b", 3)),
        (
            GenericClass(a="a", b="b", c="c"),
            GenericClass(a="a", b="c", d="e"),
            Edit("", GenericClass(a="a", b="b", c="c"), GenericClass(a="a", b="c", d="e")),
        ),
    ],
)
def test_non_recursive_object_difference(a: Any, b: Any, difference: Difference):
    assert Difference.object_difference(a, b) == difference


@pytest.mark.parametrize(
    "a,b,difference",
    [
        ([], [], NoDifference()),
        ([1, 2, 3], [1, 2, 3], NoDifference()),
        ([1, 2, 3], [1, 3, 2], Edit("", [1, 2, 3], [1, 3, 2])),
        ([], [1], Add("[0]", 1)),
        ([1, 2, 3], [5, 1, 2, 3], Add("[0]", 5)),
        ([1, 2, 3], [1, 5, 2, 3], Add("[1]", 5)),
        ([1, 2, 3], [1, 2, 5, 3], Add("[2]", 5)),
        ([1, 2, 3], [1, 2, 3, 5], Add("[3]", 5)),
        ([5, 1, 2, 3], [1, 2, 3], Delete("[0]", 5)),
        ([1, 5, 2, 3], [1, 2, 3], Delete("[1]", 5)),
        ([1, 2, 5, 3], [1, 2, 3], Delete("[2]", 5)),
        ([1, 2, 3, 5], [1, 2, 3], Delete("[3]", 5)),
        ([1, 2, 3], [5, 2, 3], Edit("[0]", 1, 5)),
        ([1, 2, 3], [1, 5, 3], Edit("[1]", 2, 5)),
        ([1, 2, 3], [1, 2, 5], Edit("[2]", 3, 5)),
        ([5, 2, 3], [1, 2, 5], Edit("", [5, 2, 3], [1, 2, 5])),
        ([1, 1, 2, 3], [1, 2, 5], Edit("", [1, 1, 2, 3], [1, 2, 5])),
        ([1, 1, 1, 1], [1, 2, 1, 1], Edit("[1]", 1, 2)),
    ],
)
def test_non_recursive_list_difference(a: Any, b: Any, difference: Difference):
    assert Difference.list_difference(a, b) == difference


@pytest.mark.parametrize(
    "a,b,difference",
    [
        (
            {1: [2, 3, 4], 2: [2], 3: [4, 2]},
            {1: [2, 3], 2: [2, 5], 3: [1, 2]},
            CompoundDifference([Delete("[1][2]", 4), Add("[2][1]", 5), Edit("[3][0]", 4, 1)]),
        ),
        (
            [{1: 2}, {3: 4, 5: 6}, {7: 8, 9: 10}],
            [{1: 2, "a": "b"}, {3: 4, 5: 6}, {7: 8, 9: 10}],
            Add("[0]['a']", "b"),
        ),
        (
            [{1: 2}, {3: 4, 5: 6}, {7: 8, 9: 10}],
            [{1: 2}, {3: 4}, {7: 8, 9: 10}],
            Delete("[1][5]", 6),
        ),
        (
            [{1: 2}, {3: 4, 5: 6}, {7: 8, 9: 10}],
            [{1: 2}, {3: 4, 5: 6}, {7: "b", 9: 10}],
            Edit("[2][7]", 8, "b"),
        ),
        (
            [{1, 2}, {3, 4, 5, 6}, {7, 8, 9}],
            [{1, 2}, {3, 4, 5, 6}, {7, 8, 9, 10}],
            Add("[2].item", 10),
        ),
        (
            [{1, 2}, {3, 4, 5, 6}, {7, 8, 9}],
            [{1, 2}, {3, 4, 5, 6}, {7, 8, 9, 10, 11}],
            Edit("[2]", {7, 8, 9}, {7, 8, 9, 10, 11}),
        ),
        (
            {
                "set": {1, 2, 3},
                "cls": GenericClass(a=1, b=GenericClass(c=2, d=3)),
                "list": [1, 2, 3, 4],
            },
            {
                "set": {1, 3},
                "cls": GenericClass(a=1, b=GenericClass(c=2, d=4)),
                "list": [1, 2, 3, 4, 5],
            },
            CompoundDifference(
                [Delete("['set'].item", 2), Edit("['cls'].b.d", 3, 4), Add("['list'][4]", 5)]
            ),
        ),
    ],
)
def test_recursive_differences(a: Any, b: Any, difference: Difference):
    assert Difference.difference(a, b) == difference


@pytest.mark.parametrize(
    "difference, expected",
    [
        (NoDifference(), False),
        (Edit("name", "old", "new"), True),
        (Add("name", "value"), True),
        (Delete("name", "value"), True),
        (
            CompoundDifference([Edit("name1", "old1", "new1"), Add("name2", "value2")]),
            True,
        ),
    ],
)
def test_bool_conversion(difference: Difference, expected: bool):
    assert bool(difference) == expected
