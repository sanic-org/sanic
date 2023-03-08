from sanic.app import Sanic
from sanic.response import empty
from sanic.signals import Event


def test_handler_operation_order(app: Sanic):
    operations = []

    @app.on_request
    async def on_request(_):
        nonlocal operations
        operations.append(1)

    @app.on_response
    async def on_response(*_):
        nonlocal operations
        operations.append(5)

    @app.get("/")
    async def handler(_):
        nonlocal operations
        operations.append(3)
        return empty()

    @app.signal(Event.HTTP_HANDLER_BEFORE)
    async def handler_before(**_):
        nonlocal operations
        operations.append(2)

    @app.signal(Event.HTTP_HANDLER_AFTER)
    async def handler_after(**_):
        nonlocal operations
        operations.append(4)

    app.test_client.get("/")
    assert operations == [1, 2, 3, 4, 5]
