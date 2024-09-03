from __future__ import annotations

from typing import Literal, Optional

import pytest

from .annotation import Annotations
from .debugger import Debugger


class TestFilter:
    def __init__(self, test_name: Optional[str] = None, debugger: Optional[Debugger] = None):
        self.test_name = test_name
        self.tests: list[pytest.Item] = []
        self.debugger = debugger

    def _filter(self, session: pytest.Session, test: pytest.Function) -> bool:
        return self.test_name is None or test.name == self.test_name

    def pytest_collection_modifyitems(
        self, session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
    ) -> Optional[Literal[True]]:
        selected_test = (test for test in items if self._filter(session, test))
        items[:] = selected_test

        session.items = items
        session.testscollected = len(session.items)
        self.tests = items
        if self.debugger is None:
            return True

    def collect_tests(self):
        pytest.main(
            ["--co"],
            plugins=[self],
        )

    @classmethod
    def get_tests(cls) -> list[pytest.Item]:
        """Return a list of collected items."""
        plugin = cls()
        plugin.collect_tests()
        return plugin.tests

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_runtest_call(self, item: pytest.Item):
        if self.debugger is not None:
            self.debugger.set_trace()
        result = yield
        if self.debugger is not None:
            self.debugger.set_quit()
        return result

    def collect_and_run_test(self):
        pytest.main("--ignore=xray".split(), plugins=[self])

    @classmethod
    def run_test(cls, debugger: Debugger, test_name: str) -> Annotations:
        plugin = cls(test_name=test_name, debugger=debugger)
        plugin.collect_and_run_test()
        return debugger.get_annotations()
