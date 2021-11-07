from sanic import Sanic, response, text
from sanic.handlers import ErrorHandler
from sanic.server.async_server import AsyncioServer


HTTP_PORT = 9999
HTTPS_PORT = 8888

http = Sanic("http")
http.config.SERVER_NAME = f"localhost:{HTTP_PORT}"
https = Sanic("https")
https.config.SERVER_NAME = f"localhost:{HTTPS_PORT}"


@https.get("/foo")
def foo(request):
    return text("foo")


@https.get("/bar")
def bar(request):
    return text("bar")


@http.get("/<path:path>")
def proxy(request, path):
    url = request.app.url_for(
        "proxy",
        path=path,
        _server=https.config.SERVER_NAME,
        _external=True,
        _scheme="http",
    )
    return response.redirect(url)


@https.main_process_start
async def start(app, _):
    http_server = await http.create_server(
        port=HTTP_PORT, return_asyncio_server=True
    )
    app.add_task(runner(http, http_server))
    app.ctx.http_server = http_server
    app.ctx.http = http


@https.main_process_stop
async def stop(app, _):
    await app.ctx.http_server.before_stop()
    await app.ctx.http_server.close()
    for connection in app.ctx.http_server.connections:
        connection.close_if_idle()
    await app.ctx.http_server.after_stop()
    app.ctx.http = False


async def runner(app: Sanic, app_server: AsyncioServer):
    app.is_running = True
    try:
        app.signalize()
        app.finalize()
        ErrorHandler.finalize(app.error_handler)
        app_server.init = True

        await app_server.before_start()
        await app_server.after_start()
        await app_server.serve_forever()
    finally:
        app.is_running = False
        app.is_stopping = True


https.run(port=HTTPS_PORT, debug=True)
