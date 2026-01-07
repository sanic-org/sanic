---
title: サニックエクステンション - OAS UI
---

# UI

Sanic Extensionsには、RedocとSwaggerの両方のインターフェースが付属しています。 あなたはそれらのいずれかまたは両方を使用する選択があります。 以下の端点があなたのためにセットアップされています。元の `/docs` にはRedocが表示されています。

- `/docs`
- `/docs/openapi.json`
- `/docs/redoc`
- `/docs/swagger`
- `/docs/openapi-config`

## 設定オプション

| **キー**                     | **Type**        | **デフォルト**           | **降順**                                                                                   |
| -------------------------- | --------------- | ------------------- | ---------------------------------------------------------------------------------------- |
| `OAS_IGNORE_HEAD`          | `bool`          | `True`              | 「HEAD」エンドポイントを表示するかどうかを設定します。                                                            |
| `OAS_IGNORE_Options`       | `bool`          | `True`              | 「OPTIONS」エンドポイントを表示するかどうかを設定します。                                                         |
| `OAS_PATH_TO_REDOC_HTML`   | `Optional[str]` | `なし`                | デフォルトのやり直しのHTMLをオーバーライドするHTMLへのパス                                                        |
| `OAS_PATH_TO_SWAGGER_HTML` | `Optional[str]` | `なし`                | デフォルトの Swagger HTML を上書きするための HTML へのパス                                                  |
| `OAS_UI_DEFAULT`           | `Optional[str]` | `"redoc"`           | `redoc` または `swagger` に設定できます。 ベースルート上に表示する UI を制御します。 `None` に設定されている場合、ベースルートは設定されません。 |
| `OAS_UI_REDOC`             | `bool`          | `True`              | Redoc UI を有効にするかどうか。                                                                     |
| `OAS_UI_SWAGGER`           | `bool`          | `True`              | Swagger UI を有効にするかどうか。                                                                   |
| `OAS_URI_TO_CONFIG`        | `str`           | `"/openapi-config"` | Swagger が使用する OpenAPI 設定への URI パス                                                        |
| `OAS_URI_TO_JSON`          | `str`           | `"/openapi.json"`   | JSON ドキュメントへの URI パスです。                                                                  |
| `OAS_URI_TO_REDOC`         | `str`           | `"/redoc"`          | 再ドックへのURIパス                                                                              |
| `OAS_URI_TO_SWAGGER`       | `str`           | `"/swagger"`        | Swagger への URI パスです。                                                                     |
| `OAS_URL_PREFIX`           | `str`           | `"/docs"`           | OpenAPIドキュメントのブループリントに使用するURLプレフィックス。                                                    |
