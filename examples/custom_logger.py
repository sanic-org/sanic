from sanic import Sanic
from sanic.response import text
import json
import logging

logging_format = "[%(asctime)s] %(process)d-%(levelname)s "
logging_format += "%(module)s::%(funcName)s():l%(lineno)d: "
logging_format += "%(message)s"
logging.basicConfig(
    format=logging_format,
    level=logging.DEBUG)

sanic = Sanic(logger=logging)

@sanic.route("/")
def test(request):
    logging.info("received request")
    return text("spam is good")

# You can also pass the logger into the run method instead of Sanic. e.g.
# sanic.run(host="0.0.0.0", port=8000, logger=logging).
sanic.run(host="0.0.0.0", port=8000)
