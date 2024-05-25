from dataclasses import dataclass

from .utils import Config


@dataclass
class TracingConfig(Config):
    filepath: str
    function: str
    lineno: int
