from sanic_testing.reusable import ReusableClient

from sanic.response import json, text


def test_no_body_requests(app):
    @app.get("/")
    async def handler(request):
        return json(
            {
                "request_id": str(request.id),
                "connection_id": id(request.conn_info),
            }
        )

    client = ReusableClient(app, port=1234)

    with client:
        _, response1 = client.get("/")
        _, response2 = client.get("/")

    assert response1.status == response2.status == 200
    assert response1.json["request_id"] != response2.json["request_id"]
    assert response1.json["connection_id"] == response2.json["connection_id"]


def test_json_body_requests(app):
    @app.post("/")
    async def handler(request):
        return json(
            {
                "request_id": str(request.id),
                "connection_id": id(request.conn_info),
                "foo": request.json.get("foo"),
            }
        )

    client = ReusableClient(app, port=1234)

    with client:
        _, response1 = client.post("/", json={"foo": True})
        _, response2 = client.post("/", json={"foo": True})

    assert response1.status == response2.status == 200
    assert response1.json["foo"] is response2.json["foo"] is True
    assert response1.json["request_id"] != response2.json["request_id"]
    assert response1.json["connection_id"] == response2.json["connection_id"]


def test_streaming_body_requests(app):
    @app.post("/", stream=True)
    async def handler(request):
        data = [part.decode("utf-8") async for part in request.stream]
        return json(
            {
                "request_id": str(request.id),
                "connection_id": id(request.conn_info),
                "data": data,
            }
        )

    data = ["hello", "world"]

    client = ReusableClient(app, port=1234)

    async def stream(data):
        for value in data:
            yield value.encode("utf-8")

    with client:
        _, response1 = client.post("/", data=stream(data))
        _, response2 = client.post("/", data=stream(data))

    assert response1.status == response2.status == 200
    assert response1.json["data"] == response2.json["data"] == data
    assert response1.json["request_id"] != response2.json["request_id"]
    assert response1.json["connection_id"] == response2.json["connection_id"]


def test_bad_headers(app):
    @app.get("/")
    async def handler(request):
        return text("")

    @app.on_response
    async def reqid(request, response):
        response.headers["x-request-id"] = request.id

    client = ReusableClient(app, port=1234)
    bad_headers = {"bad": "bad" * 5_000}

    with client:
        _, response1 = client.get("/")
        _, response2 = client.get("/", headers=bad_headers)

    assert response1.status == 200
    assert response2.status == 413
    assert (
        response1.headers["x-request-id"] != response2.headers["x-request-id"]
    )
