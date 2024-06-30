# ルーティング

.. 列::

```
これまで、様々な形でこのデコレータをたくさん見てきました。

しかし、それは何ですか？そして、どのように使うのですか？
```

.. 列::

````
```python
@app.route("/storeway")
    ...

@app.get("/to")
    ...

@app.post("/heaven")
    ...
```
````

## ルートの追加

.. 列::

```
ハンドラをエンドポイントに接続する最も基本的な方法は、 `app.add_route()` です。

詳細は [API docs](https://sanic.readthedocs.io/en/stable/sanic/api_reference.html#sanic.app.url_for) を参照してください。
```

.. 列::

````
```python
async def handler(request):
    return text("OK")

app.add_route(handler, "/test")
```
````

.. 列::

```
デフォルトでは、ルートは HTTP `GET` 呼び出しとして使用できます。ハンドラーを1つまたは複数の HTTP メソッドに応答するように変更できます。
```

.. 列::

````
```python
app.add_route(
    handler,
    '/test',
    methods=["POST", "PUT"],
)
```
````

.. 列::

```
デコレータ構文を使用すると、前の例はこれと同じです。
```

.. 列::

````
```python
@app.route('/test', methods=["POST", "PUT"])
async def handler(request):
    return text('OK')
```
````

## HTTPメソッド

それぞれの標準的な HTTP メソッドには、利便性のデコレータがあります。

### 取得

```python
@app.get('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/GET)

### POST

```python
@app.post('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/POST

### PUT

```python
@app.put('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/PUT)

### PATCH

```python
@app.patch('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/PATCH)

### 削除

```python
@app.delete('/test')
async def handler(request):
    return text('OK')
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/DELETE)

### 頭

```python
@app.head('/test')
async def handler(request):
    return empty()
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/HEAD)

### オプション

```python
@app.options('/test')
async def handler(request):
    return empty()
```

[MDN Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/OPTIONS)

.. 警告::

````
By default, Sanic will **only** consume the incoming request body on non-safe HTTP methods: `POST`, `PUT`, `PATCH`, `DELETE`. If you want to receive data in the HTTP request on any other method, you will need to do one of the following two options:

**Option #1 - Tell Sanic to consume the body using `ignore_body`**
```python
@app.request("/path", ignore_body=False)
async def handler(_):
    ...
```

**Option #2 - Manually consume the body in the handler using `receive_body`**
```python
@app.get("/path")
async def handler(request: Request):
    await request.receive_body()
```
````

## パスパラメータ

.. 列::

```
SanicはパターンマッチングとURLパスからの値抽出を可能にします。これらのパラメータはルートハンドラのキーワード引数として注入されます。
```

.. 列::

````
```python
@app.get("/tag/<tag>")
async def tag_handler(request, tag):
    return text("Tag - {}".format(tag))
```
````

.. 列::

```
パラメータの型を宣言できます。これはマッチング時に強制され、変数をキャストします。
```

.. 列::

````
```python
@app.get("/foo/<foo_id:uuid>")
async def uuid_handler(request, foo_id: UUID):
    return text("UUID - {}".format(foo_id))
```
````

.. 列::

```
`str`、`int`、`UUID`のようないくつかの標準型では、Sanicは関数のシグネチャからパスパラメータ型を推測することができます。 つまり、pathパラメータ定義に型を含める必要があるわけではありません。
```

.. 列::

````
```python
@app.get("/foo/<foo_id>")  # Notice there is no :uuid in the path parameter
async def uuid_handler(request, foo_id: UUID):
    return text("UUID - {}".format(foo_id))
```
````

### サポートされているタイプ

### `str`

.. 列::

```
**正規表現が適用されました**: `r"[^/]+"`  
**キャストタイプ**: `str`  
**一致例**:  

- `/path/to/Bob`
- `/path/to/Python%203`

v22から始まります。 `str`は空の文字列では*マッチしません*。この動作については`strorempty`を参照してください。
```

.. 列::

````
```python
@app.route("/path/to/<foo:str>")
async def handler(request, foo: str):
    ...
```
````

### `strorempty`

.. 列::

```
**Regular expression applied**: `r"[^/]*"`  
**Cast type**: `str`  
**Example matches**:

- `/path/to/Bob`
- `/path/to/Python%203`
- `/path/to/`

Unlike the `str` path parameter type, `strorempty` can also match on an empty string path segment.

*Added in v22.3*
```

.. 列::

````
```python
@app.route("/path/to/<foo:strorempty>")
async def handler(request, foo: str):
    ...
```
````

### `int`

.. 列::

```
**正規表現が適用されます**: `r"-?\d+"`  
**キャストタイプ**: `int`  
**一致例**:  

- `/path/to/10`
- `/path/to/-10`

_float, hex, octal, etc_
```

.. 列::

````
```python
@app.route("/path/to/<foo:int>")
async def handler(request, foo: int):
    ...
```
````

### `float`

.. 列::

```
**正規表現が適用されます**: `r"-?(?:\d+(?:\.\d*)?|\.\d+)"`  
**キャストタイプ**: `float`  
**マッチ例**:  

- `/path/to/10`
- `/path/to/-10`
- `/path/to/1.5`
```

.. 列::

````
```python
@app.route("/path/to/<foo:float>")
async def handler(request, foo: float):
    ...
```
````

### `alpha`

.. 列::

```
**正規表現が適用されました**: `r"[A-Za-z]+"`  
**キャストタイプ**: `str`  
**一致例**:  

- `/path/to/Bob`
- `/path/to/Python`

_数字と一致しません。 またはスペースまたはその他の特殊文字_
```

.. 列::

````
```python
@app.route("/path/to/<foo:alpha>")
async def handler(request, foo: str):
    ...
```
````

### `slug`

.. 列::

```
**正規表現が適用されます**: `r"[a-z0-9]+(?:-[a-z0-9]+)*"`  
**キャストタイプ**: `str`  
**一致例**:  

- `/path/to/some-news-story`
- `/path/to/or-has-digits-123`

*v21.6* に追加されました
```

.. 列::

````
```python
@app.route("/path/to/<article:slug>")
async def handler(request, article: str):
    ...
```
````

### `path`

.. 列::

```
**正規表現が適用されます**: `r"[^/].*?"`  
**キャストタイプ**: `str`  
**一致例**:
- `/path/to/hello`
- `/path/to/hello.txt`
- `/path/to/hello/world.txt`
```

.. 列::

````
```python
@app.route("/path/to/<foo:path>")
async def handler(request, foo: str):
    ...
```
````

.. 警告::

```
これは `/` にマッチするためです。 `path`を使ってパターンをテストすれば、別の端点に向かってトラフィックを捕まえることができません。 さらに、このタイプの使い方に応じて、アプリケーションにパストラバーサルの脆弱性を作成する可能性があります。 これに対してエンドポイントを保護するのはあなたの仕事です。 でも必要な場合はコミュニティチャンネルでお気軽にお問い合わせください :)
```

### `ymd`

.. 列::

```
**Regular expression applied**: `r"^([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))"`  
**Cast type**: `datetime.date`  
**Example matches**:  

- `/path/to/2021-03-28`
```

.. 列::

````
```python
@app.route("/path/to/<foo:ymd>")
async def handler(request, foo: datetime.date):
    ...
```
````

### `uuid`

.. 列::

```
**Regular expression applied**: `r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}"`  
**Cast type**: `UUID`  
**Example matches**:  

- `/path/to/123a123a-a12a-1a1a-a1a1-1a12a1a12345`
```

.. 列::

````
```python
@app.route("/path/to/<foo:uuid>")
async def handler(request, foo: UUID):
    ...
```
````

### ext

.. 列::

```
**正規表現が適用されました**: n/a
**キャストタイプ**: *varies*
**一致例**:
```

.. 列::

````
```python
@app.route("/path/to/<foo:ext>")
async def handler(request, foo: str, ext: str):
    ...
```
````

| 定義                                                       | 例                                                           | ファイル名    | 拡張         |
| -------------------------------------------------------- | ----------------------------------------------------------- | -------- | ---------- |
| \file:ext                                | page.txt                                    | `"page"` | `"txt"`    |
| \file:ext=jpg                            | cat.jpg                                     | `"cat"`  | `"jpg"`    |
| \file:ext=jpg\\\|png\\\|gif\\\|svg | cat.jpg                                     | `"cat"`  | `"jpg"`    |
| \<file=int:ext>                          | 123.txt                                     | `123`    | `"txt"`    |
| \<file=int:ext=jpg\\|png\\|gif\\|svg> | 123.svg                                     | `123`    | `"svg"`    |
| \<file=float:ext=tar.gz> | 3.14.tar.gz | `3.14`   | `"tar.gz"` |

ファイル拡張子は、特別なパラメータタイプ`ext`を使用して一致させることができます。 これは、ファイル名として他のタイプのパラメータを指定することができる特別な形式を使用します。 上の表に示されているように、1つまたは複数の特定の拡張子を指定します。

`path`パラメータ型は\*サポートしていません。

_v22.3_に追加されました

### Regex

.. 列::

```
**Regular expression applied**: _whatever you insert_  
**Cast type**: `str`  
**Example matches**:  

- `/path/to/2021-01-01`

This gives you the freedom to define specific matching patterns for your use case.

In the example shown, we are looking for a date that is in `YYYY-MM-DD` format.
```

.. 列::

````
```python
@app.route(r"/path/to/<foo:([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))>")
async def handler(request, foo: str):
    ...
```
````

### 正規表現の一致

多くの場合、複雑なルーティングと比較して、上記の例は単純すぎます。 我々は全く異なるルーティングマッチングパターンを使っています ここではRegexマッチングの高度な使い方を詳しく説明します

ルートの一部をマッチさせたい場合もあります。

```text
/image/123456789.jpg
```

ファイルパターンを一致させたいが、数値部分だけをキャプチャしたい場合は、正規表現の楽しみ😄:

```python
app.route(r"/image/<img_id:(?P<img_id>\d+)\.jpg>")
```

さらに、これらはすべて許容されるべきです:

```python
@app.get(r"/<foo:[a-z]{3}.txt>")                # matching on the full pattern
@app.get(r"/<foo:([a-z]{3}).txt>")              # defining a single matching group
@app.get(r"/<foo:(?P<foo>[a-z]{3}).txt>")       # defining a single named matching group
@app.get(r"/<foo:(?P<foo>[a-z]{3}).(?:txt)>")   # defining a single named matching group, with one or more non-matching groups
```

また、名前付きの一致グループを使用する場合は、セグメント ラベルと同じでなければなりません。

```python
@app.get(r"/<foo:(?P<foo>\d+).jpg>")  # OK
@app.get(r"/<foo:(?P<bar>\d+).jpg>")  # NOT OK
```

format@@0(https://docs.python.org/3/library/re.html) を参照してください。

## URLの生成

.. 列::

```
Sanicはハンドラメソッド名`app.url_for()`に基づいてURLを生成するメソッドを提供しています。 これは、アプリケーション内のハードコーディングの url パスを避けたい場合に便利です。代わりに、ハンドラ名を参照するだけです。
```

.. 列::

````
```python
@app.route('/')
async def index(request):
    # generate a URL for the endpoint `post_handler`
    url = app.url_for('post_handler', post_id=5)

    # Redirect to `/posts/5`
    return redirect(url)

@app.route('/posts/<post_id>')
async def post_handler(request, post_id):
    ...
```
````

.. 列::

```
任意の数のキーワード引数を渡せます。 リクエストパラメータでないものは、クエリ文字列の一部として実装されます。
```

.. 列::

````
```python
assert app.url_for(
    "post_handler",
    post_id=5,
    arg_one="one",
    arg_two",
) == "/posts/5?arg_one=one&arg_two"
```
````

.. 列::

```
また、単一のクエリキーに複数の値を渡すこともサポートされています。
```

.. 列::

````
```python
assert app.url_for(
    "post_handler",
    post_id=5,
    arg_one=["one", "two"],
) == "/posts/5?arg_one=one_one=two"
```
````

### 特殊キーワード引数

詳細は API Docs を参照してください。

```python
app.url_for("post_handler", post_id=5, arg_one="one", _anchor="anchor")
# '/posts/5?arg_one=one#anchor'

# _external requires you to pass an argument _server or set SERVER_NAME in app.config if not url will be same as no _external
app.url_for("post_handler", post_id=5, arg_one="one", _external=True)
# '//server/posts/5?arg_one=one'

# when specifying _scheme, _external must be True
app.url_for("post_handler", post_id=5, arg_one="one", _scheme="http", _external=True)
# 'http://server/posts/5?arg_one=one'

# you can pass all special arguments at once
app.url_for("post_handler", post_id=5, arg_one=["one", "two"], arg_two=2, _anchor="anchor", _scheme="http", _external=True, _server="another_server:8888")
# 'http://another_server:8888/posts/5?arg_one=one&arg_one=two&arg_two=2#anchor'
```

### ルート名をカスタマイズ

.. 列::

```
route (ルート)を登録する際に `name` 引数を渡すことで、カスタムルート名を使用できます。
```

.. 列::

````
```python
@app.get("/get", name="get_handler")
def handler(request):
    return text("OK")
```
````

.. 列::

```
このカスタム名を使用してURLを取得する
```

.. 列::

````
```python
assert app.url_for("get_handler", foo="bar") == "/get?foo=bar"
```
````

## Websockets routes

.. 列::

```
Websocket ルーティングは HTTP メソッドに似ています。
```

.. 列::

````
```python
async def handler(request, ws):
    message = "Start"
    while True:
        await ws.send(message)
        message = await ws.recv()

app.add_websocket_route(handler, "/test")
```
````

.. 列::

```
それはまた、コンビニエンスデコレータを持っています。
```

.. 列::

````
```python
@app.websocket("/test")
async def handler(request, ws:
    message = "Start"
    while True:
        await ws.send(message)
        message = await ws.recv()
```
````

動作の詳細については、[websockets section](/guide/advanced/websockets.md) をご覧ください。

## 厳密なスラッシュ

.. 列::

```
Sanic routes can be configured to strictly match on whether or not there is a trailing slash: `/`. This can be configured at a few levels and follows this order of precedence:

1. Route
2. Blueprint
3. BlueprintGroup
4. Application
```

.. 列::

````
```python
# provide default strict_slashes value for all routes
app = Sanic(__file__, strict_slashes=True)
```

```python
# overwrite strict_slashes value for specific route
@app.get("/get", strict_slashes=False)
def handler(request):
    return text("OK")
```

```python
# it also works for blueprints
bp = Blueprint(__file__, strict_slashes=True)

@bp.get("/bp/get", strict_slashes=False)
def handler(request):
    return text("OK")
```

```python
bp1 = Blueprint(name="bp1", url_prefix="/bp1")
bp2 = Blueprint(
    name="bp2",
    url_prefix="/bp2",
    strict_slashes=False,
)

# This will enforce strict slashes check on the routes
# under bp1 but ignore bp2 as that has an explicitly
# set the strict slashes check to false
group = Blueprint.group([bp1, bp2], strict_slashes=True)
```
````

## 静的ファイル

.. 列::

```
In order to serve static files from Sanic, use `app.static()`.

The order of arguments is important:

1. Route the files will be served from
2. Path to the files on the server

See [API docs](https://sanic.readthedocs.io/en/stable/sanic/api/app.html#sanic.app.Sanic.static) for more details.
```

.. 列::

````
```python
app.static("/static/", "/path/to/directory/")
```
````

.. tip::

```
一般的には、ディレクトリパスをスラッシュ(`/this/is/a/directory/`)で終わらせることをお勧めします。これにより、より明示的に曖昧さを削除します。
```

.. 列::

```
個々のファイルを提供することもできます。
```

.. 列::

````
```python
app.static("/", "/path/to/index.html")
```
````

.. 列::

```
エンドポイントに名前を付けることも時々役に立ちます
```

.. 列::

````
```python
app.static(
    "/user/uploads/",
    "/path/to/uploads/",
    name="uploads",
)
```
````

.. 列::

```
URL の取得はハンドラに似ていますが、ディレクトリ内に特定のファイルが必要な場合は、 `filename` 引数を追加することもできます。
```

.. 列::

````
```python
assert app.url_for(
    "static",
    name="static",
    filename="file.txt",
) == "/static/file.txt"
```
```python
assert app.url_for(
    "static",
    name="uploads",
    filename="image.png",
) == "/user/uploads/image.png"

```
````

.. tip::

````
複数の `static()`ルートを持つ場合は、手動で名前を付けることを提案されています。 これはバグを発見することが難しい可能性をほぼ確実に緩和します。

```python
app.static("/user/uploads/", "/path/to/uploads/", name="uploads")
app.static("/user/profile/", "/path/to/profile/", name="profile_pics")
```
````

#### 自動インデックス作成

.. 列::

```
indexページによって提供されるべき静的ファイルのディレクトリがある場合は、indexのファイル名を指定できます。 ディレクトリの URL に到達すると、インデックス ページが表示されます。
```

.. 列::

````
```python
app.static("/foo/", "/path/to/foo/", index="index="html")
```
````

_V23.3_に追加されました

#### ファイルブラウザー

.. 列::

```
静的ハンドラからディレクトリを提供する場合、Sanic は `directory_view=True` を使用して基本的なファイルブラウザーを表示するように設定することができます。
```

.. 列::

````
```python
app.static("/uploads/", "/path/to/dir", directory_view=True)
```
````

ブラウザーにブラウザーが表示されるようになりました：

![image](/assets/images/directory-view.png)

_V23.3_に追加されました

## ルートの説明

.. 列::

```
route (ルート)が定義された場合、任意の数のキーワード引数を `ctx_` プレフィックスで追加できます。 これらの値はルート `ctx` オブジェクトに注入されます。
```

.. 列::

````
```python
@app.get("/1", ctx_label="something")
async def handler1(request):
    ...

@app.get("/2", ctx_label="something")
async def handler2(request):
    ...

@app.get("/99")
async def handler99(request):
    ...

@app.on_request
async def do_something(request):
    if request.route.ctx.label == "something":
        ...
```
````

_v21.12_ に追加されました
