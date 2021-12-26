import pytest

from sanic.log import deprecation


def test_deprecation():
    message = r"\[DEPRECATION v9\.9\] hello"
    with pytest.warns(DeprecationWarning, match=message):
        deprecation("hello", 9.9)
