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
