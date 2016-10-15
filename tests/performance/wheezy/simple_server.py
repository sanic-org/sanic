# Run with: gunicorn --workers=1 --worker-class=meinheld.gmeinheld.MeinheldWorker simple_server:main
""" Minimal helloworld application.
"""

from wheezy.http import HTTPResponse
from wheezy.http import WSGIApplication
from wheezy.http.response import json_response
from wheezy.routing import url
from wheezy.web.handlers import BaseHandler
from wheezy.web.middleware import bootstrap_defaults
from wheezy.web.middleware import path_routing_middleware_factory

import ujson

class WelcomeHandler(BaseHandler):

    def get(self):
        response = HTTPResponse(content_type='application/json; charset=UTF-8')
        response.write(ujson.dumps({"test":True}))
        return response

all_urls = [
    url('', WelcomeHandler, name='default'),
#    url('', welcome, name='welcome')
]


options = {}
main = WSGIApplication(
    middleware=[
        bootstrap_defaults(url_mapping=all_urls),
        path_routing_middleware_factory
    ],
    options=options
)


if __name__ == '__main__':
    import sys
    from wsgiref.simple_server import make_server
    try:
        print('Visit http://localhost:{}/'.format(sys.argv[-1]))
        make_server('', int(sys.argv[-1]), main).serve_forever()
    except KeyboardInterrupt:
        pass
    print('\nThanks!')
