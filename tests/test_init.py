from importlib import import_module

import pytest


@pytest.mark.parametrize(
    "item",
    (
        "__version__",
        "Sanic",
        "Blueprint",
        "HTTPMethod",
        "HTTPResponse",
        "Request",
        "Websocket",
        "empty",
        "file",
        "html",
        "json",
        "redirect",
        "text",
    ),
)
def test_imports(item):
    import_module("sanic", item)
