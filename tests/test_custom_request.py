from io import BytesIO

from sanic import Sanic
from sanic.request import Request
from sanic.response import json_dumps, text


class CustomRequest(Request):
    """Alternative implementation for loading body (non-streaming handlers)"""

    async def receive_body(self):
        buffer = BytesIO()
        async for data in self.stream:
            buffer.write(data)
        self.body = buffer.getvalue().upper()
        buffer.close()


def test_custom_request():
    app = Sanic(name=__name__, request_class=CustomRequest)

    @app.route("/post", methods=["POST"])
    async def post_handler(request):
        return text("OK")

    @app.route("/get")
    async def get_handler(request):
        return text("OK")

    payload = {"test": "OK"}
    headers = {"content-type": "application/json"}

    request, response = app.test_client.post(
        "/post", data=json_dumps(payload), headers=headers
    )

    assert request.body == b'{"TEST":"OK"}'
    assert request.json.get("TEST") == "OK"
    assert response.text == "OK"
    assert response.status == 200

    request, response = app.test_client.get("/get")

    assert request.body == b""
    assert response.text == "OK"
    assert response.status == 200
