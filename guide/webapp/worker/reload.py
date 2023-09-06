from asyncio import sleep
from multiprocessing import Manager
from pathlib import Path
from queue import Empty, Queue
from typing import Any

import ujson

from sanic import Request, Sanic, Websocket


def setup_livereload(app: Sanic) -> None:
    @app.main_process_start
    async def main_process_start(app: Sanic):
        app.ctx.manager = Manager()
        app.shared_ctx.reload_queue = app.ctx.manager.Queue()

    @app.main_process_ready
    async def main_process_ready(app: Sanic):
        app.manager.manage(
            "Livereload",
            _run_reload_server,
            {
                "reload_queue": app.shared_ctx.reload_queue,
                "debug": app.state.is_debug,
                "state": app.manager.worker_state,
            },
        )

    @app.main_process_stop
    async def main_process_stop(app: Sanic):
        app.ctx.manager.shutdown()

    @app.before_server_start
    async def before_server_start(app: Sanic):
        app.shared_ctx.reload_queue.put("reload")

    @app.after_server_start
    async def after_server_start(app: Sanic):
        app.m.state["ready"] = True

    @app.before_server_stop
    async def before_server_stop(app: Sanic):
        app.m.state["ready"] = False


class Livereload:
    SERVER_NAME = "Reloader"
    HELLO = {
        "command": "hello",
        "protocols": [
            "http://livereload.com/protocols/official-7",
        ],
        "serverName": SERVER_NAME,
    }

    def __init__(
        self, reload_queue: Queue, debug: bool, state: dict[str, Any]
    ):
        self.reload_queue = reload_queue
        self.app = Sanic(self.SERVER_NAME)
        self.debug = debug
        self.state = state
        self.app.static(
            "/livereload.js", Path(__file__).parent / "livereload.js"
        )
        self.app.add_websocket_route(
            self.livereload_handler, "/livereload", name="livereload"
        )
        self.app.add_task(self._listen_to_queue())
        self.app.config.EVENT_AUTOREGISTER = True

    def run(self):
        kwargs = {
            "debug": self.debug,
            "access_log": False,
            "single_process": True,
            "port": 35729,
        }
        self.app.run(**kwargs)

    async def _listen_to_queue(self):
        while True:
            try:
                self.reload_queue.get_nowait()
            except Empty:
                await sleep(0.5)
                continue
            await self.app.dispatch("livereload.file.reload")

    async def livereload_handler(self, request: Request, ws: Websocket):
        await ws.recv()
        await ws.send(ujson.dumps(self.HELLO))

        while True:
            await request.app.event("livereload.file.reload")
            await self._wait_for_state()
            await ws.send(ujson.dumps({"command": "reload", "path": "..."}))

    async def _wait_for_state(self):
        while True:
            states = [
                state.get("ready")
                for state in self.state.values()
                if state.get("server")
            ]
            if all(states):
                await sleep(0.5)
                break


def _run_reload_server(
    reload_queue: Queue, debug: bool, state: dict[str, Any]
):
    Livereload(reload_queue, debug, state).run()
