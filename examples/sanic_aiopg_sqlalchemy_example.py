""" To run this example you need additional aiopg package

"""
import os
import asyncio
import datetime

import uvloop
from aiopg.sa import create_engine
import sqlalchemy as sa

from sanic import Sanic
from sanic.response import json

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

database_name = os.environ['DATABASE_NAME']
database_host = os.environ['DATABASE_HOST']
database_user = os.environ['DATABASE_USER']
database_password = os.environ['DATABASE_PASSWORD']

connection = 'postgres://{0}:{1}@{2}/{3}'.format(database_user,
                                                 database_password,
                                                 database_host,
                                                 database_name)
loop = asyncio.get_event_loop()


metadata = sa.MetaData()

polls = sa.Table('sanic_polls', metadata,
                 sa.Column('id', sa.Integer, primary_key=True),
                 sa.Column('question', sa.String(50)),
                 sa.Column("pub_date", sa.DateTime))


async def get_engine():
    return await create_engine(connection)

app = Sanic(name=__name__)
engine = loop.run_until_complete(get_engine())


async def prepare_db():
    """ Let's add some data

    """
    async with engine.acquire() as conn:
        await conn.execute('DROP TABLE IF EXISTS sanic_polls')
        await conn.execute("""CREATE TABLE sanic_polls (
                                    id serial primary key,
                                    question varchar(50),
                                    pub_date timestamp
                                );""")
        for i in range(0, 100):
            await conn.execute(
                polls.insert().values(question=i,
                                      pub_date=datetime.datetime.now())
                )


@app.route("/")
async def handle(request):
    async with engine.acquire() as conn:
        result = []
        async for row in conn.execute(polls.select()):
            result.append({"question": row.question, "pub_date": row.pub_date})
        return json({"polls": result})


if __name__ == '__main__':
    loop.run_until_complete(prepare_db())
    app.run(host='0.0.0.0', port=8000, loop=loop)
