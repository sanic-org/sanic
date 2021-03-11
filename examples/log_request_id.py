import logging

import aiotask_context as context

from sanic import Sanic, response


log = logging.getLogger(__name__)


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        try:
            record.request_id = context.get("X-Request-ID")
        except ValueError:
            record.request_id = "n/a"
        return True


LOG_SETTINGS = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
            "filters": ["requestid"],
        },
    },
    "filters": {
        "requestid": {
            "()": RequestIdFilter,
        },
    },
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s:%(lineno)d %(request_id)s | %(message)s",
        },
    },
    "loggers": {
        "": {"level": "DEBUG", "handlers": ["console"], "propagate": True},
    },
}


app = Sanic(__name__, log_config=LOG_SETTINGS)


@app.on_request
async def set_request_id(request):
    request_id = request.id
    context.set("X-Request-ID", request_id)
    log.info(f"Setting {request.id=}")


@app.on_response
async def set_request_header(request, response):
    response.headers["X-Request-ID"] = request.id


@app.route("/")
async def test(request):
    log.debug("X-Request-ID: %s", context.get("X-Request-ID"))
    log.info("Hello from test!")
    return response.json({"test": True})


@app.before_server_start
def setup(app, loop):
    loop.set_task_factory(context.task_factory)


if __name__ == "__main__":
    app.run(port=9999, debug=True)
