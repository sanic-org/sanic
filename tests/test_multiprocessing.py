import logging
import multiprocessing
import pickle
import random
import signal

import pytest

from sanic_testing.testing import HOST, PORT

from sanic import Blueprint
from sanic.log import logger
from sanic.response import text


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

    def stop_on_alarm(*args):
        for process in multiprocessing.active_children():
            process_list.add(process.pid)
            process.terminate()

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(3)
    app.run(HOST, PORT, workers=num_workers)

    assert len(process_list) == num_workers


@pytest.mark.skipif(
    not hasattr(signal, "SIGALRM"),
    reason="SIGALRM is not implemented for this platform",
)
def test_multiprocessing_with_blueprint(app):
    # Selects a number at random so we can spot check
    num_workers = random.choice(range(2, multiprocessing.cpu_count() * 2 + 1))
    process_list = set()

    def stop_on_alarm(*args):
        for process in multiprocessing.active_children():
            process_list.add(process.pid)
            process.terminate()

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(3)

    bp = Blueprint("test_text")
    app.blueprint(bp)
    app.run(HOST, PORT, workers=num_workers)

    assert len(process_list) == num_workers


# this function must be outside a test function so that it can be
# able to be pickled (local functions cannot be pickled).
def handler(request):
    return text("Hello")


# Multiprocessing on Windows requires app to be able to be pickled
@pytest.mark.parametrize("protocol", [3, 4])
def test_pickle_app(app, protocol):
    app.route("/")(handler)
    app.router.finalize()
    app.router.reset()
    p_app = pickle.dumps(app, protocol=protocol)
    del app
    up_p_app = pickle.loads(p_app)
    up_p_app.router.finalize()
    assert up_p_app
    request, response = up_p_app.test_client.get("/")
    assert response.text == "Hello"


@pytest.mark.parametrize("protocol", [3, 4])
def test_pickle_app_with_bp(app, protocol):
    bp = Blueprint("test_text")
    bp.route("/")(handler)
    app.blueprint(bp)
    app.router.finalize()
    app.router.reset()
    p_app = pickle.dumps(app, protocol=protocol)
    del app
    up_p_app = pickle.loads(p_app)
    up_p_app.router.finalize()
    assert up_p_app
    request, response = up_p_app.test_client.get("/")
    assert response.text == "Hello"


@pytest.mark.parametrize("protocol", [3, 4])
def test_pickle_app_with_static(app, protocol):
    app.route("/")(handler)
    app.static("/static", "/tmp/static")
    app.router.finalize()
    app.router.reset()
    p_app = pickle.dumps(app, protocol=protocol)
    del app
    up_p_app = pickle.loads(p_app)
    up_p_app.router.finalize()
    assert up_p_app
    request, response = up_p_app.test_client.get("/static/missing.txt")
    assert response.status == 404


def test_main_process_event(app, caplog):
    # Selects a number at random so we can spot check
    num_workers = random.choice(range(2, multiprocessing.cpu_count() * 2 + 1))

    def stop_on_alarm(*args):
        for process in multiprocessing.active_children():
            process.terminate()

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(1)

    @app.listener("main_process_start")
    def main_process_start(app, loop):
        logger.info("main_process_start")

    @app.listener("main_process_stop")
    def main_process_stop(app, loop):
        logger.info("main_process_stop")

    @app.main_process_start
    def main_process_start(app, loop):
        logger.info("main_process_start")

    @app.main_process_stop
    def main_process_stop(app, loop):
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
