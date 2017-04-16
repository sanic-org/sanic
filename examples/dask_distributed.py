from sanic import Sanic
from sanic import response

from tornado.platform.asyncio import BaseAsyncIOLoop, to_asyncio_future
from distributed import LocalCluster, Client


app = Sanic(__name__)


def square(x):
    return x**2


@app.listener('after_server_start')
async def setup(app, loop):
    # configure tornado use asyncio's loop
    ioloop = BaseAsyncIOLoop(loop)

    # init distributed client
    app.client = Client('tcp://localhost:8786', loop=ioloop, start=False)
    await to_asyncio_future(app.client._start())


@app.listener('before_server_stop')
async def stop(app, loop):
    await to_asyncio_future(app.client._shutdown())


@app.route('/<value:int>')
async def test(request, value):
    future = app.client.submit(square, value)
    result = await to_asyncio_future(future._result())
    return response.text(f'The square of {value} is {result}')


if __name__ == '__main__':
    # Distributed cluster should run somewhere else
    with LocalCluster(scheduler_port=8786, processes=False) as cluster:
        app.run(host="0.0.0.0", port=8000)
