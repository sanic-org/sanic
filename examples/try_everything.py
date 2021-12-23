import os

from sanic import Sanic, response
from sanic.exceptions import ServerError
from sanic.log import logger as log


app = Sanic("Example")


@app.route("/")
async def test_async(request):
    return response.json({"test": True})


@app.route("/sync", methods=["GET", "POST"])
def test_sync(request):
    return response.json({"test": True})


@app.route("/dynamic/<name>/<i:int>")
def test_params(request, name, i):
    return response.text("yeehaww {} {}".format(name, i))


@app.route("/exception")
def exception(request):
    raise ServerError("It's dead jim")


@app.route("/await")
async def test_await(request):
    import asyncio

    await asyncio.sleep(5)
    return response.text("I'm feeling sleepy")


@app.route("/file")
async def test_file(request):
    return await response.file(os.path.abspath("setup.py"))


@app.route("/file_stream")
async def test_file_stream(request):
    return await response.file_stream(
        os.path.abspath("setup.py"), chunk_size=1024
    )


# ----------------------------------------------- #
# Exceptions
# ----------------------------------------------- #


@app.exception(ServerError)
async def test(request, exception):
    return response.json(
        {"exception": str(exception), "status": exception.status_code},
        status=exception.status_code,
    )


# ----------------------------------------------- #
# Read from request
# ----------------------------------------------- #


@app.route("/json")
def post_json(request):
    return response.json({"received": True, "message": request.json})


@app.route("/form")
def post_form_json(request):
    return response.json(
        {
            "received": True,
            "form_data": request.form,
            "test": request.form.get("test"),
        }
    )


@app.route("/query_string")
def query_string(request):
    return response.json(
        {
            "parsed": True,
            "args": request.args,
            "url": request.url,
            "query_string": request.query_string,
        }
    )


# ----------------------------------------------- #
# Run Server
# ----------------------------------------------- #


@app.before_server_start
def before_start(app, loop):
    log.info("SERVER STARTING")


@app.after_server_start
def after_start(app, loop):
    log.info("OH OH OH OH OHHHHHHHH")


@app.before_server_stop
def before_stop(app, loop):
    log.info("SERVER STOPPING")


@app.after_server_stop
def after_stop(app, loop):
    log.info("TRIED EVERYTHING")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
