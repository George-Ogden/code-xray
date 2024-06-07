from __future__ import annotations

import argparse
import itertools
from dataclasses import asdict
from typing import Any, List, Self


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

    def to_args(self) -> List[str]:
        return list(itertools.chain(*((f"--{key}", str(self[key])) for key in self.keys())))
