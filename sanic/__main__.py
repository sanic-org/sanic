import os
import sys
import time
from argparse import ArgumentParser
from importlib import import_module
from subprocess import Popen
from signal import SIGTERM
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from .log import log
from .sanic import Sanic


class RestartHandler(PatternMatchingEventHandler):

    def __init__(self, executable, args):
        super().__init__(patterns=['*.py'])
        self._args = (
            [executable, '-m', 'sanic'] + args[1:]
            + ['--no_restart'])
        self._start()
        self._last_time = 0
        self._skip_time = 0.75

    def _start(self):
        proc = Popen(self._args)
        self.pid = proc.pid
        self._last_time = time.time()

    def on_any_event(self, event):
        now = time.time()
        if (now - self._last_time) < self._skip_time:
            return
        os.kill(self.pid, SIGTERM)
        time.sleep(0.5)
        self._start()


if __name__ == "__main__":
    parser = ArgumentParser(prog='sanic')
    parser.add_argument('--host', dest='host', type=str, default='127.0.0.1')
    parser.add_argument('--port', dest='port', type=int, default=8000)
    parser.add_argument('--workers', dest='workers', type=int, default=1, )
    parser.add_argument('--debug', dest='debug', action="store_true")
    parser.add_argument('--no_restart', dest='no_restart', action="store_true")
    parser.add_argument('module')
    args = parser.parse_args()

    try:
        if args.debug and not args.no_restart:
            path = os.getcwd()
            observer = Observer()
            handler = RestartHandler(sys.executable, sys.argv)
            observer.schedule(handler, path, recursive=True)
            observer.start()
            while True:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    os.kill(handler.pid, SIGTERM)
                    time.sleep(0.6)
                    observer.stop()
                    break
            observer.join()
        else:
            module_parts = args.module.split(".")
            module_name = ".".join(module_parts[:-1])
            app_name = module_parts[-1]
            module = import_module(module_name)
            app = getattr(module, app_name, None)
            if type(app) is not Sanic:
                raise ValueError("Module is not a Sanic app, it is a {}.  "
                                 "Perhaps you meant {}.app?"
                                 .format(type(app).__name__, args.module))
            app.run(host=args.host, port=args.port,
                    workers=args.workers, debug=args.debug)
    except ImportError:
        log.error("No module named {} found.\n"
                  "  Example File: project/sanic_server.py -> app\n"
                  "  Example Module: project.sanic_server.app"
                  .format(module_name))
    except ValueError as e:
        log.error("{}".format(e))
