import pytest

from . import Differences
from .difference import NoDifference
from .utils import LineNumber, Position


@pytest.mark.parametrize(
    "positions,expected_timestamps",
    [
        ([(1, 4), (2, 4), (3, 4)] * 2, [((1, 0),), ((1, 1),)]),
        (
            [
                (1, 4),
                (2, 8),
                (3, 8),
                (2, 8),
                (3, 8),
            ]
            * 2,
            [
                ((1, 0),),
                (
                    (1, 0),
                    (2, 0),
                ),
                (
                    (1, 0),
                    (2, 1),
                ),
                ((1, 1),),
                (
                    (1, 1),
                    (2, 0),
                ),
                (
                    (1, 1),
                    (2, 1),
                ),
            ],
        ),
        (
            [(1, 4), (2, 8), (3, 8), (1, 4), (2, 8), (4, 4), (5, 8), (1, 4), (2, 8), (3, 8)],
            [
                ((1, 0),),
                ((1, 1),),
                ((1, 2),),
            ],
        ),
        ([(1, 0), (2, 4), (3, 4), (2, 4), (3, 4)], [((1, 0),), ((1, 1),)]),
    ],
)
def test_difference_groups(positions, expected_timestamps):
    """
    Test 1:
    for i in range(2):
        ...
        ...

    Test 2:
    for i in range(2):
        for j in range(2):
            ...
    Test 3:
    for i in range(3):
        if i % 2 == 0:
            ...
        else:
            ...
    Test 4:
    ...
    for i in range(2):
        ...
    """
    differences = Differences()
    for lineno, character in positions:
        position = Position(LineNumber[1](lineno), character)
        differences.add(position, NoDifference())

    groups = differences.group()
    assert set(groups.keys()) == set(expected_timestamps).union([()])

    assert sum([len(group) for group in groups.values()]) == len(positions) + 1
