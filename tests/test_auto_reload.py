import os
import secrets
import sys

from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory
from textwrap import dedent
from time import sleep

import pytest


def write_app(filename, **runargs):
    text = secrets.token_urlsafe()
    with open(filename, "w") as f:
        f.write(dedent(f"""\
            import os
            from sanic import Sanic

            app = Sanic(__name__)
            started = False

            @app.listener("after_server_start")
            def complete(*args):
                global started
                started = True
                print("complete", os.getpid(), {text!r})

            if __name__ == "__main__":
                app.run(**{runargs!r})
            """
        ))
    return text

def scanner(proc):
    for line in proc.stdout:
        line = line.decode().strip()
        print(">", line)
        if line.startswith("complete"):
            yield line

argv = dict(
    script=[sys.executable, "reloader.py"],
    module=[sys.executable, "-m", "reloader"],
    sanic=[sys.executable, "-m", "sanic", "--port", "42104", "--debug", "reloader.app"],
)

@pytest.mark.parametrize("runargs, mode", [
    (dict(port=42102, auto_reload=True), "script"),
    (dict(port=42103, debug=True), "module"),
    (dict(), "sanic"),
])
async def test_reloader_live(runargs, mode):
    with TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "reloader.py")
        text = write_app(filename, **runargs)
        with Popen(argv[mode], cwd=tmpdir, stdout=PIPE) as proc:
            try:
                # Python apparently keeps using the old source sometimes if
                # we don't sleep before rewrite (pycache timestamp problem?)
                sleep(1)
                line = scanner(proc)
                assert text in next(line)
                # Edit source code and try again
                text = write_app(filename, **runargs)
                #print(f"Replaced reloader {text}")
                assert text in next(line)
            finally:
                proc.terminate()
