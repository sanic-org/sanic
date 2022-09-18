import pytest

from sanic import Sanic
from sanic.log import deprecation


def test_deprecation():
    message = r"\[DEPRECATION v9\.9\] hello"
    with pytest.warns(DeprecationWarning, match=message):
        deprecation("hello", 9.9)


@pytest.mark.parametrize(
    "filter,expected",
    (("default", 1), ("once", 1), ("ignore", 0)),
)
def test_deprecation_filter(app: Sanic, filter, expected, recwarn):
    app.config.DEPRECATION_FILTER = filter
    deprecation("hello", 9.9)
    assert len(recwarn) == expected
