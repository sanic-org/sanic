import logging
import multiprocessing
import pickle
import random
import signal

from asyncio import sleep

import pytest

from sanic_testing.testing import HOST, PORT

from sanic import Blueprint, text
from sanic.log import logger
from sanic.server.socket import configure_socket


@pytest.mark.skipif(
    not hasattr(signal, "SIGALRM"),
    reason="SIGALRM is not implemented for this platform, we have to come "
    "up with another timeout strategy to test these",
)
def test_multiprocessing(app):
    """Tests that the number of children we produce is correct"""
    # Selects a number at random so we can spot check
    num_workers = random.choice(range(2, multiprocessing.cpu_count() * 2 + 1))
    process_list = set()

    @app.after_server_start
    async def shutdown(app):
        await sleep(2.1)
        app.stop()

    def stop_on_alarm(*args):
        for process in multiprocessing.active_children():
            process_list.add(process.pid)

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(2)
    app.run(HOST, 4120, workers=num_workers, debug=True)

    assert len(process_list) == num_workers + 1


@pytest.mark.skipif(
    not hasattr(signal, "SIGALRM"),
    reason="SIGALRM is not implemented for this platform, we have to come "
    "up with another timeout strategy to test these",
)
def test_multiprocessing_legacy(app):
    """Tests that the number of children we produce is correct"""
    # Selects a number at random so we can spot check
    num_workers = random.choice(range(2, multiprocessing.cpu_count() * 2 + 1))
    process_list = set()

    @app.after_server_start
    async def shutdown(app):
        await sleep(2.1)
        app.stop()

    def stop_on_alarm(*args):
        for process in multiprocessing.active_children():
            process_list.add(process.pid)

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(2)
    app.run(HOST, 4121, workers=num_workers, debug=True, legacy=True)

    assert len(process_list) == num_workers


@pytest.mark.skipif(
    not hasattr(signal, "SIGALRM"),
    reason="SIGALRM is not implemented for this platform, we have to come "
    "up with another timeout strategy to test these",
)
def test_multiprocessing_legacy_sock(app):
    """Tests that the number of children we produce is correct"""
    # Selects a number at random so we can spot check
    num_workers = random.choice(range(2, multiprocessing.cpu_count() * 2 + 1))
    process_list = set()

    @app.after_server_start
    async def shutdown(app):
        await sleep(2.1)
        app.stop()

    def stop_on_alarm(*args):
        for process in multiprocessing.active_children():
            process_list.add(process.pid)

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(2)
    sock = configure_socket(
        {
            "host": HOST,
            "port": 4121,
            "unix": None,
            "backlog": 100,
        }
    )
    app.run(workers=num_workers, debug=True, legacy=True, sock=sock)
    sock.close()

    assert len(process_list) == num_workers


@pytest.mark.skipif(
    not hasattr(signal, "SIGALRM"),
    reason="SIGALRM is not implemented for this platform, we have to come "
    "up with another timeout strategy to test these",
)
def test_multiprocessing_legacy_unix(app):
    """Tests that the number of children we produce is correct"""
    # Selects a number at random so we can spot check
    num_workers = random.choice(range(2, multiprocessing.cpu_count() * 2 + 1))
    process_list = set()

    @app.after_server_start
    async def shutdown(app):
        await sleep(2.1)
        app.stop()

    def stop_on_alarm(*args):
        for process in multiprocessing.active_children():
            process_list.add(process.pid)

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(2)
    app.run(workers=num_workers, debug=True, legacy=True, unix="./test.sock")

    assert len(process_list) == num_workers


@pytest.mark.skipif(
    not hasattr(signal, "SIGALRM"),
    reason="SIGALRM is not implemented for this platform",
)
def test_multiprocessing_with_blueprint(app):
    # Selects a number at random so we can spot check
    num_workers = random.choice(range(2, multiprocessing.cpu_count() * 2 + 1))
    process_list = set()

    @app.after_server_start
    async def shutdown(app):
        await sleep(2.1)
        app.stop()

    def stop_on_alarm(*args):
        for process in multiprocessing.active_children():
            process_list.add(process.pid)

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(2)

    bp = Blueprint("test_text")
    app.blueprint(bp)
    app.run(HOST, 4121, workers=num_workers, debug=True)

    assert len(process_list) == num_workers + 1


# this function must be outside a test function so that it can be
# able to be pickled (local functions cannot be pickled).
def handler(request):
    return text("Hello")


def stop(app):
    app.stop()


# Multiprocessing on Windows requires app to be able to be pickled
@pytest.mark.parametrize("protocol", [3, 4])
def test_pickle_app(app, protocol):
    app.route("/")(handler)
    app.after_server_start(stop)
    app.router.reset()
    app.signal_router.reset()
    p_app = pickle.dumps(app, protocol=protocol)
    del app
    up_p_app = pickle.loads(p_app)
    assert up_p_app
    up_p_app.run(single_process=True)


@pytest.mark.parametrize("protocol", [3, 4])
def test_pickle_app_with_bp(app, protocol):
    bp = Blueprint("test_text")
    bp.route("/")(handler)
    bp.after_server_start(stop)
    app.blueprint(bp)
    app.router.reset()
    app.signal_router.reset()
    p_app = pickle.dumps(app, protocol=protocol)
    del app
    up_p_app = pickle.loads(p_app)
    assert up_p_app
    up_p_app.run(single_process=True)


@pytest.mark.parametrize("protocol", [3, 4])
def test_pickle_app_with_static(app, protocol):
    app.route("/")(handler)
    app.after_server_start(stop)
    app.static("/static", "/tmp/static")
    app.router.reset()
    app.signal_router.reset()
    p_app = pickle.dumps(app, protocol=protocol)
    del app
    up_p_app = pickle.loads(p_app)
    assert up_p_app
    up_p_app.run(single_process=True)


def test_main_process_event(app, caplog):
    # Selects a number at random so we can spot check
    num_workers = random.choice(range(2, multiprocessing.cpu_count() * 2 + 1))

    app.after_server_start(stop)

    @app.listener("main_process_start")
    def main_process_start(app, loop):
        logger.info("main_process_start")

    @app.listener("main_process_stop")
    def main_process_stop(app, loop):
        logger.info("main_process_stop")

    @app.main_process_start
    def main_process_start2(app, loop):
        logger.info("main_process_start")

    @app.main_process_stop
    def main_process_stop2(app, loop):
        logger.info("main_process_stop")

    with caplog.at_level(logging.INFO):
        app.run(HOST, PORT, workers=num_workers)

    assert (
        caplog.record_tuples.count(("sanic.root", 20, "main_process_start"))
        == 2
    )
    assert (
        caplog.record_tuples.count(("sanic.root", 20, "main_process_stop"))
        == 2
    )
