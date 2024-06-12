import os

import pytest

from . import ControlIndexBuilder, FunctionFinder
from .utils import LineNumber


@pytest.mark.parametrize(
    "filename,partial_index",
    [
        (
            "tests/quicksort.py",
            {
                4: 4,
                7: 4,
                8: 4,
                9: 4,
                10: 4,
                11: 4,
                12: 4,
                13: 4,
                14: 4,
                15: 15,
                16: 15,
                17: 15,
                18: 15,
                19: 15,
                20: 15,
                21: 15,
                22: 4,
                23: 4,
                24: 4,
                26: 4,
            },
        )
    ],
)
def test_control_index_builder(filename: str, partial_index: dict[int, int]):
    """`partial_index` contains all line numbers that are relevant for the function"""
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        source = f.read()

    node = FunctionFinder.find_function(source, LineNumber[1](4))
    index = ControlIndexBuilder.build_index(node)

    # Check everything is correct.
    for k, v in partial_index.items():
        assert index[LineNumber[1](k)].line_number == LineNumber[1](v)
