import os
import subprocess
import secrets
import sys

from tempfile import TemporaryDirectory
from textwrap import dedent

import pytest

def write_app(filename, **runargs):
    text = secrets.token_urlsafe()
    with open(filename, "w") as f:
        f.write(dedent(f"""\
            from sanic import Sanic
            from sanic.response import text

            app = Sanic(__name__)

            @app.listener("after_server_start")
            def complete(*args):
                print("complete", {text!r})

            kwargs = {runargs!r}
            app.run(port=42101, **kwargs)
            """
        ))
    return text

@pytest.mark.parametrize("runargs", [
    dict(auto_reload=True),
    dict(debug=True),
])
async def test_reloader_live(runargs):
    with TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "reloaderapp.py")
        text = write_app(filename, **runargs)
        with subprocess.Popen([sys.executable, filename], stdout=subprocess.PIPE) as proc:
            line = (l.decode() for l in proc.stdout if l.startswith(b"complete"))
            try:
                assert next(line) == f"complete {text}\n"
                # Edit source code and try again
                text = write_app(filename)
                assert next(line) == f"complete {text}\n"
            finally:
                proc.terminate()
