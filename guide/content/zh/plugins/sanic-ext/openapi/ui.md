---
title: Sanic 扩展 - OAS UI
---

# UI

Sanic 扩展使用Redoc和Swagger两种接口。 你可以选择使用一个，或两个。 下面的终点是为您设置的，下面的 bare `/docs` 显示重启。

- `/docs`
- `/docs/openapi.json`
- `/docs/redoc`
- `/docs/swagger`
- `/docs/openapi-config`

## 配置选项

| **密钥**                     | **Type**   | **默认**              | **去除提示**                                                    |
| -------------------------- | ---------- | ------------------- | ----------------------------------------------------------- |
| `OAS_IGNORE_HEAD`          | `bool`     | `True`              | 是否显示 `HEAD` 终点。                                             |
| `OAS_IGNORE_OPTIONS`       | `bool`     | `True`              | 是否显示 "OPTIONS" 端点。                                          |
| `OAS_PATH_TO_REDOC_HTML`   | `可选的[str]` | `无`                 | 覆盖默认的 Redoc HTML 路径                                         |
| `OAS_PATH_TO_SWAGGER_HTML` | `可选的[str]` | `无`                 | 覆盖默认的 Swagger HTML 路径                                       |
| `OAS_UI_DEFAULT`           | `可选的[str]` | `"redoc"`           | 可以设置为 `redoc` 或 `swagger` 。 控制基线路上显示的界面。 如果设置为“无”，基线路将不会设置。 |
| `OAS_UI_REDOC`             | `bool`     | `True`              | 是否启用 Redoc UI                                               |
| `OAS_UI_SWAGGER`           | `bool`     | `True`              | 是否启用 Swagger UI                                             |
| `OAS_URI_TO_CONFIG`        | `str`      | `"/openapi-config"` | Swagger 使用的 OpenAPI 配置的 URI 路径                              |
| `OAS_URI_TO_JSON`          | `str`      | `"/openapi.json"`   | JSON文档的 URI 路径。                                             |
| `OAS_URI_TO_REDOC`         | `str`      | `"/redoc"`          | 重新编码的 URI 路径。                                               |
| `OAS_URI_TO_SWAGGER`       | `str`      | `"/swagger"`        | URI 到 Swagger 的路径。                                          |
| `OAS_URL_PREFIX`           | `str`      | `"/docs"`           | 用于OpenAPI 文档蓝图的 URL 前缀。                                     |
