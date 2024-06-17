import os.path

import pytest

from . import IndentIndexBuilder
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
                10: 8,
                13: 8,
                14: 8,
                15: 12,
                16: 16,
                17: 16,
                18: 16,
                19: 16,
                20: 16,
                21: 16,
                22: 8,
                25: 8,
                26: 8,
            },
        ),
        (
            "tests/edge_cases.py",
            {
                1: 4,
                2: 4,
                3: 4,
                6: 4,
                7: 4,
                9: 4,
                10: 4,
                11: 4,
                12: 4,
                15: 4,
                16: 8,
                17: 8,
                19: 8,
                20: 12,
                21: 12,
                23: 8,
                24: 8,
                25: 8,
                26: 8,
                27: 8,
                28: 8,
                30: 8,
                32: 8,
                34: 4,
            },
        ),
    ],
)
def test_indent_index_builder(filename: str, partial_index: dict[int, int]):
    """`partial_index` contains all line numbers that are relevant for the function"""
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        source = f.read()

    index = IndentIndexBuilder.build_index(source)

    # Check everything is correct.
    for k, v in partial_index.items():
        assert index[LineNumber[1](k)] == v
