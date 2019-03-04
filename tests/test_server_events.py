import signal

import pytest

from sanic.testing import HOST, PORT

AVAILABLE_LISTENERS = [
    "before_server_start",
    "after_server_start",
    "before_server_stop",
    "after_server_stop",
]

skipif_no_alarm = pytest.mark.skipif(
    not hasattr(signal, "SIGALRM"),
    reason="SIGALRM is not implemented for this platform, we have to come "
    "up with another timeout strategy to test these",
)


def create_listener(listener_name, in_list):
    async def _listener(app, loop):
        print("DEBUG MESSAGE FOR PYTEST for {}".format(listener_name))
        in_list.insert(0, app.name + listener_name)

    return _listener


def start_stop_app(random_name_app, **run_kwargs):
    def stop_on_alarm(signum, frame):
        raise KeyboardInterrupt("SIGINT for sanic to stop gracefully")

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(1)
    try:
        random_name_app.run(HOST, PORT, **run_kwargs)
    except KeyboardInterrupt:
        pass


@skipif_no_alarm
@pytest.mark.parametrize("listener_name", AVAILABLE_LISTENERS)
def test_single_listener(app, listener_name):
    """Test that listeners on their own work"""
    output = []
    # Register listener
    app.listener(listener_name)(create_listener(listener_name, output))
    start_stop_app(app)
    assert app.name + listener_name == output.pop()


@skipif_no_alarm
@pytest.mark.parametrize("listener_name", AVAILABLE_LISTENERS)
def test_register_listener(app, listener_name):
    """
    Test that listeners on their own work with
    app.register_listener method
    """
    output = []
    # Register listener
    listener = create_listener(listener_name, output)
    app.register_listener(listener, event=listener_name)
    start_stop_app(app)
    assert app.name + listener_name == output.pop()


@skipif_no_alarm
def test_all_listeners(app):
    output = []
    for listener_name in AVAILABLE_LISTENERS:
        listener = create_listener(listener_name, output)
        app.listener(listener_name)(listener)
    start_stop_app(app)
    for listener_name in AVAILABLE_LISTENERS:
        assert app.name + listener_name == output.pop()


async def test_trigger_before_events_create_server(app):
    class MySanicDb:
        pass

    @app.listener("before_server_start")
    async def init_db(app, loop):
        app.db = MySanicDb()

    await app.create_server(debug=True, return_asyncio_server=True)

    assert hasattr(app, "db")
    assert isinstance(app.db, MySanicDb)
