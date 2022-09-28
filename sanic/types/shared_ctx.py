import os

from types import SimpleNamespace
from typing import Any, Iterable

from sanic.log import Colors, error_logger


class SharedContext(SimpleNamespace):
    SAFE = ("_lock",)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._lock = False

    def __setattr__(self, name: str, value: Any) -> None:
        if self.is_locked:
            raise RuntimeError(
                f"Cannot set {name} on locked SharedContext object"
            )
        if not os.environ.get("SANIC_WORKER_NAME"):
            to_check: Iterable[Any]
            if not isinstance(value, (tuple, frozenset)):
                to_check = [value]
            else:
                to_check = value
            for item in to_check:
                self._check(name, item)
        super().__setattr__(name, value)

    def _check(self, name: str, value: Any) -> None:
        if name in self.SAFE:
            return
        try:
            module = value.__module__
        except AttributeError:
            module = ""
        if not any(
            module.startswith(prefix)
            for prefix in ("multiprocessing", "ctypes")
        ):
            error_logger.warning(
                f"{Colors.YELLOW}Unsafe object {Colors.PURPLE}{name} "
                f"{Colors.YELLOW}with type {Colors.PURPLE}{type(value)} "
                f"{Colors.YELLOW}was added to shared_ctx. It may not "
                "not function as intended. Consider using the regular "
                f"ctx.\nFor more information, please see https://sanic.dev/en"
                "/guide/deployment/manager.html#using-shared-context-between-"
                f"worker-processes.{Colors.END}"
            )

    @property
    def is_locked(self) -> bool:
        return getattr(self, "_lock", False)

    def lock(self) -> None:
        self._lock = True
