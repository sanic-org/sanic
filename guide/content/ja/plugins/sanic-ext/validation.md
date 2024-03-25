---
title: サニックエクステンション - 検証
---

# 検証

Webアプリケーションの最も一般的に実装されている機能の1つは、ユーザー入力検証です。 明らかな理由から、これはセキュリティの問題だけでなく、単に明白な良い実践です。 データが期待値に合致していることを確認し、そうでない場合は `400` レスポンスを投げます。

## 実装

### Dataclassの検証

format@@0(https\://docs.python.org/3/library/dataclasses.html)の導入により、Pythonは定義されたスキーマを満たすオブジェクトを簡単に作成できました。 しかし、標準ライブラリは型チェック検証のみをサポートしており、実行時の検証ではありません。 Sanic Extensionsは、 `dataclasses`を使って受信するリクエストに対して実行時の検証を行う機能を追加します。 `pydantic`または`attrs`のいずれかがインストールされている場合は、それらのライブラリのいずれかを使用することもできます。

.. 列::

```
まず、モデルを定義します。
```

.. 列::

````
```python
@dataclass
class SearchParams:
    q: str
```
````

.. 列::

```
次に、ルートに添付してください
```

.. 列::

````
```python
from sanic_ext import validate

@app.route("/search")
@validate(query=SearchParams)
async def handler(request, query: SearchParams:
    return json(asdict(query))
```
````

.. 列::

```
これで、受信リクエストのバリデーションが完了するはずです。
```

.. 列::

````
```
$ curl localhost:8000/search                                       
⚠️ 400 — Bad Request
====================
Invalid request body: SearchParams. Error: missing a required argument: 'q'
```
```
$ curl localhost:8000/search\?q=python                             
{"q":"python"}
```
````

### Pydanticによる検証

Pydanticモデルも使用できます。

.. 列::

```
まず、モデルを定義します。
```

.. 列::

````
```python
class Person(BaseModel):
    name: str
    age: int
```
````

.. 列::

```
次に、ルートに添付してください
```

.. 列::

````
```python
from sanic_ext import validate

@app.post("/person")
@validate(json=Person)
async def handler(request, body: Person):
    return json(body.dict())
```
````

.. 列::

```
これで、受信リクエストのバリデーションが完了するはずです。
```

.. 列::

````
```
$ curl localhost:8000/person -d '{"name": "Alice", "age": 21}' -X POST  
{"name":"Alice","age":21}
```
````

### Attrsによる検証

Attrsも使用できます。

.. 列::

```
まず、モデルを定義します。
```

.. 列::

````
```python
@attrs.define
class Person:
    name: str
    age: int

```
````

.. 列::

```
次に、ルートに添付してください
```

.. 列::

````
```python
from sanic_ext import validate

@app.post("/person")
@validate(json=Person)
async def handler(request, body: Person):
    return json(attrs.asdict(body))
```
````

.. 列::

```
これで、受信リクエストのバリデーションが完了するはずです。
```

.. 列::

````
```
$ curl localhost:8000/person -d '{"name": "Alice", "age": 21}' -X POST  
{"name":"Alice","age":21}
```
````

## 何を検証できますか？

`validate` デコレータは、3つの場所から受信したユーザーデータを検証するために使用できます: JSON body data (`request. son`), form body data (`request.form`), and query parameters (`request.args`).

.. 列::

```
予想通り、デコレータのキーワード引数を使用してモデルをアタッチすることができます。
```

.. 列::

````
```python
@validate(
    json=ModelA,
    query=ModelB,
    form=ModelC,
)
```
````
