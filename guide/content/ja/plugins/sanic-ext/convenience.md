---
title: サニックエクステンション - Convenience
---

# 便利さ

## 固定シリアライザー

.. 列::

```
多くの場合、アプリケーションを開発する場合、常に同じ種類のレスポンスを返す特定のルートがあります。 この場合、返品シリアライザとエンドポイントを事前に定義できます。 返されるべきものは内容だけです
```

.. 列::

````
```python
from sanic_ext import serializer

@app.get("/<name>")
@serializer(text)
async def hello_world(request, name: str):
    if name.isnumeric():
        return "hello " * int(name)
    return f"Hello, {name}"
```
````

.. 列::

```
`serializer`デコレータはステータスコードを追加することもできます。
```

.. 列::

````
```python
from sanic_ext import serializer

@app.post("/")
@serializer(text, status=202)
async def create_something(request):
    ...
```
````

## カスタムシリアライザー

.. 列::

```
`@serializer`デコレータを使用して、有効な型(`HTTPResonse`)を返す限り、独自のカスタム関数を渡すこともできます。
```

.. 列::

````
```python
def message(retval, request, action, status):
    return json(
        {
            "request_id": str(request.id),
            "action": action,
            "message": retval,
        },
        status=status,
    )

@app.post("/<action>")
@serializer(message)
async def do_action(request, action: str):
    return "This is a message"
```
````

.. 列::

```
今度は、文字列だけを返すと、素敵なシリアル化された出力が返されます。
```

.. 列::

````
```python
$ curl localhost:8000/eat_cookies -X POST
{
  "request_id": "ef81c45b-235c-46d-9dbd-b550f8fa77f9",
  "action": "eat_cookies",
  "message": "This is a message"
}

```
````

## カウンターを要求する

.. 列::

```
Sanic Extensionsには`Request`のサブクラスが付属しており、ワーカープロセスごとに処理されたリクエストの数を自動的に追跡できるように設定できます。 これを有効にするには、アプリケーションコントラクターに `CounttedRequest` クラスを渡す必要があります。
```

.. 列::

````
```python
from sanic_ext import CountedRequest

app = Sanic(..., request_class=CounttedRequest)
```
````

.. 列::

```
ワーカープロセスの生涯中に提供されるリクエスト数にアクセスできるようになります。
```

.. 列::

````
```python
@app.get("/")
async def handler(request: CountedRequest):
    return json({"count": request.count})
```
````

可能であれば、リクエスト数は [worker state](../../guide/deployment/manager.md#worker-state) にも追加されます。

![](https://user-images.githubusercontent.com/166269/190922460-43bd2cfc-f81a-443b-b84f-07b6ce475cbf.png)
