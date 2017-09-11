from json import JSONDecodeError
from sanic import Sanic
import asyncio
from sanic.response import text
from sanic.exceptions import RequestTimeout
from sanic.config import Config
import aiohttp
from aiohttp import TCPConnector
from sanic.testing import SanicTestClient, HOST, PORT


class DelayableTCPConnector(TCPConnector):
    class DelayableHttpRequest(object):
        def __new__(cls, req, delay):
            cls = super(DelayableTCPConnector.DelayableHttpRequest, cls).\
                __new__(cls)
            cls.req = req
            cls.delay = delay
            return cls

        def __getattr__(self, item):
            return getattr(self.req, item)

        def send(self, *args, **kwargs):
            if self.delay and self.delay > 0:
                _ = yield from asyncio.sleep(self.delay)
            self.req.send(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        _post_connect_delay = kwargs.pop('post_connect_delay', 0)
        _pre_request_delay = kwargs.pop('pre_request_delay', 0)
        super(DelayableTCPConnector, self).__init__(*args, **kwargs)
        self._post_connect_delay = _post_connect_delay
        self._pre_request_delay = _pre_request_delay

    @asyncio.coroutine
    def connect(self, req):
        req = DelayableTCPConnector.\
            DelayableHttpRequest(req, self._pre_request_delay)
        conn = yield from super(DelayableTCPConnector, self).connect(req)
        if self._post_connect_delay and self._post_connect_delay > 0:
            _ = yield from asyncio.sleep(self._post_connect_delay)
        return conn


class DelayableSanicTestClient(SanicTestClient):
    def __init__(self, app, request_delay=1):
        super(DelayableSanicTestClient, self).__init__(app)
        self._request_delay = request_delay

    async def _local_request(self, method, uri, cookies=None, *args,
                             **kwargs):
        if uri.startswith(('http:', 'https:', 'ftp:', 'ftps://' '//')):
            url = uri
        else:
            url = 'http://{host}:{port}{uri}'.format(
                host=HOST, port=PORT, uri=uri)

        conn = DelayableTCPConnector(pre_request_delay=self._request_delay,
                                     verify_ssl=False)
        async with aiohttp.ClientSession(
                cookies=cookies, connector=conn) as session:
            # Insert a delay after creating the connection
            # But before sending the request.

            async with getattr(session, method.lower())(
                    url, *args, **kwargs) as response:
                try:
                    response.text = await response.text()
                except UnicodeDecodeError:
                    response.text = None

                try:
                    response.json = await response.json()
                except (JSONDecodeError,
                        UnicodeDecodeError,
                        aiohttp.ClientResponseError):
                    response.json = None

                response.body = await response.read()
                return response


Config.REQUEST_TIMEOUT = 1
request_timeout_default_app = Sanic('test_request_timeout_default')


@request_timeout_default_app.route('/1')
async def handler(request):
    return text('OK')


def test_default_server_error_request_timeout():
    client = DelayableSanicTestClient(request_timeout_default_app, 2)
    request, response = client.get('/1')
    assert response.status == 408
    assert response.text == 'Error: Request Timeout'
