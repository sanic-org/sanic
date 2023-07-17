import asyncio

from enum import Enum
from inspect import isawaitable

import pytest

from sanic_routing.exceptions import NotFound

from sanic import Blueprint, Sanic, empty
from sanic.exceptions import InvalidSignal, SanicException
from sanic.signals import Event


def test_add_signal(app):
    def sync_signal(*_):
        ...

    app.add_signal(sync_signal, "foo.bar.baz")

    assert len(app.signal_router.routes) == 1


def test_add_signal_method_handler(app):
    counter = 0

    class TestSanic(Sanic):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.add_signal(
                self.after_routing_signal_handler, "http.routing.after"
            )

        def after_routing_signal_handler(self, *args, **kwargs):
            nonlocal counter
            counter += 1

    app = TestSanic("Test")
    assert len(app.signal_router.routes) == 1

    @app.route("/")
    async def handler(_):
        return empty()

    app.test_client.get("/")
    assert counter == 1


def test_add_signal_decorator(app):
    @app.signal("foo.bar.baz")
    def sync_signal(*_):
        ...

    @app.signal("foo.bar.baz")
    async def async_signal(*_):
        ...

    assert len(app.signal_router.routes) == 2
    assert len(app.signal_router.dynamic_routes) == 1


@pytest.mark.parametrize(
    "signal",
    (
        "<foo>.bar.bax",
        "foo.<bar>.baz",
        "foo",
        "foo.bar",
        "foo.bar.baz.qux",
    ),
)
def test_invalid_signal(app, signal):
    with pytest.raises(InvalidSignal, match=f"Invalid signal event: {signal}"):

        @app.signal(signal)
        def handler():
            ...


@pytest.mark.asyncio
async def test_dispatch_signal_with_enum_event(app):
    counter = 0

    class FooEnum(Enum):
        FOO_BAR_BAZ = "foo.bar.baz"

    @app.signal(FooEnum.FOO_BAR_BAZ)
    def sync_signal(*_):
        nonlocal counter

        counter += 1

    app.signal_router.finalize()

    await app.dispatch("foo.bar.baz")
    assert counter == 1


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_multiple_handlers(app):
    counter = 0

    @app.signal("foo.bar.baz")
    def sync_signal(*_):
        nonlocal counter

        counter += 1

    @app.signal("foo.bar.baz")
    async def async_signal(*_):
        nonlocal counter

        counter += 1

    app.signal_router.finalize()

    assert len(app.signal_router.routes) == 3
    await app.dispatch("foo.bar.baz")
    assert counter == 2


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_triggers_event(app):
    counter = 0

    @app.signal("foo.bar.baz")
    def sync_signal(*args):
        nonlocal app
        nonlocal counter
        group, *_ = app.signal_router.get("foo.bar.baz")
        for signal in group:
            counter += signal.ctx.event.is_set()

    app.signal_router.finalize()

    await app.dispatch("foo.bar.baz")

    assert counter == 1


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_dynamic_route(app):
    counter = 0

    @app.signal("foo.bar.<baz:int>")
    def sync_signal(baz):
        nonlocal counter

        counter += baz

    app.signal_router.finalize()

    await app.dispatch("foo.bar.9")
    assert counter == 9


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_with_requirements(app):
    counter = 0

    @app.signal("foo.bar.baz", condition={"one": "two"})
    def sync_signal(*_):
        nonlocal counter
        counter += 1

    app.signal_router.finalize()

    await app.dispatch("foo.bar.baz")
    assert counter == 0
    await app.dispatch("foo.bar.baz", condition={"one": "two"})
    assert counter == 1


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_with_requirements_exclusive(app):
    counter = 0

    @app.signal("foo.bar.baz", condition={"one": "two"}, exclusive=False)
    def sync_signal(*_):
        nonlocal counter
        counter += 1

    app.signal_router.finalize()

    await app.dispatch("foo.bar.baz")
    assert counter == 1
    await app.dispatch("foo.bar.baz", condition={"one": "two"})
    assert counter == 2


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_with_context(app):
    counter = 0

    @app.signal("foo.bar.baz")
    def sync_signal(amount):
        nonlocal counter
        counter += amount

    app.signal_router.finalize()

    await app.dispatch("foo.bar.baz", context={"amount": 9})
    assert counter == 9


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_with_context_fail(app):
    counter = 0

    @app.signal("foo.bar.baz")
    def sync_signal(amount):
        nonlocal counter
        counter += amount

    app.signal_router.finalize()

    with pytest.raises(TypeError):
        await app.dispatch("foo.bar.baz", {"amount": 9})


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_on_bp(app):
    bp = Blueprint("bp")

    app_counter = 0
    bp_counter = 0

    @app.signal("foo.bar.baz")
    def app_signal():
        nonlocal app_counter
        app_counter += 1

    @bp.signal("foo.bar.baz")
    def bp_signal():
        nonlocal bp_counter
        bp_counter += 1

    app.blueprint(bp)
    app.signal_router.finalize()

    await app.dispatch("foo.bar.baz")
    assert app_counter == 1
    assert bp_counter == 1

    await bp.dispatch("foo.bar.baz")
    assert app_counter == 1
    assert bp_counter == 2


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_on_bp_alone(app):
    bp = Blueprint("bp")

    bp_counter = 0

    @bp.signal("foo.bar.baz")
    def bp_signal():
        nonlocal bp_counter
        bp_counter += 1

    app.blueprint(bp)
    app.signal_router.finalize()
    await app.dispatch("foo.bar.baz")
    await bp.dispatch("foo.bar.baz")
    assert bp_counter == 2


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_event(app):
    app_counter = 0

    @app.signal("foo.bar.baz")
    def app_signal():
        ...

    async def do_wait():
        nonlocal app_counter
        await app.event("foo.bar.baz")
        app_counter += 1

    app.signal_router.finalize()

    await app.dispatch("foo.bar.baz")
    waiter = app.event("foo.bar.baz")
    assert isawaitable(waiter)

    fut = asyncio.ensure_future(do_wait())
    await app.dispatch("foo.bar.baz")
    await fut

    assert app_counter == 1


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_event_on_bp(app):
    bp = Blueprint("bp")
    bp_counter = 0

    @bp.signal("foo.bar.baz")
    def bp_signal():
        ...

    async def do_wait():
        nonlocal bp_counter
        await bp.event("foo.bar.baz")
        bp_counter += 1

    app.blueprint(bp)
    app.signal_router.finalize()
    signal_group, *_ = app.signal_router.get(
        "foo.bar.baz", condition={"blueprint": "bp"}
    )

    await bp.dispatch("foo.bar.baz")
    waiter = bp.event("foo.bar.baz")
    assert isawaitable(waiter)

    fut = do_wait()
    for signal in signal_group:
        signal.ctx.event.set()
    await asyncio.gather(fut)

    assert bp_counter == 1


def test_bad_finalize(app):
    counter = 0

    @app.signal("foo.bar.baz")
    def sync_signal(amount):
        nonlocal counter
        counter += amount

    with pytest.raises(
        RuntimeError, match="Cannot finalize signals outside of event loop"
    ):
        app.signal_router.finalize()

    assert counter == 0


@pytest.mark.asyncio
async def test_event_not_exist(app):
    with pytest.raises(NotFound, match="Could not find signal does.not.exist"):
        await app.event("does.not.exist")


@pytest.mark.asyncio
async def test_event_not_exist_on_bp(app):
    bp = Blueprint("bp")
    app.blueprint(bp)

    with pytest.raises(NotFound, match="Could not find signal does.not.exist"):
        await bp.event("does.not.exist")


@pytest.mark.asyncio
async def test_event_not_exist_with_autoregister(app):
    app.config.EVENT_AUTOREGISTER = True
    try:
        await app.event("does.not.exist", timeout=0.1)
    except asyncio.TimeoutError:
        ...


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_non_exist_event_with_autoregister(app):
    @app.signal("some.stand.in")
    async def signal_handler():
        ...

    app.config.EVENT_AUTOREGISTER = True
    app_counter = 0
    app.signal_router.finalize()

    async def do_wait():
        nonlocal app_counter
        await app.event("foo.bar.baz")
        app_counter += 1

    fut = asyncio.ensure_future(do_wait())
    await app.dispatch("foo.bar.baz")
    await fut

    assert app_counter == 1


@pytest.mark.asyncio
async def test_dispatch_not_exist(app):
    @app.signal("do.something.start")
    async def signal_handler():
        ...

    app.signal_router.finalize()
    await app.dispatch("does.not.exist")


def test_event_on_bp_not_registered():
    bp = Blueprint("bp")

    @bp.signal("foo.bar.baz")
    def bp_signal():
        ...

    with pytest.raises(
        SanicException,
        match="<Blueprint bp> has not yet been registered to an app",
    ):
        bp.event("foo.bar.baz")


@pytest.mark.parametrize(
    "event,expected",
    (
        ("foo.bar.baz", True),
        ("server.init.before", True),
        ("server.init.somethingelse", False),
        ("http.request.start", False),
        ("sanic.notice.anything", True),
    ),
)
def test_signal_reservation(app, event, expected):
    if not expected:
        with pytest.raises(
            InvalidSignal,
            match=f"Cannot declare reserved signal event: {event}",
        ):
            app.signal(event)(lambda: ...)
    else:
        app.signal(event)(lambda: ...)


@pytest.mark.asyncio
async def test_report_exception(app: Sanic):
    @app.report_exception
    async def catch_any_exception(app: Sanic, exception: Exception):
        ...

    @app.route("/")
    async def handler(request):
        1 / 0

    app.signal_router.finalize()

    registered_signal_handlers = [
        handler
        for handler, *_ in app.signal_router.get(
            Event.SERVER_GLOBAL_EXCEPTION.value
        )
    ]

    assert catch_any_exception in registered_signal_handlers


def test_report_exception_runs(app: Sanic):
    event = asyncio.Event()

    @app.report_exception
    async def catch_any_exception(app: Sanic, exception: Exception):
        event.set()

    @app.route("/")
    async def handler(request):
        1 / 0

    app.test_client.get("/")

    assert event.is_set()
