import uuid
import logging

from io import StringIO
from importlib import reload

import pytest
from unittest.mock import Mock

import sanic
from sanic.response import text
from sanic.log import LOGGING_CONFIG_DEFAULTS
from sanic import Sanic


logging_format = '''module: %(module)s; \
function: %(funcName)s(); \
message: %(message)s'''


def reset_logging():
    logging.shutdown()
    reload(logging)


def test_log():
    log_stream = StringIO()
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        format=logging_format,
        level=logging.DEBUG,
        stream=log_stream
    )
    log = logging.getLogger()
    app = Sanic('test_logging')
    rand_string = str(uuid.uuid4())

    @app.route('/')
    def handler(request):
        log.info(rand_string)
        return text('hello')

    request, response = app.test_client.get('/')
    log_text = log_stream.getvalue()
    assert rand_string in log_text


def test_logging_defaults():
    reset_logging()
    app = Sanic("test_logging")

    for fmt in [h.formatter for h in logging.getLogger('root').handlers]:
        assert fmt._fmt == LOGGING_CONFIG_DEFAULTS['formatters']['generic']['format']

    for fmt in [h.formatter for h in logging.getLogger('sanic.error').handlers]:
        assert fmt._fmt == LOGGING_CONFIG_DEFAULTS['formatters']['generic']['format']

    for fmt in [h.formatter for h in logging.getLogger('sanic.access').handlers]:
        assert fmt._fmt == LOGGING_CONFIG_DEFAULTS['formatters']['access']['format']


def test_logging_pass_customer_logconfig():
    reset_logging()

    modified_config = LOGGING_CONFIG_DEFAULTS
    modified_config['formatters']['generic']['format'] = '%(asctime)s - (%(name)s)[%(levelname)s]: %(message)s'
    modified_config['formatters']['access']['format'] = '%(asctime)s - (%(name)s)[%(levelname)s]: %(message)s'

    app = Sanic("test_logging", log_config=modified_config)

    for fmt in [h.formatter for h in logging.getLogger('root').handlers]:
        assert fmt._fmt == modified_config['formatters']['generic']['format']

    for fmt in [h.formatter for h in logging.getLogger('sanic.error').handlers]:
        assert fmt._fmt == modified_config['formatters']['generic']['format']

    for fmt in [h.formatter for h in logging.getLogger('sanic.access').handlers]:
        assert fmt._fmt == modified_config['formatters']['access']['format']


@pytest.mark.parametrize('debug', (True, False, ))
def test_log_connection_lost(debug, monkeypatch):
    """ Should not log Connection lost exception on non debug """
    app = Sanic('connection_lost')
    stream = StringIO()
    root = logging.getLogger('root')
    root.addHandler(logging.StreamHandler(stream))
    monkeypatch.setattr(sanic.server, 'logger', root)

    @app.route('/conn_lost')
    async def conn_lost(request):
        response = text('Ok')
        response.output = Mock(side_effect=RuntimeError)
        return response

    with pytest.raises(ValueError):
        # catch ValueError: Exception during request
        app.test_client.get('/conn_lost', debug=debug)

    log = stream.getvalue()

    if debug:
        assert log.startswith(
            'Connection lost before response written @')
    else:
        assert 'Connection lost before response written @' not in log
