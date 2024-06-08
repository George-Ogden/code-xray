import contextlib
import sys
from typing import Any, Dict, List

from .annotation import Annotations
from .config import TracingConfig
from .debugger import Debugger
from .function_finder import FunctionFinder
from .test_filter import TestFilter


def annotate(config: TracingConfig) -> Annotations:
    filepath = config.filepath
    function_name = config.function
    lineno = config.lineno

    # Redirect the stdout to the stderr.
    redirection = contextlib.redirect_stdout(sys.stderr)

    print("Pytest logs (collecting):")
    with redirection:
        potential_tests = TestFilter.get_tests(filepath=filepath, function_name=function_name)
    print(
        f"Found {len(potential_tests)} potential tests: [{','.join(test.name for test in potential_tests)}]"
    )

    debugger = Debugger(filepath, lineno)
    print("Pytest logs (running tests):")
    with redirection:
        annotations = TestFilter.run_tests(debugger, filepath, function_name)

    print(f"Annotating {annotations.line_count} lines in {filepath}.")
    return annotations
