import random

from sanic.response import json


try:
    from ujson import loads
except ImportError:
    from json import loads


def test_storage(app):
    @app.middleware("request")
    def store(request):
        try:
            request["foo"]
        except KeyError:
            pass
        user = request.get("user", "sanic")  # No _storagedict yet -> default
        request["user"] = user
        request["bar"] = request["user"]
        sidekick = request.get("sidekick", "tails")  # Item missing -> default
        request["sidekick"] = sidekick
        del request["sidekick"]

    @app.route("/")
    def handler(request):
        return json(
            {
                "user": request.get("user"),
                "sidekick": request.get("sidekick"),
                "has_bar": "bar" in request,
                "has_sidekick": "sidekick" in request,
            }
        )

    request, response = app.test_client.get("/")

    assert response.json == {
        "user": "sanic",
        "sidekick": None,
        "has_bar": True,
        "has_sidekick": False,
    }
    response_json = loads(response.text)
    assert response_json["user"] == "sanic"
    assert response_json.get("sidekick") is None


def test_app_injection(app):
    expected = random.choice(range(0, 100))

    @app.listener("after_server_start")
    async def inject_data(app, loop):
        app.injected = expected

    @app.get("/")
    async def handler(request):
        return json({"injected": request.app.injected})

    request, response = app.test_client.get("/")

    response_json = loads(response.text)
    assert response_json["injected"] == expected
