import asyncio

from asyncio import CancelledError

import pytest

from sanic import Request, Sanic, json


def test_can_raise_in_handler(app: Sanic):
    @app.get("/")
    async def handler(request: Request):
        raise CancelledError("STOP!!")

    @app.exception(CancelledError)
    async def handle_cancel(request: Request, exc: CancelledError):
        return json({"message": exc.args[0]}, status=418)

    _, response = app.test_client.get("/")
    assert response.status == 418
    assert response.json["message"] == "STOP!!"
