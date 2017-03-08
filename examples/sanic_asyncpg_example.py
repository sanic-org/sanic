""" To run this example you need additional asyncpg package

"""
import os
import asyncio

import uvloop
from asyncpg import connect

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
async def create_db(app, loop):
    """
    Create some table and add some data
    """
    conn = await connect(**DB_CONFIG)
    await conn.execute('DROP TABLE IF EXISTS sanic_post')
    await conn.execute("""CREATE TABLE sanic_post (
        id serial primary key,
        content varchar(50),
        post_date timestamp);"""
                       )
    for i in range(0, 100):
        await conn.execute(f"""INSERT INTO sanic_post
                           (id, content, post_date) VALUES ({i}, {i}, now())""")


@app.route("/")
async def handler(request):
    conn = await connect(**DB_CONFIG)
    results = await conn.fetch('SELECT * FROM sanic_post')
    return json({'posts': jsonify(results)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
