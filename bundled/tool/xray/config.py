from dataclasses import dataclass

from .utils import Config, LineNumber


@dataclass
class TracingConfig(Config):
    filepath: str
    function: str
    lineno: LineNumber[0]
