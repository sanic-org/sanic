from os import getenv

from sentry_sdk import init as sentry_init
from sentry_sdk.integrations.sanic import SanicIntegration

from sanic import Sanic
from sanic.response import json


sentry_init(
    dsn=getenv("SENTRY_DSN"),
    integrations=[SanicIntegration()],
)

app = Sanic("Example")


# noinspection PyUnusedLocal
@app.route("/working")
async def working_path(request):
    return json({"response": "Working API Response"})


# noinspection PyUnusedLocal
@app.route("/raise-error")
async def raise_error(request):
    raise Exception("Testing Sentry Integration")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=getenv("PORT", 8080))
