from io import BytesIO

from sanic import Sanic
from sanic.request import Request
from sanic.response import json_dumps, text


class CustomRequest(Request):
    __slots__ = ("body_buffer",)

    def body_init(self):
        self.body_buffer = BytesIO()

    def body_push(self, data):
        self.body_buffer.write(data)

    def body_finish(self):
        self.body = self.body_buffer.getvalue()
        self.body_buffer.close()


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

    assert isinstance(request.body_buffer, BytesIO)
    assert request.body_buffer.closed
    assert request.body == b'{"test":"OK"}'
    assert request.json.get("test") == "OK"
    assert response.text == "OK"
    assert response.status == 200

    request, response = app.test_client.get("/get")

    assert isinstance(request.body_buffer, BytesIO)
    assert request.body_buffer.closed
    assert request.body == b""
    assert response.text == "OK"
    assert response.status == 200
