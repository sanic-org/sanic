import pytest

from sanic import Blueprint, Sanic
from sanic.exceptions import SanicException


@pytest.fixture
def app():
    return Sanic("my_app")


@pytest.fixture
def bp(app):
    return Blueprint("my_bp")


def test_app_str(app):
    assert str(app) == "<Sanic my_app>"


def test_app_repr(app):
    assert repr(app) == 'Sanic(name="my_app")'


def test_bp_str(bp):
    assert str(bp) == "<Blueprint my_bp>"


def test_bp_repr(bp):
    assert repr(bp) == (
        'Blueprint(name="my_bp", url_prefix=None, host=None, '
        "version=None, strict_slashes=None)"
    )


def test_bp_repr_with_values(bp):
    bp.host = "example.com"
    bp.url_prefix = "/foo"
    bp.version = 3
    bp.strict_slashes = True
    assert repr(bp) == (
        'Blueprint(name="my_bp", url_prefix="/foo", host="example.com", '
        "version=3, strict_slashes=True)"
    )


@pytest.mark.parametrize(
    "name",
    (
        "something",
        "some-thing",
        "some_thing",
        "Something",
        "SomeThing",
        "Some-Thing",
        "Some_Thing",
        "SomeThing123",
        "something123",
        "some-thing123",
        "some_thing123",
        "some-Thing123",
        "some_Thing123",
    ),
)
def test_names_okay(name):
    app = Sanic(name)
    bp = Blueprint(name)

    assert app.name == name
    assert bp.name == name


@pytest.mark.parametrize(
    "name",
    (
        "123something",
        "some thing",
        "something!",
    ),
)
def test_names_not_okay(name):
    app_message = (
        f"Sanic instance named '{name}' uses an invalid format. Names must "
        "begin with a character and may only contain alphanumeric "
        "characters, _, or -."
    )
    bp_message = (
        f"Blueprint instance named '{name}' uses an invalid format. Names "
        "must begin with a character and may only contain alphanumeric "
        "characters, _, or -."
    )

    with pytest.raises(SanicException, match=app_message):
        Sanic(name)

    with pytest.raises(SanicException, match=bp_message):
        Blueprint(name)
