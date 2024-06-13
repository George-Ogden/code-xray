import os.path

import pytest

from . import FunctionFinder
from .utils import LineNumber


@pytest.mark.parametrize(
    "filename,lineno,name",
    [
        ("tests/quicksort.py", 1, "unused_fn1"),
        ("tests/quicksort.py", 4, "sort"),
        ("tests/quicksort.py", 28, "unused_fn2"),
        ("tests/edge_cases.py", 1, "main"),
    ],
)
def test_function_finder(filename: str, lineno: int, name: str):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        source = f.read()

    line_number = LineNumber[1](lineno)
    assert FunctionFinder.find_function(source, line_number).name == name
