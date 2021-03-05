import os
import secrets
import sys

from contextlib import suppress
from subprocess import PIPE, Popen, TimeoutExpired
from tempfile import TemporaryDirectory
from textwrap import dedent
from threading import Timer
from time import sleep

import pytest


# We need to interrupt the autoreloader without killing it, so that the server gets terminated
# https://stefan.sofa-rockers.org/2013/08/15/handling-sub-process-hierarchies-python-linux-os-x/

try:
    from signal import CTRL_BREAK_EVENT
    from subprocess import CREATE_NEW_PROCESS_GROUP

    flags = CREATE_NEW_PROCESS_GROUP
except ImportError:
    flags = 0


def terminate(proc):
    if flags:
        proc.send_signal(CTRL_BREAK_EVENT)
    else:
        proc.terminate()


def write_app(filename, **runargs):
    text = secrets.token_urlsafe()
    with open(filename, "w") as f:
        f.write(
            dedent(
                f"""\
            import os
            from sanic import Sanic

            app = Sanic(__name__)

            app.route("/")(lambda x: x)

            @app.listener("after_server_start")
            def complete(*args):
                print("complete", os.getpid(), {text!r})

            if __name__ == "__main__":
                app.run(**{runargs!r})
            """
            )
        )
    return text


def scanner(proc):
    for line in proc.stdout:
        line = line.decode().strip()
        if line.startswith("complete"):
            yield line


argv = dict(
    script=[sys.executable, "reloader.py"],
    module=[sys.executable, "-m", "reloader"],
    sanic=[
        sys.executable,
        "-m",
        "sanic",
        "--port",
        "42104",
        "--debug",
        "reloader.app",
    ],
)


@pytest.mark.parametrize(
    "runargs, mode",
    [
        (dict(port=42102, auto_reload=True), "script"),
        (dict(port=42103, debug=True), "module"),
        ({}, "sanic"),
    ],
)
async def test_reloader_live(runargs, mode):
    with TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "reloader.py")
        text = write_app(filename, **runargs)
        proc = Popen(argv[mode], cwd=tmpdir, stdout=PIPE, creationflags=flags)
        try:
            timeout = Timer(5, terminate, [proc])
            timeout.start()
            # Python apparently keeps using the old source sometimes if
            # we don't sleep before rewrite (pycache timestamp problem?)
            sleep(1)
            line = scanner(proc)
            assert text in next(line)
            # Edit source code and try again
            text = write_app(filename, **runargs)
            assert text in next(line)
        finally:
            timeout.cancel()
            terminate(proc)
            with suppress(TimeoutExpired):
                proc.wait(timeout=3)
