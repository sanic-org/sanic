# This demo requires aioredis and environmental variables established in ENV_VARS
import json
import logging
import os

from datetime import datetime

import aioredis

import sanic
from sanic import Sanic


ENV_VARS = ["REDIS_HOST", "REDIS_PORT",
            "REDIS_MINPOOL", "REDIS_MAXPOOL",
            "REDIS_PASS", "APP_LOGFILE"]

app = Sanic(name=__name__)

logger = None


@app.middleware("request")
async def log_uri(request):
    # Simple middleware to log the URI endpoint that was called
    logger.info("URI called: {0}".format(request.url))


@app.listener('before_server_start')
async def before_server_start(app, loop):
    logger.info("Starting redis pool")
    app.redis_pool = await aioredis.create_pool(
        (app.config.REDIS_HOST, int(app.config.REDIS_PORT)),
        minsize=int(app.config.REDIS_MINPOOL),
        maxsize=int(app.config.REDIS_MAXPOOL),
        password=app.config.REDIS_PASS)


@app.listener('after_server_stop')
async def after_server_stop(app, loop):
    logger.info("Closing redis pool")
    app.redis_pool.close()
    await app.redis_pool.wait_closed()


@app.middleware("request")
async def attach_db_connectors(request):
    # Just put the db objects in the request for easier access
    logger.info("Passing redis pool to request object")
    request["redis"] = request.app.redis_pool


@app.route("/state/<user_id>", methods=["GET"])
async def access_state(request, user_id):
    try:
        # Check to see if the value is in cache, if so lets return that
        with await request["redis"] as redis_conn:
            state = await redis_conn.get(user_id, encoding="utf-8")
            if state:
                return sanic.response.json({"msg": "Success",
                                            "status": 200,
                                            "success": True,
                                            "data": json.loads(state),
                                            "finished_at": datetime.now().isoformat()})
        # Then state object is not in redis
        logger.critical("Unable to find user_data in cache.")
        return sanic.response.HTTPResponse({"msg": "User state not found",
                                            "success": False,
                                            "status": 404,
                                            "finished_at": datetime.now().isoformat()}, status=404)
    except aioredis.ProtocolError:
        logger.critical("Unable to connect to state cache")
        return sanic.response.HTTPResponse({"msg": "Internal Server Error",
                                            "status": 500,
                                            "success": False,
                                            "finished_at": datetime.now().isoformat()}, status=500)


@app.route("/state/<user_id>/push", methods=["POST"])
async def set_state(request, user_id):
    try:
        # Pull a connection from the pool
        with await request["redis"] as redis_conn:
            # Set the value in cache to your new value
            await redis_conn.set(user_id, json.dumps(request.json), expire=1800)
            logger.info("Successfully pushed state to cache")
            return sanic.response.HTTPResponse({"msg": "Successfully pushed state to cache",
                                                "success": True,
                                                "status": 200,
                                                "finished_at": datetime.now().isoformat()})
    except aioredis.ProtocolError:
        logger.critical("Unable to connect to state cache")
        return sanic.response.HTTPResponse({"msg": "Internal Server Error",
                                            "status": 500,
                                            "success": False,
                                            "finished_at": datetime.now().isoformat()}, status=500)


def configure():
    # Setup environment variables
    env_vars = [os.environ.get(v, None) for v in ENV_VARS]
    if not all(env_vars):
        # Send back environment variables that were not set
        return False, ", ".join([ENV_VARS[i] for i, flag in env_vars if not flag])
    else:
        # Add all the env vars to our app config
        app.config.update({k: v for k, v in zip(ENV_VARS, env_vars)})
        setup_logging()
    return True, None


def setup_logging():
    logging_format = "[%(asctime)s] %(process)d-%(levelname)s "
    logging_format += "%(module)s::%(funcName)s():l%(lineno)d: "
    logging_format += "%(message)s"

    logging.basicConfig(
        filename=app.config.APP_LOGFILE,
        format=logging_format,
        level=logging.DEBUG)


def main(result, missing):
    if result:
        try:
            app.run(host="0.0.0.0", port=8080, debug=True)
        except:
            logging.critical("User killed server. Closing")
    else:
        logging.critical("Unable to start. Missing environment variables [{0}]".format(missing))


if __name__ == "__main__":
    result, missing = configure()
    logger = logging.getLogger()
    main(result, missing)
