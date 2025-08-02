import pytest

from .line_number import LineNumber
from .position import Position


@pytest.mark.parametrize(
    "position, expected",
    [
        (Position(LineNumber[1](25), 4, 5), dict(character=4, line=24)),
        (Position(LineNumber[0](0), 1), dict(character=1, line=0)),
    ],
)
def test_position_to_json(position: Position, expected: dict[str, int]):
    assert expected == position.to_json()
