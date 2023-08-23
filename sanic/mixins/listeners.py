from enum import Enum, auto
from functools import partial
from typing import Callable, List, Optional, Union, overload

from sanic.base.meta import SanicMeta
from sanic.exceptions import BadRequest
from sanic.models.futures import FutureListener
from sanic.models.handler_types import ListenerType, Sanic


class ListenerEvent(str, Enum):
    def _generate_next_value_(name: str, *args) -> str:  # type: ignore
        return name.lower()

    BEFORE_SERVER_START = "server.init.before"
    AFTER_SERVER_START = "server.init.after"
    BEFORE_SERVER_STOP = "server.shutdown.before"
    AFTER_SERVER_STOP = "server.shutdown.after"
    MAIN_PROCESS_START = auto()
    MAIN_PROCESS_READY = auto()
    MAIN_PROCESS_STOP = auto()
    RELOAD_PROCESS_START = auto()
    RELOAD_PROCESS_STOP = auto()
    BEFORE_RELOAD_TRIGGER = auto()
    AFTER_RELOAD_TRIGGER = auto()


class ListenerMixin(metaclass=SanicMeta):
    def __init__(self, *args, **kwargs) -> None:
        self._future_listeners: List[FutureListener] = []

    def _apply_listener(self, listener: FutureListener):
        raise NotImplementedError  # noqa

    @overload
    def listener(
        self,
        listener_or_event: ListenerType[Sanic],
        event_or_none: str,
        apply: bool = ...,
    ) -> ListenerType[Sanic]:
        ...

    @overload
    def listener(
        self,
        listener_or_event: str,
        event_or_none: None = ...,
        apply: bool = ...,
    ) -> Callable[[ListenerType[Sanic]], ListenerType[Sanic]]:
        ...

    def listener(
        self,
        listener_or_event: Union[ListenerType[Sanic], str],
        event_or_none: Optional[str] = None,
        apply: bool = True,
    ) -> Union[
        ListenerType[Sanic],
        Callable[[ListenerType[Sanic]], ListenerType[Sanic]],
    ]:
        """
        Create a listener from a decorated function.

        To be used as a decorator:

        .. code-block:: python

            @bp.listener("before_server_start")
            async def before_server_start(app, loop):
                ...

        `See user guide re: listeners
        <https://sanicframework.org/guide/basics/listeners.html#listeners>`__

        :param event: event to listen to
        """

        def register_listener(
            listener: ListenerType[Sanic], event: str
        ) -> ListenerType[Sanic]:
            nonlocal apply

            future_listener = FutureListener(listener, event)
            self._future_listeners.append(future_listener)
            if apply:
                self._apply_listener(future_listener)
            return listener

        if callable(listener_or_event):
            if event_or_none is None:
                raise BadRequest(
                    "Invalid event registration: Missing event name."
                )
            return register_listener(listener_or_event, event_or_none)
        else:
            return partial(register_listener, event=listener_or_event)

    def main_process_start(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the main_process_start event.

        This event is fired only on the main process and **NOT** on any
        worker processes. You should typically use this event to initialize
        resources that are shared across workers, or to initialize resources
        that are not safe to be initialized in a worker process.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.main_process_start
            async def on_main_process_start(app: Sanic):
                print("Main process started")
            ```
        """  # noqa: E501
        return self.listener(listener, "main_process_start")

    def main_process_ready(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the main_process_ready event.

        This event is fired only on the main process and **NOT** on any
        worker processes. It is fired after the main process has started and
        the Worker Manager has been initialized (ie, you will have access to
        `app.manager` instance). The typical use case for this event is to
        add a managed process to the Worker Manager.

        See [Running custom processes](/en/guide/deployment/manager.html#running-custom-processes) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.main_process_ready
            async def on_main_process_ready(app: Sanic):
                print("Main process ready")
            ```
        """  # noqa: E501
        return self.listener(listener, "main_process_ready")

    def main_process_stop(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        return self.listener(listener, "main_process_stop")

    def reload_process_start(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        return self.listener(listener, "reload_process_start")

    def reload_process_stop(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        return self.listener(listener, "reload_process_stop")

    def before_reload_trigger(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        return self.listener(listener, "before_reload_trigger")

    def after_reload_trigger(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        return self.listener(listener, "after_reload_trigger")

    def before_server_start(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        return self.listener(listener, "before_server_start")

    def after_server_start(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        return self.listener(listener, "after_server_start")

    def before_server_stop(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        return self.listener(listener, "before_server_stop")

    def after_server_stop(
        self, listener: ListenerType[Sanic]
    ) -> ListenerType[Sanic]:
        return self.listener(listener, "after_server_stop")
