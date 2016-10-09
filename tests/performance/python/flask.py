# launch with
# gunicorn  --workers=1 --worker-class=meinheld.gmeinheld.MeinheldWorker falcon:api
from flask import Flask
app = Flask(__name__)
from ujson import dumps

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def hello_world():
    return dumps({"test": True})

if __name__ == '__main__':
    import sys
    app.run(port=sys.argv[-1])