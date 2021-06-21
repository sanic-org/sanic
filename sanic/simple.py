from pathlib import Path

from sanic import Sanic
from sanic.exceptions import SanicException
from sanic.response import redirect


def create_simple_server(directory: Path):
    if not directory.is_dir():
        raise SanicException(
            "Cannot setup Sanic Simple Server without a path to a directory"
        )

    app = Sanic("SimpleServer")
    app.static("/", directory, name="main")

    @app.get("/")
    def index(_):
        return redirect(app.url_for("main", filename="index.html"))

    return app
