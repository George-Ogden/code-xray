import ast
from dataclasses import dataclass

from .utils import Config


@dataclass
class File:
    filepath: str
    source: str


@dataclass
class TracingConfig(Config):
    file: File
    node: ast.FunctionDef
    test: str
