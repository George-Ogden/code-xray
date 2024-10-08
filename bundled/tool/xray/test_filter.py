from __future__ import annotations

import os.path
from typing import Literal, Optional

import pytest

from .annotation import Annotations
from .debugger import Debugger


class TestFilter:
    def __init__(self, test_name: Optional[str] = None, debugger: Optional[Debugger] = None):
        if test_name is None:
            self.test_name = None
        else:
            *filenames, self.test_name = test_name.split(":")
            self.filename = ":".join(filenames)
            self.status = None
        self.tests: list[pytest.Item] = []
        self.debugger = debugger

    def _filter(self, session: pytest.Session, test: pytest.Function) -> bool:
        filename, _, _ = test.reportinfo()
        return self.test_name is None or (
            os.path.samefile(self.filename, filename) and test.name == self.test_name
        )

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

    def pytest_runtest_logreport(self, report: pytest.TestReport):
        if report.when == "call":
            match report.outcome:
                case "passed":
                    self.status = True
                case "failed":
                    self.status = False

    def collect_and_run_test(self):
        pytest.main("--ignore=xray".split(), plugins=[self])

    @classmethod
    def run_test(cls, debugger: Debugger, test_name: str) -> tuple[bool, Annotations]:
        plugin = cls(test_name=test_name, debugger=debugger)
        plugin.collect_and_run_test()
        return plugin.status, debugger.get_annotations()
