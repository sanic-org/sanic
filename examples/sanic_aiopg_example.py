""" To run this example you need additional aiopg package

"""
import os
import asyncio

import uvloop
import aiopg

from sanic import Sanic
from sanic.response import json

database_name = os.environ['DATABASE_NAME']
database_host = os.environ['DATABASE_HOST']
database_user = os.environ['DATABASE_USER']
database_password = os.environ['DATABASE_PASSWORD']

connection = 'postgres://{0}:{1}@{2}/{3}'.format(database_user,
                                                 database_password,
                                                 database_host,
                                                 database_name)


async def get_pool():
    return await aiopg.create_pool(connection)

app = Sanic(name=__name__)

@app.listener('before_server_start')
async def prepare_db(app, loop):
    """
    Let's create some table and add some data
    """
    async with aiopg.create_pool(connection) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute('DROP TABLE IF EXISTS sanic_polls')
                await cur.execute("""CREATE TABLE sanic_polls (
                                        id serial primary key,
                                        question varchar(50),
                                        pub_date timestamp
                                    );""")
                for i in range(0, 100):
                    await cur.execute("""INSERT INTO sanic_polls
                                    (id, question, pub_date) VALUES ({}, {}, now())
                    """.format(i, i))


@app.route("/")
async def handle(request):
    result = []
    async def test_select():
        async with aiopg.create_pool(connection) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT question, pub_date FROM sanic_polls")
                    async for row in cur:
                        result.append({"question": row[0], "pub_date": row[1]})
    res = await test_select()
    return json({'polls': result})

if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=8000,
            debug=True)
