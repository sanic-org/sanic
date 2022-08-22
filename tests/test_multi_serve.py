# import logging

# from unittest.mock import Mock

# import pytest

# from sanic import Sanic
# from sanic.response import text
# from sanic.server.async_server import AsyncioServer
# from sanic.signals import Event
# from sanic.touchup.schemes.ode import OptionalDispatchEvent


# try:
#     from unittest.mock import AsyncMock
# except ImportError:
#     from tests.asyncmock import AsyncMock  # type: ignore


# @pytest.fixture
# def app_one():
#     app = Sanic("One")

#     @app.get("/one")
#     async def one(request):
#         return text("one")

#     return app


# @pytest.fixture
# def app_two():
#     app = Sanic("Two")

#     @app.get("/two")
#     async def two(request):
#         return text("two")

#     return app


# @pytest.fixture(autouse=True)
# def clean():
#     Sanic._app_registry = {}
#     yield


# def test_serve_same_app_multiple_tuples(app_one, run_multi):
#     app_one.prepare(port=23456)
#     app_one.prepare(port=23457)

#     logs = run_multi(app_one)
#     assert (
#         "sanic.root",
#         logging.INFO,
#         "Goin' Fast @ http://127.0.0.1:23456",
#     ) in logs
#     assert (
#         "sanic.root",
#         logging.INFO,
#         "Goin' Fast @ http://127.0.0.1:23457",
#     ) in logs


# def test_serve_multiple_apps(app_one, app_two, run_multi):
#     app_one.prepare(port=23456)
#     app_two.prepare(port=23457)

#     logs = run_multi(app_one)
#     assert (
#         "sanic.root",
#         logging.INFO,
#         "Goin' Fast @ http://127.0.0.1:23456",
#     ) in logs
#     assert (
#         "sanic.root",
#         logging.INFO,
#         "Goin' Fast @ http://127.0.0.1:23457",
#     ) in logs


# def test_listeners_on_secondary_app(app_one, app_two, run_multi):
#     app_one.prepare(port=23456)
#     app_two.prepare(port=23457)

#     before_start = AsyncMock()
#     after_start = AsyncMock()
#     before_stop = AsyncMock()
#     after_stop = AsyncMock()

#     app_two.before_server_start(before_start)
#     app_two.after_server_start(after_start)
#     app_two.before_server_stop(before_stop)
#     app_two.after_server_stop(after_stop)

#     run_multi(app_one)

#     before_start.assert_awaited_once()
#     after_start.assert_awaited_once()
#     before_stop.assert_awaited_once()
#     after_stop.assert_awaited_once()


# @pytest.mark.parametrize(
#     "events",
#     (
#         (Event.HTTP_LIFECYCLE_BEGIN,),
#         (Event.HTTP_LIFECYCLE_BEGIN, Event.HTTP_LIFECYCLE_COMPLETE),
#         (
#             Event.HTTP_LIFECYCLE_BEGIN,
#             Event.HTTP_LIFECYCLE_COMPLETE,
#             Event.HTTP_LIFECYCLE_REQUEST,
#         ),
#     ),
# )
# def test_signal_synchronization(app_one, app_two, run_multi, events):
#     app_one.prepare(port=23456)
#     app_two.prepare(port=23457)

#     for event in events:
#         app_one.signal(event)(AsyncMock())

#     run_multi(app_one)

#     assert len(app_two.signal_router.routes) == len(events) + 1

#     signal_handlers = {
#         signal.handler
#         for signal in app_two.signal_router.routes
#         if signal.name.startswith("http")
#     }

#     assert len(signal_handlers) == 1
#     assert list(signal_handlers)[0] is OptionalDispatchEvent.noop


# def test_warning_main_process_listeners_on_secondary(
#     app_one, app_two, run_multi
# ):
#     app_two.main_process_start(AsyncMock())
#     app_two.main_process_stop(AsyncMock())
#     app_one.prepare(port=23456)
#     app_two.prepare(port=23457)

#     log = run_multi(app_one)

#     message = (
#         f"Sanic found 2 listener(s) on "
#         "secondary applications attached to the main "
#         "process. These will be ignored since main "
#         "process listeners can only be attached to your "
#         "primary application: "
#         f"{repr(app_one)}"
#     )

#     assert ("sanic.error", logging.WARNING, message) in log


# def test_no_applications():
#     Sanic._app_registry = {}
#     message = "Did not find any applications."
#     with pytest.raises(RuntimeError, match=message):
#         Sanic.serve()


# def test_oserror_warning(app_one, app_two, run_multi, capfd):
#     orig = AsyncioServer.__await__
#     AsyncioServer.__await__ = Mock(side_effect=OSError("foo"))
#     app_one.prepare(port=23456, workers=2)
#     app_two.prepare(port=23457, workers=2)

#     run_multi(app_one)

#     captured = capfd.readouterr()
#     assert (
#         "An OSError was detected on startup. The encountered error was: foo"
#     ) in captured.err

#     AsyncioServer.__await__ = orig


# def test_running_multiple_offset_warning(app_one, app_two, run_multi, capfd):
#     app_one.prepare(port=23456, workers=2)
#     app_two.prepare(port=23457)

#     run_multi(app_one)

#     captured = capfd.readouterr()
#     assert (
#         f"The primary application {repr(app_one)} is running "
#         "with 2 worker(s). All "
#         "application instances will run with the same number. "
#         f"You requested {repr(app_two)} to run with "
#         "1 worker(s), which will be ignored "
#         "in favor of the primary application."
#     ) in captured.err


# def test_running_multiple_secondary(app_one, app_two, run_multi, capfd):
#     app_one.prepare(port=23456, workers=2)
#     app_two.prepare(port=23457)

#     before_start = AsyncMock()
#     app_two.before_server_start(before_start)
#     run_multi(app_one)

#     before_start.await_count == 2
