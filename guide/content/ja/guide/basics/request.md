# リクエスト

API ドキュメント: [sanic.request](/api/sanic.request) を参照してください。

:class:`sanic.request.Request`インスタンスには、パラメータで入手可能な役立つ情報がたくさん含まれています。 詳細については、format@@0(https://sanic.readthedocs.io/)を参照してください。

[handlers](./handlers.md) のセクションで見たように、ルートハンドラの最初の引数は通常、 :class:の `sanic.request.Request` オブジェクトです。 Sanic は非同期フレームワークなので、ハンドラは[`asyncio.Task`](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task)の中で実行され、イベントループによってスケジュールされます。 これは、ハンドラが分離されたコンテキストで実行され、リクエストオブジェクトはそのハンドラのタスクに固有であることを意味します。

.. 列::

```
規約により、引数は `request` という名前になりますが、好きな名前を付けることができます。 引数の名前は重要ではありません。以下のハンドラの両方が有効です。
```

.. 列::

````
```python
@app.get("/foo")
async def typical_use_case(request):
    return text("I said foo!")
```

```python
@app.get("/foo")
async def atypical_use_case(req):
    return text("I said foo!")
```
````

.. 列::

```
リクエストオブジェクトに注釈を付けるのはとても簡単です。
    
```

.. 列::

````
```python
from sanic.request import Request
from sanic.response import text

@app.get("/typed")
async def typed_handler(request: Request):
    return text("Done.")
```
````

.. tip::

```
最新のIDEを使用していると仮定すると、コード補完とドキュメントを支援するために型注釈を活用する必要があります。 これは特に、 **MANY** のプロパティとメソッドがあるので、 `request` オブジェクトを使用する場合に便利です。
    
利用可能なプロパティとメソッドの完全なリストは、[API ドキュメント](/api/sanic.request) を参照してください。
```

## 本文

`Request`オブジェクトは、いくつかの方法でリクエストボディのコンテンツにアクセスできます。

### JSON

.. 列::

```
**Parameter**: `request.json`  
**Description**: 解析されたJSONオブジェクト
```

.. 列::

````
```bash
$ curl localhost:8000 -d '{"foo": "bar"}'
```

```python
>>> print(request.json)
{'foo': 'bar'}
```
````

### Raw

.. 列::

```
**Parameter**: `request.body`  
**Description**: リクエストボディからの生のバイト
```

.. 列::

````
```bash
$ curl localhost:8000 -d '{"foo": "bar"}'
```

```python
>>> print(request.body)
b'{"foo": "bar"}'
```
````

### フォーム

.. 列::

```
**Parameter**: `request.form`  
**Description**: The form data

.. tip:: FYI

    The `request.form` object is one of a few types that is a dictionary with each value being a list. This is because HTTP allows a single key to be reused to send multiple values.  

    Most of the time you will want to use the `.get()` method to access the first element and not a list. If you do want a list of all items, you can use `.getlist()`.
```

.. 列::

````
```bash
$ curl localhost:8000 -d 'foo=bar'
```

```python
>>> print(request.body)
b'foo=bar'

>>> print(request.form)
{'foo': ['bar']}

>>> print(request.form.get("foo"))
bar

>>> print(request.form.getlist("foo"))
['bar']
```
````

### アップロードしました

.. 列::

```
**Parameter**: `request.files`  
**Description**: The files uploaded to the server

.. tip:: FYI

    The `request.files` object is one of a few types that is a dictionary with each value being a list. This is because HTTP allows a single key to be reused to send multiple values.  

    Most of the time you will want to use the `.get()` method to access the first element and not a list. If you do want a list of all items, you can use `.getlist()`.
```

.. 列::

````
```bash
$ curl -F 'my_file=@/path/to/TEST' http://localhost:8000
```

```python
>>> print(request.body)
b'--------------------------cb566ad845ad02d3\r\nContent-Disposition: form-data; name="my_file"; filename="TEST"\r\nContent-Type: application/octet-stream\r\n\r\nhello\n\r\n--------------------------cb566ad845ad02d3--\r\n'

>>> print(request.files)
{'my_file': [File(type='application/octet-stream', body=b'hello\n', name='TEST')]}

>>> print(request.files.get("my_file"))
File(type='application/octet-stream', body=b'hello\n', name='TEST')

>>> print(request.files.getlist("my_file"))
[File(type='application/octet-stream', body=b'hello\n', name='TEST')]
```
````

## コンテキスト

### コンテキストをリクエスト

`request.ctx`オブジェクトは、リクエストに関して必要な情報を保存するためのプレイグラウンドです。 これはリクエストの期間のみ有効で、リクエストに固有のものです。

これはすべてのリクエストで共有される `app.ctx` オブジェクトで解釈できます。 それらを混乱させないように注意してください!

デフォルトでは `request.ctx` オブジェクトは `SimpleNamespace` オブジェクトで、任意の属性を設定できます。 Sanicはこのオブジェクトを何にも使用しないので、名前の衝突を心配することなく自由に使用できます。

### 典型的な使用例

これは、認証されたユーザーの詳細などのアイテムを格納するためによく使用されます。 あとで [middleware](./middleware.md) に入りますが、ここに簡単な例があります。

```python
@app.on_request
async def run_before_handler(request):
    request.ctx.user = await fetch_user_by_token(request.token)

@app.route('/hi')
async def hi_my_name_is(request):
    if not request.ctx.user:
        return text("Hmm... I don't know you)
    return text(f"Hi, my name is {request.ctx.user.name}")
```

ご覧のとおり、 `request. tx`オブジェクトは、複数のハンドラにアクセスするために必要な情報を格納するのに最適な場所です。 しかし、format@@0(./middleware) で学びます。 d)を使用して、別のミドルウェアから情報を保存することもできます。

### 接続の内容

.. 列::

```
Often times your API will need to serve multiple concurrent (or consecutive) requests to the same client. This happens, for example, very often with progressive web apps that need to query multiple endpoints to get data.

The HTTP protocol calls for an easing of overhead time caused by the connection with the use of [keep alive headers](../running/configuration.md#keep-alive-timeout).

When multiple requests share a single connection, Sanic provides a context object to allow those requests to share state.
```

.. 列::

````
```python
@app.on_request
async def increment_foo(request):
    if not hasattr(request.conn_info.ctx, "foo"):
        request.conn_info.ctx.foo = 0
    request.conn_info.ctx.foo += 1

@app.get("/")
async def count_foo(request):
    return text(f"request.conn_info.ctx.foo={request.conn_info.ctx.foo}")
```

```bash
$ curl localhost:8000 localhost:8000 localhost:8000
request.conn_info.ctx.foo=1
request.conn_info.ctx.foo=2
request.conn_info.ctx.foo=3
```
````

.. 警告::

```
リクエスト間の情報を1つのHTTP接続で保存するのに便利な場所に見えます。 単一の接続上のすべてのリクエストが単一のエンドユーザーから来たと仮定しないでください。 これは、HTTP プロキシとロードバランサが複数の接続をサーバに複数回接続できるためです。

**単一のユーザーに関する情報を保存するには、これを使用しないでください** 。 `request.ctx` オブジェクトを使用してください。
```

### カスタムリクエストオブジェクト

[application customization](./app.md#custom-requests)で説明したように、リクエストオブジェクトに追加機能を追加するために、 :class:`sanic.request.Request` のサブクラスを作成できます。 これは、アプリケーションに固有の追加の属性やメソッドを追加する場合に便利です。

.. 列::

```
たとえば、アプリケーションがユーザー ID を含むカスタム ヘッダーを送信するとします。 そのヘッダーを解析し、ユーザーIDを保存するカスタムリクエストオブジェクトを作成できます。
```

.. 列::

````
```python
from sanic import Sanic, Request

class CustomRequest(Request):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = self.headers.get("X-User-ID")

app = Sanic("Example", request_class=CustomRequest)
```
````

.. 列::

```
ハンドラで `user_id` 属性にアクセスできるようになりました。
```

.. 列::

````
```python
@app.route("/")
async def handler(request: CustomRequest):
    return text(f"User ID: {request.user_id}")
```
````

### カスタムリクエストのコンテキスト

デフォルトでは、リクエスト コンテキスト (`request.ctx`) は [`Simplenamespace`](https://docs.python.org/3/library/types.html#types.SimpleNamespace) オブジェクトで、任意の属性を設定できます。 これはアプリケーション全体でロジックを再利用するのに非常に役立ちます。 IDEで利用可能な属性がわからないため、開発経験では困難な場合があります。

これを支援するために、デフォルトの `SimpleNamespace` の代わりに使用されるカスタムリクエストコンテキストオブジェクトを作成できます。 これにより、型ヒントをコンテキストオブジェクトに追加し、それらをIDEで使用できるようにできます。

.. 列::

```
:class:`sanic.request.Request`クラスをサブクラス化し、カスタムリクエストタイプを作成します。 次に、カスタムコンテキストオブジェクトのインスタンスを返す、 `make_context()` メソッドを追加する必要があります。 *注意: `make_context` メソッドは静的メソッドである必要があります。*
```

.. 列::

````
```python
from sanic import Sanic, Request
from types import SimpleNamespace

class CustomRequest(Request):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctx.user_id = self.headers.get("X-User-ID")

    @staticmethod
    def make_context() -> CustomContext:
        return CustomContext()

@dataclass
class CustomContext:
    user_id: str = None
```
````

.. note::

```
これはSanic poweruser 機能で、大きなコードベースでリクエストコンテキストオブジェクトを入力するのに非常に便利です。 それはもちろん必要ではありませんが、非常に役に立ちます。
```

_V23.6_に追加されました

## パラメータ

.. 列::

```
パスパラメータから抽出された値は、引数としてハンドラに注入され、より具体的にはキーワード引数として注入されます。 format@@0(./routing.md) には詳細が記載されています。
```

.. 列::

````
```python
@app.route('/tag/<tag>')
async def tag_handler(request, tag):
    return text("Tag - {}".format(tag))

# or, explicitly as keyword arguments
@app.route('/tag/<tag>')
async def tag_handler(request, *, tag):
    return text("Tag - {}".format(tag))
```
````

## 引数

`request`インスタンスには、クエリパラメータを取得するための2つの属性があります。

- `request.args`
- `request.query_args`

これにより、リクエストパス（URL内の `?` の後の部分）からクエリパラメータにアクセスできます。

### 典型的な使用例

ほとんどの場合、`request.args` オブジェクトを使用してクエリパラメータにアクセスします。 これは解析されたクエリ文字列を辞書として使用します。

これははるかに一般的なパターンです。

.. 列::

```
何かを検索するために使用する `q` パラメータを持つ `/search` エンドポイントがある例を考えてみましょう。
```

.. 列::

````
```python
@app.get("/search")
async def search(request):
   query = request.args.get("q")
    if not query:
        return text("No query string provided")
    return text(f"Searching for: {query}")
```
````

### クエリ文字列の解析

場合によっては、クエリ文字列に生の文字列またはタプルのリストとしてアクセスしたい場合があります。 これには、 `request.query_string` と `request.query_args` 属性を使用できます。

また、HTTP は 1 つのキーに対して複数の値を許可することに注意する必要があります。 `request.args` は通常の辞書のように見えるかもしれませんが、実際には1つのキーに対して複数の値を与える特別な型です。 `request.args.getlist()`メソッドを使用することでアクセスできます。

- `request.query_string` - 生クエリ文字列
- `request.query_args` - タプルのリストとして解析されたクエリー文字列。
- `request.args` - _special_辞書として解析されたクエリ文字列。
  - `request.args.get()` - キーの最初の値を取得します (通常の辞書のように動作します)
  - `request.args.getlist()` - キーの値をすべて取得します

```sh
curl "http://localhost:8000?key1=val1&key2=val2&key1=val3"
```

```python
>>> print(request.args)
{'key1': ['val1', 'val3'], 'key2': ['val2']}

>>> print(request.args.get("key1"))
val1

>>> print(request.args.getlist("key1"))
['val1', 'val3']

>>> print(request.query_args)
[('key1', 'val1'), ('key2', 'val2'), ('key1', 'val3')]

>>> print(request.query_string)
key1=val1&key2=val2&key1=val3

```

.. tip:: FYI

```
`request.args` オブジェクトは、それぞれの値がリストになる辞書である数少ない型の1つです。 これは、HTTP が 1 つのキーを再利用して複数の値を送信することを可能にするためです。  

ほとんどの場合、リストではなく最初の要素にアクセスするために `.get()` メソッドを使用します。 全てのアイテムのリストが必要な場合は、 `.getlist()` を使用します。
```

## 現在のリクエスト取得

場合によっては、アプリケーション内の現在のリクエストにアクセスできない場所でアクセスする必要があることがあります。 典型的な例は、`logging`形式です。 `Request.get_current()`を使用して、現在のリクエストをフェッチすることができます (もしあれば)。

リクエストオブジェクトは、ハンドラを実行している単一の[`asyncio.Task`](https://docs.python.org/3/library/asyncio-task.html#asyncio.Task)に制限されていることを覚えておいてください。 そのタスクに参加していない場合、リクエストオブジェクトはありません。

```python
import logging

from sanic import Request, Sanic, json
from sanic.exceptions import SanicException
from sanic.log import LOGGING_CONFIG_DEFAULTS

LOGGING_FORMAT = (
    "%(asctime)s - (%(name)s)[%(levelname)s][%(host)s]: "
    "%(request_id)s %(request)s %(message)s %(status)d %(byte)d"
)

old_factory = logging.getLogRecordFactory()

def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.request_id = ""

    try:
        request = Request.get_current()
    except SanicException:
        ...
    else:
        record.request_id = str(request.id)

    return record

logging.setLogRecordFactory(record_factory)


LOGGING_CONFIG_DEFAULTS["formatters"]["access"]["format"] = LOGGING_FORMAT
app = Sanic("Example", log_config=LOGGING_CONFIG_DEFAULTS)
```

この例では、すべてのアクセスログメッセージに `request.id` を追加しています。

_v22.6_に追加されました
