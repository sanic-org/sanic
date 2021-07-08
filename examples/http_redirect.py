from sanic import Sanic, response, text


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


@https.listener("main_process_start")
async def start(app, _):
    global http
    app.http_server = await http.create_server(
        port=HTTP_PORT, return_asyncio_server=True
    )
    app.http_server.after_start()


@https.listener("main_process_stop")
async def stop(app, _):
    app.http_server.before_stop()
    await app.http_server.close()
    app.http_server.after_stop()


https.run(port=HTTPS_PORT, debug=True)
