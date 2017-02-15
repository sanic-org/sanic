from io import StringIO
from random import choice
from string import ascii_letters
import signal

import pytest

from sanic import Sanic
from sanic.testing import HOST, PORT

AVAILABLE_LISTENERS = [
    'before_server_start',
    'after_server_start',
    'before_server_stop',
    'after_server_stop'
]


def create_listener(listener_name, in_list):
    async def _listener(app, loop):
        print('DEBUG MESSAGE FOR PYTEST for {}'.format(listener_name))
        in_list.insert(0, app.name + listener_name)
    return _listener


def start_stop_app(random_name_app, **run_kwargs):

    def stop_on_alarm(signum, frame):
        raise KeyboardInterrupt('SIGINT for sanic to stop gracefully')

    signal.signal(signal.SIGALRM, stop_on_alarm)
    signal.alarm(1)
    try:
        random_name_app.run(HOST, PORT, **run_kwargs)
    except KeyboardInterrupt:
        pass


@pytest.mark.parametrize('listener_name', AVAILABLE_LISTENERS)
def test_single_listener(listener_name):
    """Test that listeners on their own work"""
    random_name_app = Sanic(''.join(
        [choice(ascii_letters) for _ in range(choice(range(5, 10)))]))
    output = list()
    # Register listener
    random_name_app.listener(listener_name)(
        create_listener(listener_name, output))
    start_stop_app(random_name_app)
    assert random_name_app.name + listener_name == output.pop()


def test_all_listeners():
    random_name_app = Sanic(''.join(
        [choice(ascii_letters) for _ in range(choice(range(5, 10)))]))
    output = list()
    for listener_name in AVAILABLE_LISTENERS:
        listener = create_listener(listener_name, output)
        random_name_app.listener(listener_name)(listener)
    start_stop_app(random_name_app)
    for listener_name in AVAILABLE_LISTENERS:
        assert random_name_app.name + listener_name == output.pop()
