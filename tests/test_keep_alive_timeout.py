from json import JSONDecodeError
from sanic import Sanic
import asyncio
from asyncio import sleep as aio_sleep
from sanic.response import text
from sanic.config import Config
from sanic import server
import aiohttp
from aiohttp import TCPConnector
from sanic.testing import SanicTestClient, HOST


class ReuseableTCPConnector(TCPConnector):
    def __init__(self, *args, **kwargs):
        super(ReuseableTCPConnector, self).__init__(*args, **kwargs)
        self.old_proto = None

    @asyncio.coroutine
    def connect(self, req, traces=None):
        new_conn = yield from super(ReuseableTCPConnector, self)\
                                                         .connect(req, traces=traces)
        if self.old_proto is not None:
            if self.old_proto != new_conn._protocol:
                raise RuntimeError(
                    "We got a new connection, wanted the same one!")
        print(new_conn.__dict__)
        self.old_proto = new_conn._protocol
        return new_conn


class ReuseableSanicTestClient(SanicTestClient):
    def __init__(self, app, loop=None):
        super().__init__(app, port=app.test_port)
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._server = None
        self._tcp_connector = None
        self._session = None

    # Copied from SanicTestClient, but with some changes to reuse the
    # same loop for the same app.
    def _sanic_endpoint_test(
            self, method='get', uri='/', gather_request=True,
            debug=False, server_kwargs={},
            *request_args, **request_kwargs):
        loop = self._loop
        results = [None, None]
        exceptions = []
        do_kill_server = request_kwargs.pop('end_server', False)
        if gather_request:
            def _collect_request(request):
                if results[0] is None:
                    results[0] = request

            self.app.request_middleware.appendleft(_collect_request)

        @self.app.listener('after_server_start')
        async def _collect_response(loop):
            try:
                if do_kill_server:
                    request_kwargs['end_session'] = True
                response = await self._local_request(
                    method, uri, *request_args,
                    **request_kwargs)
                results[-1] = response
            except Exception as e2:
                import traceback
                traceback.print_tb(e2.__traceback__)
                exceptions.append(e2)
            # Don't stop here! self.app.stop()

        if self._server is not None:
            _server = self._server
        else:
            _server_co = self.app.create_server(host=HOST, debug=debug,
                                                port=self.app.test_port,
                                                **server_kwargs)

            server.trigger_events(
                self.app.listeners['before_server_start'], loop)

            try:
                loop._stopping = False
                http_server = loop.run_until_complete(_server_co)
            except Exception as e1:
                import traceback
                traceback.print_tb(e1.__traceback__)
                raise e1
            self._server = _server = http_server
        server.trigger_events(
            self.app.listeners['after_server_start'], loop)
        self.app.listeners['after_server_start'].pop()

        if do_kill_server:
            try:
                _server.close()
                self._server = None
                loop.run_until_complete(_server.wait_closed())
                self.app.stop()
            except Exception as e3:
                import traceback
                traceback.print_tb(e3.__traceback__)
                exceptions.append(e3)
        if exceptions:
            raise ValueError(
                "Exception during request: {}".format(exceptions))

        if gather_request:
            self.app.request_middleware.pop()
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

    # Copied from SanicTestClient, but with some changes to reuse the
    # same TCPConnection and the sane ClientSession more than once.
    # Note, you cannot use the same session if you are in a _different_
    # loop, so the changes above are required too.
    async def _local_request(self, method, uri, cookies=None, *args,
                             **kwargs):
        request_keepalive = kwargs.pop('request_keepalive',
                                       Config.KEEP_ALIVE_TIMEOUT)
        if uri.startswith(('http:', 'https:', 'ftp:', 'ftps://' '//')):
            url = uri
        else:
            url = 'http://{host}:{port}{uri}'.format(
                host=HOST, port=self.port, uri=uri)
        do_kill_session = kwargs.pop('end_session', False)
        if self._session:
            session = self._session
        else:
            if self._tcp_connector:
                conn = self._tcp_connector
            else:
                conn = ReuseableTCPConnector(verify_ssl=False,
                                             loop=self._loop,
                                             keepalive_timeout=
                                             request_keepalive)
                self._tcp_connector = conn
            session = aiohttp.ClientSession(cookies=cookies,
                                            connector=conn,
                                            loop=self._loop)
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
        if do_kill_session:
            await session.close()
            self._session = None
        return response


Config.KEEP_ALIVE_TIMEOUT = 2
Config.KEEP_ALIVE = True
keep_alive_timeout_app_reuse = Sanic('test_ka_timeout_reuse')
keep_alive_app_client_timeout = Sanic('test_ka_client_timeout')
keep_alive_app_server_timeout = Sanic('test_ka_server_timeout')


@keep_alive_timeout_app_reuse.route('/1')
async def handler1(request):
    return text('OK')


@keep_alive_app_client_timeout.route('/1')
async def handler2(request):
    return text('OK')


@keep_alive_app_server_timeout.route('/1')
async def handler3(request):
    return text('OK')


def test_keep_alive_timeout_reuse():
    """If the server keep-alive timeout and client keep-alive timeout are
     both longer than the delay, the client _and_ server will successfully
     reuse the existing connection."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = ReuseableSanicTestClient(keep_alive_timeout_app_reuse, loop)
    headers = {
        'Connection': 'keep-alive'
    }
    request, response = client.get('/1', headers=headers)
    assert response.status == 200
    assert response.text == 'OK'
    loop.run_until_complete(aio_sleep(1))
    request, response = client.get('/1', end_server=True)
    assert response.status == 200
    assert response.text == 'OK'


def test_keep_alive_client_timeout():
    """If the server keep-alive timeout is longer than the client
    keep-alive timeout, client will try to create a new connection here."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = ReuseableSanicTestClient(keep_alive_app_client_timeout,
                                      loop)
    headers = {
        'Connection': 'keep-alive'
    }
    request, response = client.get('/1', headers=headers,
                                   request_keepalive=1)
    assert response.status == 200
    assert response.text == 'OK'
    loop.run_until_complete(aio_sleep(2))
    exception = None
    try:
        request, response = client.get('/1', end_server=True,
                                       request_keepalive=1)
    except ValueError as e:
        exception = e
    assert exception is not None
    assert isinstance(exception, ValueError)
    assert "got a new connection" in exception.args[0]


def test_keep_alive_server_timeout():
    """If the client keep-alive timeout is longer than the server
    keep-alive timeout, the client will either a 'Connection reset' error
    _or_ a new connection. Depending on how the event-loop handles the
    broken server connection."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = ReuseableSanicTestClient(keep_alive_app_server_timeout,
                                      loop)
    headers = {
        'Connection': 'keep-alive'
    }
    request, response = client.get('/1', headers=headers,
                                   request_keepalive=60)
    assert response.status == 200
    assert response.text == 'OK'
    loop.run_until_complete(aio_sleep(3))
    exception = None
    try:
        request, response = client.get('/1', request_keepalive=60,
                                       end_server=True)
    except ValueError as e:
        exception = e
    assert exception is not None
    assert isinstance(exception, ValueError)
    assert "Connection reset" in exception.args[0] or \
           "got a new connection" in exception.args[0]

