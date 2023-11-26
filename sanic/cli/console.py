import threading
import time

from code import InteractiveConsole
from textwrap import dedent

import sanic

from sanic import Sanic, response
from sanic.log import Colors


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
    import readline
except ImportError:
    print(
        "Module 'readline' not available. History navigation will be limited.",
        file=sys.stderr,
    )


class SanicREPL(InteractiveConsole):
    def __init__(self, app: Sanic):
        locals_available = {
            "app": app,
            "sanic": sanic,
            "Sanic": Sanic,
        }
        client_availability = ""
        variable_descriptions = [
            f"  - {Colors.BOLD + Colors.SANIC}app{Colors.END}: The Sanic application instance - {Colors.BOLD + Colors.BLUE}{str(app)}{Colors.END}",  # noqa: E501
            f"  - {Colors.BOLD + Colors.SANIC}sanic{Colors.END}: The Sanic module",  # noqa: E501
            f"  - {Colors.BOLD + Colors.SANIC}Sanic{Colors.END}: The Sanic class",  # noqa: E501
        ]
        if HTTPX_AVAILABLE:
            locals_available["client"] = SanicClient(app)
            variable_descriptions.append(
                f"  - {Colors.BOLD + Colors.SANIC}client{Colors.END}: The Sanic client instance"
            )
        else:
            client_availability = (
                f"\n{Colors.YELLOW}The client has been disabled. "
                f"To enable it, install httpx:\n\tpip install httpx{Colors.END}\n"
            )
        super().__init__(locals=locals_available)
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
        self.app = app
        self.resume()
        self.exit_message = (
            "Closing the REPL. Press CTRL+C to exit completely."
        )
        self.banner_message = "\n".join(
            [
                f"\n{Colors.BOLD}Welcome to the Sanic interactive console{Colors.END}",
                client_availability,
                "The following variables are available for your convenience:",
                *variable_descriptions,
                f"\nTo exit, press {Colors.BOLD}CTRL+C{Colors.END}\n",
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
            print(self.exit_message)
            return super().runsource(source, filename, symbol)
        if not self.is_paused() or source.strip() == "resume()":
            return super().runsource(source, filename, symbol)
        else:
            print("Console is paused. Please wait for it to be resumed.")
            return False

    def is_paused(self):
        return not self._pause_event.is_set()

    def _console(self):
        self._started_event.set()
        self.interact(banner=self.banner_message, exitmsg=self.exit_message)

    def _monitor(self):
        try:
            while True:
                if not self._started_event.is_set():
                    self.app.manager.wait_for_ack()
                    self._interact_thread.start()
                elif self.app.manager._all_workers_ack() and self.is_paused():
                    self.resume()
                    print(">>> ", end="", flush=True)
                elif (
                    not self.app.manager._all_workers_ack()
                    and not self.is_paused()
                ):
                    self.pause()
                time.sleep(0.1)
        except (ConnectionResetError, BrokenPipeError):
            pass

    def run(self):
        self._monitor_thread.start()
