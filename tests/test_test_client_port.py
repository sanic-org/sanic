import socket

from sanic.testing import PORT, SanicTestClient
from sanic.response import json, text

# ------------------------------------------------------------ #
#  UTF-8
# ------------------------------------------------------------ #


def test_test_client_port_none(app):
    @app.get('/get')
    def handler(request):
        return text('OK')

    test_client = SanicTestClient(app, port=None)

    request, response = test_client.get('/get')
    assert response.text == 'OK'

    request, response = test_client.post('/get')
    assert response.status == 405


def test_test_client_port_default(app):
    @app.get('/get')
    def handler(request):
        return json(request.transport.get_extra_info('sockname')[1])

    test_client = SanicTestClient(app)
    assert test_client.port == PORT

    request, response = test_client.get('/get')
    assert response.json == PORT
