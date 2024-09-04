import contextlib
import os.path
import sys
from typing import Optional

from .annotation import Annotations
from .config import File, TracingConfig
from .control_index import ControlIndex, ControlIndexBuilder
from .debugger import Debugger
from .function_finder import FunctionFinder, FunctionPosition
from .indent_index import IndentIndex, IndentIndexBuilder
from .line_index import LineIndex, LineIndexBuilder
from .observations import Observations
from .test_filter import TestFilter
from .utils import LineNumber


def annotate(config: TracingConfig) -> tuple[bool, Annotations]:
    file = config.file
    test_name = config.test
    node = config.node

    debugger = Debugger(file, node)
    print("Pytest logs (running tests):")
    with contextlib.redirect_stdout(sys.stderr):
        result, annotations = TestFilter.run_test(debugger=debugger, test_name=test_name)

    return result, annotations


def get_function(source: str, line_number: LineNumber) -> Optional[FunctionPosition]:
    return FunctionFinder.get_function(source, line_number)


def list_tests(filename: str) -> list[str]:
    print("Pytest logs (collecting):")
    with contextlib.redirect_stdout(sys.stderr):
        tests = TestFilter.get_tests()
    # filename:test_name
    return [
        f"{os.path.relpath(test.reportinfo()[0], start=os.path.dirname(filename))}:{test.name}"
        for test in tests
    ]
