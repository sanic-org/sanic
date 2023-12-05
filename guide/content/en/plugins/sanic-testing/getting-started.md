---
title: Sanic Testing - Getting Started
---

# Getting Started

Sanic Testing is the *official* testing client for Sanic. Its primary use is to power the tests of the Sanic project itself. However, it is also meant as an easy-to-use client for getting your API tests up and running quickly.

## Minimum requirements

- **Python**: 3.7+
- **Sanic**: 21.3+

Versions of Sanic older than 21.3 have this module integrated into Sanic itself as `sanic.testing`.

## Install

Sanic Testing can be installed from PyPI:

```
pip install sanic-testing
```

## Basic Usage

As long as the `sanic-testing` package is in the environment, there is nothing you need to do to start using it.

### Writing a sync test

In order to use the test client, you just need to access the property `test_client` on your application instance:

```python
import pytest
from sanic import Sanic, response

@pytest.fixture
def app():
    sanic_app = Sanic("TestSanic")

    @sanic_app.get("/")
    def basic(request):
        return response.text("foo")

    return sanic_app

def test_basic_test_client(app):
    request, response = app.test_client.get("/")

    assert request.method.lower() == "get"
    assert response.body == b"foo"
    assert response.status == 200
```

### Writing an async test

In order to use the async test client in `pytest`, you should install the `pytest-asyncio` plugin.

```
pip install pytest-asyncio
```

You can then create an async test and use the ASGI client:

```python
import pytest
from sanic import Sanic, response

@pytest.fixture
def app():
    sanic_app = Sanic(__name__)

    @sanic_app.get("/")
    def basic(request):
        return response.text("foo")

    return sanic_app

@pytest.mark.asyncio
async def test_basic_asgi_client(app):
    request, response = await app.asgi_client.get("/")

    assert request.method.lower() == "get"
    assert response.body == b"foo"
    assert response.status == 200
```
