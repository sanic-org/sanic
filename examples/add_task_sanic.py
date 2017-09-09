# -*- coding: utf-8 -*-

import asyncio

from sanic import Sanic

app = Sanic()


async def notify_server_started_after_five_seconds():
    await asyncio.sleep(5)
    print('Server successfully started!')

app.add_task(notify_server_started_after_five_seconds())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
