# Response

Use functions in `sanic.response` module to create responses.

- `text` - Plain text response

```python
from sanic import response


@app.route('/text')
def handle_request(request):
    return response.text('Hello world!')
```

- `html` - HTML response

```python
from sanic import response


@app.route('/html')
def handle_request(request):
    return response.html('<p>Hello world!</p>')
```

- `json` - JSON response


```python
from sanic import response


@app.route('/json')
def handle_request(request):
    return response.json({'message': 'Hello world!'})
```

- `file` - File response

```python
from sanic import response


@app.route('/file')
async def handle_request(request):
    return await response.file('/srv/www/whatever.png')
```

- `stream` - Streaming response

```python
from sanic import response

@app.route("/streaming")
async def index(request):
    async def streaming_fn(response):
        await response.write('foo')
        await response.write('bar')
    return response.stream(streaming_fn, content_type='text/plain')
```

- `redirect` - Redirect response

```python
from sanic import response


@app.route('/redirect')
def handle_request(request):
    return response.redirect('/json')
```

- `raw` - Raw response, response without encoding the body

```python
from sanic import response


@app.route('/raw')
def handle_request(request):
    return response.raw('raw data')
```


To modify headers or status code, pass the `headers` or `status` argument to those functions:

```python
from sanic import response


@app.route('/json')
def handle_request(request):
    return response.json(
        {'message': 'Hello world!'},
        headers={'X-Served-By': 'sanic'},
        status=200
    )
```
