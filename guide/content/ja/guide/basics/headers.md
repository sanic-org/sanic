# ヘッダー

リクエストヘッダーとレスポンスヘッダーは `Request` オブジェクトと `HTTPResponse` オブジェクトでそれぞれ使用できます。 1つのキーが複数の値を持つことを可能にする[`multidict` package](https://multidict.io/en/stable/multidict.html#cimmultidict) を使用します。

.. tip:: FYI

```
ヘッダキーは解析時に *小文字* に変換されます。ヘッダの場合は大文字化は考慮されません。
```

## リクエスト

Sanic は、リクエストヘッダの正規化を開発者に提示する前に試みています。 一般的なユースケースに意味のある抽出物を作ることもできます

.. 列::

```
#### トークン

`トークン <token>`または `ベアラー <token>`の形式の承認トークンは、リクエストオブジェクト`request.token`に抽出されます。
```

.. 列::

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

### プロキシヘッダー

Sanicはプロキシヘッダーのための特別な扱いを持っています。 詳細は [プロキシ ヘッダー](/guide/advanced/proxy-headers.md) をご覧ください。

### ホストヘッダーと動的なURLの構築

.. 列::

```
The *effective host* is available via `request.host`. This is not necessarily the same as the host header, as it prefers proxy-forwarded host and can be forced by the server name setting.

Webapps should generally use this accessor so that they can function the same no matter how they are deployed. The actual host header, if needed, can be found via `request.headers`

The effective host is also used in dynamic URL construction via `request.url_for`, which uses the request to determine the external address of a handler.

.. tip:: Be wary of malicious clients

    These URLs can be manipulated by sending misleading host headers. `app.url_for` should be used instead if this is a concern.
```

.. 列::

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

### その他のヘッダー

.. 列::

```
すべてのリクエストヘッダは `request.headers` 上で利用可能で、辞書形式でアクセスできます。 大文字化はヘッダとは見なされず、大文字または小文字のいずれかのキーでアクセスできます。
```

.. 列::

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
💡 request.headers オブジェクトは、それぞれの値がリストになる辞書である数少ない型の1つです。 これは、HTTP が 1 つのキーを再利用して複数の値を送信することを可能にするためです。

ほとんどの場合、.get() または . を使用します。 etone() メソッドは、リストではなく最初の要素にアクセスします。すべての要素のリストが必要な場合は、.getall() を使用できます。
```

### 要求ID

.. 列::

```
`X-Request-ID` ヘッダーでリクエストを追跡するのは便利なことや必要なことがよくあります。`request.id` に簡単にアクセスできます。
```

.. 列::

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

## 回答

Sanicは次のレスポンスヘッダーを自動的に設定します（適切な場合）：

- `content-length`
- `content-type`
- `connection`
- `transfer-encoding`

ほとんどの状況では、これらのヘッダーを設定することを心配する必要はありません。

.. 列::

```
設定したい他のヘッダーは、route (ルート)ハンドラか、レスポンスミドルウェアのどちらかで行うことができます。
```

.. 列::

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

.. 列::

```
A common [middleware](middleware.md) you might want is to add a `X-Request-ID` header to every response. As stated above: `request.id` will provide the ID from the incoming request. But, even if no ID was supplied in the request headers, one will be automatically supplied for you.

[See API docs for more details](https://sanic.readthedocs.io/en/latest/sanic/api_reference.html#sanic.request.Request.id)
```

.. 列::

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

