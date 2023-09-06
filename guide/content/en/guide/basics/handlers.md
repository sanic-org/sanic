# Handlers

The next important building block are your _handlers_. These are also sometimes called "views".

In Sanic, a handler is any callable that takes at least a `Request` instance as an argument, and returns either an `HTTPResponse` instance, or a coroutine that does the same.



.. column::

    Huh? 😕

    It is a **function**; either synchronous or asynchronous.

    The job of the handler is to respond to an endpoint and do something. This is where the majority of your business logic will go.

.. column::

    ```python
    def i_am_a_handler(request):
        return HTTPResponse()

    async def i_am_ALSO_a_handler(request):
        return HTTPResponse()
    ```

.. tip:: Heads up

    If you want to learn more about encapsulating your logic, checkout [class based views](/guide/advanced/class-based-views.md).


.. column::

    Then, all you need to do is wire it up to an endpoint. We'll learn more about [routing soon](./routing.md).

    Let's look at a practical example.

    - We use a convenience decorator on our app instance: `@app.get()`
    - And a handy convenience method for generating out response object: `text()`

    Mission accomplished :muscle:

.. column::

    ```python
    from sanic.response import text

    @app.get("/foo")
    async def foo_handler(request):
        return text("I said foo!")
    ```

---

## A word about _async_...

.. column::

    It is entirely possible to write handlers that are synchronous.

    In this example, we are using the _blocking_ `time.sleep()` to simulate 100ms of processing time. Perhaps this represents fetching data from a DB, or a 3rd-party website.

    Using four (4) worker processes and a common benchmarking tool:

    - **956** requests in 30.10s
    - Or, about **31.76** requests/second

.. column::

    ```python
    @app.get("/sync")
    def sync_handler(request):
        time.sleep(0.1)
        return text("Done.")
    ```


.. column::

    Just by changing to the asynchronous alternative `asyncio.sleep()`, we see an incredible change in performance. 🚀

    Using the same four (4) worker processes:

    - **115,590** requests in 30.08s
    - Or, about **3,843.17** requests/second

    .. attrs::
        :class: is-size-3
    
        🤯

    Okay... this is a ridiculously overdramatic result. And any benchmark you see is inherently very biased. This example is meant to over-the-top show the benefit of `async/await` in the web world. Results will certainly vary. Tools like Sanic and other async Python libraries are not magic bullets that make things faster. They make them _more efficient_.

    In our example, the asynchronous version is so much better because while one request is sleeping, it is able to start another one, and another one, and another one, and another one...

    But, this is the point! Sanic is fast because it takes the available resources and squeezes performance out of them. It can handle many requests concurrently, which means more requests per second.

.. column::

    ```python
    @app.get("/async")
    async def async_handler(request):
        await asyncio.sleep(0.1)
        return text("Done.")
    ```



.. warning:: A common mistake!

    Don't do this! You need to ping a website. What do you use? `pip install your-fav-request-library` 🙈

    Instead, try using a client that is `async/await` capable. Your server will thank you. Avoid using blocking tools, and favor those that play well in the asynchronous ecosystem. If you need recommendations, check out [Awesome Sanic](https://github.com/mekicha/awesome-sanic).

    Sanic uses [httpx](https://www.python-httpx.org/) inside of its testing package (sanic-testing) :wink:.


---

## A fully annotated handler

For those that are using type annotations...

```python
from sanic.response import HTTPResponse, text
from sanic.request import Request

@app.get("/typed")
async def typed_handler(request: Request) -> HTTPResponse:
    return text("Done.")
```
