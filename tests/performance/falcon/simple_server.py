# Run with: gunicorn --workers=1 --worker-class=meinheld.gmeinheld.MeinheldWorker falc:app

import falcon
import ujson as json


class TestResource:
    def on_get(self, req, resp):
        resp.body = json.dumps({"test": True})


app = falcon.API()
app.add_route("/", TestResource())
