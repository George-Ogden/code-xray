import contextlib
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
    function_name = config.function
    lineno = config.lineno
    filepath = file.filepath
    node = config.node

    # Redirect the stdout to the stderr.
    redirection = contextlib.redirect_stdout(sys.stderr)

    print("Pytest logs (collecting):")
    with redirection:
        potential_tests = TestFilter.get_tests(filepath=filepath, function_name=function_name)
    print(
        f"Found {len(potential_tests)} potential tests: [{','.join(test.name for test in potential_tests)}]"
    )

    debugger = Debugger(file, node)
    print("Pytest logs (running tests):")
    with redirection:
        annotations = TestFilter.run_tests(
            debugger=debugger, filepath=filepath, function_name=function_name
        )

    return annotations
