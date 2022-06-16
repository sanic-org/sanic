from asyncio import Event
from pathlib import Path

from sanic import Sanic


parent_dir = Path(__file__).parent.parent
localhost_dir = str(parent_dir / "certs/localhost")
sanic_dir = str(parent_dir / "certs/sanic.example")


def test_server_starts(app: Sanic):
    ev = Event()

    @app.after_server_start
    def shutdown(*_):
        ev.set()
        app.stop()

    print(localhost_dir)
    print(sanic_dir)
    app.run(version=3, ssl=[localhost_dir, sanic_dir])

    assert ev.is_set()
