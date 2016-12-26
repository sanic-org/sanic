from sanic import Sanic
from sanic.server import HttpProtocol
from sanic.response import text
from sanic.utils import sanic_endpoint_test

app = Sanic('test_custom_porotocol')


class CustomHttpProtocol(HttpProtocol):

    def write_response(self, response):
        if isinstance(response, str):
            response = text(response)
        self.transport.write(
            response.output(self.request.version)
        )
        self.transport.close()


@app.route('/1')
async def handler_1(request):
    return 'OK'


def test_use_custom_protocol():
    server_kwargs = {
        'protocol': CustomHttpProtocol
    }
    request, response = sanic_endpoint_test(app, uri='/1',
                                            server_kwargs=server_kwargs)
    assert response.status == 200
    assert response.text == 'OK'
