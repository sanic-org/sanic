# launch with
# gunicorn  --workers=1 --worker-class=meinheld.gmeinheld.MeinheldWorker falcon:api
import sys
import falcon
import ujson as json

class Resource:
    def on_get(self, req, resp):
        resp.body = json.dumps({"test": True})

api = falcon.API()
api.add_route('/', Resource())
