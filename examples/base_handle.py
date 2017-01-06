from sanic.blueprints import Blueprint
from sanic.sanic import Sanic
from sanic.views import BaseHandle

bp = Blueprint('my_bluprint')


@bp.route_handle('/test')
class MyHandle(BaseHandle):
    '''
    封装成类，请求单上下文，可以方便的存取
    Package into a class, request a single context,
     you can easily access(Baidu Translate)
    '''

    async def post(self, request, *args, **kwargs):
        return self.response.make_json({'data': 'post ok'})

    async def get(self, request, *args, **kwargs):
        return self.response.make_json({
            'data': 'get ok'
        })


app = Sanic(__name__)
app.blueprint(bp)
app.run(host='0.0.0.0', port='8000', debug=True)
