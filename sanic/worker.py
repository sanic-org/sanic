import os
import asyncio
import logging
try:
    import ssl
except ImportError:
    ssl = None

import uvloop
import gunicorn.workers.base as base

from sanic.server import trigger_events, serve, HttpProtocol
from sanic.websocket import WebSocketProtocol


class GunicornWorker(base.Worker):

    def __init__(self, *args, **kw):  # pragma: no cover
        super().__init__(*args, **kw)
        cfg = self.cfg
        if cfg.is_ssl:
            self.ssl_context = self._create_ssl_context(cfg)
        else:
            self.ssl_context = None
        self.servers = []
        self.connections = set()

    def init_process(self):
        # create new event_loop after fork
        asyncio.get_event_loop().close()

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        super().init_process()

    def run(self):
        self._runner = asyncio.async(self._run(), loop=self.loop)

        try:
            self.loop.run_until_complete(self._runner)
        finally:
            trigger_events(self._server_settings.get('before_stop', []), self.loop)
            self.loop.close()
            trigger_events(self._server_settings.get('after_stop', []), self.loop)

    async def close(self):
        if self.servers:
            # stop accepting connections
            self.log.info("Stopping server: %s, connections: %s",
                          self.pid, len(self.connections))
            for server in self.servers:
                server.close()
                await server.wait_closed()
            self.servers.clear()

            # prepare connections for closing
            for conn in self.connections:
                conn.close_if_idle()

            while self.connections:
                await asyncio.sleep(0.1)

    async def _run(self):
        is_debug = self.log.loglevel == logging.DEBUG
        protocol = (WebSocketProtocol if self.app.callable.websocket_enabled
                    else HttpProtocol)
        self._server_settings = self.app.callable._helper(
            host=None,
            port=None,
            loop=self.loop,
            debug=is_debug,
            protocol=protocol,
            ssl=self.ssl_context,
            run_async=True
        )
        self._server_settings.pop('sock')
        for sock in self.sockets:
            self.servers.append(await serve(
                sock=sock,
                connections=self.connections,
                **self._server_settings
            ))

        trigger_events(self._server_settings.get('after_start', []), self.loop)
        # If our parent changed then we shut down.
        pid = os.getpid()
        try:
            while self.alive:
                self.notify()

                if pid == os.getpid() and self.ppid != os.getppid():
                    self.alive = False
                    self.log.info("Parent changed, shutting down: %s", self)
                else:
                    await asyncio.sleep(1.0, loop=self.loop)
        except (Exception, BaseException, GeneratorExit, KeyboardInterrupt):
            pass

        await self.close()

    @staticmethod
    def _create_ssl_context(cfg):
        """ Creates SSLContext instance for usage in asyncio.create_server.
        See ssl.SSLSocket.__init__ for more details.
        """
        ctx = ssl.SSLContext(cfg.ssl_version)
        ctx.load_cert_chain(cfg.certfile, cfg.keyfile)
        ctx.verify_mode = cfg.cert_reqs
        if cfg.ca_certs:
            ctx.load_verify_locations(cfg.ca_certs)
        if cfg.ciphers:
            ctx.set_ciphers(cfg.ciphers)
        return ctx
