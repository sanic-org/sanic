import os
import asyncio

import uvloop
from asyncpg import connect, create_pool

from sanic import Sanic
from sanic.response import json

DB_CONFIG = {
    'host': '<host>',
    'user': '<user>',
    'password': '<password>',
    'port': '<port>',
    'database': '<database>'
}


def jsonify(records):
    """
    Parse asyncpg record response into JSON format
    """
    return [dict(r.items()) for r in records]


app = Sanic(__name__)


@app.listener('before_server_start')
async def register_db(app, loop):
    app.pool = await create_pool(**DB_CONFIG, loop=loop, max_size=100)
    async with app.pool.acquire() as connection:
        await connection.execute('DROP TABLE IF EXISTS sanic_post')
        await connection.execute("""CREATE TABLE sanic_post (
                                id serial primary key,
                                content varchar(50),
                                post_date timestamp
                            );""")
        for i in range(0, 1000):
            await connection.execute(f"""INSERT INTO sanic_post
                (id, content, post_date) VALUES ({i}, {i}, now())""")


@app.get('/')
async def root_get(request):
    async with app.pool.acquire() as connection:
        results = await connection.fetch('SELECT * FROM sanic_post')
        return json({'posts': jsonify(results)})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
