# 请求头(Headers)

请求和响应头分别在 `Request` 和 `HTTPResponse` 对象中起作用。 它们利用了 [multidict 包](https://multidict.readthedocs.io/en/stable/multidict.html#cimultidict)，该包允许单个键拥有多个值。

.. tip:: 提示一下

```
解析时，头部键会被转换为**小写**形式。对于头部字段名称不考虑大小写。
```

## 请求（Request）

Sanic 在将请求头呈现给开发者之前，确实会尝试对它们进行一些规范化处理，并针对常见用例提取一些潜在有意义的信息。

.. column::

```
#### 认证信息（Tokens）

格式为 `Token <token>` 或 `Bearer <token>` 的授权令牌会被提取到请求对象中，即：`request.token`。
```

.. column::

````
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
````

### 代理头(Proxy headers)

Sanic 对于代理头（proxy headers）信息有特别的处理方式。 See the [proxy headers](../advanced/proxy-headers.md) section for more details.

### 主机标头和动态URL的构建(Host header and dynamic URL construction)

.. column::

```
通过 request.host 可获取到有效主机名。有效主机名不一定与主机头相同，因为它优先采用代理转发的主机名，并且可以通过服务器名称设置强制指定。

Web 应用通常应使用此访问器，以便无论部署方式如何都能保持相同的功能。如有需要，实际主机头可以通过 request.headers 获取。

有效主机名还用于通过 request.url_for 动态构建 URL，该方法使用请求来确定处理器的外部地址。

.. tip:: 警惕恶意客户端

    这些 URL 可能通过发送误导性主机头信息被操纵。如果对此有所顾虑，建议改用 `app.url_for`。
```

.. column::

````
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
````

### 其他请求头(Other headers)

.. column::

```
所有请求头都可以通过 `request.headers` 访问，可以以字典形式访问这些头信息。对于头信息的大小写不作考虑，因此可以使用大写或小写键来访问。
```

.. column::

````
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
````

.. tip:: 提示一下

```
💡 `request.headers` 对象是一种特殊类型的字典，其中每个值都是一个列表。这是因为 HTTP 协议允许同一键被复用以发送多个值。

大多数时候，您可能想要通过 .get() 或 .getone() 方法获取第一个元素而非整个列表。如果您确实需要获取所有项目的列表，可以使用 .getall() 方法。
```

### 请求ID（Request ID）

.. column::

```
通常，通过 `X-Request-ID` 头部追踪请求是很方便或必要的。您可以轻松地通过以下方式访问该请求ID：`request.id`。
```

.. column::

````
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
````

## 响应(Response)

Sanic 会自动为您设置以下响应头部（在适当的情况下）：

- `content-length`
- `content-type`
- `connection`
- `transfer-encoding`

在大多数情况下，您无需担心设置这些响应头的信息。

.. column::

```
如果您想设置任何其他头部，可以在路由处理器中或响应中间件中完成。
```

.. column::

````
```python
@app.route("/")
async def handler(request):
    return text("Done.", headers={"content-language": "en-US"})

@app.middleware("response")
async def add_csp(request, response):
    response.headers["content-security-policy"] = "default-src 'none'; script-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self';base-uri 'self';form-action 'self'"
```
````

.. column::

```
一个常见的[中间件](middleware.md)应用场景是向每个响应添加一个 `X-Request-ID` 头部。如上所述：`request.id` 将提供来自传入请求的 ID。但是，即使请求头中没有提供 ID，也会自动为您提供一个 ID。

[有关更多详细信息，请查阅 API 文档](https://sanic.readthedocs.io/en/latest/sanic/api_reference.html#sanic.request.Request.id)
```

.. column::

````
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
````

