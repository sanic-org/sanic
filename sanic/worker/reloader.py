from typing import Any


class Reloader:
    def __init__(self, publisher):
        self.publisher = publisher

    def __call__(self, **kwargs: Any) -> None:
        print("RELOADER", kwargs)
