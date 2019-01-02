from sanic import Sanic
from sanic.response import text
from random import randint

app = Sanic()


@app.middleware('request')
def append_request(request):
    # Add new key with random value
    request['num'] = randint(0, 100)


@app.get('/pop')
def pop_handler(request):
    # Pop key from request object
    num = request.pop('num')
    return text(num)


@app.get('/key_exist')
def key_exist_handler(request):
    # Check the key is exist or not
    if 'num' in request:
        return text('num exist in request')

    return text('num does not exist in reqeust')


app.run(host="0.0.0.0", port=8000, debug=True)
