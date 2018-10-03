import pytest

from sanic import Sanic


@pytest.fixture
def app(request):
    return Sanic(request.node.name)
