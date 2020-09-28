import asyncio
import logging
import os
import subprocess
import sys

import httpcore
import httpx
import pytest

from sanic import Sanic
from sanic.response import text


pytestmark = pytest.mark.skipif(os.name != "posix", reason="UNIX only")
SOCKPATH = "/tmp/sanictest.sock"
SOCKPATH2 = "/tmp/sanictest2.sock"


@pytest.fixture(autouse=True)
def socket_cleanup():
    try:
        os.unlink(SOCKPATH)
    except FileNotFoundError:
        pass
    try:
        os.unlink(SOCKPATH2)
    except FileNotFoundError:
        pass
    # Run test function
    yield
    try:
        os.unlink(SOCKPATH2)
    except FileNotFoundError:
        pass
    try:
        os.unlink(SOCKPATH)
    except FileNotFoundError:
        pass


def test_unix_socket_creation(caplog):
    from socket import AF_UNIX, socket

    with socket(AF_UNIX) as sock:
        sock.bind(SOCKPATH)
    assert os.path.exists(SOCKPATH)
    ino = os.stat(SOCKPATH).st_ino

    app = Sanic(name=__name__)

    @app.listener("after_server_start")
    def running(app, loop):
        assert os.path.exists(SOCKPATH)
        assert ino != os.stat(SOCKPATH).st_ino
        app.stop()

    with caplog.at_level(logging.INFO):
        app.run(unix=SOCKPATH)

    assert (
        "sanic.root",
        logging.INFO,
        f"Goin' Fast @ {SOCKPATH} http://...",
    ) in caplog.record_tuples
    assert not os.path.exists(SOCKPATH)


def test_invalid_paths():
    app = Sanic(name=__name__)

    with pytest.raises(FileExistsError):
        app.run(unix=".")

    with pytest.raises(FileNotFoundError):
        app.run(unix="no-such-directory/sanictest.sock")


def test_dont_replace_file():
    with open(SOCKPATH, "w") as f:
        f.write("File, not socket")

    app = Sanic(name=__name__)

    @app.listener("after_server_start")
    def stop(app, loop):
        app.stop()

    with pytest.raises(FileExistsError):
        app.run(unix=SOCKPATH)


def test_dont_follow_symlink():
    from socket import AF_UNIX, socket

    with socket(AF_UNIX) as sock:
        sock.bind(SOCKPATH2)
    os.symlink(SOCKPATH2, SOCKPATH)

    app = Sanic(name=__name__)

    @app.listener("after_server_start")
    def stop(app, loop):
        app.stop()

    with pytest.raises(FileExistsError):
        app.run(unix=SOCKPATH)


def test_socket_deleted_while_running():
    app = Sanic(name=__name__)

    @app.listener("after_server_start")
    async def hack(app, loop):
        os.unlink(SOCKPATH)
        app.stop()

    app.run(host="myhost.invalid", unix=SOCKPATH)


def test_socket_replaced_with_file():
    app = Sanic(name=__name__)

    @app.listener("after_server_start")
    async def hack(app, loop):
        os.unlink(SOCKPATH)
        with open(SOCKPATH, "w") as f:
            f.write("Not a socket")
        app.stop()

    app.run(host="myhost.invalid", unix=SOCKPATH)


def test_unix_connection():
    app = Sanic(name=__name__)

    @app.get("/")
    def handler(request):
        return text(f"{request.conn_info.server}")

    @app.listener("after_server_start")
    async def client(app, loop):
        transport = httpcore.AsyncConnectionPool(uds=SOCKPATH)
        try:
            async with httpx.AsyncClient(transport=transport) as client:
                r = await client.get("http://myhost.invalid/")
                assert r.status_code == 200
                assert r.text == os.path.abspath(SOCKPATH)
        finally:
            app.stop()

    app.run(host="myhost.invalid", unix=SOCKPATH)


app_multi = Sanic(name=__name__)


def handler(request):
    return text(f"{request.conn_info.server}")


async def client(app, loop):
    try:
        async with httpx.AsyncClient(uds=SOCKPATH) as client:
            r = await client.get("http://myhost.invalid/")
            assert r.status_code == 200
            assert r.text == os.path.abspath(SOCKPATH)
    finally:
        app.stop()


def test_unix_connection_multiple_workers():
    app_multi.get("/")(handler)
    app_multi.listener("after_server_start")(client)
    app_multi.run(host="myhost.invalid", unix=SOCKPATH, workers=2)


async def test_zero_downtime():
    """Graceful server termination and socket replacement on restarts"""
    from signal import SIGINT
    from time import monotonic as current_time

    async def client():
        transport = httpcore.AsyncConnectionPool(uds=SOCKPATH)
        for _ in range(40):
            async with httpx.AsyncClient(transport=transport) as client:
                r = await client.get("http://localhost/sleep/0.1")
                assert r.status_code == 200
                assert r.text == f"Slept 0.1 seconds.\n"

    def spawn():
        command = [
            sys.executable,
            "-m",
            "sanic",
            "--unix",
            SOCKPATH,
            "examples.delayed_response.app",
        ]
        DN = subprocess.DEVNULL
        return subprocess.Popen(
            command, stdin=DN, stdout=DN, stderr=subprocess.PIPE
        )

    try:
        processes = [spawn()]
        while not os.path.exists(SOCKPATH):
            if processes[0].poll() is not None:
                raise Exception("Worker did not start properly")
            await asyncio.sleep(0.0001)
        ino = os.stat(SOCKPATH).st_ino
        task = asyncio.get_event_loop().create_task(client())
        start_time = current_time()
        while current_time() < start_time + 4:
            # Start a new one and wait until the socket is replaced
            processes.append(spawn())
            while ino == os.stat(SOCKPATH).st_ino:
                await asyncio.sleep(0.001)
            ino = os.stat(SOCKPATH).st_ino
            # Graceful termination of the previous one
            processes[-2].send_signal(SIGINT)
        # Wait until client has completed all requests
        await task
        processes[-1].send_signal(SIGINT)
        for worker in processes:
            try:
                worker.wait(1.0)
            except subprocess.TimeoutExpired:
                raise Exception(
                    f"Worker would not terminate:\n{worker.stderr}"
                )
    finally:
        for worker in processes:
            worker.kill()
    # Test for clean run and termination
    assert len(processes) > 5
    assert [worker.poll() for worker in processes] == len(processes) * [0]
    assert not os.path.exists(SOCKPATH)
