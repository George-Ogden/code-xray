from dataclasses import dataclass

from . import Config


@dataclass
class MyConfig(Config):
    attr1: int
    attr2: str
