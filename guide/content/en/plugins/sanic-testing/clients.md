---
title: Sanic Testing - Test Clients
---

# Test Clients

There are three different test clients available to you, each of them presents different capabilities.

## Regular sync client: `SanicTestClient`

The `SanicTestClient` runs an actual version of the Sanic Server on your local network to run its tests. Each time it calls an endpoint it will spin up a version of the application and bind it to a socket on the host OS. Then, it will use `httpx` to make calls directly to that application.

This is the typical way that Sanic applications are tested.

.. column::

    Once installing Sanic Testing, the regular `SanicTestClient` can be used without further setup. This is because Sanic does the leg work for you under the hood. 

.. column::

    ```python
    app.test_client.get("/path/to/endpoint")
    ```

.. column::

    However, you may find it desirable to instantiate the client yourself.

.. column::

    ```python
    from sanic_testing.testing import SanicTestClient

    test_client = SanicTestClient(app)
    test_client.get("/path/to/endpoint")
    ```

.. column::

    A third option for starting the test client is to use the `TestManager`. This is a convenience object that sets up both the `SanicTestClient` and the `SanicASGITestClient`.

.. column::

    ```python
    from sanic_testing import TestManager

    mgr = TestManager(app)
    app.test_client.get("/path/to/endpoint")
    # or
    mgr.test_client.get("/path/to/endpoint")
    ```

You can make a request by using one of the following methods

- `SanicTestClient.get`
- `SanicTestClient.post`
- `SanicTestClient.put`
- `SanicTestClient.patch`
- `SanicTestClient.delete`
- `SanicTestClient.options`
- `SanicTestClient.head`
- `SanicTestClient.websocket`
- `SanicTestClient.request`

You can use these methods *almost* identically as you would when using `httpx`. Any argument that you would pass to `httpx` will be accepted, **with one caveat**: If you are using `test_client.request` and want to manually specify the HTTP method, you should use: `http_method`:

```python
test_client.request("/path/to/endpoint", http_method="get")
```

## ASGI async client: `SanicASGITestClient`

Unlike the `SanicTestClient` that spins up a server on every request, the `SanicASGITestClient` does not. Instead it makes use of the `httpx` library to execute Sanic as an ASGI application to reach inside and execute the route handlers.

.. column::

    This test client provides all of the same methods and generally works as the `SanicTestClient`. The only difference is that you will need to add an `await` to each call:

.. column::

    ```python
    await app.test_client.get("/path/to/endpoint")
    ```

The `SanicASGITestClient` can be used in the exact same three ways as the `SanicTestClient`.


.. note::

    The `SanicASGITestClient` does not need to only be used with ASGI applications. The same way that the `SanicTestClient` does not need to only test sync endpoints. Both of these clients are capable of testing *any* Sanic application.


## Persistent service client: `ReusableClient`

This client works under a similar premise as the `SanicTestClient` in that it stands up an instance of your application and makes real HTTP requests to it. However, unlike the `SanicTestClient`, when using the `ReusableClient` you control the lifecycle of the application.

That means that every request **does not** start a new web server. Instead you will start the server and stop it as needed and can make multiple requests to the same running instance.

.. column::

    Unlike the other two clients, you **must** instantiate this client for use:

.. column::

    ```python
    from sanic_testing.reusable import ReusableClient

    client = ReusableClient(app)
    ```

.. column::

    Once created, you will use the client inside of a context manager. Once outside of the scope of the manager, the server will shutdown.

.. column::

    ```python
    from sanic_testing.reusable import ReusableClient

    def test_multiple_endpoints_on_same_server(app):
        client = ReusableClient(app)
        with client:
            _, response = client.get("/path/to/1")
            assert response.status == 200

            _, response = client.get("/path/to/2")
            assert response.status == 200
    ```
