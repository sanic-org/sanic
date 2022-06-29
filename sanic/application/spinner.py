import os
import sys
import time

from contextlib import contextmanager
from queue import Queue
from threading import Thread


if os.name == "nt":  # noqa
    import ctypes  # noqa

    class _CursorInfo(ctypes.Structure):
        _fields_ = [("size", ctypes.c_int), ("visible", ctypes.c_byte)]


class Spinner:  # noqa
    def __init__(self, message: str) -> None:
        self.message = message
        self.queue: Queue[int] = Queue()
        self.spinner = self.cursor()
        self.thread = Thread(target=self.run)

    def start(self):
        self.queue.put(1)
        self.thread.start()
        self.hide()

    def run(self):
        while self.queue.get():
            output = f"\r{self.message} [{next(self.spinner)}]"
            sys.stdout.write(output)
            sys.stdout.flush()
            time.sleep(0.1)
            self.queue.put(1)

    def stop(self):
        self.queue.put(0)
        self.thread.join()
        self.show()

    @staticmethod
    def cursor():
        while True:
            for cursor in "|/-\\":
                yield cursor

    @staticmethod
    def hide():
        if os.name == "nt":
            ci = _CursorInfo()
            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            ctypes.windll.kernel32.GetConsoleCursorInfo(
                handle, ctypes.byref(ci)
            )
            ci.visible = False
            ctypes.windll.kernel32.SetConsoleCursorInfo(
                handle, ctypes.byref(ci)
            )
        elif os.name == "posix":
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()

    @staticmethod
    def show():
        if os.name == "nt":
            ci = _CursorInfo()
            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            ctypes.windll.kernel32.GetConsoleCursorInfo(
                handle, ctypes.byref(ci)
            )
            ci.visible = True
            ctypes.windll.kernel32.SetConsoleCursorInfo(
                handle, ctypes.byref(ci)
            )
        elif os.name == "posix":
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()


@contextmanager
def loading(message: str = "Loading"):  # noqa
    spinner = Spinner(message)
    spinner.start()
    yield
    spinner.stop()
