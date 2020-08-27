import random

from sanic.response import json


try:
    from ujson import loads
except ImportError:
    from json import loads


def test_custom_context(app):
    @app.middleware("request")
    def store(request):
        request.ctx.user = "sanic"
        request.ctx.session = None

    @app.route("/")
    def handler(request):
        # Accessing non-existant key should fail with AttributeError
        try:
            invalid = request.ctx.missing
        except AttributeError as e:
            invalid = str(e)
        return json(
            {
                "user": request.ctx.user,
                "session": request.ctx.session,
                "has_user": hasattr(request.ctx, "user"),
                "has_session": hasattr(request.ctx, "session"),
                "has_missing": hasattr(request.ctx, "missing"),
                "invalid": invalid,
            }
        )

    @app.middleware("response")
    def modify(request, response):
        # Using response-middleware to access request ctx
        try:
            user = request.ctx.user
        except AttributeError as e:
            user = str(e)
        try:
            invalid = request.ctx.missing
        except AttributeError as e:
            invalid = str(e)

        j = loads(response.body)
        j["response_mw_valid"] = user
        j["response_mw_invalid"] = invalid
        return json(j)

    request, response = app.test_client.get("/")
    assert response.json == {
        "user": "sanic",
        "session": None,
        "has_user": True,
        "has_session": True,
        "has_missing": False,
        "invalid": "'types.SimpleNamespace' object has no attribute 'missing'",
        "response_mw_valid": "sanic",
        "response_mw_invalid": "'types.SimpleNamespace' object has no attribute 'missing'",
    }


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
