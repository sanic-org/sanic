# Versioning

エンドポイントにバージョンを追加するためのAPI構築の標準的な方法です。 これにより、互換性のないエンドポイントを簡単に区別することができます。

バージョンを追加すると、`/v{version}`のURLプレフィックスがエンドポイントに追加されます。

バージョンは `int` 、`float` 、または `str` です。 許容可能な値:

- `1`, `2`, `3`
- `1.1`, `2.25`, `3.0`
- `"1"`、`"v1"`、`"v1.1"`

## ルートごと

.. 列::

```
バージョン番号をルートに直接渡すことができます。
```

.. 列::

````
```python
# /v1/text
@app.route("/text", version=1)
def handle_request(request):
    return response. ext("Hello world! Version 1")

# /v2/text
@app.route("/text", version=2)
def handle_request(request):
    return response.text("Hello world! Version 2")
```
````

## 設計図ごと

.. 列::

```
また、バージョン番号を blueprint に渡すこともできます。blueprint 内のすべてのルートに適用されます。
```

.. 列::

````
```python
bp = Blueprint("test", url_prefix="/foo", version=1)

# /v1/foo/html
@bp.route("/html")
def handle_request(request):
    return response.html(" "<p>Hello world!</p>")
```
````

## ブループリントグループごと

.. 列::

```
In order to simplify the management of the versioned blueprints, you can provide a version number in the blueprint
group. The same will be inherited to all the blueprint grouped under it if the blueprints don't already override the
same information with a value specified while creating a blueprint instance.

When using blueprint groups for managing the versions, the following order is followed to apply the Version prefix to
the routes being registered.

1. Route Level configuration
2. Blueprint level configuration
3. Blueprint Group level configuration

If we find a more pointed versioning specification, we will pick that over the more generic versioning specification
provided under the Blueprint or Blueprint Group
```

.. 列::

````
```python
from sanic.blueprints import Blueprint
from sanic.response import json

bp1 = Blueprint(
    name="blueprint-1",
    url_prefix="/bp1",
    version=1.25,
)
bp2 = Blueprint(
    name="blueprint-2",
    url_prefix="/bp2",
)

group = Blueprint.group(
    [bp1, bp2],
    url_prefix="/bp-group",
    version="v2",
)

# GET /v1.25/bp-group/bp1/endpoint-1
@bp1.get("/endpoint-1")
async def handle_endpoint_1_bp1(request):
    return json({"Source": "blueprint-1/endpoint-1"})

# GET /v2/bp-group/bp2/endpoint-2
@bp2.get("/endpoint-1")
async def handle_endpoint_1_bp2(request):
    return json({"Source": "blueprint-2/endpoint-1"})

# GET /v1/bp-group/bp2/endpoint-2
@bp2.get("/endpoint-2", version=1)
async def handle_endpoint_2_bp2(request):
    return json({"Source": "blueprint-2/endpoint-2"})
```
````

## バージョン接頭辞：

上記のように、ルートに適用される`version`は、生成されたURIパスの最初のセグメントである**常に**です。 したがって、バージョンの前にパスセグメントを追加するために、 `version` 引数が渡されるすべての場所を渡すことができます。`version_prefix` も渡すことができます。

引数 `version_prefix` は以下のように定義できます：

- `app.route` と `bp.route` デコレーター （そしてすべてのコンビニエンスデコレーターも）
- `Blueprint` インスタンス
- `Blueprint.group` コンストラクター
- `BlueprintGroup` インスタンス
- `app.blueprint` 登録

複数の場所に定義がある場合、より具体的な定義はより一般的に優先されます。 このリストはその階層を提供します。

`version_prefix` のデフォルト値は `/v` です。

.. 列::

```
`/api` にバージョン管理されたルートをマウントできる機能がよくあります。これは `version_prefix` で簡単に実現できます。
```

.. 列::

````
```python
# /v1/my/path
app.route("/my/path", version=1, version_prefix="/api/v")
```
````

.. 列::

```
おそらく、`/api` ルートを単一の `BlueprintGroup` にロードすることでしょう。
```

.. 列::

````
```python
# /v1/my/path
app = Sanic(__name__)
v2ip = Blueprint("v2ip", url_prefix="/ip", version=2)
api = Blueprint.group(v2ip, version_prefix="/api/version")

# /api/version2/ip
@v2ip.get("/")
async def handler(request):
    return text(request.ip)

app.blueprint(api)
```
````

そのため、ルートのURIは以下のようになります。

```
version_prefix + version + url_prefix + URI 定義
```

.. tip::

````
`url_prefix` と同じように、 `version_prefix` 内でパスパラメータを定義することができます。 すべてのルートがハンドラにそのパラメータを注入することを覚えておいてください。

```python
version_prefix="/<foo:str>/v"
```
````

_V21.6_に追加されました
