import argparse
import sys
from dataclasses import dataclass
from typing import Any, Dict

from .debugger import Debugger
from .test_filter import TestFilter
from .utils import Config, ParserBuilder


@dataclass
class TracingConfig(Config):
    filepath: str
    function: str
    lineno: int


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
    log(debugger.frame)
    log(f"Annotating {len(annotations)} lines in {filepath}.")
    send(annotations)


if __name__ == "__main__":
    config = parse_config()
    main(config)
