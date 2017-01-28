from sanic import Sanic
import asyncio
from signal import signal, SIGINT
import uvloop


def test_loop_policy():
    app = Sanic('test_loop_policy')

    server = app.create_server(host="0.0.0.0", port=8000)

    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(server)
    signal(SIGINT, lambda s, f: loop.close())

    # serve() sets the event loop policy to uvloop but
    # doesn't get called until we run the server task
    assert isinstance(asyncio.get_event_loop_policy(),
                      asyncio.unix_events._UnixDefaultEventLoopPolicy)

    try:
        loop.run_until_complete(task)
    except:
        loop.stop()

    assert isinstance(asyncio.get_event_loop_policy(),
                      uvloop.EventLoopPolicy)
