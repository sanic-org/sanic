from sanic.testing import SanicASGITestClient


def test_asgi_client_instantiation(app):
    assert isinstance(app.asgi_client, SanicASGITestClient)
