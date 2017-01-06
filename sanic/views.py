from .exceptions import InvalidUsage
from sanic.response import Response
import logging

logger = logging.getLogger(__name__)


class HTTPMethodView:
    """ Simple class based implementation of view for the sanic.
    You should implement methods (get, post, put, patch, delete) for the class
    to every HTTP method you want to support.

    For example:
        class DummyView(View):

            def get(self, request, *args, **kwargs):
                return text('I am get method')

            def put(self, request, *args, **kwargs):
                return text('I am put method')
    etc.

    If someone tries to use a non-implemented method, there will be a
    405 response.

    If you need any url params just mention them in method definition:
        class DummyView(View):

            def get(self, request, my_param_here, *args, **kwargs):
                return text('I am get method with %s' % my_param_here)

    To add the view into the routing you could use
        1) app.add_route(DummyView(), '/')
        2) app.route('/')(DummyView())
    """

    def __call__(self, request, *args, **kwargs):
        handler = getattr(self, request.method.lower(), None)
        if handler:
            return handler(request, *args, **kwargs)
        raise InvalidUsage(
            'Method {} not allowed for URL {}'.format(
                request.method, request.url), status_code=405)


class BaseHandle():
    '''
      封装成类，请求单上下文，可以方便的存取
      Package into a class, request a single context,
       you can easily access(Baidu Translate)
      '''
    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.response = Response(request)

    def __call__(self, *args, **kwargs):
        return self._execute(*args, **kwargs)

    async def _execute(self, request, *args, **kwargs):
        await self.prepare(request, *args, **kwargs)
        handler = getattr(self, request.method.lower(), None)
        if handler:
            try:
                result = await handler(request, *args, **kwargs)
            except Exception as e:
                logger.exception(str(e.args))
                raise e
            result = result or self.response
            return result
        raise InvalidUsage('Method {} not allowed for URL {}'.format(
            request.method, request.url), status_code=405)

    async def prepare(self, request, *args, **kwargs):
        pass
