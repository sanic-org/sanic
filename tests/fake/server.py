import json

from sanic import Sanic, text
from sanic.application.constants import Mode
from sanic.config import Config
from sanic.log import LOGGING_CONFIG_DEFAULTS, logger


LOGGING_CONFIG = {**LOGGING_CONFIG_DEFAULTS}
LOGGING_CONFIG["formatters"]["generic"]["format"] = "%(message)s"
LOGGING_CONFIG["loggers"]["sanic.root"]["level"] = "DEBUG"

app = Sanic("FakeServer", log_config=LOGGING_CONFIG)


@app.get("/")
async def handler(request):
    return text(request.ip)


@app.main_process_start
async def app_info_dump(app: Sanic, _):
    app_data = {
        "access_log": app.config.ACCESS_LOG,
        "auto_reload": app.auto_reload,
        "debug": app.debug,
        "noisy_exceptions": app.config.NOISY_EXCEPTIONS,
    }
    logger.info(json.dumps(app_data))


@app.main_process_stop
async def app_cleanup(app: Sanic, _):
    app.state.auto_reload = False
    app.state.mode = Mode.PRODUCTION
    app.config = Config()


@app.after_server_start
async def shutdown(app: Sanic, _):
    app.stop()


def create_app():
    return app


def create_app_with_args(args):
    try:
        logger.info(f"foo={args.foo}")
    except AttributeError:
        logger.info(f"module={args.module}")

    return app
