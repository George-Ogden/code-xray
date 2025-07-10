import pytest

from .colons import escape_colons, unescape_colons


@pytest.mark.parametrize(
    "unescaped,escaped",
    [
        ("filename.py", "filename.py"),
        ("file:with:colons.py", r"file\:with\:colons.py"),
        ("filewithdouble::colons.py", r"filewithdouble\:\:colons.py"),
    ],
)
def test_colon_escape(
    unescaped: str,
    escaped: str,
):
    assert escape_colons(unescaped) == escaped
    assert unescape_colons(escaped) == unescaped
