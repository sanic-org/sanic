from bottle import route, run
import ujson


@route('/')
def index():
    return ujson.dumps({'test': True})


run(server='gunicorn', host='0.0.0.0', port=8080)
