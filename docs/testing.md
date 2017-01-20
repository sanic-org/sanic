# Testing

Sanic endpoints can be tested locally using the `sanic.utils` module, which
depends on the additional [aiohttp](https://aiohttp.readthedocs.io/en/stable/)
library. The `sanic_endpoint_test` function runs a local server, issues a
configurable request to an endpoint, and returns the result. It takes the
following arguments:

- `app` An instance of a Sanic app.
- `method` *(default `'get'`)* A string representing the HTTP method to use.
- `uri` *(default `'/'`)* A string representing the endpoint to test.
- `gather_request` *(default `True`)* A boolean which determines whether the
  original request will be returned by the function. If set to `True`, the
  return value is a tuple of `(request, response)`, if `False` only the
  response is returned.
- `loop` *(default `None`)* The event loop to use.
- `debug` *(default `False`)* A boolean which determines whether to run the
  server in debug mode.

The function further takes the `*request_args` and `**request_kwargs`, which
are passed directly to the aiohttp ClientSession request. For example, to
supply data with a GET request, `method` would be `get` and the keyword
argument `params={'value', 'key'}` would be supplied. More information about
the available arguments to aiohttp can be found
[in the documentation for ClientSession](https://aiohttp.readthedocs.io/en/stable/client_reference.html#client-session).

Below is a complete example of an endpoint test,
using [pytest](http://doc.pytest.org/en/latest/). The test checks that the
`/challenge` endpoint responds to a GET request with a supplied challenge
string.

```python
import pytest
import aiohttp
from sanic.utils import sanic_endpoint_test

# Import the Sanic app, usually created with Sanic(__name__)
from external_server import app

def test_endpoint_challenge():
    # Create the challenge data
    request_data = {'challenge': 'dummy_challenge'}

    # Send the request to the endpoint, using the default `get` method
    request, response = sanic_endpoint_test(app,
                                            uri='/challenge',
                                            params=request_data)

    # Assert that the server responds with the challenge string
    assert response.text == request_data['challenge']
```

**Previous:** [Custom protocols](custom_protocol.html)

**Next:** [Sanic extensions](extensions.html)
