import pytest

from . import LineNumber


def test_LineNumber0_properties():
    ln = LineNumber[0](5)
    assert ln.zero == 5
    assert ln.one == 6


def test_LineNumber1_properties():
    ln = LineNumber[1](5)
    assert ln.zero == 4
    assert ln.one == 5


def test_LineNumber_str():
    ln = LineNumber[0](5)
    assert str(ln) == "5"


def test_LineNumber_repr():
    ln = LineNumber[1](5)
    assert repr(ln) == "(1)5"


def test_LineNumber0_add():
    ln = LineNumber[0](5)
    ln2 = ln + 3
    assert ln2.zero == 8
    assert ln2.one == 9
    assert isinstance(ln2, LineNumber[0])


def test_LineNumber1_add():
    ln = LineNumber[1](2)
    ln2 = ln + 3
    assert ln2.zero == 4
    assert ln2.one == 5
    assert isinstance(ln2, LineNumber[1])


def test_LineNumber_eq():
    ln0 = LineNumber[0](1)
    ln1 = LineNumber[1](2)
    assert ln0 == ln1


def test_LineNumber_neq():
    ln0 = LineNumber[0](1)
    ln1 = LineNumber[1](1)
    assert ln0 != ln1


def test_LineNumber_cls_getitem_zero():
    ln_cls = LineNumber[0]
    assert ln_cls is LineNumber[0]


def test_LineNumber_cls_getitem_one():
    ln_cls = LineNumber[1]
    assert ln_cls is LineNumber[1]


def test_LineNumber_cls_getitem_invalid():
    with pytest.raises(ValueError):
        LineNumber[2]


def test_LineNumber_cls_getitem_twice():
    with pytest.raises(TypeError):
        LineNumber[0][0]
