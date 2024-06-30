# ストリーミング

## ストリーミングのリクエスト

Sanicでは、クライアントから送信されたデータをストリーミングして、バイトが到着するとデータの処理を開始することができます。

.. column::

```
エンドポイントで有効にすると、`await request.stream.read()`を使ってリクエストボディをストリーミングできます。

このメソッドは、ボディが完了すると`None`を返します。
```

.. 列::

````
```python
from sanic.views import stream

class SimpleView(HTTPMethodView):
    @stream
    async def post(self, request):
        result = ""
        while True:
            body = await request.stream.read()
            if body is None:
                break
            result += body.decode("utf-8")
        return text(result)
```
````

.. column::

```
また、デコレータのキーワード引数で有効にすることも...
```

.. column::

````
```python
@app.post("/stream", stream=True)
async def handler(request):
        ...
        body = await request.stream.read()
        ...
```
````

.. column::

```
...`add_route()`メソッドを使うこともできます。
```

.. column::

````
```python
bp.add_route(
    bp_handler,
    "/bp_stream",
    methods=["POST"],
    stream=True,
)
```
````

.. tip:: 参考

```
post、put、patchデコレータのみが stream 引数を持っています。
```

## Response ストリーミング

.. column::

```
Sanicでは、クライアントにコンテンツをストリーミングできます。
```

.. column::

````
```python
@app.route("/")
async def test(request):
    response = await request.respond(content_type="text/csv")
    await response.send("foo,")
    await response.send("bar")

    # 以下の関数を呼び出して、ストリームを明示的に終了することもできます:
    await response.eof()
```
````

これは、データベースのような外部サービスで発生するクライアントにコンテンツをストリーミングしたい場合に便利です。 たとえば、`asyncpg` が提供する非同期カーソルを使用して、データベースレコードをクライアントにストリーミングできます。

```python
@app.route("/")
async def index(request):
    response = await request.respond()
    conn = await asyncpg.connect(database='test')
    async with conn.transaction():
        async for record in conn.cursor('SELECT generate_series(0, 10)'):
            await response.send(record[0])
```

`await response.eof()` を呼び出すことで、ストリームを明示的に終了させることができます。 これは `await response.send("", True)` を置き換える便利なメソッドです。 ハンドラがクライアントに送り返すものが何も残っていないと判断した _後に_ **1度だけ** 呼び出されるべきです。 Sanic サーバーで使用するのは_任意_ですが、SanicをASGIモードで動作させている場合は、**必ず**明示的にストリームを終了させなければなりません。

_v21.6で`eof`の呼び出しが任意になりました_

## ファイルストリーミング

.. column::

```
Sanicは、大きなファイルを送信する場合に便利な `sanic.response.file_stream` 関数を提供します。`StreamingHTTPResponse`オブジェクトを返し、デフォルトではチャンク転送エンコーディングを使用します。このため、Sanicはレスポンスに`Content-Length` HTTPヘッダーを追加しません。

典型的な使用例は、ビデオファイルをストリーミングしている場合です。
```

.. column::

````
```python
@app.route("/mp4")
async def handler_file_stream(request):
    return await response.file_stream(
        "/path/to/sample.mp4",
        chunk_size=1024,
        mime_type="application/metalink4+xml",
        headers={
            "Content-Disposition": 'Attachment; filename="nicer_name.meta4"',
            "Content-Type": "application/metalink4+xml",
        },
    )
```
````

.. column::

```
`Content-Length`ヘッダーを使用したい場合は、チャンク転送エンコーディングを無効にし、`Content-Length`ヘッダーを手動で追加するだけです。
```

.. column::

````
```python
from aiofiles import os as async_os
from sanic.response import file_stream

@app.route("/")
async def index(request):
    file_path = "/srv/www/whatever.png"

    file_stat = await async_os.stat(file_path)
    headers = {"Content-Length": str(file_stat.st_size)}

    return await file_stream(
        file_path,
        headers=headers,
    )
```
````
