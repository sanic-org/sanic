import inspect
import os
import sys

from sanic import Sanic
from sanic.exceptions import ServerError
from sanic.response import json, text


currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe()))
)
sys.path.insert(0, currentdir + "/../../../")


app = Sanic("test")


@app.route("/")
async def test(request):
    return json({"test": True})


@app.route("/sync", methods=["GET", "POST"])
def test(request):
    return json({"test": True})


@app.route("/text/<name>/<butt:int>")
def rtext(request, name, butt):
    return text("yeehaww {} {}".format(name, butt))


@app.route("/exception")
def exception(request):
    raise ServerError("yep")


@app.route("/exception/async")
async def test(request):
    raise ServerError("asunk")


@app.route("/post_json")
def post_json(request):
    return json({"received": True, "message": request.json})


@app.route("/query_string")
def query_string(request):
    return json(
        {
            "parsed": True,
            "args": request.args,
            "url": request.url,
            "query_string": request.query_string,
        }
    )


app.run(host="0.0.0.0", port=sys.argv[1])


# import asyncio_redis
# import asyncpg
# async def setup(sanic, loop):
#     sanic.conn = []
#     sanic.redis = []
#     for x in range(10):
#         sanic.conn.append(await asyncpg.connect(user='postgres', password='zomgdev', database='postgres', host='192.168.99.100'))
#     for n in range(30):
#         connection = await asyncio_redis.Connection.create(host='192.168.99.100', port=6379)
#         sanic.redis.append(connection)


# c=0
# @app.route("/postgres")
# async def postgres(request):
#     global c
#     values = await app.conn[c].fetch('''SELECT * FROM players''')
#     c += 1
#     if c == 10:
#         c = 0
#     return text("yep")

# r=0
# @app.route("/redis")
# async def redis(request):
#     global r
#     try:
#         values = await app.redis[r].get('my_key')
#     except asyncio_redis.exceptions.ConnectionLostError:
#         app.redis[r] = await asyncio_redis.Connection.create(host='127.0.0.1', port=6379)
#         values = await app.redis[r].get('my_key')

#     r += 1
#     if r == 30:
#         r = 0
#     return text(values)
