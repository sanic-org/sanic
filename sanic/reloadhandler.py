import os
import sys

import threading
import subprocess
import signal

try:
    import uvloop as async_loop
except ImportError:
    async_loop = asyncio

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class WatchdogReloaderLoop(object):

    def __init__(self, extra_files=None, interval=1, **kwargs):
        self.app = kwargs.pop('app')
        self.event_loop = kwargs.pop('event_loop')
        super().__init__(extra_files=extra_files, interval=interval, **kwargs)

        self.observable_paths = set()

        def _check_modification(filename):
            if filename in self.extra_files:
                self.trigger_reload(filename)
            dirname = os.path.dirname(filename)
            if dirname.startswith(tuple(self.observable_paths)):
                if filename.endswith(('.pyc', '.pyo')):
                    self.trigger_reload(filename[:-1])
                elif filename.endswith('.py'):
                    self.trigger_reload(filename)

        class _CustomHandler(FileSystemEventHandler):

            def on_created(self, event):
                _check_modification(event.src_path)

            def on_modified(self, event):
                _check_modification(event.src_path)

            def on_moved(self, event):
                _check_modification(event.src_path)
                _check_modification(event.dest_path)

            def on_deleted(self, event):
                _check_modification(event.src_path)

        reloader_name = Observer.__name__.lower()
        if reloader_name.endswith('observer'):
            reloader_name = reloader_name[:-8]
        reloader_name += ' reloader'

        self.name = reloader_name

        self.observer_class = Observer
        self.event_handler = _CustomHandler()
        self.should_reload = False

    def trigger_reload(self, filename):
        """Trigger reload."""
        self.event_loop.call_soon_threadsafe(self._stop_app)

        self.log_reload(filename)
        sys.exit(3)

    def _stop_app(self):
        self.app.stop()

    def run(self):
        watches = {}
        observer = self.observer_class()
        observer.start()

        while not self.should_reload:
            to_delete = set(watches)
            paths = _find_observable_paths(self.extra_files)
            for path in paths:
                if path not in watches:
                    try:
                        watches[path] = observer.schedule(
                            self.event_handler, path, recursive=True)
                    except OSError:
                        # Clear this path from list of watches We don't want
                        # the same error message showing again in the next
                        # iteration.
                        watches[path] = None
                to_delete.discard(path)
            for path in to_delete:
                watch = watches.pop(path, None)
                if watch is not None:
                    observer.unschedule(watch)
            self.observable_paths = paths
            self._sleep(self.interval)

        sys.exit(3)


def run_with_reload(app, **dataset):
    event_loop = async_loop.new_event_loop()

    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))

    reloader = WatchdogReloaderLoop(app=app, event_loop=event_loop)

    thread = threading.Thread(target=reloader.run, args=())
    thread.setDaemon(True)
    thread.start()

    dataset['loop'] = event_loop

    app._run(**dataset)

    args = [sys.executable] + sys.argv

    env_copy = os.environ.copy()

    subprocess.call(args, env=env_copy, close_fds=False)
