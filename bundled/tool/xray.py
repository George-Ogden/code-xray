import ast
import os.path
from typing import Optional

import pytest
from pygls.workspace import text_document


class FunctionFinder(ast.NodeVisitor):
    """Find the function defined on the given line (1-based indexed)."""

    class FunctionNodeFoundException(Exception):
        def __init__(self, node: ast.FunctionDef):
            self.node = node

    def __init__(self, lineno: int):
        self.lineno = lineno

    def visit_FunctionDef(self, node):
        if node.lineno == self.lineno:
            raise FunctionFinder.FunctionNodeFoundException(node)

    @classmethod
    def find_function(cls, filepath: str, lineno: int) -> Optional[str]:
        """Return the function name for the function defined in `filename` on line `lineno` (0-indexed)."""
        document = text_document.TextDocument(filepath)
        source = document.source
        tree = ast.parse(source)

        name: Optional[str] = None
        try:
            FunctionFinder(lineno=lineno + 1).visit(tree)
        except FunctionFinder.FunctionNodeFoundException as e:
            name = e.node.name

        return name


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
