import argparse
import sys
from typing import Any, Dict

import pytest

from .config import TracingConfig
from .debugger import Debugger
from .test_filter import TestFilter
from .utils import ParserBuilder


def parse_args() -> argparse.Namespace:
    parser_builder = ParserBuilder()
    parser_builder.add_dataclass(TracingConfig)
    parser = parser_builder.build()
    args = parser.parse_args()
    return args


def parse_config() -> TracingConfig:
    args = parse_args()
    return TracingConfig.from_args(args)


def log(input: Any, /, **kwargs: Any):
    """Log debugging information (use like print)."""
    print(input, **kwargs, file=sys.stderr)


def send(annotations: Dict[int, str]):
    """Send back the annotations."""
    for line, annotation in annotations.items():
        print(f"{line}:{annotation}")


def main(config: TracingConfig):
    filepath = config.filepath
    function_name = config.function
    lineno = config.lineno
    potential_tests = TestFilter.get_tests(filepath=filepath, function_name=function_name)
    log(
        f"Found {len(potential_tests)} potential tests: [{','.join(test.name for test in potential_tests)}]"
    )
    debugger = Debugger(filepath, lineno)
    annotations = TestFilter.run_tests(debugger, filepath, function_name)
    log(f"Debugger returned with state {debugger.frame}")
    log(f"Annotating {len(annotations)} lines in {filepath}.")
    send(annotations)


if __name__ == "__main__":
    config = parse_config()
    log(f"Running with Python version {sys.version}")
    log(f"Running with pytest version {pytest.__version__}")
    main(config)
