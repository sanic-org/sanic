---
title: Sanic Extensions - CORS保護
---

# CORS保護

クロスオリジンリソース共有(CORS)は、単独で_巨大_トピックです。 ここのドキュメントでは、_何_についての詳細を説明することはできません。 あなたは非常にそれによって提示されたセキュリティの問題を理解するために、独自にいくつかの研究を行うことを奨励されています, そして、ソリューションの背後にある理論. [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) は素晴らしい第一歩です。

超簡単な言葉で CORS保護は、ウェブページが別のドメインから情報にアクセスできる方法と時間を容易にするためにブラウザが使用するフレームワークです。 これは、シングルページアプリケーションを構築するすべての人にとって非常に重要です。 フロントエンドは `https://portal.myapp.com` のようなドメインであることがよくありますが、 `https://api.myapp.com` からバックエンドにアクセスする必要があります。

ここでの実装は[`sanic-cors`](https://github.com/ashleysommer/sanic-cors)に大きくインスパイアされており、順番には [`flask-cors`](https://github.com/corydolphin/flask-cors) に基づいています。 したがって、ほぼ`sanic-cors`を`sanic-ext`に置き換えることができます。

## 基本的な実装

.. 列::

```
format@@0(method) の例に示すように。 d#options), Sanic Extensionsは自動的にCORS保護を有効にします。しかし、あまり使いすぎることはありません。

*裸の最小値*では、アプリケーションにアクセスする目的の起点に`config.CORS_ORIGINS`を設定することを**高度に** 推奨します。
```

.. 列::

````
```python
from sanic import Sanic, text
from sanic_ext import Extend

app = Sanic(__name__)
app.config.CORS_ORIGINS = "http://foobar.com,http://bar.com"
Extend(app)

@app.get("/")
async def hello_world(request):
    return text("Hello, world.")
```

```
$ curl localhost:8000 -X OPTIONS -i
HTTP/1.1 204 No Content
allow: GET,HEAD,OPTIONS
access-control-allow-origin: http://foobar.com
connection: keep-alive
```
````

## 設定

ただし、CORSの設定を開始すると、CORSの保護の真の機能が実現します。 ここにすべてのオプションの表があります。

| キー                         | タイプ                              | デフォルト   | 説明                                                                                                                                                                                      |
| -------------------------- | -------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CORS_ALLOW_HEADERS`       | `str` または `List[str]`            | `"*"`   | `access-control-allow-headers` に表示されるヘッダーの一覧です。                                                                                                                                         |
| `CORS_ALWAYS_SEND`         | `bool`                           | `True`  | `True` の場合、 `access-control-allow-origin` の値は常に設定されます。 `False` の場合、`Origin` ヘッダーがある場合にのみ設定されます。                                                                                         |
| `CORS_AUTOMATIC_OPTIONS`   | `bool`                           | `True`  | 入力されるプリフライトリクエストが受信されると、`access-control-allow-headers` 、 `access-control-max-age` 、 `access-control-allow-methods` ヘッダの値を自動的に設定するかどうか。 `False`の場合、これらの値は`@cors`デコレータで装飾されたルートにのみ設定されます。 |
| `CORS_EXPOSE_HEADERS`      | `str` または `List[str]`            | `""`    | `access-control-expose-headers` ヘッダに設定されるヘッダの特定のリスト。                                                                                                                                    |
| `CORS_MAX_AGE`             | `str`, `int`, `timedelta`        | `0`     | プリフライト応答の最大秒数は `access-control-max-age` ヘッダーを使用してキャッシュできます。 偽の値を指定すると、ヘッダーは設定されません。                                                                                                     |
| `CORS_METHODS`             | `str` または `List[str]`            | `""`    | `access-control-allow-methods` ヘッダーに設定されているように、許可されたオリジンがアクセスできるHTTPメソッドです。                                                                                                             |
| `CORS_ORIGINS`             | `str`, `List[str]`, `re.Pattern` | `"*"`   | `access-control-allow-origin` ヘッダーに設定されているように、リソースにアクセスできるオリジンです。                                                                                                                       |
| `CORS_SEND_WILD`           | `bool`                           | `False` | `True`の場合、`origin`リクエストヘッダの代わりにワイルドカード`*`オリジンを送信します。                                                                                                                                    |
| `CORS_SUPPORT_CREDENTIALS` | `bool`                           | `False` | `access-control-allow-credentials` ヘッダーを設定します。                                                                                                                                          |
| `CORS_VARY_HEADER`         | `bool`                           | `True`  | `vary`ヘッダを追加するかどうか。                                                                                                                                                                     |

_上記の「リスト[str]」と書かれている簡潔さのために、`リスト`、`set`、`frozenset`、または`tuple`のいずれかのインスタンスは受け入れられます。 あるいは、値が `str` の場合、カンマ区切りのリストにすることもできます。_

## ルートレベルの上書き

.. 列::

```
特定のルートのアプリ全体の設定を上書きする必要がある場合もあります。 これを可能にするには、 `@sanic_ext.cors()` デコレータを使用して、ルート固有の値を設定します。

このデコレータで上書きできる値は次のとおりです。

- `origins`
- `expose_headers`
- `allow_headers`
- `allow_methods`
- `supports_credentials`
- `max_age`
```

.. 列::

````
```python
from sanic_ext import cors

app.config.CORS_ORIGinS = "https://foo.com"

@app.get("/", host="bar.com")
@cors(origs="https://bar.com")
async def hello_world(request):
    return text("Hello, world.")
```
````
