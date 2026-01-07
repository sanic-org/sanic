# 回答

すべての [handlers](./handlers.md) _通常_ レスポンスオブジェクトを返し、 [middleware](./middleware.md) は任意でレスポンスオブジェクトを返すことができます。

そのステートメントを明確にするには:

- ハンドラがクライアントにバイトを送信するための独自のパターンを処理するストリーミングエンドポイントでない限り、 戻り値は :class:`sanic のインスタンスでなければなりません。 esponse.HTTPResponse` (format@@0(../advanced/streaming.md#response-streaming)を参照してください)。 **ほとんどの** ユースケースでは、レスポンスを返す必要があります。
- ミドルウェアがレスポンスオブジェクトを返す場合は、ハンドラが何でも代わりに使用されます (詳細については、 [middleware](./middleware.md) を参照)。

基本的なハンドラーは以下のようになります。 :class:`sanic.response.HTTPResponse` オブジェクトは、クライアントに返されるステータス、本文、およびヘッダーを設定できます。

```python
from sanic import HTTPResponse, Sanic

app = Sanic("TestApp")

@app.route("")
def handler(_):
    return HTTPResponse()
```

ただし、通常、以下で説明する便利な方法のいずれかを使用する方が簡単です。

## メソッド

レスポンスオブジェクトを生成する最も簡単な方法は、コンビニエンス関数のいずれかを使用することです。

### テキスト

.. 列::

```
**デフォルト Content-Type**: `text/plain; charset=utf-8`  
**Description**: プレーン テキストを返す
```

.. 列::

````
```python
from sanic import text

@app.route("/")
async def handler(request):
    return text("Hi 😎)
```
````

### HTML

.. 列::

```
**Default Content-Type**: `text/html; charset=utf-8`  
**Description**: HTML ドキュメントを返す
```

.. 列::

````
```python
from sanic import html

@app.route("/")
async def handler(request):
    return html('<!DOCTYPE html><html lang="en"><meta charset="UTF-8"><div>Hi 😎</div>')
```
````

### JSON

.. 列::

```
**デフォルト Content-Type**: `application/json`  
**Description**: JSON ドキュメントを返す
```

.. 列::

````
```python
from sanic import json

@app.route("/")
async def handler(request):
    return json({"foo": "bar"})
```
````

デフォルトでは、Sanic は [`ujson`](https://github.com/ultrajson/ultrajson) を JSON エンコーダとして出荷します。 `ujson` がインストールされていない場合、標準ライブラリ `json` に戻ります。

あなたが望むならば、これを変更するのは超簡単です。

```python
from sanic import json
from orjson import dump

json({"foo": "bar"}, dumps=dumps)
```

また、アプリケーション全体で使用する実装を初期化時に宣言することもできます。

```python
from orjson import dump

app = Sanic(..., dumps=dumps)
```

### ファイル

.. 列::

```
**Default Content-Type**: N/A  
**Description**: ファイルを返す
```

.. 列::

````
```python
from sanic import file

@app.route("/")
async def handler(request):
    return await file("/path/to/whatever.png")
```
````

Sanicはファイルを調べ、MIMEタイプを推測し、コンテンツ型に適切な値を使用します。 必要に応じて、次のように説明できます。

```python
file("/path/to/whatever.png", mime_type="image/png")
```

ファイル名を上書きすることもできます:

```python
file("/path/to/whatever.png", filename="super-awesome-increverble.png")
```

### ファイルストリーミング

.. 列::

```
**Default Content-Type**: N/A  
**Description**: クライアントにファイルをストリーミングします。ビデオのような大きなファイルをストリーミングするときに便利です。
```

.. 列::

````
```python
from sanic.response import file_stream

@app.route("/")
async def handler(request):
    return await file_stream("/path/to/whatever.mp4")
```
````

`file()`メソッドと同様に、`file_stream()`はファイルのMIMEタイプを決定しようとします。

### Raw

.. 列::

```
**Default Content-Type**: `application/octet-stream`  
**Description**: body をエンコードせずに raw bytes を送る
```

.. 列::

````
```python
from sanic import raw

@app.route("/")
async def handler(request):
    return raw(b"raw bytes")
```
````

### リダイレクト

.. 列::

```
**デフォルトのContent-Type**: `text/html; charset=utf-8`  
**Description**: クライアントを別のパスにリダイレクトするために `302` レスポンスを送信する
```

.. 列::

````
```python
from sanic import redirect

@app.route("/")
async def handler(request):
    return redirect("/login")
```
````

### なし

.. 列::

```
**Default Content-Type**: N/A  
**Description**: [RFC 2616] (https://tools.ietf.org/search/rfc2616#section-7.2.1) で定義されている空のメッセージで応答するためのものです。
```

.. 列::

````
```python
from sanic import empty

@app.route("/")
async def handler(request):
    return empty()
```

デフォルトは `204` ステータスです。
````

## 既定のステータス

レスポンスのデフォルトの HTTP ステータスコードは `200` です。 変更が必要な場合は、responseメソッドで行うことができます。

```python
@app.post("/")
async def create_new(request):
    new_thing = await do_create(request)
    return json({"created": True, "id": new_thing.thing_id}, status=201)
```

## JSON データを返す

v22.12 から始まります。`sanic.json` コンビニエンスメソッドを使用すると、 :class:`sanic.response.types.JSONResponse` という `HTTPResponse` のサブクラスが返されます。 このオブジェクト
には、一般的なJSONボディを変更するための便利なメソッドがいくつかあります。

```python
from sanic import json

resp = json(...)
```

- `resp.set_body(<raw_body>)` - JSONオブジェクトの本体を渡された値に設定します。
- `resp.append(<value>)` - `list.append` のようにボディに値を追加します（ルートJSONが配列の場合のみ動作します）
- `resp.extend(<value>)` - `list.extend` のように値をボディに拡張します（ルートJSONが配列の場合のみ動作します）
- `resp.update(<value>)` - `dict.update` のような値で本文を更新します (ルートJSONがオブジェクトの場合のみ動作します)
- `resp.pop()` - `list.pop` や `dict.pop` のような値をポップします (ルートJSONが配列またはオブジェクトの場合にのみ動作します)

.. 警告::

```
生の Python オブジェクトは `JSONResponse` オブジェクトに `raw_body` として保存されます。 この値を新しい値で上書きしても安全ですが、変更しようとしないでください。 代わりに上記の方法を使用する必要があります。
```

```python
resp = json({"foo": "bar"})

# This is OKAY
resp.raw_body = {"foo": "bar", "something": "else"}

# This is better
resp.set_body({"foo": "bar", "something": "else"})

# This is also works well
resp.update({"something": "else"})

# This is NOT OKAY
resp.raw_body.update({"something": "else"})
```

```python
# Or, even treat it like a list
resp = json(["foo", "bar"])

# This is OKAY
resp.raw_body = ["foo", "bar", "something", "else"]

# This is better
resp.extend(["something", "else"])

# This is also works well
resp.append("something")
resp.append("else")

# This is NOT OKAY
resp.raw_body.append("something")
```

_v22.9_に追加されました
