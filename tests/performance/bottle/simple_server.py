# Run with: gunicorn --workers=1 --worker-class=meinheld.gmeinheld.MeinheldWorker -b :8000 simple_server:app
import bottle
import ujson

from bottle import route, run


@route("/")
def index():
    return ujson.dumps({"test": True})


app = bottle.default_app()
