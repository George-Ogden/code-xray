import contextlib
import os.path
import sys

from .annotation import Annotations
from .config import File, TracingConfig
from .control_index import ControlIndex, ControlIndexBuilder
from .debugger import Debugger
from .function_finder import FunctionFinder
from .indent_index import IndentIndex, IndentIndexBuilder
from .line_index import LineIndex, LineIndexBuilder
from .observations import Observations
from .test_filter import TestFilter


def annotate(config: TracingConfig) -> Annotations:
    file = config.file
    test_name = config.test
    node = config.node

    debugger = Debugger(file, node)
    print("Pytest logs (running tests):")
    with contextlib.redirect_stdout(sys.stderr):
        annotations = TestFilter.run_test(debugger=debugger, test_name=test_name)

    return annotations


def list_tests(filename: str) -> list[str]:
    print("Pytest logs (collecting):")
    with contextlib.redirect_stdout(sys.stderr):
        tests = TestFilter.get_tests()
    # filename:test_name
    return [
        f"{os.path.relpath(test.reportinfo()[0], start=os.path.dirname(filename))}:{test.name}"
        for test in tests
    ]
