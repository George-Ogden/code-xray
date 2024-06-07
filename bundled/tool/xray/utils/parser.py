from __future__ import annotations

import argparse
from typing import Any, Optional, Type

from .config import Config


class ParserBuilder:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

    def add_dataclass(self, config: Type[Config]) -> ParserBuilder:
        for key in config.keys():
            additional_options = {}
            if key in config.__annotations__:
                additional_options["type"] = config.__annotations__[key]
            self.add_argument(key, **additional_options)
        return self

    def add_argument(
        self, name: str, default: Optional[Any] = None, **additional_options: Any
    ) -> ParserBuilder:
        if default is not None:
            if type(default) == bool:
                additional_options["action"] = "store_true"
            elif "type" not in additional_options:
                additional_options["type"] = type(default)
        self.parser.add_argument(f"--{name}", default=default, **additional_options)
        return self

    def build(self) -> argparse.ArgumentParser:
        return self.parser
