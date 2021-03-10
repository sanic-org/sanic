import sys

from dataclasses import asdict, dataclass
from functools import partial
from json import dumps as sdumps

import pytest


try:
    from ujson import dumps as udumps

    NO_UJSON = False
    DEFAULT_DUMPS = udumps
except ModuleNotFoundError:
    NO_UJSON = True
    DEFAULT_DUMPS = partial(sdumps, separators=(",", ":"))

from sanic import Sanic
from sanic.response import BaseHTTPResponse, json


@dataclass
class Foo:
    bar: str

    def __json__(self):
        return udumps(asdict(self))


@pytest.fixture
def foo():
    return Foo(bar="bar")


@pytest.fixture
def payload(foo):
    return {"foo": foo}


@pytest.fixture(autouse=True)
def default_back_to_ujson():
    yield
    BaseHTTPResponse._dumps = DEFAULT_DUMPS


def test_change_encoder():
    Sanic("...", dumps=sdumps)
    assert BaseHTTPResponse._dumps == sdumps


def test_change_encoder_to_some_custom():
    def my_custom_encoder():
        return "foo"

    Sanic("...", dumps=my_custom_encoder)
    assert BaseHTTPResponse._dumps == my_custom_encoder


@pytest.mark.skipif(NO_UJSON is True, reason="ujson not installed")
def test_json_response_ujson(payload):
    """ujson will look at __json__"""
    response = json(payload)
    assert response.body == b'{"foo":{"bar":"bar"}}'

    with pytest.raises(
        TypeError, match="Object of type Foo is not JSON serializable"
    ):
        json(payload, dumps=sdumps)

    Sanic("...", dumps=sdumps)
    with pytest.raises(
        TypeError, match="Object of type Foo is not JSON serializable"
    ):
        json(payload)


@pytest.mark.skipif(NO_UJSON is True, reason="ujson not installed")
def test_json_response_json():
    """One of the easiest ways to tell the difference is that ujson cannot
    serialize over 64 bits"""
    too_big_for_ujson = 111111111111111111111

    with pytest.raises(OverflowError, match="int too big to convert"):
        json(too_big_for_ujson)

    response = json(too_big_for_ujson, dumps=sdumps)
    assert sys.getsizeof(response.body) == 54

    Sanic("...", dumps=sdumps)
    response = json(too_big_for_ujson)
    assert sys.getsizeof(response.body) == 54
