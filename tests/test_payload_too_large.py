from sanic.exceptions import PayloadTooLarge
from sanic.response import text


def test_payload_too_large_from_error_handler(app):
    app.config.REQUEST_MAX_SIZE = 1

    @app.route("/1")
    async def handler1(request):
        return text("OK")

    @app.exception(PayloadTooLarge)
    def handler_exception(request, exception):
        return text("Payload Too Large from error_handler.", 413)

    response = app.test_client.get("/1", gather_request=False)
    assert response.status == 413
    assert response.text == "Payload Too Large from error_handler."


def test_payload_too_large_at_data_received_default(app):
    app.config.REQUEST_MAX_SIZE = 1

    @app.route("/1")
    async def handler2(request):
        return text("OK")

    response = app.test_client.get("/1", gather_request=False)
    assert response.status == 413
    assert "Request header" in response.text


def test_payload_too_large_at_on_header_default(app):
    app.config.REQUEST_MAX_SIZE = 500

    @app.post("/1")
    async def handler3(request):
        return text("OK")

    data = "a" * 1000
    response = app.test_client.post("/1", gather_request=False, data=data)
    assert response.status == 413
    assert "Request body" in response.text
