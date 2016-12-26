from sanic import Sanic
from sanic.server import HttpProtocol
from sanic.response import text

app = Sanic(__name__)


class CustomHttpProtocol(HttpProtocol):

    def write_response(self, response):
        if isinstance(response, str):
            response = text(response)
        self.transport.write(
            response.output(self.request.version)
        )
        self.transport.close()


@app.route("/")
async def test(request):
    return 'Hello, world!'


app.run(host="0.0.0.0", port=8000, protocol=CustomHttpProtocol)
