import os.path

import pytest

from . import FunctionFinder
from .utils import LineNumber


@pytest.mark.parametrize(
    "filename,lineno,name",
    [
        ("tests/quicksort.py", 1, "unused_fn1"),
        ("tests/quicksort.py", 2, "unused_fn1"),
        ("tests/quicksort.py", 4, "sort"),
        ("tests/quicksort.py", 5, "sort"),
        ("tests/quicksort.py", 8, "sort"),
        ("tests/quicksort.py", 26, "sort"),
        ("tests/quicksort.py", 28, "unused_fn2"),
        ("tests/edge_cases.py", 1, "main"),
        ("tests/classes.py", 3, "TestClass.static"),
        ("tests/classes.py", 4, "TestClass.static"),
        ("tests/classes.py", 7, "TestClass.class_"),
        ("tests/classes.py", 8, "TestClass.class_"),
        ("tests/classes.py", 10, "TestClass.instance"),
        ("tests/classes.py", 11, "TestClass.instance"),
        ("tests/classes.py", 14, "TestClass.InnerClass.method"),
        ("tests/classes.py", 15, "TestClass.InnerClass.method"),
        ("tests/classes.py", 18, "external"),
        ("tests/classes.py", 19, "external"),
    ],
)
def test_function_finder(filename: str, lineno: int, name: str):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        source = f.read()

    line_number = LineNumber[1](lineno)
    assert FunctionFinder.find_function(source, line_number).name == name.split(".")[-1]

    assert FunctionFinder.get_function(source, line_number).name == name
