# Response

Use functions in `sanic.response` module to create responses.

## Plain Text

```python
from sanic.response import text


@app.route('/text')
def handle_request(request):
    return text('Hello world!')
```

## HTML

```python
from sanic.response import html


@app.route('/html')
def handle_request(request):
    return html('<p>Hello world!</p>')
```

## JSON


```python
from sanic.response import json


@app.route('/json')
def handle_request(request):
    return json({'message': 'Hello world!'})
```

## File

```python
from sanic.response import file


@app.route('/file')
async def handle_request(request):
    return await file('/srv/www/whatever.png')
```

## Streaming

```python
from sanic.response import stream

@app.route("/streaming")
async def index(request):
    async def streaming_fn(response):
        response.write('foo')
        response.write('bar')
    return stream(streaming_fn, content_type='text/plain')
```

## Redirect

```python
from sanic.response import redirect


@app.route('/redirect')
def handle_request(request):
    return redirect('/json')
```

## Raw

Response without encoding the body

```python
from sanic.response import raw


@app.route('/raw')
def handle_request(request):
    return raw('raw data')
```

## Modify headers or status

To modify headers or status code, pass the `headers` or `status` argument to those functions:

```python
from sanic.response import json


@app.route('/json')
def handle_request(request):
    return json(
        {'message': 'Hello world!'},
        headers={'X-Served-By': 'sanic'},
        status=200
    )
```
