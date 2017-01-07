from multiprocessing import Array, Event, Process
from time import sleep, time
from ujson import loads as json_loads
from asyncio import get_event_loop
from os import killpg, kill
from signal import SIGUSR1, signal, SIGINT, SIGTERM, SIGKILL

from sanic import Sanic
from sanic.response import json, text
from sanic.exceptions import Handler
from sanic.utils import local_request, HOST, PORT


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

# TODO: Figure out why this freezes on pytest but not when
# executed via interpreter

def skip_test_multiprocessing():
    app = Sanic('test_json')

    response = Array('c', 50)
    @app.route('/')
    async def handler(request):
        return json({"test": True})

    stop_event = Event()
    async def after_start(*args, **kwargs):
        http_response = await local_request('get', '/')
        response.value = http_response.text.encode()
        stop_event.set()

    def rescue_crew():
        sleep(5)
        stop_event.set()

    rescue_process = Process(target=rescue_crew)
    rescue_process.start()

    app.serve_multiple({
        'host': HOST,
        'port': PORT,
        'after_start': after_start,
        'request_handler': app.handle_request,
        'request_max_size': 100000,
    }, workers=2, stop_event=stop_event)

    rescue_process.terminate()

    try:
        results = json_loads(response.value)
    except:
        raise ValueError("Expected JSON response but got '{}'".format(response))

    stop_event.set()
    assert results.get('test') == True


def test_drain_connections():
    app = Sanic('test_stop')

    @app.route('/')
    async def handler(request):
        return json({"test": True})

    stop_event = Event()
    async def after_start(*args, **kwargs):
        http_response = await local_request('get', '/')
        stop_event.set()

    start = time()
    app.serve_multiple({
        'host': HOST,
        'port': PORT,
        'after_start': after_start,
        'request_handler': app.handle_request,
    }, workers=2, stop_event=stop_event)
    end = time()

    assert end - start < 0.05

def skip_test_workers():
    app = Sanic('test_workers')

    @app.route('/')
    async def handler(request):
        return text('ok')

    stop_event = Event()

    d = []
    async def after_start(*args, **kwargs):
        http_response = await local_request('get', '/')
        d.append(http_response.text)
        stop_event.set()

    p = Process(target=app.run, kwargs={'host':HOST,
                                        'port':PORT,
                                        'after_start': after_start,
                                        'workers':2,
                                        'stop_event':stop_event})
    p.start()
    loop = get_event_loop()
    loop.run_until_complete(after_start())
    #killpg(p.pid, SIGUSR1)
    kill(p.pid, SIGUSR1)

    assert d[0] == 1
