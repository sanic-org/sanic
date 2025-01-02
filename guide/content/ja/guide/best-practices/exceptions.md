# 例外

## サニック例外の使用

場合によっては、ハンドラの実行を停止し、ステータスコード応答を返すようSanicに指示する必要があります。 これに対して「SanicException」を発生させることができ、Sanicはあなたのために残りを行います。

オプションの `status_code` 引数を渡すことができます。 デフォルトでは、SanicExceptionは内部サーバーエラー500レスポンスを返します。

```python
from sanic.exception import SanicException

@app.route("/youshallnotpass")
async def no_no(request):
        raise SanicException("Something went wrong .", status_code=501)
```

Sanicは多くの標準的な例外を提供します。 それぞれが自動的にレスポンス内に適切なHTTPステータスコードを発生させます。 詳細については、format@@0(https://sanic.readthedocs.io/en/latest/sanic/api_reference.html#module-sanic.exceptions) を参照してください。

.. 列::

```
より一般的な例外は、あなた自身を実装すべきである。

- `BadRequest` (400)
- `Unauthorized` (401)
- `Forbidden` (403)
- `NotFound` (404)
- `ServerError` (500)
```

.. 列::

````
```python
from sanic import exceptions

@app.route("/login")
async def login(request):
    user = await some_login_func(request)
    if not user:
        raise exceptions.NotFound(
            f"Could not find user with username={request.json.username}"
        )
```
````

## 例外のプロパティ

Sanic のすべての例外は `SanicException` に由来します。 そのクラスには、開発者がアプリケーション全体で例外を一貫して報告するのに役立ついくつかのプロパティがあります。

- `message`
- `status_code`
- `quiet`
- `headers`
- `context`
- `extra`

これらのプロパティはすべて、作成時に例外に渡すことができます。 最初の3つはクラス変数としても使えます

.. 列::

```
### `message`

`message` プロパティは、Pythonの他の例外と同じように表示されるメッセージを明らかに制御します。 特に便利なのは、`message` プロパティをクラス定義に設定することで、アプリケーション全体で言語を簡単に標準化できます。
```

.. 列::

````
```python
class CustomError(SanicException):
    message = "Something bad happened"

raise CustomError
# or
raise CustomError("Override the default message with something else")
```
````

.. 列::

```
### `status_code`

このプロパティは、例外が発生したときに応答コードを設定するために使用されます。 これは、通常、クライアントからの不正な情報に応答しているカスタム400シリーズの例外を作成する場合に特に便利です。
```

.. 列::

````
```python
class TeapotError(SanicException):
    status_code = 418
    message = "Sorry, I cannot brew coffee"

raise TeapotError
# or
raise TeapotError(status_code=400)
```
````

.. 列::

```
### `quiet`

デフォルトでは、Sanic が `error_logger` に例外を出力します。 場合によっては、これは望ましくない場合があります。特に例外を使用して例外ハンドラでイベントをトリガーする場合は (format@@0を参照してください)。 exceptions.md#handling)) `quiet=True` を使ってログ出力を抑制することができます。
```

.. 列::

````
```python
class SilentError(SanicException):
    message = "Something happened, but not shown in logs"
    quiet = True

raise SilentError
# or
raise InvalidUsage("blah blah", quiet=True)
```
````

.. 列::

```
デバッグ中に`quiet=True`プロパティをグローバルに無視したい場合があります。 `NOISY_EXCEPTIONS`

*バージョン21.12*に追加された、このプロパティに関係なく、Sanicにすべての例外を強制的にログアウトさせることができます
```

.. 列::

````
```python
app.config.NOISY_EXCEPTIONS = True
```
````

.. 列::

```
### `headers`

`SanicException` を使ってレスポンスを作成するのはとても強力です。 これは、 `status_code` を制御するだけでなく、 reponse ヘッダを例外から直接制御することもできるからです。
```

.. 列::

````
```python
class MyException(SanicException):
    headers = {
      "X-Foo": "bar"
    }

raise MyException
# or
raise InvalidUsage("blah blah", headers={
    "X-Foo": "bar"
})
```
````

.. 列::

```
### `extra`

See [contextual exceptions](./exceptions.md#contextual-exceptions)

*Added in v21.12*
```

.. 列::

````
```python
raise SanicException(..., extra={"name": "Adam"})
```
````

.. 列::

```
### `context`

See [contextual exceptions](./exceptions.md#contextual-exceptions)

*Added in v21.12*
```

.. 列::

````
```python
raise SanicException(..., context={"foo": "bar"})
```
````

## 取扱い方法

Sanicはエラーページをレンダリングすることで自動的に例外を処理するため、多くの場合、自分で処理する必要はありません。 ただし、例外が発生したときに何をすべきかをもっと制御したい場合は、ハンドラを自分で実装することができます。

Sanicはこのためのデコレータを提供します。これはSanic標準の例外だけでなく、アプリケーションが投げるかもしれない**any**例外にも適用されます。

.. 列::

```
ハンドラを追加する最も簡単な方法は、 `@app.exception()` を使用して1つ以上の例外を渡すことです。
```

.. 列::

````
```python
from sanic.exceptionimport NotFound

@app.exception(NotFound, SomeCustomException)
async def ignore_404s(request, exception):
    return text("Yep, I find the page: {}".format(request.url))
```
````

.. 列::

```
`Exception` をキャッチすることで、キャッチオールハンドラを作成することもできます。
```

.. 列::

````
```python
@app.exception(Exception)
async def catch_anything(request, exception):
    ...
```
````

.. 列::

```
`app.error_handler.add()`を使ってエラーハンドラを追加することもできます。
```

.. 列::

````
```python
async def server_error_handler(request, exception):
    return text("Oops, server error", status=500)

app.error_handler.add(Exception, server_error_handler)
```
````

## ビルトインエラー処理

Sanic は、HTML、JSON、およびテキストの3つのフォーマットを除外して出荷します。 以下の例は format@@0(#fallback-handler) セクションにあります。

.. 列::

```
`error_format` キーワード引数でどの形式を使用するかを _per route_ で制御できます。

*v21.9* で追加しました
```

.. 列::

````
```python
@app.request("/", error_format="text")
async def handler(request):
    ...
```
````

## カスタムエラーの処理

場合によっては、デフォルトで提供されるエラー処理機能を追加したい場合があります。 その場合、Sanic のデフォルトエラーハンドラを次のようにサブクラス化できます。

```python
from sanic.handlers import ErrorHandler

class CustomErrorHandler(ErrorHandler):
    def default(self, request: Request, exception: Exception) -> HTTPResponse:
        ''' handles errors that have no error handlers assigned '''
        # You custom error handling logic...
        status_code = getattr(exception, "status_code", 500)
        return json({
          "error": str(exception),
          "foo": "bar"
        }, status=status_code)

app.error_handler = CustomErrorHandler()
```

## Fallback handler

Sanic には 3 つのフォールバック例外ハンドラが付属しています:

1. HTML
2. テキスト
3. JSON

これらのハンドラは、アプリケーションが format@@0(/guide/deployment/development.md) かどうかによって詳細のレベルが異なります。

デフォルトでは、Sanicは「自動」モードになります。 つまり、受信リクエストと潜在的なマッチングハンドラを使用して、適切な応答形式を選択するということです。 例えば、ブラウザでは常にHTMLエラーページを提供する必要があります。 curl を使用すると、JSON またはプレーンテキストが表示されることがあります。

### HTML

```python
app.config.FALLBACK_ERROR_FORMAT = "html"
```

.. 列::

````
```python
app.config.DEBUG = True
```

![Error](/assets/images/error-display-html-debug.png)
````

.. 列::

````
```python
app.config.DEBUG = False
```

![Error](/assets/images/error-display-html-prod.png)
````

### テキスト

```python
app.config.FALLBACK_ERROR_FORMAT = "text"
```

.. 列::

````
```python
app.config.DEBUG = True
```

```sh
curl localhost:8000/exc -i
HTTP/1.1 500 Internal Server Error
content-length: 620
connection: keep-alive
content-type: text/plain; charset=utf-8

⚠️ 500 — Internal Server Error
==============================
That time when that thing broke that other thing? That happened.

ServerError: That time when that thing broke that other thing? That happened. while handling path /exc
Traceback of TestApp (most recent call last):

  ServerError: That time when that thing broke that other thing? That happened.
    File /path/to/sanic/app.py, line 979, in handle_request
    response = await response

    File /path/to/server.py, line 16, in handler
    do_something(cause_error=True)

    File /path/to/something.py, line 9, in do_something
    raise ServerError(
```
````

.. 列::

````
```python
app.config.DEBUG = False
```

```sh
curl localhost:8000/exc -i
HTTP/1.1 500 Internal Server Error
content-length: 134
connection: keep-alive
content-type: text/plain; charset=utf-8

⚠️ 500 — Internal Server Error
==============================
That time when that thing broke that other thing? That happened.
```
````

### JSON

```python
app.config.FALLBACK_ERROR_FORMAT = "json"
```

.. 列::

````
```python
app.config.DEBUG = True
```

```sh
curl localhost:8000/exc -i
HTTP/1.1 500 Internal Server Error
content-length: 572
connection: keep-alive
content-type: application/jso

{
  "description": "Internal Server Error",
  "status": 500,
  "message": "That time when that thing broke that other thing? That happened.",
  "path": "/exc",
  "args": {},
  "exceptions": [
    {
      "type": "ServerError",
      "exception": "That time when that thing broke that other thing? That happened.",
      "frames": [
        {
          "file": "/path/to/sanic/app.py",
          "line": 979,
          "name": "handle_request",
          "src": "response = await response"
        },
        {
          "file": "/path/to/server.py",
          "line": 16,
          "name": "handler",
          "src": "do_something(cause_error=True)"
        },
        {
          "file": "/path/to/something.py",
          "line": 9,
          "name": "do_something",
          "src": "raise ServerError("
        }
      ]
    }
  ]
}
```
````

.. 列::

````
```python
app.config.DEBUG = False
```

```sh
curl localhost:8000/exc -i
HTTP/1.1 500 Internal Server Error
content-length: 129
connection: keep-alive
content-type: application/json

{
  "description": "Internal Server Error",
  "status": 500,
  "message": "That time when that thing broke that other thing? That happened."
}

```
````

### 自動

Sanicはまた、どのフォールバックオプションを使用するかを推測するためのオプションも提供します。

```python
app.config.FALLBACK_ERROR_FORMAT = "auto"
```

## 文脈の例外

アプリケーション全体で例外を一貫して発生させる機能を簡素化するデフォルトの例外メッセージ。

```python
class TeapotError(SanicException):
    status_code = 418
    message = "Sorry, I cannot brew coffee"

raise TeapotError
```

しかし、これには二つのことが欠けています:

1. 動的で予測可能なメッセージ形式
2. エラーメッセージにコンテキストを追加する機能 (詳細は後で)

_v21.12_ に追加されました

Sanicの例外のいずれかを使用すると、実行時に追加の詳細を提供する2つのオプションがあります。

```python
raise TeapotError(extra={"foo": "bar"}, context={"foo": "bar"})
```

違いは何であり、いつそれぞれを使用することに決めるべきか。

- `extra` - オブジェクト自体はプロダクションクライアントに **決して**送られません\*\* 。 内部使用のみを目的としています。 それは何のために使用することができますか?
  - 1分後に表示されるように、動的なエラーメッセージを生成します
  - ロガーにランタイムの詳細を提供する
  - デバッグ情報（開発モードの場合はレンダリングされます）
- `context` - このオブジェクトは常にプロダクションクライアントに送信されます。 これは一般的に、何が起こったのかのコンテキストについての追加の詳細を送信するために使用されます。 それは何のために使用することができますか?
  - `BadRequest`検証問題に代替値を提供します
  - お客様がサポートチケットを開くために役立つ詳細を記載して回答する
  - 現在ログインしているユーザー情報のような状態情報を表示します

### `extra`を使った動的で予測可能なメッセージ

サニック例外は、`extra`キーワード引数を使って発生した例外インスタンスに追加情報を提供することができます。

```python
class TeapotError(SanicException):
    status_code = 418

    @property
    def message(self):
        return f"Sorry {self.extra['name']}, I cannot make you coffee"

raise TeapotError(extra={"name": "Adam"})
```

新機能では、例外インスタンスに `extra` メタを渡すことができます。 これは、上記の例のように、動的データをメッセージテキストに渡すのに特に役立ちます。 この`extra` infoオブジェクトは `PRODUCTION` モードでは抑制されますが、 `DEVELOPMENT` モードでは表示されます。

.. 列::

```
**開発版**

![image](~@assets/images/error-extra-debug.png)
```

.. 列::

```
**製品**

![image](~@assets/images/error-extra-prod.png)
```

### エラーメッセージに追加の `コンテキスト`

サニック例外は、何が起こったかについてユーザに意図した情報を渡すための引数`context`でも発生します。 これは、マイクロサービスやエラーメッセージを JSON 形式で渡すことを意図した API を作成する場合に特に便利です。 このユースケースでは、パース可能なエラーメッセージ以外にも、クライアントに詳細を返すコンテキストを持たせたいと考えています。

```python
raise TeapotError(context={"foo": "bar"})
```

この情報は **私たちが常にエラーで渡したい** です(利用可能な場合)。 次のようにすべきです:

.. 列::

````
**PRODUCTION**

```json
{
  "description": "I'm a teapot",
  "status": 418,
  "message": "Sorry Adam, I cannot make you coffee",
  "context": {
    "foo": "bar"
  }
}
```
````

.. 列::

````
**DEVELOPMENT**

```json
{
  "description": "I'm a teapot",
  "status": 418,
  "message": "Sorry Adam, I cannot make you coffee",
  "context": {
    "foo": "bar"
  },
  "path": "/",
  "args": {},
  "exceptions": [
    {
      "type": "TeapotError",
      "exception": "Sorry Adam, I cannot make you coffee",
      "frames": [
        {
          "file": "handle_request",
          "line": 83,
          "name": "handle_request",
          "src": ""
        },
        {
          "file": "/tmp/p.py",
          "line": 17,
          "name": "handler",
          "src": "raise TeapotError("
        }
      ]
    }
  ]
}
```
````

## エラー報告

Sanic には [signal](../advanced/signals.md#built-in-signals) があり、例外報告プロセスにフックすることができます。 これは、Sentry や Rollbar のようなサードパーティのサービスに例外情報を送信したい場合に便利です。 これは、以下のようにエラー報告ハンドラを付けることで便利に実現できます。

```python
@app.report_exception
async def catch_any_exception(app: Sanic, exception: Exception):
print("Caught exception:)
```

.. note::

```
このハンドラはバックグラウンドタスクにディスパッチされ、任意のレスポンスデータを操作するために使用される**IS NOT** です。 ログまたはレポートの目的でのみ使用することを意図しています。 クライアントにエラー・レスポンスを返す能力には影響を与えるべきではありません
```

_V23.6_に追加されました
