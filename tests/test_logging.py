import asyncio
import uuid
from sanic.response import text
from sanic import Sanic
from io import StringIO
from sanic.utils import sanic_endpoint_test
import logging

logging_format = '''module: %(module)s; \
function: %(funcName)s(); \
message: %(message)s'''


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

    request, response = sanic_endpoint_test(app)
    log_text = log_stream.getvalue()
    assert rand_string in log_text

if __name__ == "__main__":
    test_log()
