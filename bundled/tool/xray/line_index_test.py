import os.path

import pytest

from . import FunctionFinder, LineIndexBuilder
from .utils import LineNumber


@pytest.mark.parametrize(
    "filename,partial_index",
    [
        ("tests/quicksort.py:4", {8: 9, 10: 12, 22: 24}),
        ("tests/edge_cases.py:1", {1: 4, 6: 8, 9: 13, 25: 26, 27: 28, 34: 36}),
    ],
)
def test_line_index_builder(filename: str, partial_index: dict[int, int]):
    """`partial_index` contains all line numbers that should be different (one-based indexing)"""
    filename, lineno = filename.split(":")
    line_number = LineNumber[1](int(lineno))

    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        source = f.read()

    node = FunctionFinder.find_function(source, line_number)
    index = LineIndexBuilder.build_index(node)

    # Check everything mismatches or is the same.
    for k, v in index.items():
        assert k == v or partial_index[k.one] == v.one

    # Check that the given items are included.
    for k, v in partial_index.items():
        assert index[LineNumber[1](k)] == LineNumber[1](v)
