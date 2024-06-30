from enum import Enum, auto
from functools import partial
from typing import Callable, List, Optional, Union, cast, overload

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
        *,
        priority: int = 0,
    ) -> ListenerType[Sanic]: ...

    @overload
    def listener(
        self,
        listener_or_event: str,
        event_or_none: None = ...,
        apply: bool = ...,
        *,
        priority: int = 0,
    ) -> Callable[[ListenerType[Sanic]], ListenerType[Sanic]]: ...

    def listener(
        self,
        listener_or_event: Union[ListenerType[Sanic], str],
        event_or_none: Optional[str] = None,
        apply: bool = True,
        *,
        priority: int = 0,
    ) -> Union[
        ListenerType[Sanic],
        Callable[[ListenerType[Sanic]], ListenerType[Sanic]],
    ]:
        """Create a listener for a specific event in the application's lifecycle.

        See [Listeners](/en/guide/basics/listeners) for more details.

        .. note::
            Overloaded signatures allow for different ways of calling this method, depending on the types of the arguments.

            Usually, it is prederred to use one of the convenience methods such as `before_server_start` or `after_server_stop` instead of calling this method directly.

            ```python
            @app.before_server_start
            async def prefered_method(_):
                ...

            @app.listener("before_server_start")
            async def not_prefered_method(_):
                ...

        Args:
            listener_or_event (Union[ListenerType[Sanic], str]): A listener function or an event name.
            event_or_none (Optional[str]): The event name to listen for if `listener_or_event` is a function. Defaults to `None`.
            apply (bool): Whether to apply the listener immediately. Defaults to `True`.
            priority (int): The priority of the listener. Defaults to `0`.

        Returns:
            Union[ListenerType[Sanic], Callable[[ListenerType[Sanic]], ListenerType[Sanic]]]: The listener or a callable that takes a listener.

        Example:
            The following code snippet shows how you can use this method as a decorator:

            ```python
            @bp.listener("before_server_start")
            async def before_server_start(app, loop):
                ...
            ```
        """  # noqa: E501

        def register_listener(
            listener: ListenerType[Sanic], event: str, priority: int = 0
        ) -> ListenerType[Sanic]:
            """A helper function to register a listener for an event.

            Typically will not be called directly.

            Args:
                listener (ListenerType[Sanic]): The listener function to
                    register.
                event (str): The event name to listen for.

            Returns:
                ListenerType[Sanic]: The listener function that was registered.
            """
            nonlocal apply

            future_listener = FutureListener(listener, event, priority)
            self._future_listeners.append(future_listener)
            if apply:
                self._apply_listener(future_listener)
            return listener

        if callable(listener_or_event):
            if event_or_none is None:
                raise BadRequest(
                    "Invalid event registration: Missing event name."
                )
            return register_listener(
                listener_or_event, event_or_none, priority
            )
        else:
            return partial(
                register_listener, event=listener_or_event, priority=priority
            )

    def _setup_listener(
        self,
        listener: Optional[ListenerType[Sanic]],
        event: str,
        priority: int,
    ) -> ListenerType[Sanic]:
        if listener is not None:
            return self.listener(listener, event, priority=priority)
        return cast(
            ListenerType[Sanic],
            partial(self.listener, event_or_none=event, priority=priority),
        )

    def main_process_start(
        self, listener: Optional[ListenerType[Sanic]], *, priority: int = 0
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the main_process_start event.

        This event is fired only on the main process and **NOT** on any
        worker processes. You should typically use this event to initialize
        resources that are shared across workers, or to initialize resources
        that are not safe to be initialized in a worker process.

        See [Listeners](/en/guide/basics/listeners) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.main_process_start
            async def on_main_process_start(app: Sanic):
                print("Main process started")
            ```
        """  # noqa: E501
        return self._setup_listener(listener, "main_process_start", priority)

    def main_process_ready(
        self, listener: Optional[ListenerType[Sanic]], *, priority: int = 0
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the main_process_ready event.

        This event is fired only on the main process and **NOT** on any
        worker processes. It is fired after the main process has started and
        the Worker Manager has been initialized (ie, you will have access to
        `app.manager` instance). The typical use case for this event is to
        add a managed process to the Worker Manager.

        See [Running custom processes](/en/guide/deployment/manager.html#running-custom-processes) and [Listeners](/en/guide/basics/listeners.html) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.main_process_ready
            async def on_main_process_ready(app: Sanic):
                print("Main process ready")
            ```
        """  # noqa: E501
        return self._setup_listener(listener, "main_process_ready", priority)

    def main_process_stop(
        self, listener: Optional[ListenerType[Sanic]], *, priority: int = 0
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the main_process_stop event.

        This event is fired only on the main process and **NOT** on any
        worker processes. You should typically use this event to clean up
        resources that were initialized in the main_process_start event.

        See [Listeners](/en/guide/basics/listeners) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.main_process_stop
            async def on_main_process_stop(app: Sanic):
                print("Main process stopped")
            ```
        """  # noqa: E501
        return self._setup_listener(listener, "main_process_stop", priority)

    def reload_process_start(
        self, listener: Optional[ListenerType[Sanic]], *, priority: int = 0
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the reload_process_start event.

        This event is fired only on the reload process and **NOT** on any
        worker processes. This is similar to the main_process_start event,
        except that it is fired only when the reload process is started.

        See [Listeners](/en/guide/basics/listeners) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.reload_process_start
            async def on_reload_process_start(app: Sanic):
                print("Reload process started")
            ```
        """  # noqa: E501
        return self._setup_listener(listener, "reload_process_start", priority)

    def reload_process_stop(
        self, listener: Optional[ListenerType[Sanic]], *, priority: int = 0
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the reload_process_stop event.

        This event is fired only on the reload process and **NOT** on any
        worker processes. This is similar to the main_process_stop event,
        except that it is fired only when the reload process is stopped.

        See [Listeners](/en/guide/basics/listeners) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.reload_process_stop
            async def on_reload_process_stop(app: Sanic):
                print("Reload process stopped")
            ```
        """  # noqa: E501
        return self._setup_listener(listener, "reload_process_stop", priority)

    def before_reload_trigger(
        self, listener: Optional[ListenerType[Sanic]], *, priority: int = 0
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the before_reload_trigger event.

        This event is fired only on the reload process and **NOT** on any
        worker processes. This event is fired before the reload process
        triggers the reload. A change event has been detected and the reload
        process is about to be triggered.

        See [Listeners](/en/guide/basics/listeners) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.before_reload_trigger
            async def on_before_reload_trigger(app: Sanic):
                print("Before reload trigger")
            ```
        """  # noqa: E501
        return self._setup_listener(
            listener, "before_reload_trigger", priority
        )

    def after_reload_trigger(
        self, listener: Optional[ListenerType[Sanic]], *, priority: int = 0
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the after_reload_trigger event.

        This event is fired only on the reload process and **NOT** on any
        worker processes. This event is fired after the reload process
        triggers the reload. A change event has been detected and the reload
        process has been triggered.

        See [Listeners](/en/guide/basics/listeners) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.after_reload_trigger
            async def on_after_reload_trigger(app: Sanic, changed: set[str]):
                print("After reload trigger, changed files: ", changed)
            ```
        """  # noqa: E501
        return self._setup_listener(listener, "after_reload_trigger", priority)

    def before_server_start(
        self,
        listener: Optional[ListenerType[Sanic]] = None,
        *,
        priority: int = 0,
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the before_server_start event.

        This event is fired on all worker processes. You should typically
        use this event to initialize resources that are global in nature, or
        will be shared across requests and various parts of the application.

        A common use case for this event is to initialize a database connection
        pool, or to initialize a cache client.

        See [Listeners](/en/guide/basics/listeners) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.before_server_start
            async def on_before_server_start(app: Sanic):
                print("Before server start")
            ```
        """  # noqa: E501
        return self._setup_listener(listener, "before_server_start", priority)

    def after_server_start(
        self, listener: Optional[ListenerType[Sanic]], *, priority: int = 0
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the after_server_start event.

        This event is fired on all worker processes. You should typically
        use this event to run background tasks, or perform other actions that
        are not directly related to handling requests. In theory, it is
        possible that some requests may be handled before this event is fired,
        so you should not use this event to initialize resources that are
        required for handling requests.

        A common use case for this event is to start a background task that
        periodically performs some action, such as clearing a cache or
        performing a health check.

        See [Listeners](/en/guide/basics/listeners) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.after_server_start
            async def on_after_server_start(app: Sanic):
                print("After server start")
            ```
        """  # noqa: E501
        return self._setup_listener(listener, "after_server_start", priority)

    def before_server_stop(
        self, listener: Optional[ListenerType[Sanic]], *, priority: int = 0
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the before_server_stop event.

        This event is fired on all worker processes. This event is fired
        before the server starts shutting down. You should not use this event
        to perform any actions that are required for handling requests, as
        some requests may continue to be handled after this event is fired.

        A common use case for this event is to stop a background task that
        was started in the after_server_start event.

        See [Listeners](/en/guide/basics/listeners) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.before_server_stop
            async def on_before_server_stop(app: Sanic):
                print("Before server stop")
            ```
        """  # noqa: E501
        return self._setup_listener(listener, "before_server_stop", priority)

    def after_server_stop(
        self, listener: Optional[ListenerType[Sanic]], *, priority: int = 0
    ) -> ListenerType[Sanic]:
        """Decorator for registering a listener for the after_server_stop event.

        This event is fired on all worker processes. This event is fired
        after the server has stopped shutting down, and all requests have
        been handled. You should typically use this event to clean up
        resources that were initialized in the before_server_start event.

        A common use case for this event is to close a database connection
        pool, or to close a cache client.

        See [Listeners](/en/guide/basics/listeners) for more details.

        Args:
            listener (ListenerType[Sanic]): The listener handler to attach.

        Examples:
            ```python
            @app.after_server_stop
            async def on_after_server_stop(app: Sanic):
                print("After server stop")
            ```
        """  # noqa: E501
        return self._setup_listener(listener, "after_server_stop", priority)
