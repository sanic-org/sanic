from pathlib import Path

from sanic import Sanic
from sanic.exceptions import SanicException


def create_simple_server(directory: Path):
    if not directory.is_dir():
        raise SanicException(
            "Cannot setup Sanic Simple Server without a path to a directory"
        )

    app = Sanic("SimpleServer")
    app.static(
        "/", directory, name="main", directory_view=True, index="index.html"
    )

    return app
