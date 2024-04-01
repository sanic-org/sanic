import concurrent.futures
import sys
import threading
import time
import traceback

from ast import PyCF_ALLOW_TOP_LEVEL_AWAIT
from asyncio import iscoroutine, new_event_loop
from code import InteractiveConsole
from types import FunctionType
from typing import Any, Dict, NamedTuple, Optional, Sequence, Tuple, Union

import sanic

from sanic import Request, Sanic
from sanic.compat import Header
from sanic.helpers import Default
from sanic.http.constants import Stage
from sanic.log import Colors
from sanic.models.protocol_types import TransportProtocol
from sanic.response.types import HTTPResponse


try:
    from httpx import Client

    HTTPX_AVAILABLE = True

    class SanicClient(Client):
        def __init__(self, app: Sanic):
            base_url = app.get_server_location(
                app.state.server_info[0].settings
            )
            super().__init__(base_url=base_url)

except ImportError:
    HTTPX_AVAILABLE = False

try:
    import readline  # noqa
except ImportError:
    print(
        "Module 'readline' not available. History navigation will be limited.",
        file=sys.stderr,
    )

repl_app: Optional[Sanic] = None
repl_response: Optional[HTTPResponse] = None


class REPLProtocol(TransportProtocol):
    def __init__(self):
        self.stage = Stage.IDLE
        self.request_body = True

    def respond(self, response):
        global repl_response
        repl_response = response
        response.stream = self
        return response

    async def send(self, data, end_stream): ...


class Result(NamedTuple):
    request: Request
    response: HTTPResponse


def make_request(
    url: str = "/",
    headers: Optional[Union[Dict[str, Any], Sequence[Tuple[str, str]]]] = None,
    method: str = "GET",
    body: Optional[str] = None,
):
    assert repl_app, "No Sanic app has been registered."
    headers = headers or {}
    protocol = REPLProtocol()
    request = Request(  # type: ignore
        url.encode(),
        Header(headers),
        "1.1",
        method,
        protocol,
        repl_app,
    )
    if body is not None:
        request.body = body.encode()
    request.stream = protocol  # type: ignore
    request.conn_info = None
    return request


async def respond(request) -> HTTPResponse:
    assert repl_app, "No Sanic app has been registered."
    await repl_app.handle_request(request)
    assert repl_response
    return repl_response


async def do(
    url: str = "/",
    headers: Optional[Union[Dict[str, Any], Sequence[Tuple[str, str]]]] = None,
    method: str = "GET",
    body: Optional[str] = None,
) -> Result:
    request = make_request(url, headers, method, body)
    response = await respond(request)
    return Result(request, response)


class SanicREPL(InteractiveConsole):
    def __init__(self, app: Sanic, start: Optional[Default] = None):
        global repl_app
        repl_app = app
        locals_available = {
            "app": app,
            "sanic": sanic,
            "do": do,
        }
        client_availability = ""
        variable_descriptions = [
            f"  - {Colors.BOLD + Colors.SANIC}app{Colors.END}: The Sanic application instance - {Colors.BOLD + Colors.BLUE}{str(app)}{Colors.END}",  # noqa: E501
            f"  - {Colors.BOLD + Colors.SANIC}sanic{Colors.END}: The Sanic module - {Colors.BOLD + Colors.BLUE}import sanic{Colors.END}",  # noqa: E501
            f"  - {Colors.BOLD + Colors.SANIC}do{Colors.END}: An async function to fake a request to the application - {Colors.BOLD + Colors.BLUE}Result(request, response){Colors.END}",  # noqa: E501
        ]
        if HTTPX_AVAILABLE:
            locals_available["client"] = SanicClient(app)
            variable_descriptions.append(
                f"  - {Colors.BOLD + Colors.SANIC}client{Colors.END}: A client to access the Sanic app instance using httpx - {Colors.BOLD + Colors.BLUE}from httpx import Client{Colors.END}",  # noqa: E501
            )
        else:
            client_availability = (
                f"\n{Colors.YELLOW}The HTTP client has been disabled. "
                "To enable it, install httpx:\n\t"
                f"pip install httpx{Colors.END}\n"
            )
        super().__init__(locals=locals_available)
        self.compile.compiler.flags |= PyCF_ALLOW_TOP_LEVEL_AWAIT
        self.loop = new_event_loop()
        self._start = start
        self._pause_event = threading.Event()
        self._started_event = threading.Event()
        self._interact_thread = threading.Thread(
            target=self._console,
            daemon=True,
        )
        self._monitor_thread = threading.Thread(
            target=self._monitor,
            daemon=True,
        )
        self._async_thread = threading.Thread(
            target=self.loop.run_forever,
            daemon=True,
        )
        self.app = app
        self.resume()
        self.exit_message = "Closing the REPL."
        self.banner_message = "\n".join(
            [
                f"\n{Colors.BOLD}Welcome to the Sanic interactive console{Colors.END}",  # noqa: E501
                client_availability,
                "The following objects are available for your convenience:",  # noqa: E501
                *variable_descriptions,
                "\nThe async/await keywords are available for use here.",  # noqa: E501
                f"To exit, press {Colors.BOLD}CTRL+C{Colors.END}, "
                f"{Colors.BOLD}CTRL+D{Colors.END}, or type {Colors.BOLD}exit(){Colors.END}.\n",  # noqa: E501
            ]
        )

    def pause(self):
        if self.is_paused():
            return
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def runsource(self, source, filename="<input>", symbol="single"):
        if source.strip() == "exit()":
            self._shutdown()
            return False

        if self.is_paused():
            print("Console is paused. Please wait for it to be resumed.")
            return False

        return super().runsource(source, filename, symbol)

    def runcode(self, code):
        future = concurrent.futures.Future()

        async def callback():
            func = FunctionType(code, self.locals)
            try:
                result = func()
                if iscoroutine(result):
                    result = await result
            except BaseException:
                traceback.print_exc()
                result = False
            future.set_result(result)

        self.loop.call_soon_threadsafe(self.loop.create_task, callback())
        return future.result()

    def is_paused(self):
        return not self._pause_event.is_set()

    def _console(self):
        self._started_event.set()
        self.interact(banner=self.banner_message, exitmsg=self.exit_message)
        self._shutdown()

    def _monitor(self):
        if isinstance(self._start, Default):
            enter = f"{Colors.BOLD + Colors.SANIC}ENTER{Colors.END}"
            start = input(f"\nPress {enter} at anytime to start the REPL.\n\n")
            if start:
                return
        try:
            while True:
                if not self._started_event.is_set():
                    self.app.manager.wait_for_ack()
                    self._interact_thread.start()
                elif self.app.manager._all_workers_ack() and self.is_paused():
                    self.resume()
                    print(sys.ps1, end="", flush=True)
                elif (
                    not self.app.manager._all_workers_ack()
                    and not self.is_paused()
                ):
                    self.pause()
                time.sleep(0.1)
        except (ConnectionResetError, BrokenPipeError):
            pass

    def _shutdown(self):
        self.app.manager.monitor_publisher.send("__TERMINATE__")

    def run(self):
        self._monitor_thread.start()
        self._async_thread.start()
