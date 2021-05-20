import json

from sanic import Sanic, text
from sanic.log import LOGGING_CONFIG_DEFAULTS, logger


LOGGING_CONFIG = {**LOGGING_CONFIG_DEFAULTS}
LOGGING_CONFIG["formatters"]["generic"]["format"] = "%(message)s"
app = Sanic(__name__, log_config=LOGGING_CONFIG)


@app.get("/")
async def handler(request):
    return text(request.ip)


@app.before_server_start
async def app_info_dump(app: Sanic, _):
    app_data = {
        "access_log": app.config.ACCESS_LOG,
        "auto_reload": app.auto_reload,
        "debug": app.debug,
    }
    logger.info(json.dumps(app_data))


@app.after_server_start
async def shutdown(app: Sanic, _):
    app.stop()
