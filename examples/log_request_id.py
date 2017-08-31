'''
Based on example from https://github.com/Skyscanner/aiotask-context
and `examples/{override_logging,run_async}.py`.

Needs https://github.com/Skyscanner/aiotask-context/tree/52efbc21e2e1def2d52abb9a8e951f3ce5e6f690 or newer

$ pip install git+https://github.com/Skyscanner/aiotask-context.git
'''

import asyncio
import uuid
import logging
from signal import signal, SIGINT

from sanic import Sanic
from sanic import response

import uvloop
import aiotask_context as context

log = logging.getLogger(__name__)


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = context.get('X-Request-ID')
        return True


LOG_SETTINGS = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'filters': ['requestid'],
        },
    },
    'filters': {
        'requestid': {
            '()': RequestIdFilter,
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s %(name)s:%(lineno)d %(request_id)s | %(message)s',
        },
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': True
        },
    }
}


app = Sanic(__name__, log_config=LOG_SETTINGS)


@app.middleware('request')
async def set_request_id(request):
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
    context.set("X-Request-ID", request_id)


@app.route("/")
async def test(request):
    log.debug('X-Request-ID: %s', context.get('X-Request-ID'))
    log.info('Hello from test!')
    return response.json({"test": True})


if __name__ == '__main__':
    asyncio.set_event_loop(uvloop.new_event_loop())
    server = app.create_server(host="0.0.0.0", port=8000)
    loop = asyncio.get_event_loop()
    loop.set_task_factory(context.task_factory)
    task = asyncio.ensure_future(server)
    try:
        loop.run_forever()
    except:
        loop.stop()
