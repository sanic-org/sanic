import logging
import ssl

from asyncio import Event
from pathlib import Path

import pytest

from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import QuicConnection
from aioquic.quic.events import ConnectionTerminated, ProtocolNegotiated

from sanic import Sanic
from sanic.http.constants import HTTP
from sanic.http.http3 import get_config
from sanic.http.tls.context import CertSimple


parent_dir = Path(__file__).parent.parent
localhost_dir = parent_dir / "certs/localhost"


def get_server_config(app: Sanic) -> QuicConfiguration:
    return get_config(
        app,
        CertSimple(
            localhost_dir / "fullchain.pem", localhost_dir / "privkey.pem"
        ),
    )


@pytest.mark.parametrize(
    "alpn_protocols,negotiated",
    ((["h3"], True), (["hq-interop"], False), (["siduck"], False)),
)
def test_alpn(app: Sanic, alpn_protocols, negotiated):
    client = QuicConnection(
        configuration=QuicConfiguration(
            alpn_protocols=alpn_protocols,
            is_client=True,
            verify_mode=ssl.CERT_NONE,
        )
    )
    server = QuicConnection(
        configuration=get_server_config(app),
        original_destination_connection_id=(
            client.original_destination_connection_id
        ),
    )
    client_addr = ("1.2.3.4", 1234)
    server_addr = ("2.3.4.5", 4433)

    client.connect(server_addr, now=0.0)
    for _ in range(5):
        for data, _ in client.datagrams_to_send(now=0.0):
            server.receive_datagram(data, client_addr, now=0.0)
        for data, _ in server.datagrams_to_send(now=0.0):
            client.receive_datagram(data, server_addr, now=0.0)

    if not negotiated:
        # The client reports the close once draining ends.
        client.handle_timer(now=client.get_timer())

    events = []
    while (event := client.next_event()) is not None:
        events.append(type(event))
    assert (ProtocolNegotiated in events) is negotiated
    assert (ConnectionTerminated in events) is not negotiated


def test_datagrams_disabled(app: Sanic):
    assert get_server_config(app).max_datagram_frame_size is None


@pytest.mark.parametrize("version", (3, HTTP.VERSION_3))
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
