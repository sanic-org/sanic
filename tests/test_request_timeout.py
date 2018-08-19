from json import JSONDecodeError

from sanic import Sanic
import asyncio
from sanic.response import text
from sanic.config import Config
import aiohttp
from aiohttp import TCPConnector, ClientResponse
from sanic.testing import SanicTestClient, HOST, PORT

try:
    # setuptools v39.0 and above.
    try:
        from setuptools.extern import packaging
    except ImportError:
        # Before setuptools v39.0
        from pkg_resources.extern import packaging
    version = packaging.version
except ImportError:
    raise RuntimeError("The 'packaging' library is missing.")

aiohttp_version = version.parse(aiohttp.__version__)

class DelayableTCPConnector(TCPConnector):

    class RequestContextManager(object):
        def __new__(cls, req, delay):
            cls = super(DelayableTCPConnector.RequestContextManager, cls).\
                __new__(cls)
            cls.req = req
            cls.send_task = None
            cls.resp = None
            cls.orig_send = getattr(req, 'send')
            cls.orig_start = None
            cls.delay = delay
            cls._acting_as = req
            return cls

        def __getattr__(self, item):
            acting_as = self._acting_as
            return getattr(acting_as, item)

        async def start(self, connection, read_until_eof=False):
            if self.send_task is None:
                raise RuntimeError("do a send() before you do a start()")
            resp = await self.send_task
            self.send_task = None
            self.resp = resp
            self._acting_as = self.resp
            self.orig_start = getattr(resp, 'start')

            try:
                if aiohttp_version >= version.parse("3.3.0"):
                    ret = await self.orig_start(connection)
                else:
                    ret = await self.orig_start(connection,
                                                read_until_eof)
            except Exception as e:
                raise e
            return ret

        def close(self):
            if self.resp is not None:
                self.resp.close()
            if self.send_task is not None:
                self.send_task.cancel()

        async def delayed_send(self, *args, **kwargs):
            req = self.req
            if self.delay and self.delay > 0:
                #sync_sleep(self.delay)
                await asyncio.sleep(self.delay)
            t = req.loop.time()
            print("sending at {}".format(t), flush=True)
            conn = next(iter(args))  # first arg is connection

            if aiohttp_version >= version.parse("3.1.0"):
                try:
                    delayed_resp = await self.orig_send(*args, **kwargs)
                except Exception as e:
                    if aiohttp_version >= version.parse("3.3.0"):
                        return aiohttp.ClientResponse(req.method, req.url,
                                                      writer=None,
                                                      continue100=None,
                                                      timer=None,
                                                      request_info=None,
                                                      traces=[],
                                                      loop=req.loop,
                                                      session=None)
                    else:
                        return aiohttp.ClientResponse(req.method, req.url,
                                                      writer=None,
                                                      continue100=None,
                                                      timer=None,
                                                      request_info=None,
                                                      auto_decompress=None,
                                                      traces=[],
                                                      loop=req.loop,
                                                      session=None)
            else:
                try:
                    delayed_resp = self.orig_send(*args, **kwargs)
                except Exception as e:
                    return aiohttp.ClientResponse(req.method, req.url)
            return delayed_resp

        if aiohttp_version >= version.parse("3.1.0"):
            # aiohttp changed the request.send method to async
            async def send(self, *args, **kwargs):
                gen = self.delayed_send(*args, **kwargs)
                task = self.req.loop.create_task(gen)
                self.send_task = task
                self._acting_as = task
                return self
        else:
            def send(self, *args, **kwargs):
                gen = self.delayed_send(*args, **kwargs)
                task = self.req.loop.create_task(gen)
                self.send_task = task
                self._acting_as = task
                return self

    def __init__(self, *args, **kwargs):
        _post_connect_delay = kwargs.pop('post_connect_delay', 0)
        _pre_request_delay = kwargs.pop('pre_request_delay', 0)
        super(DelayableTCPConnector, self).__init__(*args, **kwargs)
        self._post_connect_delay = _post_connect_delay
        self._pre_request_delay = _pre_request_delay

    if aiohttp_version >= version.parse("3.3.0"):
        async def connect(self, req, traces, timeout):
            d_req = DelayableTCPConnector.\
                RequestContextManager(req, self._pre_request_delay)
            conn = await super(DelayableTCPConnector, self).\
                connect(req, traces, timeout)
            if self._post_connect_delay and self._post_connect_delay > 0:
                await asyncio.sleep(self._post_connect_delay,
                                    loop=self._loop)
            req.send = d_req.send
            t = req.loop.time()
            print("Connected at {}".format(t), flush=True)
            return conn
    elif aiohttp_version >= version.parse("3.0.0"):
        async def connect(self, req, traces=None):
            d_req = DelayableTCPConnector.\
                RequestContextManager(req, self._pre_request_delay)
            conn = await super(DelayableTCPConnector, self).\
                connect(req, traces=traces)
            if self._post_connect_delay and self._post_connect_delay > 0:
                await asyncio.sleep(self._post_connect_delay,
                                    loop=self._loop)
            req.send = d_req.send
            t = req.loop.time()
            print("Connected at {}".format(t), flush=True)
            return conn
    else:

        async def connect(self, req):
            d_req = DelayableTCPConnector.\
                RequestContextManager(req, self._pre_request_delay)
            conn = await super(DelayableTCPConnector, self).connect(req)
            if self._post_connect_delay and self._post_connect_delay > 0:
                await asyncio.sleep(self._post_connect_delay,
                                   loop=self._loop)
            req.send = d_req.send
            t = req.loop.time()
            print("Connected at {}".format(t), flush=True)
            return conn


class DelayableSanicTestClient(SanicTestClient):
    def __init__(self, app, loop, request_delay=1):
        super(DelayableSanicTestClient, self).__init__(app)
        self._request_delay = request_delay
        self._loop = None

    async def _local_request(self, method, uri, cookies=None, *args,
                             **kwargs):
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        if uri.startswith(('http:', 'https:', 'ftp:', 'ftps://' '//')):
            url = uri
        else:
            url = 'http://{host}:{port}{uri}'.format(
                host=HOST, port=self.port, uri=uri)
        conn = DelayableTCPConnector(pre_request_delay=self._request_delay,
                                     verify_ssl=False, loop=self._loop)
        async with aiohttp.ClientSession(cookies=cookies, connector=conn,
                                         loop=self._loop) as session:
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


Config.REQUEST_TIMEOUT = 2
request_timeout_default_app = Sanic('test_request_timeout_default')
request_no_timeout_app = Sanic('test_request_no_timeout')


@request_timeout_default_app.route('/1')
async def handler1(request):
    return text('OK')


@request_no_timeout_app.route('/1')
async def handler2(request):
    return text('OK')


def test_default_server_error_request_timeout():
    client = DelayableSanicTestClient(request_timeout_default_app, None, 3)
    request, response = client.get('/1')
    assert response.status == 408
    assert response.text == 'Error: Request Timeout'


def test_default_server_error_request_dont_timeout():
    client = DelayableSanicTestClient(request_no_timeout_app, None, 1)
    request, response = client.get('/1')
    assert response.status == 200
    assert response.text == 'OK'
