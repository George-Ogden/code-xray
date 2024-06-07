from . import ParserBuilder
from .conftest import MyConfig


def test_parser_add_argument():
    builder = ParserBuilder()
    builder.add_argument("test_arg", default=42)
    parser = builder.build()
    args = parser.parse_args(["--test_arg", "100"])
    assert args.test_arg == 100


def test_parser_add_argument_with_type():
    builder = ParserBuilder()
    builder.add_argument("test_arg", type=str)
    parser = builder.build()
    args = parser.parse_args(["--test_arg", "hello"])
    assert args.test_arg == "hello"


def test_parser_add_argument_boolean():
    builder = ParserBuilder()
    builder.add_argument("test_bool", default=False)
    parser = builder.build()
    args = parser.parse_args(["--test_bool"])
    assert args.test_bool is True


def test_parser_add_dataclass():
    builder = ParserBuilder()
    builder.add_dataclass(MyConfig)
    parser = builder.build()
    args = parser.parse_args(["--attr1", "123", "--attr2", "test_string"])
    assert args.attr1 == 123
    assert args.attr2 == "test_string"
