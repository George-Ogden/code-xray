import itertools

import pytest

from . import ControlIndex, Differences
from .control_index import ControlNode
from .difference import NoDifference
from .utils import LineNumber, Position


@pytest.mark.parametrize(
    "positions,expected_timestamps,control_index",
    [
        ([(1, 4), (2, 4), (3, 4)] * 2, [(1,), (2,)], {1: 1, 2: 1, 3: 1}),
        (
            [(1, 4), (2, 8), (3, 8), (2, 8), (3, 8)] * 2,
            [(1,), (1, 1), (1, 2), (2,), (2, 1), (2, 2)],
            {1: 1, 2: 2, 3: 2},
        ),
        (
            [
                (1, 4),
                (2, 8),
                (3, 8),
                (1, 4),
                (2, 8),
                (5, 8),
                (1, 4),
                (2, 8),
                (3, 8),
            ],
            [(1,), (2,), (3,)],
            {1: 1, 2: 1, 3: 1, 4: 1, 5: 1},
        ),
        (
            [(1, 0), (2, 4), (3, 4), (2, 4), (3, 4)],
            [(), (1,), (2,)],
            {1: 0, 2: 2, 3: 2},
        ),
    ],
)
def test_difference_groups(positions, expected_timestamps, control_index: ControlIndex):
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
    Positions contains (lineno, character) for the order of visited lines.
    Expected_timestamps contains timestamps (tuple of (block, timestamp_id)) that we expect to see.
    """
    differences = Differences()
    for lineno, character in positions:
        position = Position(LineNumber[1](lineno), character)
        differences.add(position, NoDifference())

    node = None
    index = {}
    for line, target in itertools.chain([(0, None)], control_index.items()):
        line_number = LineNumber[1](line)
        if target is None:
            node = ControlNode(None, line_number=line_number)
        elif line == target:
            node = ControlNode(node, line_number=line_number)
        index[line_number] = node

    groups = differences.group(index)

    # Check the timestamps match.
    assert set(groups.keys()) == set(expected_timestamps)

    # Check all the positions are there.
    assert sum([len(group) for group in groups.values()]) == len(positions)
