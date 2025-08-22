import sys
from typing import Any

import pytest


def requires_modern_python(*test_case: Any):
    should_skip = tuple(sys.version_info) < (3, 12, 0)
    marks = []
    if should_skip:
        marks.append(pytest.mark.skip)
    return pytest.param(*test_case, marks=marks)
