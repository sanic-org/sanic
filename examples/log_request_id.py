import logging

from contextvars import ContextVar

from sanic import Sanic, response


log = logging.getLogger(__name__)


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        try:
            record.request_id = app.ctx.request_id.get(None) or "n/a"
        except AttributeError:
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
    request.app.ctx.request_id.set(request.id)
    log.info(f"Setting {request.id=}")


@app.on_response
async def set_request_header(request, response):
    response.headers["X-Request-ID"] = request.id


@app.route("/")
async def test(request):
    log.debug("X-Request-ID: %s", request.id)
    log.info("Hello from test!")
    return response.json({"test": True})


@app.before_server_start
def setup(app, loop):
    app.ctx.request_id = ContextVar("request_id")


if __name__ == "__main__":
    app.run(port=9999, debug=True)
