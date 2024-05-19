from __future__ import annotations

import os.path

import pytest


class TestFilter:
    def __init__(self, filepath: str, function_name: str):
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
    ):
        session.items = [test for test in items if self._filter(session, test)]
        session.testscollected = len(session.items)
        self.tests = session.items
        return session

    def collect_tests(self):
        pytest.main(["-qq", "--co"], plugins=[self])

    @classmethod
    def get_tests(cls, filepath: str, function_name: str) -> list[pytest.Item]:
        plugin = cls(filepath=filepath, function_name=function_name)
        plugin.collect_tests()
        return plugin.tests
