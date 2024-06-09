import contextlib
import sys
from typing import Any, Dict, List

from .annotation import Annotations
from .config import File, TracingConfig
from .debugger import Debugger
from .function_finder import FunctionFinder
from .line_index import Index, LineIndexBuilder
from .test_filter import TestFilter


def annotate(config: TracingConfig) -> Annotations:
    file = config.file
    function_name = config.function
    lineno = config.lineno
    filepath = file.filepath

    # Redirect the stdout to the stderr.
    redirection = contextlib.redirect_stdout(sys.stderr)

    print("Pytest logs (collecting):")
    with redirection:
        potential_tests = TestFilter.get_tests(filepath=filepath, function_name=function_name)
    print(
        f"Found {len(potential_tests)} potential tests: [{','.join(test.name for test in potential_tests)}]"
    )

    debugger = Debugger(file, lineno)
    print("Pytest logs (running tests):")
    with redirection:
        annotations = TestFilter.run_tests(
            debugger=debugger, filepath=filepath, function_name=function_name
        )

    print(f"Annotating {annotations.line_count} lines in {filepath}.")
    return annotations
