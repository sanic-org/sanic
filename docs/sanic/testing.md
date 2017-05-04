# Testing

Sanic endpoints can be tested locally using the `test_client` object, which
depends on the additional [aiohttp](https://aiohttp.readthedocs.io/en/stable/)
library. 

The `test_client` exposes `get`, `post`, `put`, `delete`, `patch`, `head` and `options` methods
for you to run against your application. A simple example (using pytest) is like follows:

```python
# Import the Sanic app, usually created with Sanic(__name__)
from external_server import app

def test_index_returns_200():
    request, response = app.test_client.get('/')
    assert response.status == 200

def test_index_put_not_allowed():
    request, response = app.test_client.put('/')
    assert response.status == 405
```

Internally, each time you call one of the `test_client` methods, the Sanic app is run at `127.0.01:42101` and 
your test request is executed against your application, using `aiohttp`. 

The `test_client` methods accept the following arguments and keyword arguments:

- `uri` *(default `'/'`)* A string representing the URI to test.
- `gather_request` *(default `True`)* A boolean which determines whether the
  original request will be returned by the function. If set to `True`, the
  return value is a tuple of `(request, response)`, if `False` only the
  response is returned.
- `server_kwargs` *(default `{}`) a dict of additional arguments to pass into `app.run` before the test request is run.
- `debug` *(default `False`)* A boolean which determines whether to run the server in debug mode.

The function further takes the `*request_args` and `**request_kwargs`, which are passed directly to the aiohttp ClientSession request.

For example, to supply data to a GET request, you would do the following:

```python
def test_get_request_includes_data():
    params = {'key1': 'value1', 'key2': 'value2'}
    request, response = app.test_client.get('/', params=params)
    assert request.args.get('key1') == 'value1'
```

And to supply data to a JSON POST request:

```python
def test_post_json_request_includes_data():
    data = {'key1': 'value1', 'key2': 'value2'}
    request, response = app.test_client.post('/', data=json.dumps(data))
    assert request.json.get('key1') == 'value1'
```


More information about
the available arguments to aiohttp can be found
[in the documentation for ClientSession](https://aiohttp.readthedocs.io/en/stable/client_reference.html#client-session).


### Deprecated: `sanic_endpoint_test`

Prior to version 0.3.2, testing was provided through the `sanic_endpoint_test` method. This method will be deprecated in the next major version after 0.4.0; please use the `test_client` instead.

```
from sanic.utils import sanic_endpoint_test

def test_index_returns_200():
    request, response = sanic_endpoint_test(app)
    assert response.status == 200
```

