---
title: Sanic Extensions - OAS Decorators
---

# デコレーター

スキーマにコンテンツを追加する主なメカニズムは、エンドポイントを飾ることです。 過去に
が`sanic-openapi`を使ったことがあるなら、これはよく知っているはずです。 The decorators and their arguments match closely
the [OAS v3.0 specification](https://swagger.io/specification/).

.. 列::

```
All of the examples show will wrap around a route definition. When you are creating these, you should make sure that
your Sanic route decorator (`@app.route`, `@app.get`, etc) is the outermost decorator. That is to say that you should
put that first and then one or more of the below decorators after.
```

.. 列::

````
```python
from sanic_ext import openapi

@app.get("/path/to/<something>")
@openapi.summary("This is a summary")
@openapi.description("This is a description")
async def handler(request, something: str):
    ...
```
````

.. 列::

```
You will also see a lot of the below examples reference a model object. For the sake of simplicity, the examples will
use `UserProfile` that will look like this. The point is that it can be any well-typed class. You could easily imagine
this being a `dataclass` or some other kind of model object.
```

.. 列::

````
```python
class UserProfile:
    name: str
    age: int
    email: str
```
````

## 定義デコレーター

### `@openapi.definition`

`@openapi.definition` デコレータを使用すると、一度にパス上の操作のすべての部分を定義できます。 それは装飾者の残りの部分と同じ操作定義を作成する能力を持っているという点でオムニバス
デコレータです。
複数のフィールド固有のデコレータまたは単一のデコレータを使用することは、開発者にとってスタイルの選択です。

フィールドは意図的に複数の型を受け入れることで、操作を定義するのが最も簡単になります。

**引数**

| フィールド         | タイプ                                                                                                                                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `body`        | **dict, RequestBody, _YourModel_**                                                                                                                                                                               |
| `deprecated`  | **bool**                                                                                                                                                                                                         |
| `description` | **str**                                                                                                                                                                                                          |
| `document`    | **str, ExternalDocumentation**                                                                                                                                                                                   |
| `exclude`     | **bool**                                                                                                                                                                                                         |
| `operation`   | **str**                                                                                                                                                                                                          |
| `パラメータ`       | **str, dict, Parameter, [str], [dict], [Parameter]** |
| `response`    | **dict, Response, _YourModel_, [dict], [Response]**                                                      |
| `summary`     | **str**                                                                                                                                                                                                          |
| `tag`         | **str, Tag, [str], [Tag]**                                                                               |
| `secured`     | **Dict[str, Any]**                                                                                                                                           |

**例**

.. 列::

````
```python
@openapi.definition(
    body=RequestBody(UserProfile, required=True),
    summary="User profile update",
    tag="one",
    response=[Success, Response, status=400)],
)
```
````

.. 列::

_より多くの例については以下を参照してください。 以下のデコレータのいずれかの値は、対応する
キーワード引数で使用できます。_

## フィールド固有の装飾

以下のデコレータは `@openapi` に基づいています。

### body

**引数**

| フィールド       | タイプ                                |
| ----------- | ---------------------------------- |
| **content** | **_YourModel_, dict, RequestBody** |

**例**

.. 列::

````
```python
@openapi.body(UserProfile)
```

```python
@openapi.body({"application/json": UserProfile})
```

```python
@openapi.body(RequestBody({"application/json": UserProfile}))
```
````

.. 列::

````
```python
@openapi.body({"content": UserProfile})
```

```python
@openapi.body(RequestBody(UserProfile))
```

```python
@openapi.body({"application/json": {"description": ...}})
```
````

### 非推奨です

**引数**

_なし_

**例**

.. 列::

````
```python
@openapi.deprecated()
```
````

.. 列::

````
```python
@openapi.deprecated
```
````

### 説明

**引数**

| フィールド  | タイプ     |
| ------ | ------- |
| `text` | **str** |

**例**

.. 列::

````
```python
@openapi.description(
    """This is a **description**.

## You can use `markdown`

- And
- make
- lists.
"""
)
```
````

.. 列::

### ドキュメント

**引数**

| フィールド         | タイプ     |
| ------------- | ------- |
| `url`         | **str** |
| `description` | **str** |

**例**

.. 列::

````
```python
@openapi.document("http://example.com/docs")
```
````

.. 列::

````
```python
@openapi.document(ExternalDocumentation("http://example.com/more"))
```
````

### 除外する

他のデコレータと同様にルート定義に使用したり、ブループリントで呼び出したりできます。

**引数**

| フィールド  | タイプ      | デフォルト    |
| ------ | -------- | -------- |
| `flag` | **bool** | **True** |
| `bp`   | **設計図**  |          |

**例**

.. 列::

````
```python
@openapi.exclude()
```
````

.. 列::

````
```python
openapi.exclude(bp=some_blueprint)
```
````

### 操作

操作 ID を設定します。

**引数**

| フィールド  | タイプ     |
| ------ | ------- |
| `name` | **str** |

**例**

.. 列::

````
```python
@openapi.operation("doNothing")
```
````

.. 列::

**引数**

| フィールド      | タイプ                                       | デフォルト       |
| ---------- | ----------------------------------------- | ----------- |
| `name`     | **str**                                   |             |
| `schema`   | _**type**_                                | **str**     |
| `location` | **"query", "header", "path" or "cookie"** | **"query"** |

**例**

.. 列::

````
```python
@openapi.parameter("thing")
```

```python
@openapi.parameter(parameter=Parameter("foobar", deprecated=True))
```
````

.. 列::

````
```python
@openapi.parameter("Authorization", str, "header")
```

```python
@openapi.parameter("thing", required=True, allowEmptyValue=False)
```
````

### 応答

**引数**

`Response` オブジェクトを使用する場合は、他の引数を渡すべきではありません。

| フィールド         | タイプ                           |
| ------------- | ----------------------------- |
| `status`      | **int**                       |
| `content`     | **_type_, _YourModel_, dict** |
| `description` | **str**                       |
| `response`    | **応答**                        |

**例**

.. 列::

````
```python
@openapi.response(200, str, "This is endpoint returns a string")
```

```python
@openapi.response(200, {"text/plain": str}, "...")
```

```python
@openapi.response(response=Response(UserProfile, description="..."))
```

```python
@openapi.response(
    response=Response(
        {
            "application/json": UserProfile,
        },
        description="...",
        status=201,
    )
)
```
````

.. 列::

````
```python
@openapi.response(200, UserProfile, "...")
```

```python
@openapi.response(
    200,
    {
        "application/json": UserProfile,
    },
    "Description...",
)
```
````

### summary

**引数**

| フィールド  | タイプ     |
| ------ | ------- |
| `text` | **str** |

**例**

.. 列::

````
```python
@openapi.summary("This is an endpoint")
```
````

.. 列::

### タグ

**引数**

| フィールド   | タイプ          |
| ------- | ------------ |
| `*args` | **str, Tag** |

**例**

.. 列::

````
```python
@openapi.tag("foo")
```
````

.. 列::

````
```python
@openapi.tag("foo", Tag("bar"))
```
````

### 保護されている

**引数**

| フィールド             | タイプ                                                                         |
| ----------------- | --------------------------------------------------------------------------- |
| `*args, **kwargs` | **str, Dict[str, Any]** |

**例**

.. 列::

````
```python
@openapi.secured()
```
````

.. 列::

.. 列::

````
```python
@openapi.secured("foo")
```
````

.. 列::

````
```python
@openapi.secured("token1", "token2")
```
````

.. 列::

````
```python
@openapi.secured({"my_api_key": []})
```
````

.. 列::

````
```python
@openapi.secured(my_api_key=[])
```
````

`add_security_scheme` を使用することを忘れないでください。 詳細は [security](./security.md) を参照してください。
\`\`

## Pydanticとの統合

Pydanticモデルはformat@@0(https\://pydantic-docs.helpmanual.io/usage/schema/)を生成する機能を持っています。

.. 列::

```
Pydanticモデルスキーマ生成を利用するには、スキーマの代わりに出力を渡してください。
```

.. 列::

````
```python
from sanic import Sanic, json
from sanic_ext import validate, openapi
from pydantic import BaseModel, Field

@openapi.component
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

class ItemList(BaseModel):
    items: List[Item]

app = Sanic("test")

@app.get("/")
@openapi.definition(
    body={
        "application/json": ItemList.schema(
            ref_template="#/components/schemas/{model}"
        )
    },
)
async def get(request):
    return json({})
```
````

.. note::

```
`ref_template`を設定することが重要です。デフォルトではPydanticは標準のOASではないテンプレートを選択します。 これにより、最終的なドキュメントを生成する際にスキーマが見つかりません。
```

_v22.9_に追加されました
