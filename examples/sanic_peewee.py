## You need the following additional packages for this example
# aiopg
# peewee_async
# peewee


## sanic imports
from sanic import Sanic
from sanic.response import json

## peewee_async related imports
import peewee
from peewee_async import Manager, PostgresqlDatabase

 # we instantiate a custom loop so we can pass it to our db manager

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

@app.listener('before_server_start')
def setup(app, loop):
    database = PostgresqlDatabase(database='test',
                                  host='127.0.0.1',
                                  user='postgres',
                                  password='mysecretpassword')

    objects = Manager(database, loop=loop)

@app.route('/post/<key>/<value>')
async def post(request, key, value):
    """
    Save get parameters to database
    """
    obj = await objects.create(KeyValue, key=key, text=value)
    return json({'object_id': obj.id})


@app.route('/get')
async def get(request):
    """
    Load all objects from database
    """
    all_objects = await objects.execute(KeyValue.select())
    serialized_obj = []
    for obj in all_objects:
        serialized_obj.append({
            'id': obj.id,
            'key': obj.key,
            'value': obj.text}
        )

    return json({'objects': serialized_obj})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
