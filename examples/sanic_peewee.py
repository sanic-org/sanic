## You need the following additional packages for this example
# aiopg
# peewee_async
# peewee


## sanic imports
from sanic import Sanic
from sanic.response import json

## peewee_async related imports
import uvloop
import peewee
from peewee_async import Manager, PostgresqlDatabase

 # we instantiate a custom loop so we can pass it to our db manager
loop = uvloop.new_event_loop()

database = PostgresqlDatabase(database='test',
                              host='127.0.0.1',
                              user='postgres',
                              password='mysecretpassword')

objects = Manager(database, loop=loop)

## from peewee_async docs:
# Also there’s no need to connect and re-connect before executing async queries
# with manager! It’s all automatic. But you can run Manager.connect() or
# Manager.close() when you need it.


# let's create a simple key value store:
class KeyValue(peewee.Model):
    key = peewee.CharField(max_length=40, unique=True)
    text = peewee.TextField(default='')

    class Meta:
        database = database

# create table synchronously
KeyValue.create_table(True)

# OPTIONAL: close synchronous connection
database.close()

# OPTIONAL: disable any future syncronous calls
objects.database.allow_sync = False # this will raise AssertionError on ANY sync call


app = Sanic('peewee_example')

@app.route('/post')
async def post(request):
    """ This is actually a GET request, you probably want POST in real life,
    with some data parameters"""
    obj = await objects.create(KeyValue, key='my_first_async_db', text="I was inserted asynchronously!")
    return json({'object_id': obj.id})


@app.route('/get')
async def get(request):
    all_objects = await objects.execute(KeyValue.select())
    serialized_obj = []
    for obj in all_objects:
        serialized_obj.append({obj.key: obj.text})

    return json({'objects': serialized_obj})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, loop=loop)

