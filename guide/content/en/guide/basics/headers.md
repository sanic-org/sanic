# Headers

Request and response headers are available in the `Request` and `HTTPResponse` objects, respectively. They make use of the [`multidict` package](https://multidict.readthedocs.io/en/stable/multidict.html#cimultidict) that allows a single key to have multiple values.


.. tip:: FYI

    Header keys are converted to *lowercase* when parsed. Capitalization is not considered for headers.


## Request

Sanic does attempt to do some normalization on request headers before presenting them to the developer, and also make some potentially meaningful extractions for common use cases.

.. column::

    #### Tokens

    Authorization tokens in the form `Token <token>` or `Bearer <token>` are extracted to the request object: `request.token`.

.. column::

    ```python
    @app.route("/")
    async def handler(request):
        return text(request.token)
    ```

    ```sh
    curl localhost:8000 \
        -H "Authorization: Token ABCDEF12345679"
    ABCDEF12345679
    ```

    ```sh
    curl localhost:8000 \
        -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
    ```

### Proxy headers

Sanic has special handling for proxy headers. See the [proxy headers](/guide/advanced/proxy-headers.md) section for more details.

### Host header and dynamic URL construction

.. column::

    The *effective host* is available via `request.host`. This is not necessarily the same as the host header, as it prefers proxy-forwarded host and can be forced by the server name setting.

    Webapps should generally use this accessor so that they can function the same no matter how they are deployed. The actual host header, if needed, can be found via `request.headers`

    The effective host is also used in dynamic URL construction via `request.url_for`, which uses the request to determine the external address of a handler.

    .. tip:: Be wary of malicious clients

        These URLs can be manipulated by sending misleading host headers. `app.url_for` should be used instead if this is a concern.

.. column::

    ```python
    app.config.SERVER_NAME = "https://example.com"

    @app.route("/hosts", name="foo")
    async def handler(request):
        return json(
            {
                "effective host": request.host,
                "host header": request.headers.get("host"),
                "forwarded host": request.forwarded.get("host"),
                "you are here": request.url_for("foo"),
            }
        )
    ```

    ```sh
    curl localhost:8000/hosts
    {
      "effective host": "example.com",
      "host header": "localhost:8000",
      "forwarded host": null,
      "you are here": "https://example.com/hosts"
    }
    ```

### Other headers

.. column::


    All request headers are available on `request.headers`, and can be accessed in dictionary form. Capitalization is not considered for headers, and can be accessed using either uppercase or lowercase keys.

.. column::

    ```python
    @app.route("/")
    async def handler(request):
        return json(
            {
                "foo_weakref": request.headers["foo"],
                "foo_get": request.headers.get("Foo"),
                "foo_getone": request.headers.getone("FOO"),
                "foo_getall": request.headers.getall("fOo"),
                "all": list(request.headers.items()),
            }
        )
    ```

    ```sh
    curl localhost:9999/headers -H "Foo: one" -H "FOO: two"|jq
    {
      "foo_weakref": "one",
      "foo_get": "one",
      "foo_getone": "one",
      "foo_getall": [
        "one",
        "two"
      ],
      "all": [
        [
          "host",
          "localhost:9999"
        ],
        [
          "user-agent",
          "curl/7.76.1"
        ],
        [
          "accept",
          "*/*"
        ],
        [
          "foo",
          "one"
        ],
        [
          "foo",
          "two"
        ]
      ]
    }
    ```



.. tip:: FYI

    💡 The request.headers object is one of a few types that is a dictionary with each value being a list. This is because HTTP allows a single key to be reused to send multiple values.

    Most of the time you will want to use the .get() or .getone() methods to access the first element and not a list. If you do want a list of all items, you can use .getall().


### Request ID

.. column::

    Often it is convenient or necessary to track a request by its `X-Request-ID` header. You can easily access that as: `request.id`.

.. column::

    ```python
    @app.route("/")
    async def handler(request):
        return text(request.id)
    ```

    ```sh
    curl localhost:8000 \
        -H "X-Request-ID: ABCDEF12345679"
    ABCDEF12345679
    ```

## Response

Sanic will automatically set the following response headers (when appropriate) for you:

- `content-length`
- `content-type`
- `connection`
- `transfer-encoding`

In most circumstances, you should never need to worry about setting these headers.

.. column::

    Any other header that you would like to set can be done either in the route handler, or a response middleware.

.. column::

    ```python
    @app.route("/")
    async def handler(request):
        return text("Done.", headers={"content-language": "en-US"})

    @app.middleware("response")
    async def add_csp(request, response):
        response.headers["content-security-policy"] = "default-src 'none'; script-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self';base-uri 'self';form-action 'self'"
    ```


.. column::

    A common [middleware](middleware.md) you might want is to add a `X-Request-ID` header to every response. As stated above: `request.id` will provide the ID from the incoming request. But, even if no ID was supplied in the request headers, one will be automatically supplied for you.

    [See API docs for more details](https://sanic.readthedocs.io/en/latest/sanic/api_reference.html#sanic.request.Request.id)

.. column::

    ```python
    @app.route("/")
    async def handler(request):
        return text(str(request.id))

    @app.on_response
    async def add_request_id_header(request, response):
        response.headers["X-Request-ID"] = request.id
    ```

    ```sh
    curl localhost:8000 -i
    HTTP/1.1 200 OK
    X-Request-ID: 805a958e-9906-4e7a-8fe0-cbe83590431b
    content-length: 36
    connection: keep-alive
    content-type: text/plain; charset=utf-8

    805a958e-9906-4e7a-8fe0-cbe83590431b
    ```

