# バージョン進行

API構築では、エンドポイントにバージョンを追加するのが標準的な方法です。 これにより、互換性のないエンドポイントを簡単に区別することができます。

バージョンを追加すると、`/v{version}`のURLプレフィックスがエンドポイントに追加されます。

バージョンは `int` 、`float` 、または `str` にすることができます。 許容値:

- `1`, `2`, `3`
- `1.1`, `2.25`, `3.0`
- `"1"`、`"v1"`、`"v1.1"`

## ルートごとのバージョン

.. column::

```
バージョン番号をルートに直接渡すことができます。
```

.. column::

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

## Blueprintごとのバージョン

.. column::

```
Blueprintにバージョン番号を渡すこともできます。 これは、そのBlueprint内のすべてのルートに適用されます。
```

.. column::

````
```python
bp = Blueprint("test", url_prefix="/foo", version=1)

# /v1/foo/html
@bp.route("/html")
def handle_request(request):
    return response.html(" "<p>Hello world!</p>")
```
````

## Blueprintグループごとのバージョン

.. column::

```
バージョン化されたBlueprintの管理を簡素化するために、グループにバージョン番号を提供できます。Blueprintインスタンスを作成する際に指定された値で同じ情報を上書きしない場合、 その下方でグループ化されたすべてのBlueprintにも同じ情報が継承されます。

バージョン管理にblueprintグループを使用する場合、ルートの登録中に以下の順序でバージョンプレフィックスが適用されます。

1. ルートレベルの設定
2. Blueprintレベルの設定
3. Blueprintグループレベルの設定

もし、より小さな単位でのバージョン管理仕様が見つかれば、BlueprintやBlueprintグループの下で提供される一般的なバージョン管理仕様よりも、そちらを選ぶことになります。
```

.. column::

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

## バージョンプレフィックス

上で見たように、ルートに適用される`version`は、**常に**生成されたURIパスの最初のセグメントになります。 したがって、バージョンの前にパスセグメントを追加できるように、`version`引数が渡されるすべての場所で、`version_prefix`を渡すこともできます。

引数 `version_prefix` は以下の場所で定義できます：

- `app.route` と `bp.route` デコレーター (そして、すべての便利なデコレータ)
- `Blueprint`のインスタンス化
- `Blueprint.group` コンストラクタ
- `BlueprintGroup`のインスタンス化
- `app.blueprint` の登録

複数の場所に定義がある場合、より具体的な定義はより一般的な定義を上書きします。 上のリストはそのヒエラルキーと対応しています。

`version_prefix` のデフォルト値は `/v` です。

.. column::

```
バージョン管理されたルートを `/api` にマウントしたいという状況がよくあります。これは`version_prefix`で簡単に実現できます。
```

.. column::

````
```python
# /v1/my/path
app.route("/my/path", version=1, version_prefix="/api/v")
```
````

.. column::

```
おそらく、より説得力のある使用法は、すべての`/api`ルートを単一の`BlueprintGroup`にロードすることです。
```

.. column::

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
