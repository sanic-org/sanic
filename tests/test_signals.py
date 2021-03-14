import asyncio

from inspect import isawaitable

import pytest

from sanic_routing.exceptions import NotFound

from sanic import Blueprint
from sanic.exceptions import InvalidSignal, SanicException


def test_add_signal(app):
    def sync_signal(*_):
        ...

    app.add_signal(sync_signal, "foo.bar.baz")

    assert len(app.signal_router.routes) == 1


def test_add_signal_decorator(app):
    @app.signal("foo.bar.baz")
    def sync_signal(*_):
        ...

    @app.signal("foo.bar.baz")
    async def async_signal(*_):
        ...

    assert len(app.signal_router.routes) == 1


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

    await app.dispatch("foo.bar.baz")
    assert counter == 2


@pytest.mark.asyncio
async def test_dispatch_signal_triggers_triggers_event(app):
    counter = 0

    @app.signal("foo.bar.baz")
    def sync_signal(*args):
        nonlocal app
        nonlocal counter
        signal, *_ = app.signal_router.get("foo.bar.baz")
        counter += signal.ctx.event.is_set()

    app.signal_router.finalize()

    await app.dispatch("foo.bar.baz")
    signal, *_ = app.signal_router.get("foo.bar.baz")

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
    signal, *_ = app.signal_router.get(
        "foo.bar.baz", condition={"blueprint": "bp"}
    )

    await bp.dispatch("foo.bar.baz")
    waiter = bp.event("foo.bar.baz")
    assert isawaitable(waiter)

    fut = asyncio.ensure_future(do_wait())
    signal.ctx.event.set()
    await fut

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


def test_event_not_exist(app):
    with pytest.raises(NotFound, match="Could not find signal does.not.exist"):
        app.event("does.not.exist")


def test_event_not_exist_on_bp(app):
    bp = Blueprint("bp")
    app.blueprint(bp)

    with pytest.raises(NotFound, match="Could not find signal does.not.exist"):
        bp.event("does.not.exist")


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
        ("server.init.before", False),
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
