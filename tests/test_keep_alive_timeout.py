from json import JSONDecodeError
from sanic import Sanic
from time import sleep as sync_sleep
import asyncio
from sanic.response import text
from sanic.config import Config
import aiohttp
from aiohttp import TCPConnector
from sanic.testing import SanicTestClient, HOST, PORT


class ReuseableTCPConnector(TCPConnector):
    def __init__(self, *args, **kwargs):
        super(ReuseableTCPConnector, self).__init__(*args, **kwargs)
        self.conn = None

    @asyncio.coroutine
    def connect(self, req):
        if self.conn:
            return self.conn
        conn = yield from super(ReuseableTCPConnector, self).connect(req)
        self.conn = conn
        return conn

    def close(self):
        return super(ReuseableTCPConnector, self).close()


class ReuseableSanicTestClient(SanicTestClient):
    def __init__(self, app):
        super(ReuseableSanicTestClient, self).__init__(app)
        self._tcp_connector = None
        self._session = None

    def _sanic_endpoint_test(
            self, method='get', uri='/', gather_request=True,
            debug=False, server_kwargs={},
            *request_args, **request_kwargs):
        results = [None, None]
        exceptions = []

        if gather_request:
            def _collect_request(request):
                if results[0] is None:
                    results[0] = request

            self.app.request_middleware.appendleft(_collect_request)

        @self.app.listener('after_server_start')
        async def _collect_response(sanic, loop):
            try:
                response = await self._local_request(
                    method, uri, *request_args,
                    **request_kwargs)
                results[-1] = response
            except Exception as e:
                log.error(
                    'Exception:\n{}'.format(traceback.format_exc()))
                exceptions.append(e)
            self.app.stop()

        server = self.app.create_server(host=HOST, debug=debug, port=PORT, **server_kwargs)
        self.app.listeners['after_server_start'].pop()

        if exceptions:
            raise ValueError(
                "Exception during request: {}".format(exceptions))

        if gather_request:
            try:
                request, response = results
                return request, response
            except:
                raise ValueError(
                    "Request and response object expected, got ({})".format(
                        results))
        else:
            try:
                return results[-1]
            except:
                raise ValueError(
                    "Request object expected, got ({})".format(results))

    async def _local_request(self, method, uri, cookies=None, *args,
                             **kwargs):
        if uri.startswith(('http:', 'https:', 'ftp:', 'ftps://' '//')):
            url = uri
        else:
            url = 'http://{host}:{port}{uri}'.format(
                host=HOST, port=PORT, uri=uri)
        if self._session:
            session = self._session
        else:
            if self._tcp_connector:
                conn = self._tcp_connector
            else:
                conn = ReuseableTCPConnector(verify_ssl=False)
                self._tcp_connector = conn
            session = aiohttp.ClientSession(cookies=cookies,
                                            connector=conn)
            self._session = session

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


Config.KEEP_ALIVE_TIMEOUT = 30
Config.KEEP_ALIVE = True
keep_alive_timeout_app = Sanic('test_request_timeout')


@keep_alive_timeout_app.route('/1')
async def handler(request):
    return text('OK')


def test_keep_alive_timeout():
    client = ReuseableSanicTestClient(keep_alive_timeout_app)
    headers = {
        'Connection': 'keep-alive'
    }
    request, response = client.get('/1', headers=headers)
    assert response.status == 200
    #sync_sleep(2)
    request, response = client.get('/1')
    assert response.status == 200


