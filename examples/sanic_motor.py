""" sanic motor (async driver for mongodb) example
Required packages:
pymongo==3.4.0
motor==1.1
sanic==0.2.0
"""
from sanic import Sanic
from sanic.response import json


app = Sanic('motor_mongodb')


def get_db():
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_uri = "mongodb://127.0.0.1:27017/test"
    client = AsyncIOMotorClient(mongo_uri)
    return client['test']


@app.route('/objects', methods=['GET'])
async def get(request):
    db = get_db()
    docs = await db.test_col.find().to_list(length=100)
    for doc in docs:
        doc['id'] = str(doc['_id'])
        del doc['_id']
    return json(docs)


@app.route('/post', methods=['POST'])
async def new(request):
    doc = request.json
    print(doc)
    db = get_db()
    object_id = await db.test_col.save(doc)
    return json({'object_id': str(object_id)})


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000)
