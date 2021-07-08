import pytest

from sanic import Blueprint, Sanic


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
        f"Sanic instance named '{name}' uses a format that isdeprecated. "
        "Starting in version 21.12, Sanic objects must be named only using "
        "alphanumeric characters, _, or -."
    )
    bp_message = (
        f"Blueprint instance named '{name}' uses a format that isdeprecated. "
        "Starting in version 21.12, Blueprint objects must be named only using "
        "alphanumeric characters, _, or -."
    )

    with pytest.warns(DeprecationWarning) as app_e:
        app = Sanic(name)

    with pytest.warns(DeprecationWarning) as bp_e:
        bp = Blueprint(name)

    assert app.name == name
    assert bp.name == name

    assert app_e[0].message.args[0] == app_message
    assert bp_e[0].message.args[0] == bp_message
