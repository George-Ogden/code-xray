from __future__ import annotations

import contextlib
import os
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def silence_output(f: Callable[..., T]) -> Callable[..., T]:
    """Redirect the stdout to /dev/null"""

    def wrapper(*args: Any, **kwargs: Any) -> T:
        with open(os.devnull, "w") as devnull:
            with contextlib.redirect_stdout(devnull):
                return f(*args, **kwargs)

    return wrapper
