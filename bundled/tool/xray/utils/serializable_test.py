from . import Serializable


class SimpleSerializable(Serializable):
    def __init__(self, x, y):
        self.x = x
        self.y = y


class NestedSerializable(Serializable):
    def __init__(self, a, b):
        self.a = SimpleSerializable(*a)
        self.b = b


def test_simple_serializable():
    obj = SimpleSerializable(10, "test")
    expected_output = {"x": 10, "y": "test"}
    assert obj.to_json() == expected_output


def test_nested_serializable():
    obj = NestedSerializable((1, "nested"), 20)
    expected_output = {"a": {"x": 1, "y": "nested"}, "b": 20}
    assert obj.to_json() == expected_output


def test_serialize_simple_dict():
    obj = {"key1": "value1", "key2": 2}
    expected_output = {"key1": "value1", "key2": 2}
    assert Serializable.serialize(obj) == expected_output


def test_serialize_with_serializable():
    obj = {"nested": SimpleSerializable(5, "value")}
    expected_output = {"nested": {"x": 5, "y": "value"}}
    assert Serializable.serialize(obj) == expected_output


def test_serialize_non_serializable():
    obj = [1, 2, 3]
    expected_output = [1, 2, 3]
    assert Serializable.serialize(obj) == expected_output
