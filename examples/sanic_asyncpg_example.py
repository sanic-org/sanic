""" To run this example you need additional asyncpg package

"""
import os
import asyncio

import uvloop
from asyncpg import create_pool

from sanic import Sanic
from sanic.response import json

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

DB_CONFIG = {
    'host': '<host>',
    'user': '<username>',
    'password': '<password>',
    'port': '<port>',
    'database': '<database>'
}

def jsonify(records):
    """ Parse asyncpg record response into JSON format

    """
    return [{key: value for key, value in
             zip(r.keys(), r.values())} for r in records]

loop = asyncio.get_event_loop()

async def make_pool():
    return await create_pool(**DB_CONFIG)

app = Sanic(__name__)
pool = loop.run_until_complete(make_pool())

async def create_db():
    """ Create some table and add some data

    """
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute('DROP TABLE IF EXISTS sanic_post')
            await connection.execute("""CREATE TABLE sanic_post (
                                    id serial primary key,
                                    content varchar(50),
                                    post_date timestamp
                                );""")
            for i in range(0, 100):
                await connection.execute(f"""INSERT INTO sanic_post
                    (id, content, post_date) VALUES ({i}, {i}, now())""")


@app.route("/")
async def handler(request):
    async with pool.acquire() as connection:
        async with connection.transaction():
            results = await connection.fetch('SELECT * FROM sanic_post')
            return json({'posts': jsonify(results)})


if __name__ == '__main__':
    loop.run_until_complete(create_db())
    app.run(host='0.0.0.0', port=8000, loop=loop)
