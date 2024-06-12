import ast
from dataclasses import dataclass

from .utils import Config, LineNumber


@dataclass
class File:
    filepath: str
    source: str


@dataclass
class TracingConfig(Config):
    file: File
    function: str
    lineno: LineNumber[0]
    node: ast.FunctionDef
