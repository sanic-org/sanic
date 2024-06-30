---
title: Sanic Extensions - 設定
---

# 設定

Sanic Extensionsは、format@@0(../../guide/deployment/configuration.md)と同じ方法で設定できます。 これにより、Sanic Extensionsを非常に簡単に構成できます。

```python
app = Sanic("MyApp")
app.config.OAS_URL_PREFIX = "/apidocs"
```

しかし、検討すべき設定オプションはいくつかあります。

## 手動の`extend`

.. 列::

```
Sanic Extensionsはアプリケーションに自動的にアタッチされますが、手動で`extend`を選択することができます。 これを行うと、すべての設定値をキーワード引数(小文字)として渡すことができます。
```

.. 列::

````
```python
app = Sanic("MyApp")
app.extend(oas_url_prefix="/apidocs")
```
````

.. 列::

```
あるいは、一度に 1 つの `dict` として渡すこともできます。
```

.. 列::

````
```python
app = Sanic("MyApp")
app.extend(config={"oas_url_prefix": "/apidocs"})
```
````

.. 列::

```
これらのソリューションはどちらも、IDEによって構成設定の名前が検出できないという事実に苦しんでいます。 したがって、使用できる型注釈付きオブジェクトもあります。これは開発に役立つはずです。
```

.. 列::

````
```python
from sanic_ext import Config

app = Sanic("MyApp")
app.extend(config=Config(oas_url_prefix="/apidocs"))
```
````

## 設定

.. note::

````
多くの場合、アプリケーションのためにこれらを変更する最も簡単な方法 (環境に依存して変更しない可能性が高いので) `appに直接設定することです。 onfig` オブジェクト

ここで示すように、設定キーの大文字のバージョンを使用します。

```python
app = Sanic("MyApp")
app.config.OAS_URL_PREFIX = "/apidocs"
```
````

### `cors`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **説明**: CORS 保護を有効にするかどうか

### `cors_allow_headers`

- **タイプ**: `str`
- **デフォルト**: `"*"`
- **説明**: ヘッダの値: `access-control-allow-headers`

### `cors_always_send`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **説明**: ヘッダを常に送信するかどうか: `access-control-allow-origin`

### `cors_automatic_options`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **Description**: _ない_ルートの「OPTIONS」エンドポイントを自動的に生成するかどうか

### `cors_expose_headers`

- **タイプ**: `str`
- **デフォルト**: `""`
- **説明**: ヘッダの値: `access-control-expose-headers`

### `cors_max_age`

- **タイプ**: `int`
- **デフォルト**: `5`
- **説明**: ヘッダの値: `access-control-max-age`

### `cors_methods`

- **タイプ**: `str`
- **デフォルト**: `""`
- **説明**: ヘッダの値: `access-control-access-control-allow-methods`

### `cors_origins`

- **タイプ**: `str`
- **デフォルト**: `""`
- **説明**: ヘッダの値: `access-control-allow-origin`

.. 警告::

```
`*`をここに置くときは注意してください。 セキュリティの問題である可能性があるため、何をしているかを知っていない限り、これをしないでください。
```

### `cors_send_wildcard`

- **タイプ**: `bool`
- **デフォルト**: `False`
- **Description**: リクエストオリジンの代わりにワイルドカードを送信するかどうか

### `cors_supports_credentials`

- **タイプ**: `bool`
- **デフォルト**: `False`
- **説明**: ヘッダの値: `access-control-allow-credentials`

### `cors_vary_header`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **Description**: `vary`ヘッダーを追加するかどうか

### `http_all_methods`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **Description**: 許可されている HTTP の `CONNECT` と `TRACE` メソッドを追加します

### `http_auto_head`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **Description**: 自動的に `HEAD` ハンドラを `GET` ルートに追加します。

### `http_auto_options`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **説明**: 自動的に `OPTIONS` ハンドラをルートなしで追加します

### `http_auto_trace`

- **タイプ**: `bool`
- **デフォルト**: `False`
- **説明**: 自動的に `TRACE` ハンドラをルートなしで追加します

### `oas`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **説明**: OpenAPI仕様の生成を有効にするかどうか

### `oas_autodoc`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **説明**: ルート関数のdocstringからOpenAPIの詳細を自動的に抽出するかどうか

### `oas_ignore_head`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **Description**: When `True`, `HEAD`エンドポイントをOpenAPI仕様に追加しません

### `oas_ignore_options`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **説明**: When `True` はOpenAPI仕様に`OPTIONS`エンドポイントを追加しません

### `oas_path_to_redoc_html`

- **タイプ**: `Optional[str]`
- **デフォルト**: `None`
- **Description**: 既存のやり直しHTMLをオーバーライドするHTMLファイルへのパス

### `oas_path_to_swagger_html`

- **タイプ**: `Optional[str]`
- **デフォルト**: `None`
- **説明**: 既存の Swagger HTML をオーバーライドする HTML ファイルへのパス

### `oas_ui_default`

- **タイプ**: `Optional[str]`
- **デフォルト**: `"redoc"`
- **説明**: どのOASドキュメントを `oas_url_prefix` エンドポイントで提供します。`None` の場所にドキュメントがありません。

### `oas_ui_redoc`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **説明**: やり直しのUIを有効にするかどうか

### `oas_ui_swagger`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **説明**: Swagger UI を有効にするかどうか

### `oas_ui_swagger_version`

- **タイプ**: `str`
- **デフォルト**: `"4.1.0"`
- **説明**: どのSwaggerバージョンを使用するか

### `oas_uri_to_config`

- **タイプ**: `str`
- **Default**: `"/swagger-config"`
- **説明**: Swagger 設定を提供するパス

### `oas_uri_to_json`

- **タイプ**: `str`
- **Default**: `"/openapi.json"`
- **説明**: OpenAPI JSON を提供するためのパス

### `oas_uri_to_redoc`

- **タイプ**: `str`
- **デフォルト**: `"/redoc"`
- **説明**: やり直しへのパス

### `oas_uri_to_swagger`

- **タイプ**: `str`
- **Default**: `"/swagger"`
- **説明**: Swagger へのパス

### `oas_url_prefix`

- **タイプ**: `str`
- **Default**: `"/docs"`
- **説明**: OASドキュメントのすべてのwitllが添付するブループリントのURLプレフィックス。

### `swagger_ui_configuration`

- **タイプ**: `Dict[str, Any]`
- **デフォルト**: `{"apisSorter": "alpha", "operationsSorter": "alpha", "docExpansion": "full"}`
- **説明**: フロントエンドに提供される Swagger ドキュメント

### `templating_enable_async`

- **タイプ**: `bool`
- **デフォルト**: `True`
- **Description**: 神社`Environment` に `enable_async` を設定するかどうか

### `templating_path_to_templates`

- **タイプ**: `Union[str, os.PathLike, Sequence[Union[str, os.PathLike]]] `
- **デフォルト**: `templates`
- **説明**: テンプレートファイルがどこにあるか、単一のパス、または複数のパスです。

### `trace_excluded_headers`

- **タイプ**: `Sequence[str]`
- **デフォルト**: `("authorization", "cookie")`
- **Description**: `TRACE`リクエストへのレスポンスから抑制されるヘッダーを指定します。
