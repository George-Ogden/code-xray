from __future__ import annotations

import argparse
import contextlib
import os
from dataclasses import asdict
from typing import Any, Callable, List, Optional, Self, Type, TypeVar


class Config:
    @classmethod
    def keys(cls) -> List[str]:
        return cls.__match_args__

    def __getitem__(self, key) -> Any:
        return getattr(self, key)

    def set_args(self, args: argparse.Namespace) -> Self:
        for attribute in asdict(self):
            value = getattr(self, attribute)
            if isinstance(value, Config):
                value.set_args(args)
            elif attribute in args:
                setattr(self, attribute, getattr(args, attribute))
        return self

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> Self:
        args = vars(args)
        attributes = {key: args.pop(key) for key in cls.keys()}
        config = cls(**attributes)
        return config.set_args(args)


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


T = TypeVar("T")


def silence_output(f: Callable[..., T]) -> Callable[..., T]:
    """Redirect the stdout to /dev/null"""

    def wrapper(*args: Any, **kwargs: Any) -> T:
        with open(os.devnull, "w") as devnull:
            with contextlib.redirect_stdout(devnull):
                return f(*args, **kwargs)

    return wrapper
