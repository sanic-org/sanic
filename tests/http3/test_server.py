import logging
import sys

from asyncio import Event
from pathlib import Path

import pytest

from sanic import Sanic
from sanic.compat import UVLOOP_INSTALLED
from sanic.http.constants import HTTP


parent_dir = Path(__file__).parent.parent
localhost_dir = parent_dir / "certs/localhost"


@pytest.mark.parametrize("version", (3, HTTP.VERSION_3))
@pytest.mark.skipif(
    sys.version_info < (3, 8) and not UVLOOP_INSTALLED,
    reason="In 3.7 w/o uvloop the port is not always released",
)
def test_server_starts_http3(app: Sanic, version, caplog):
    ev = Event()

    @app.after_server_start
    def shutdown(*_):
        ev.set()
        app.stop()

    with caplog.at_level(logging.INFO):
        app.run(
            version=version,
            ssl={
                "cert": localhost_dir / "fullchain.pem",
                "key": localhost_dir / "privkey.pem",
            },
            single_process=True,
        )

    assert ev.is_set()
    assert (
        "sanic.root",
        logging.INFO,
        "server: sanic, HTTP/3",
    ) in caplog.record_tuples


@pytest.mark.skipif(
    sys.version_info < (3, 8) and not UVLOOP_INSTALLED,
    reason="In 3.7 w/o uvloop the port is not always released",
)
def test_server_starts_http1_and_http3(app: Sanic, caplog):
    @app.after_server_start
    def shutdown(*_):
        app.stop()

    app.prepare(
        version=3,
        ssl={
            "cert": localhost_dir / "fullchain.pem",
            "key": localhost_dir / "privkey.pem",
        },
    )
    app.prepare(
        version=1,
        ssl={
            "cert": localhost_dir / "fullchain.pem",
            "key": localhost_dir / "privkey.pem",
        },
    )
    with caplog.at_level(logging.INFO):
        Sanic.serve_single()

    assert (
        "sanic.root",
        logging.INFO,
        "server: sanic, HTTP/1.1",
    ) in caplog.record_tuples
    assert (
        "sanic.root",
        logging.INFO,
        "server: sanic, HTTP/3",
    ) in caplog.record_tuples


@pytest.mark.skipif(
    sys.version_info < (3, 8) and not UVLOOP_INSTALLED,
    reason="In 3.7 w/o uvloop the port is not always released",
)
def test_server_starts_http1_and_http3_bad_order(app: Sanic, caplog):
    @app.after_server_start
    def shutdown(*_):
        app.stop()

    app.prepare(
        version=1,
        ssl={
            "cert": localhost_dir / "fullchain.pem",
            "key": localhost_dir / "privkey.pem",
        },
    )
    message = (
        "Serving HTTP/3 instances as a secondary server is not supported. "
        "There can only be a single HTTP/3 worker and it must be the first "
        "instance prepared."
    )
    with pytest.raises(RuntimeError, match=message):
        app.prepare(
            version=3,
            ssl={
                "cert": localhost_dir / "fullchain.pem",
                "key": localhost_dir / "privkey.pem",
            },
        )
