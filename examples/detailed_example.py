import json
import logging
import os

import aioredis

import sanic
from sanic import Sanic


ENV_VARS = ["REDIS_HOST", "REDIS_PORT",
            "REDIS_MINPOOL", "REDIS_MAXPOOL",
            "REDIS_PASS", "APP_LOGFILE"]

app = Sanic(name=__name__)

logger = None


@app.middleware("request")
async def attach_db_connectors(request):
    if not hasattr(request.app.config, "REDIS"):
        logger.info("Setting up connection to Redis Cache")
        request.app.config.REDIS = await aioredis.create_pool((app.config.REDIS_HOST, int(app.config.REDIS_PORT)),
                                                              minsize=int(app.config.REDIS_MINPOOL),
                                                              maxsize=int(app.config.REDIS_MAXPOOL),
                                                              password=app.config.REDIS_PASS)
    # Just put the db objects in the request for easier access
    request["redis"] = request.app.config.REDIS


@app.route("/state/<user_id>", methods=["GET"])
async def access_state(request, user_id):
    try:
        # Check to see if the value is in cache, if so lets return that
        with await request["redis"] as redis_conn:
            state = await redis_conn.get(user_id, encoding="utf-8")
            if state:
                return sanic.response.json(json.loads(state))
        # Then state object is not in redis
        logger.critical("Unable to find user_data in cache.")
        return sanic.response.HTTPResponse({"msg": "User state not found"}, status=404)

    except aioredis.ProtocolError:
        logger.critical("Unable to connect to state cache")
        return sanic.response.HTTPResponse({"msg": "Internal Server Error"}, status=500)


@app.route("/state/<user_id>/push", methods=["POST"])
async def set_state(request, user_id):
    try:
        with await request["redis"] as redis_conn:
            # Set the value in cache to your new value
            await redis_conn.set(user_id, json.dumps(request.json), expire=1800)
            logger.info("Successfully retrieved from cache")
            return sanic.response.HTTPResponse({"msg": "Successfully pushed state to cache"})
    except aioredis.ProtocolError:
        logger.critical("UNable to connect to state cache")
        return sanic.response.HTTPResponse({"msg": "Interal Server Error"}, status=500)


def configure():
    # Setup environment variables
    env_vars = [os.environ.get(v, None) for v in ENV_VARS]
    if not all(env_vars):
        # Send back environment variables that were not set
        return False, [ENV_VARS[i] for i, flag in env_vars if not flag]
    else:
        app.config.update({k: v for k, v in zip(ENV_VARS, env_vars)})
        setup_logging()
        logging.info("Configuraiton complete")
    return True, []

def setup_logging():
    logging_format = "[%(asctime)s] %(process)d-%(levelname)s "
    logging_format += "%(module)s::%(funcName)s():l%(lineno)d: "
    logging_format += "%(message)s"

    print(app.config.APP_LOGFILE)
    logging.basicConfig(
        filename=app.config.APP_LOGFILE,
        format=logging_format,
        level=logging.DEBUG
    )

if __name__ == "__main__":
    result, missing = configure()
    logger = logging.getLogger()
    if result:
        try:
            app.run(host="0.0.0.0", port=8080, debug=True)
        except:
            logger.critical("User killed server. Closing")
    else:
        need_string = ", ".join(missing)
        logger.critical("Unable to start. Missing environment variables [{0}]".format(need_string))
