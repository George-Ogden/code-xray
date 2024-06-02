import argparse
import contextlib
import sys
from typing import Dict

import pytest

from . import annotate
from .config import TracingConfig
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


def send(annotations: Dict[int, str]):
    """Send back the annotations."""
    for line, annotation in annotations.items():
        print(f"{line}:{annotation}")


def main():
    config = parse_config()
    with contextlib.redirect_stdout(sys.stderr):
        print_versions()
        annotations = annotate(config)
    send(annotations)


def print_versions():
    print(f"Running with Python version {sys.version}")
    print(f"Running with pytest version {pytest.__version__}")


if __name__ == "__main__":
    main()
