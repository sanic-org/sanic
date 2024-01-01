# 信头

请求和响应头分别在 `Request` 和 `HTTPResponse` 对象中可用。 他们使用 [`multidict` 包](https://multidict.readthocs.io/en/stable/multidict.html#cimultidict) 让单个键有多个值。

.. tip:: FYI

```
解析后头键会转换为 *lowercase*。头部不考虑大小写。
```

## 请求

Sanic确实试图在请求头上实现某种正常化，然后将它们提交给开发者。 并为普通用途案件进行一些可能有意义的抽查。

.. 列:

```
#### Tokens

认证令牌在 `Token <token>` 或 `Wearer <token>中被提取到请求对象： `request.token` 。
```

.. 列:

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

### 代理信头

Sanic对代理头有特殊处理。 详情请查看[代理头](/guide/advanced/proxy-headers.md)部分。

### 主机头和动态URL设计

.. 列:

```
有效主机*可通过 `request.host`获取。 这不一定与主机头相同，因为它喜欢代理转发的主机，并且可以通过服务器名称设置强制执行。

网络应用通常应使用此访问器，以便不论如何部署，它们都能够正常运行。 如果需要，实际主机头可以通过“请求”找到。 eaders`

有效主机也用于通过 `required 构造动态 URL 。 rl_for`, 它使用请求来确定处理程序的外部地址。

提示：请警惕恶意客户端

    这些URL可以通过发送误导的主机头来操纵。 `app.url_for` 如果是关注的话应该被使用。
```

.. 列:

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

### 其他标题

.. 列:

```
所有请求标题都在 `request.headers` 上可用，可以用字典形式访问。 大写不被视为头件，可以使用大写或小写键访问。
```

.. 列:

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

.. tip:: FYI

```
💡 request.headers对象是几种类型的字典之一，每个值都是一个列表。 这是因为HTTP允许重用单个键来发送多个值。

您想要使用 .get() 或 . 的大部分时间。 etone() 方法来访问第一个元素而不是列表。如果你确实想要一个所有项目的列表，你可以使用 .getall()。
```

### 请求ID

.. 列:

```
通常，跟踪通过 `X-Request-ID` 文件头的请求是方便或必要的。您可以轻松访问 `request.id` 。
```

.. 列:

````
```python
@app.route("/")
async def 处理器(请求):
    return text(request). d)
```

```sh
curl localhost:8000 \
    - H "X-Request-ID: ABCDEF12345679"
ABCDEF12345679
```
````

## 答复

Sanic 将自动为您设置以下响应头(在适当时)：

- `content-length`
- `content-type`
- `connection`
- `transfer-encoding`

在大多数情况下，您永远不必担心设置这些信头。

.. 列:

```
您想要设置的任何其他页眉都可以在路由处理器或响应中间件中完成。
```

.. 列:

````
```python
@app.route("/")
async def handler(request):
    return text("完成"). , headers={"content-language": "en-US"})

@app.middleware("response")
async def add_csp(request, response):
    响应。 eaders["content-security policy"] = "default-src 'none'; script-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self';base-uri 'self';form-action 'self''
```
````

.. 列:

```
A common [middleware](middleware.md) you might want is to add a `X-Request-ID` header to every response. As stated above: `request.id` will provide the ID from the incoming request. But, even if no ID was supplied in the request headers, one will be automatically supplied for you.

[See API docs for more details](https://sanic.readthedocs.io/en/latest/sanic/api_reference.html#sanic.request.Request.id)
```

.. 列:

````
```python
@app.route("/")
async def handler(request):
    return text(str(request.id))

@app. n_response
async def add_request_id_header(request, response):
    response.headers["X-Request-ID"] = request。 d
```

```sh
curl localhost:8000 -i
HTTP/1。 200 OK
X-Request-ID： 805a958e-9906-4e7a-8fe0-cbe83590431b
内容长度： 36
连接： 保持
内容类型： text/pla；charset=utf-8

805a958e-9906-4e7a-8fe0-cbe83590431b
```
````
