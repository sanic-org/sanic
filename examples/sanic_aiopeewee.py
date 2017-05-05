from sanic import Sanic
from sanic.response import json

from aiopeewee import AioModel, AioMySQLDatabase
from peewee import CharField, TextField, DateTimeField
from peewee import ForeignKeyField, PrimaryKeyField
from playhouse.shortcuts import model_to_dict


db = AioMySQLDatabase('test', user='root', password='',
                      host='127.0.0.1', port=3306)


class User(AioModel):
    username = CharField()

    class Meta:
        database = db


class Blog(AioModel):
    user = ForeignKeyField(User)
    title = CharField(max_length=25)
    content = TextField(default='')
    pub_date = DateTimeField(null=True)
    pk = PrimaryKeyField()

    class Meta:
        database = db


app = Sanic(__name__)


@app.listener('before_server_start')
async def setup(app, loop):
    # create connection pool
    await db.connect(loop)
    # create table if not exists
    await db.create_tables([User, Blog], safe=True)


@app.listener('before_server_stop')
async def stop(app, loop):
    # close connection pool
    await db.close()
    await to_asyncio_future(app.client._shutdown())


@app.post('/users')
async def add_user(request):
    user = await User.create(**request.json)
    return json(model_to_dict(user))


@app.get('/users/count')
async def user_count(request):
    count = await User.select().count()
    return json({'count': count})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
