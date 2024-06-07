import argparse

from .conftest import MyConfig


def test_config_keys():
    assert set(MyConfig.keys()) == {"attr1", "attr2"}


def test_config_getitem():
    config = MyConfig(attr1=10, attr2="test")
    assert config["attr1"] == 10
    assert config["attr2"] == "test"


def test_config_set_args():
    config = MyConfig(attr1=10, attr2="test")
    args = argparse.Namespace(attr1=20, attr2="updated")
    config.set_args(args)
    assert config.attr1 == 20
    assert config.attr2 == "updated"


def test_config_from_args():
    args = argparse.Namespace(attr1=30, attr2="new_value")
    config = MyConfig.from_args(args)
    assert config.attr1 == 30
    assert config.attr2 == "new_value"


def test_config_to_args():
    config = MyConfig(attr1=40, attr2="another_value")
    assert config.to_args() == [
        "--attr1",
        "40",
        "--attr2",
        "another_value",
    ] or config.to_args() == ["--attr2", "another_value", "--attr1", "40"]
