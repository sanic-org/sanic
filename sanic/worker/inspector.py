import logging
import ssl
import sys

from contextlib import contextmanager
from datetime import datetime
from multiprocessing.connection import Connection
from pathlib import Path
from signal import SIGINT, SIGTERM
from signal import signal as signal_func
from socket import create_connection, timeout
from textwrap import indent
from typing import Any, Dict, Union

from sanic.application.logo import get_logo
from sanic.application.motd import MOTDTTY
from sanic.helpers import Default
from sanic.log import LOGGING_CONFIG_DEFAULTS, Colors, error_logger, logger
from sanic.server.socket import configure_socket


try:  # no cov
    from ujson import dumps, loads
except ModuleNotFoundError:  # no cov
    from json import dumps, loads  # type: ignore

OK = b"OK"
ER = b"ER"


class Inspector:
    def __init__(
        self,
        publisher: Connection,
        app_info: Dict[str, Any],
        worker_state: Dict[str, Any],
        host: str,
        port: int,
        tls_key: Union[Path, str, Default],
        tls_cert: Union[Path, str, Default],
    ):
        self._publisher = publisher
        self.run = True
        self.app_info = app_info
        self.worker_state = worker_state
        self.host = host
        self.port = port
        self.tls_key = tls_key
        self.tls_cert = tls_cert

    def __call__(self) -> None:
        signal_func(SIGINT, self.stop)
        signal_func(SIGTERM, self.stop)

        with self.socket() as sock:
            host, port = sock.getsockname()
            logger.info(f"Inspector started @ {host}:{port}")

            while self.run:
                try:
                    conn, _ = sock.accept()
                except timeout:
                    continue
                except ssl.SSLError as e:
                    print("SSL error: ", e)
                    continue
                else:
                    okay = conn.recv(2)
                    if okay != OK:
                        error_logger.error("Invalid start")
                        conn.close()
                        continue
                    conn.send(OK)
                    action = conn.recv(64)
                    if action == b"reload":
                        conn.send(b"\n")
                        self.reload()
                    elif action == b"shutdown":
                        conn.send(b"\n")
                        self.shutdown()
                    else:
                        data = dumps(self.state_to_json())
                        conn.send(data.encode())
                conn.send(b"\r\n\r\n")
                conn.close()

    def stop(self, *_):
        self.run = False

    def state_to_json(self):
        output = {"info": self.app_info}
        output["workers"] = self.make_safe(dict(self.worker_state))
        return output

    def reload(self):
        message = "__ALL_PROCESSES__:"
        self._publisher.send(message)

    def shutdown(self):
        message = "__TERMINATE__"
        self._publisher.send(message)

    @contextmanager
    def socket(self):
        sock = configure_socket(
            {"host": self.host, "port": self.port, "unix": None, "backlog": 1}
        )
        assert sock
        sock.settimeout(15)

        if not isinstance(self.tls_key, Default) and not isinstance(
            self.tls_cert, Default
        ):
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(self.tls_cert, self.tls_key)
            yield context.wrap_socket(sock, server_side=True)
        else:
            yield sock
        logger.debug("Inspector closing")
        sock.close()

    @staticmethod
    def make_safe(obj: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in obj.items():
            if isinstance(value, dict):
                obj[key] = Inspector.make_safe(value)
            elif isinstance(value, datetime):
                obj[key] = value.isoformat()
        return obj


class InspectorClient:
    def __init__(self, host: str, port: int, secure: bool):
        self.host = host
        self.port = port
        self.secure = secure

    @contextmanager
    def socket(self):
        context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        error = sys.stderr.write
        try:
            sock = create_connection((self.host, self.port))
            sock.settimeout(15)
            if self.secure:
                sock = context.wrap_socket(sock, server_hostname="localhost")

            sock.sendall(OK)
            if sock.recv(2) != OK:
                raise ValueError
            yield sock
            if not sock._closed:
                sock.close()
        except (
            ConnectionRefusedError,
            ConnectionResetError,
            TimeoutError,
            ValueError,
        ):
            error(
                f"{Colors.RED}Could not connect to inspector at: "
                f"{Colors.YELLOW}{self.host}:{self.port}{Colors.END}\n"
                "Either the application is not running, or it did not start "
                "an inspector instance.\n"
            )
            sys.exit(1)

    def run(self, action: str):
        out = sys.stdout.write
        logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)
        with self.socket() as sock:
            sock.sendall(action.encode())
            more = True
            data = b""
            while more:
                received = sock.recv(4096)
                if received.endswith(b"\r\n\r\n"):
                    more = False
                data += received
        if action == "raw":
            out(data.decode())
        elif action == "pretty":
            loaded = loads(data)
            display = loaded.pop("info")
            extra = display.pop("extra", {})
            display["packages"] = ", ".join(display["packages"])
            MOTDTTY(
                get_logo(), f"{self.host}:{self.port}", display, extra
            ).display(
                version=False,
                action="Inspecting",
                out=out,
            )
            for name, info in loaded["workers"].items():
                info = "\n".join(
                    f"\t{key}: {Colors.BLUE}{value}{Colors.END}"
                    for key, value in info.items()
                )
                name = f"{Colors.BOLD}{Colors.SANIC}{name}{Colors.END}"
                out("\n" + indent("\n".join([name, info]), "  ") + "\n")
