from __future__ import annotations

import os
import secrets
import socket
import stat

from ipaddress import ip_address
from typing import Any, Dict, Optional

from sanic.exceptions import ServerError
from sanic.http.constants import HTTP


def bind_socket(host: str, port: int, *, backlog=100) -> socket.socket:
    """Create TCP server socket.
    :param host: IPv4, IPv6 or hostname may be specified
    :param port: TCP port number
    :param backlog: Maximum number of connections to queue
    :return: socket.socket object
    """
    location = (host, port)
    # socket.share, socket.fromshare
    try:  # IP address: family must be specified for IPv6 at least
        ip = ip_address(host)
        host = str(ip)
        sock = socket.socket(
            socket.AF_INET6 if ip.version == 6 else socket.AF_INET
        )
    except ValueError:  # Hostname, may become AF_INET or AF_INET6
        sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(location)
    sock.listen(backlog)
    sock.set_inheritable(True)
    return sock


def bind_unix_socket(path: str, *, mode=0o666, backlog=100) -> socket.socket:
    """Create unix socket.
    :param path: filesystem path
    :param backlog: Maximum number of connections to queue
    :return: socket.socket object
    """

    # Sanitise and pre-verify socket path
    path = os.path.abspath(path)
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Socket folder does not exist: {folder}")
    try:
        if not stat.S_ISSOCK(os.stat(path, follow_symlinks=False).st_mode):
            raise FileExistsError(f"Existing file is not a socket: {path}")
    except FileNotFoundError:
        pass
    # Create new socket with a random temporary name
    tmp_path = f"{path}.{secrets.token_urlsafe()}"
    sock = socket.socket(socket.AF_UNIX)
    try:
        # Critical section begins (filename races)
        sock.bind(tmp_path)
        try:
            os.chmod(tmp_path, mode)
            # Start listening before rename to avoid connection failures
            sock.listen(backlog)
            os.rename(tmp_path, path)
        except:  # noqa: E722
            try:
                os.unlink(tmp_path)
            finally:
                raise
    except:  # noqa: E722
        try:
            sock.close()
        finally:
            raise
    return sock


def remove_unix_socket(path: Optional[str]) -> None:
    """Remove dead unix socket during server exit."""
    if not path:
        return
    try:
        if stat.S_ISSOCK(os.stat(path, follow_symlinks=False).st_mode):
            # Is it actually dead (doesn't belong to a new server instance)?
            with socket.socket(socket.AF_UNIX) as testsock:
                try:
                    testsock.connect(path)
                except ConnectionRefusedError:
                    os.unlink(path)
    except FileNotFoundError:
        pass


def configure_socket(
    server_settings: Dict[str, Any]
) -> Optional[socket.SocketType]:
    # Create a listening socket or use the one in settings
    if server_settings.get("version") is HTTP.VERSION_3:
        return None
    sock = server_settings.get("sock")
    unix = server_settings["unix"]
    backlog = server_settings["backlog"]
    if unix:
        sock = bind_unix_socket(unix, backlog=backlog)
        server_settings["unix"] = unix
    if sock is None:
        try:
            sock = bind_socket(
                server_settings["host"],
                server_settings["port"],
                backlog=backlog,
            )
        except OSError as e:  # no cov
            error = ServerError(
                f"Sanic server could not start: {e}.\n\n"
                "This may have happened if you are running Sanic in the "
                "global scope and not inside of a "
                '`if __name__ == "__main__"` block.\n\nSee more information: '
                "https://sanic.dev/en/guide/deployment/manager.html#"
                "how-sanic-server-starts-processes\n"
            )
            error.quiet = True
            raise error
        sock.set_inheritable(True)
        server_settings["sock"] = sock
        server_settings["host"] = None
        server_settings["port"] = None
    return sock
