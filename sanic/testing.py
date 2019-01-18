
import asyncio
import http
import io
import json
import queue
import threading
import types
import typing
from urllib.parse import unquote, urljoin, urlparse, parse_qs

import requests

from starlette.types import ASGIApp, Message, Scope
from starlette.websockets import WebSocketDisconnect

HOST = "127.0.0.1"
PORT = 42101


# Annotations for `Session.request()`
Cookies = typing.Union[
    typing.MutableMapping[str, str], requests.cookies.RequestsCookieJar
]
Params = typing.Union[bytes, typing.MutableMapping[str, str]]
DataType = typing.Union[bytes, typing.MutableMapping[str, str], typing.IO]
TimeOut = typing.Union[float, typing.Tuple[float, float]]
FileType = typing.MutableMapping[str, typing.IO]
AuthType = typing.Union[
    typing.Tuple[str, str],
    requests.auth.AuthBase,
    typing.Callable[[requests.Request], requests.Request],
]


class _HeaderDict(requests.packages.urllib3._collections.HTTPHeaderDict):
    def get_all(self, key: str, default: str) -> str:
        return self.getheaders(key)


class _MockOriginalResponse:
    """
    We have to jump through some hoops to present the response as if
    it was made using urllib3.
    """

    def __init__(self, headers: typing.List[typing.Tuple[bytes, bytes]]) -> None:
        self.msg = _HeaderDict(headers)
        self.closed = False

    def isclosed(self) -> bool:
        return self.closed


class _Upgrade(Exception):
    def __init__(self, session: "WebSocketTestSession") -> None:
        self.session = session


def _get_reason_phrase(status_code: int) -> str:
    try:
        return http.HTTPStatus(status_code).phrase
    except ValueError:
        return ""


class _ASGIAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, app: ASGIApp, raise_server_exceptions: bool = True) -> None:
        self.app = app
        self.raise_server_exceptions = raise_server_exceptions

    def send(  # type: ignore
        self, request: requests.PreparedRequest, *args: typing.Any, **kwargs: typing.Any
    ) -> requests.Response:
        scheme, netloc, path, params, query, fragement = urlparse(  # type: ignore
            request.url
        )

        default_port = {"http": 80, "ws": 80, "https": 443, "wss": 443}[scheme]

        if ":" in netloc:
            host, port_string = netloc.split(":", 1)
            port = int(port_string)
        else:
            host = netloc
            port = default_port

        # Include the 'host' header.
        if "host" in request.headers:
            headers = []  # type: typing.List[typing.Tuple[bytes, bytes]]
        elif port == default_port:
            headers = [(b"host", host.encode())]
        else:
            headers = [(b"host", ("%s:%d" % (host, port)).encode())]

        # Include other request headers.
        headers += [
            (key.lower().encode(), value.encode())
            for key, value in request.headers.items()
        ]

        if scheme in {"ws", "wss"}:
            subprotocol = request.headers.get("sec-websocket-protocol", None)
            if subprotocol is None:
                subprotocols = []  # type: typing.Sequence[str]
            else:
                subprotocols = [value.strip() for value in subprotocol.split(",")]
            scope = {
                "type": "websocket",
                "path": unquote(path),
                "root_path": "",
                "scheme": scheme,
                "query_string": query.encode(),
                "headers": headers,
                "client": ["testclient", 50000],
                "server": [host, port],
                "subprotocols": subprotocols,
            }
            session = WebSocketTestSession(self.app, scope)
            raise _Upgrade(session)

        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": request.method,
            "path": unquote(path),
            "root_path": "",
            "scheme": scheme,
            "query_string": query.encode(),
            "headers": headers,
            "client": ["testclient", 50000],
            "server": [host, port],
            "extensions": {"http.response.template": {}},
        }

        async def receive() -> Message:
            nonlocal request_complete, response_complete

            if request_complete:
                while not response_complete:
                    await asyncio.sleep(0.0001)
                return {"type": "http.disconnect"}

            body = request.body
            if isinstance(body, str):
                body_bytes = body.encode("utf-8")  # type: bytes
            elif body is None:
                body_bytes = b""
            elif isinstance(body, types.GeneratorType):
                try:
                    chunk = body.send(None)
                    if isinstance(chunk, str):
                        chunk = chunk.encode("utf-8")
                    return {"type": "http.request", "body": chunk, "more_body": True}
                except StopIteration:
                    request_complete = True
                    return {"type": "http.request", "body": b""}
            else:
                body_bytes = body

            request_complete = True
            return {"type": "http.request", "body": body_bytes}

        async def send(message: Message) -> None:
            nonlocal raw_kwargs, response_started, response_complete, template, context

            if message["type"] == "http.response.start":
                assert (
                    not response_started
                ), 'Received multiple "http.response.start" messages.'
                raw_kwargs["version"] = 11
                raw_kwargs["status"] = message["status"]
                raw_kwargs["reason"] = _get_reason_phrase(message["status"])
                raw_kwargs["headers"] = [
                    (key.decode(), value.decode()) for key, value in message["headers"]
                ]
                raw_kwargs["preload_content"] = False
                raw_kwargs["original_response"] = _MockOriginalResponse(
                    raw_kwargs["headers"]
                )
                response_started = True
            elif message["type"] == "http.response.body":
                assert (
                    response_started
                ), 'Received "http.response.body" without "http.response.start".'
                assert (
                    not response_complete
                ), 'Received "http.response.body" after response completed.'
                body = message.get("body", b"")
                more_body = message.get("more_body", False)
                if request.method != "HEAD":
                    raw_kwargs["body"].write(body)
                if not more_body:
                    raw_kwargs["body"].seek(0)
                    response_complete = True
            elif message["type"] == "http.response.template":
                template = message["template"]
                context = message["context"]

        request_complete = False
        response_started = False
        response_complete = False
        raw_kwargs = {"body": io.BytesIO()}  # type: typing.Dict[str, typing.Any]
        template = None
        context = None

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self.app.is_running = True
        try:
            connection = self.app(scope)
            loop.run_until_complete(connection(receive, send))
        except BaseException as exc:
            if self.raise_server_exceptions:
                raise exc from None

        if self.raise_server_exceptions:
            assert response_started, "TestClient did not receive any response."
        elif not response_started:
            raw_kwargs = {
                "version": 11,
                "status": 500,
                "reason": "Internal Server Error",
                "headers": [],
                "preload_content": False,
                "original_response": _MockOriginalResponse([]),
                "body": io.BytesIO(),
            }

        raw = requests.packages.urllib3.HTTPResponse(**raw_kwargs)
        response = self.build_response(request, raw)
        if template is not None:
            response.template = template
            response.context = context
        return response


class SanicTestClient(requests.Session):
    __test__ = False  # For pytest to not discover this up.

    def __init__(
        self,
        app: ASGIApp,
        base_url: str = "http://%s:%d" % (HOST, PORT),
        raise_server_exceptions: bool = True,
    ) -> None:
        super(SanicTestClient, self).__init__()
        adapter = _ASGIAdapter(app, raise_server_exceptions=raise_server_exceptions)
        self.mount("http://", adapter)
        self.mount("https://", adapter)
        self.mount("ws://", adapter)
        self.mount("wss://", adapter)
        self.headers.update({"user-agent": "testclient"})
        self.app = app
        self.base_url = base_url

    def request(
        self,
        method: str,
        url: str = '/',
        params: Params = None,
        data: DataType = None,
        headers: typing.MutableMapping[str, str] = None,
        cookies: Cookies = None,
        files: FileType = None,
        auth: AuthType = None,
        timeout: TimeOut = None,
        allow_redirects: bool = None,
        proxies: typing.MutableMapping[str, str] = None,
        hooks: typing.Any = None,
        stream: bool = None,
        verify: typing.Union[bool, str] = None,
        cert: typing.Union[str, typing.Tuple[str, str]] = None,
        json: typing.Any = None,
        debug = None,
        gather_request = True
    ) -> requests.Response:
        if debug is not None:
            self.app.debug = debug

        url = urljoin(self.base_url, url)
        response = super().request(
            method,
            url,
            params=params,
            data=data,
            headers=headers,
            cookies=cookies,
            files=files,
            auth=auth,
            timeout=timeout,
            allow_redirects=allow_redirects,
            proxies=proxies,
            hooks=hooks,
            stream=stream,
            verify=verify,
            cert=cert,
            json=json,
        )

        response.status = response.status_code
        response.body = response.content
        try:
            response.json = response.json()
        except:
            response.json = None

        if gather_request:
            request = response.request
            parsed = urlparse(request.url)
            request.scheme = parsed.scheme
            request.path = parsed.path
            request.args = parse_qs(parsed.query)
            return request, response

        return response

    def get(self, *args, **kwargs):
        if 'uri' in kwargs:
            kwargs['url'] = kwargs.pop('uri')
        return self.request("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        if 'uri' in kwargs:
            kwargs['url'] = kwargs.pop('uri')
        return self.request("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        if 'uri' in kwargs:
            kwargs['url'] = kwargs.pop('uri')
        return self.request("put", *args, **kwargs)

    def delete(self, *args, **kwargs):
        if 'uri' in kwargs:
            kwargs['url'] = kwargs.pop('uri')
        return self.request("delete", *args, **kwargs)

    def patch(self, *args, **kwargs):
        if 'uri' in kwargs:
            kwargs['url'] = kwargs.pop('uri')
        return self.request("patch", *args, **kwargs)

    def options(self, *args, **kwargs):
        if 'uri' in kwargs:
            kwargs['url'] = kwargs.pop('uri')
        return self.request("options", *args, **kwargs)

    def head(self, *args, **kwargs):
        if 'uri' in kwargs:
            kwargs['url'] = kwargs.pop('uri')
        return self.request("head", *args, **kwargs)
