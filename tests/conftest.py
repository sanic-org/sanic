import sys
import pytest

from sanic import Sanic

if sys.platform in ["win32", "cygwin"]:
    collect_ignore = ["test_worker.py"]


@pytest.fixture
def app(request):
    return Sanic(request.node.name)
