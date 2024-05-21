from __future__ import annotations

import os.path
from typing import Literal, Optional

import pytest

from .debugger import Debugger


class TestFilter:
    def __init__(self, filepath: str, function_name: str, debugger: Optional[Debugger] = None):
        root, extension = os.path.splitext(filepath)
        dirname, basename = os.path.split(root)
        self.acceptable_filepaths = {
            f"{root}_test{extension}",
            f"{root}_tests{extension}",
            os.path.join(dirname, f"test_{basename}{extension}"),
        }
        self.acceptable_function_names = {
            f"test_{function_name}",
            f"{function_name}_test",
        }
        self.tests: list[pytest.Item] = []
        self.debugger = debugger

    def _filter(self, session: pytest.Session, test: pytest.Function) -> bool:
        function_name = test.originalname
        filename, line_number, test_name = test.location
        filepath = os.path.abspath(filename)
        return (
            filepath in self.acceptable_filepaths
            and function_name in self.acceptable_function_names
        )

    def pytest_collection_modifyitems(
        self, session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
    ) -> Optional[Literal[True]]:
        items[:] = [test for test in items if self._filter(session, test)]
        session.items = items
        session.testscollected = len(session.items)
        self.tests = items
        if self.debugger is None:
            return True

    def collect_tests(self):
        pytest.main(["-qq", "--co"], plugins=[self])

    @classmethod
    def get_tests(cls, filepath: str, function_name: str) -> list[pytest.Item]:
        """Return a list of collected items."""
        plugin = cls(filepath=filepath, function_name=function_name)
        plugin.collect_tests()
        return plugin.tests

    def pytest_runtest_setup(self, item: pytest.Item):
        if self.debugger is not None:
            self.debugger.set_trace()

    def pytest_runtest_teardown(self, item: pytest.Item):
        if self.debugger is not None:
            self.debugger.set_quit()

    def collect_and_run_tests(self):
        pytest.main(["-qq"], plugins=[self])

    @classmethod
    def run_tests(
        cls, debugger: Debugger, filepath: str, function_name: str
    ) -> dict[int, list[str]]:
        plugin = cls(filepath=filepath, function_name=function_name, debugger=debugger)
        plugin.collect_and_run_tests()
        return debugger.difference_logs
