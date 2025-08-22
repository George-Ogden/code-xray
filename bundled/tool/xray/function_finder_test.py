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
        ("tests/edge_cases.py", 46, "comment"),
        ("tests/edge_cases.py", 50, "space"),
        ("tests/edge_cases.py", 56, "test_bar"),
        ("tests/edge_cases.py", 61, "extra_space"),
        ("tests/modern_python.py", 1, "parametric"),
        ("tests/modern_python.py", 4, "bounded_parametric"),
        ("tests/classes.py", 3, "TestClass.static"),
        ("tests/classes.py", 4, "TestClass.static"),
        ("tests/classes.py", 7, "TestClass.class_"),
        ("tests/classes.py", 8, "TestClass.class_"),
        ("tests/classes.py", 10, "TestClass.instance"),
        ("tests/classes.py", 11, "TestClass.instance"),
        ("tests/classes.py", 14, "TestClass.InnerClass.method"),
        ("tests/classes.py", 15, "TestClass.InnerClass.method"),
        ("tests/classes.py", 18, "TestClass.docstring"),
        ("tests/classes.py", 20, "TestClass.docstring"),
        ("tests/classes.py", 22, "TestClass.single_line"),
        ("tests/classes.py", 25, "TestClass.multiline"),
        ("tests/classes.py", 29, "TestClass.multiline"),
        ("tests/classes.py", 32, "TestClass.multiline_docstring"),
        ("tests/classes.py", 38, "TestClass.multiline_docstring"),
        ("tests/classes.py", 41, "external"),
        ("tests/classes.py", 42, "external"),
        ("tests/classes.py", 46, "multiline"),
    ],
)
def test_function_finder(filename: str, lineno: int, name: str):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        source = f.read()

    line_number = LineNumber[1](lineno)
    assert FunctionFinder.find_function(source, line_number).name == name.split(".")[-1]

    assert FunctionFinder.get_function(source, line_number).name == name


@pytest.mark.parametrize(
    "filename,linenos",
    [
        ("tests/quicksort.py", [1, 4, 28]),
        ("tests/edge_cases.py", [1, 46, 50, 56, 61]),
        ("tests/modern_python.py", [1, 4]),
        ("tests/classes.py", [3, 7, 10, 14, 18, 22, 25, 32, 41, 46]),
    ],
)
def test_function_finder_list(filename: str, linenos: list[int]):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        source = f.read()

    assert FunctionFinder.find_all_functions(source) == [
        LineNumber[1](lineno) for lineno in linenos
    ]
