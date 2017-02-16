import os

from sanic import Sanic
from sanic.log import log
from sanic.response import json, text, file
from sanic.exceptions import ServerError

app = Sanic(__name__)


@app.route("/")
async def test_async(request):
    return json({"test": True})


@app.route("/sync", methods=['GET', 'POST'])
def test_sync(request):
    return json({"test": True})


@app.route("/dynamic/<name>/<id:int>")
def test_params(request, name, id):
    return text("yeehaww {} {}".format(name, id))


@app.route("/exception")
def exception(request):
    raise ServerError("It's dead jim")

@app.route("/await")
async def test_await(request):
    import asyncio
    await asyncio.sleep(5)
    return text("I'm feeling sleepy")

@app.route("/file")
async def test_file(request):
    return await file(os.path.abspath("setup.py"))


# ----------------------------------------------- #
# Exceptions
# ----------------------------------------------- #

@app.exception(ServerError)
async def test(request, exception):
    return json({"exception": "{}".format(exception), "status": exception.status_code}, status=exception.status_code)


# ----------------------------------------------- #
# Read from request
# ----------------------------------------------- #

@app.route("/json")
def post_json(request):
    return json({"received": True, "message": request.json})


@app.route("/form")
def post_json(request):
    return json({"received": True, "form_data": request.form, "test": request.form.get('test')})


@app.route("/query_string")
def query_string(request):
    return json({"parsed": True, "args": request.args, "url": request.url, "query_string": request.query_string})


# ----------------------------------------------- #
# Run Server
# ----------------------------------------------- #

@app.listener('after_server_start')
def after_start(app, loop):
    log.info("OH OH OH OH OHHHHHHHH")


@app.listener('before_server_stop')
def before_stop(app, loop):
    log.info("TRIED EVERYTHING")


app.run(host="0.0.0.0", port=8000, debug=True)
