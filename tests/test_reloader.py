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

TIMER_DELAY = 2


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


def write_listener_app(filename, **runargs):
    start_text = secrets.token_urlsafe()
    stop_text = secrets.token_urlsafe()
    with open(filename, "w") as f:
        f.write(
            dedent(
                f"""\
            import os
            from sanic import Sanic

            app = Sanic(__name__)

            app.route("/")(lambda x: x)

            @app.reload_process_start
            async def reload_start(*_):
                print("reload_start", os.getpid(), {start_text!r})

            @app.reload_process_stop
            async def reload_stop(*_):
                print("reload_stop", os.getpid(), {stop_text!r})

            if __name__ == "__main__":
                app.run(**{runargs!r})
            """
            )
        )
    return start_text, stop_text


def write_json_config_app(filename, jsonfile, **runargs):
    with open(filename, "w") as f:
        f.write(
            dedent(
                f"""\
            import os
            from sanic import Sanic
            import json

            app = Sanic(__name__)
            with open("{jsonfile}", "r") as f:
                config = json.load(f)
            app.config.update_config(config)

            app.route("/")(lambda x: x)

            @app.listener("after_server_start")
            def complete(*args):
                print("complete", os.getpid(), app.config.FOO)

            if __name__ == "__main__":
                app.run(**{runargs!r})
            """
            )
        )


def write_file(filename):
    text = secrets.token_urlsafe()
    with open(filename, "w") as f:
        f.write(f"""{{"FOO": "{text}"}}""")
    return text


def scanner(proc, trigger="complete"):
    for line in proc.stdout:
        line = line.decode().strip()
        if line.startswith(trigger):
            yield line


argv = dict(
    script=[sys.executable, "reloader.py"],
    module=[sys.executable, "-m", "reloader"],
    sanic=[
        sys.executable,
        "-m",
        "sanic",
        "--port",
        "42204",
        "--auto-reload",
        "reloader.app",
    ],
)


@pytest.mark.parametrize(
    "runargs, mode",
    [
        (dict(port=42202, auto_reload=True), "script"),
        (dict(port=42203, auto_reload=True), "module"),
        ({}, "sanic"),
    ],
)
@pytest.mark.xfail
async def test_reloader_live(runargs, mode):
    with TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "reloader.py")
        text = write_app(filename, **runargs)
        command = argv[mode]
        proc = Popen(command, cwd=tmpdir, stdout=PIPE, creationflags=flags)
        try:
            timeout = Timer(TIMER_DELAY, terminate, [proc])
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


@pytest.mark.parametrize(
    "runargs, mode",
    [
        (dict(port=42302, auto_reload=True), "script"),
        (dict(port=42303, auto_reload=True), "module"),
        ({}, "sanic"),
    ],
)
@pytest.mark.xfail
async def test_reloader_live_with_dir(runargs, mode):
    with TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "reloader.py")
        config_file = os.path.join(tmpdir, "config.json")
        runargs["reload_dir"] = tmpdir
        write_json_config_app(filename, config_file, **runargs)
        text = write_file(config_file)
        command = argv[mode]
        if mode == "sanic":
            command += ["--reload-dir", tmpdir]
        proc = Popen(command, cwd=tmpdir, stdout=PIPE, creationflags=flags)
        try:
            timeout = Timer(TIMER_DELAY, terminate, [proc])
            timeout.start()
            # Python apparently keeps using the old source sometimes if
            # we don't sleep before rewrite (pycache timestamp problem?)
            sleep(1)
            line = scanner(proc)
            assert text in next(line)
            # Edit source code and try again
            text = write_file(config_file)
            assert text in next(line)
        finally:
            timeout.cancel()
            terminate(proc)
            with suppress(TimeoutExpired):
                proc.wait(timeout=3)


def test_reload_listeners():
    with TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "reloader.py")
        start_text, stop_text = write_listener_app(
            filename, port=42305, auto_reload=True
        )

        proc = Popen(
            argv["script"], cwd=tmpdir, stdout=PIPE, creationflags=flags
        )
        try:
            timeout = Timer(TIMER_DELAY, terminate, [proc])
            timeout.start()
            # Python apparently keeps using the old source sometimes if
            # we don't sleep before rewrite (pycache timestamp problem?)
            sleep(1)
            line = scanner(proc, "reload_start")
            assert start_text in next(line)
            line = scanner(proc, "reload_stop")
            assert stop_text in next(line)
        finally:
            timeout.cancel()
            terminate(proc)
            with suppress(TimeoutExpired):
                proc.wait(timeout=3)
