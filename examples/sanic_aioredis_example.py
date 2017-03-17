""" To run this example you need additional aioredis package
"""
from sanic import Sanic, response
import aioredis

app = Sanic(__name__)


@app.route("/")
async def handle(request):
    async with request.app.redis_pool.get() as redis:
        await redis.set('test-my-key', 'value')
        val = await redis.get('test-my-key')
    return response.text(val.decode('utf-8'))


@app.listener('before_server_start')
async def before_server_start(app, loop):
    app.redis_pool = await aioredis.create_pool(
        ('localhost', 6379),
        minsize=5,
        maxsize=10,
        loop=loop
    )


@app.listener('after_server_stop')
async def after_server_stop(app, loop):
    app.redis_pool.close()
    await app.redis_pool.wait_closed()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
