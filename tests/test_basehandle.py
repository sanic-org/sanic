from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.utils import sanic_endpoint_test
from sanic.views import BaseHandle
import ujson


# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_bp():
    app = Sanic('test_basehandle')
    bp = Blueprint('test_basehandle')

    @bp.route_handle('/test')
    class MyHandle(BaseHandle):
        async def post(self, request, *args, **kwargs):
            return self.response.make_json({'data': 'post ok'})

        async def get(self, request, *args, **kwargs):
            return self.response.make_json({
                'data': 'get ok'
            })

    app.blueprint(bp)
    request, response = sanic_endpoint_test(app, method='get', uri='/test')
    data = ujson.loads(response.text)
    assert data['data'] == 'get ok'
    request, response = sanic_endpoint_test(app, method='post', uri='/test')
    data = ujson.loads(response.text)
    assert data['data'] == 'post ok'
