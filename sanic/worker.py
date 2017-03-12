import asyncio
import os

import uvloop
import gunicorn.workers.base as base


class GunicornWorker(base.Worker):

    def __init__(self, *args, **kw):  # pragma: no cover
        super().__init__(*args, **kw)
        self.servers = []
        self.connections = {}

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
            self.loop.close()

    async def close(self):
        try:
            if hasattr(self.wsgi, 'close'):
                await self.wsgi.close()
        except:
            self.log.exception('Process shutdown exception')

    async def _run(self):
        for sock in self.sockets:
            self.servers.append(await self.app.callable.create_server(
                sock=sock, host=None, port=None, loop=self.loop))

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

        if self.servers:
            for server in self.servers:
                server.close()

        await self.close()
