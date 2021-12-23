from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import stream, text
from sanic.views import HTTPMethodView
from sanic.views import stream as stream_decorator


bp = Blueprint("bp_example")
app = Sanic("Example")


class SimpleView(HTTPMethodView):
    @stream_decorator
    async def post(self, request):
        result = ""
        while True:
            body = await request.stream.get()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)


@app.post("/stream", stream=True)
async def handler(request):
    async def streaming(response):
        while True:
            body = await request.stream.get()
            if body is None:
                break
            body = body.decode("utf-8").replace("1", "A")
            await response.write(body)

    return stream(streaming)


@bp.put("/bp_stream", stream=True)
async def bp_handler(request):
    result = ""
    while True:
        body = await request.stream.get()
        if body is None:
            break
        result += body.decode("utf-8").replace("1", "A")
    return text(result)


async def post_handler(request):
    result = ""
    while True:
        body = await request.stream.get()
        if body is None:
            break
        result += body.decode("utf-8")
    return text(result)


app.blueprint(bp)
app.add_route(SimpleView.as_view(), "/method_view")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
