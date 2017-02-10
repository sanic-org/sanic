import asyncio
import sanic
from sanic.response import html
import datetime
import random

app = sanic.Sanic()

async def time(websocket, path):
    while True:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        await websocket.send(now)
        await asyncio.sleep(random.random() * 3)

app.websocket(time, 'localhost', 3000)

@app.route('/')
def hello(request):
    return html(open('ws.html').read())

app.run(port=8000)
