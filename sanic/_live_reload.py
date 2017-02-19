import os
import signal
import time

from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer


class SanicEventHandler(RegexMatchingEventHandler):
    def __init__(self, interval=1):
        super().__init__(regexes=['.*\.py', '.*\.pyc', '.*\.pyo'])
        self.interval = interval
        self.last_reload = self.current_time

    def on_created(self, event):
        self.trigger_reload(event.src_path)

    def on_modified(self, event):
        self.trigger_reload(event.src_path)

    def on_moved(self, event):
        self.trigger_reload(event.src_path)

    def on_deleted(self, event):
        self.trigger_reload(event.src_path)

    @property
    def current_time(self):
        return time.time()

    def trigger_reload(self, src_path):
        if self.current_time - self.last_reload > self.interval:
            os.kill(os.getpid(), signal.SIGHUP)
            # TODO: Add a log for the src_path and reload mechanisms
            self.last_reload = self.current_time

if __name__ == '__main__':
    import sys
    handler = SanicEventHandler()
    observer = Observer()
    observer.schedule(event_handler=handler, path=sys.argv[1], recursive=True)
    observer.start()
    try:
        while observer.isAlive():
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
