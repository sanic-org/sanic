from sanic.response import text
from sanic.server import HttpProtocol


class CustomHttpProtocol(HttpProtocol):
    def write_response(self, response):
        if isinstance(response, str):
            response = text(response)
        self.transport.write(response.output(self.request.version))
        self.transport.close()


def test_use_custom_protocol(app):
    @app.route("/1")
    async def handler_1(request):
        return "OK"

    server_kwargs = {"protocol": CustomHttpProtocol}
    request, response = app.test_client.get("/1", server_kwargs=server_kwargs)
    assert response.status == 200
    assert response.text == "OK"
