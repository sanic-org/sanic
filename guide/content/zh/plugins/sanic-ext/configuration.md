---
title: Sanic 扩展 - 配置
---

# 配置

Sanic 扩展可以使用[你可以配置Sanic](../../guide/running/configuration.md)同样的方式进行配置。 这使得配置Sanic扩展变得非常容易。

```python
app = Sanic("MyApp")
app.config.OAS_URL_PREFIX = "/apidocs"
```

然而，还有一些其他配置方案应加以考虑。

## 手动`extend`

.. 列:

```
尽管Sanic 扩展会自动附加到您的应用程序，但您可以手动选择 `extend`。 当你这样做时，你可以传递所有的配置值作为关键字参数(小写)。
```

.. 列:

````
```python
app = Sanic("MyApp")
app.extend(oas_url_prefix="/apidocs")
```
````

.. 列:

```
或者，也可以同时将其作为一个单一的词语。
```

.. 列:

````
```python
app = Sanic("MyApp")
app.extend(config={"oas_url_prefix": "/apidocs"})
```
````

.. 列:

```
由于配置设置的名称无法被IDE发现，这两种解决办法都受到影响。 因此，您也可以使用一个类型注释的对象。这将有助于开发体验。
```

.. 列:

````
```python
来自sanic_ext import Config

app = Sanic("MyApp")
app.extend(config=Config(oas_url_prefix="/apidocs"))
```
````

## 设置

.. 注：

````
通常最容易改变申请的方式(因为它们可能不会因环境而改变)， 将它们直接设置在“应用”上。 onfig`对象。

只需使用这里显示的配置密钥的大写版本：

```python
app = Sanic("MyApp")
app.config.OAS_URL_PREFIX = "/apidocs"
```
````

### `cors`

- **类型**: `bool`
- **默认**: `True`
- **描述**：是否启用 CORS 保护

### `cors_allow_headers`

- **类型**: `str`
- **默认**: `"*"`
- **描述**: 标题值: `access-control-allow-headers`

### `cors_always_send`

- **类型**: `bool`
- **默认**: `True`
- **描述**: 是否总是发送头部: `access-control-allow-origin`

### `cors_automatic_options`

- **类型**: `bool`
- **默认**: `True`
- **描述**：是否为那些没有\*定义过一个的路由自动生成 "OPTIONS" 端点

### `cors_expose_headers`

- **类型**: `str`
- **默认**: `""`
- **描述**: 标题值: `access-control-expose-headers`

### `cors_max_age`

- **类型**: `int`
- **默认**: `5`
- **描述**: 标题值: `access-control-max-age`

### `cors_methods`

- **类型**: `str`
- **默认**: `""`
- **描述**: 标题值: `access-control-access-allow-methods`

### `cors_origins`

- **类型**: `str`
- **默认**: `""`
- **描述**: 标题值: `access-control-allow-origin`

.. 警告：:

```
如果你把`*`放在这里，请非常小心。 不要这样做，除非你知道你正在做什么，因为它可能是一个安全问题。
```

### `cors_send_wildcard`

- **类型**: `bool`
- **默认**: `False`
- **描述**：是否发送通配符来源而不是传入请求来源

### `cors_supports_credentials`

- **类型**: `bool`
- **默认**: `False`
- **描述**: 标题值: `access-control-allow-credentials`

### `cors_vary_header`

- **类型**: `bool`
- **默认**: `True`
- **描述**：是否添加 `vary` 标题

### `http_all_methods`

- **类型**: `bool`
- **默认**: `True`
- **描述**: 添加 HTTP `CONNECT` 和 `TRACE` 方法为允许方法

### `http_auto_head`

- **类型**: `bool`
- **默认**: `True`
- **描述**：自动将 `HEAD` 处理程序添加到任何 `GET` 路由

### `http_auto_options`

- **类型**: `bool`
- **默认**: `True`
- **描述**：自动将 `OpTIONS` 处理程序添加到任何路由中，无需此说明

### `http_auto_trace`

- **类型**: `bool`
- **默认**: `False`
- **描述**：自动将 `TRACE` 处理程序添加到任何路由中无需添加。

### `oas`

- **类型**: `bool`
- **默认**: `True`
- **描述**：是否启用 OpenAPI 规范生成

### `oas_autodoc`

- **类型**: `bool`
- **默认**: `True`
- **描述**：是否从路由函数的 docstring 自动提取OpenAPI 详细信息

### `oas_ignore_head`

- **类型**: `bool`
- **默认**: `True`
- **描述**: WHen `True`, 它将不会在 OpenAPI 规范中添加 `HEAD` 端点

### `oas_ignore_options`

- **类型**: `bool`
- **默认**: `True`
- **描述**: WHen `True`, 它不会在 OpenAPI 规范中添加 `OPTIONS` 端点

### `oas_path_to_redoc_html`

- **类型**: `可选的[str]`
- **默认**: `None`
- **描述**：HTML文件路径以覆盖现有的 Redoc HTML

### `oas_path_to_swagger_html`

- **类型**: `可选的[str]`
- **默认**: `None`
- **描述**：要覆盖现有的 Swagger HTML 文件的路径

### `oas_ui_default`

- **类型**: `可选的[str]`
- **默认**: \`"redoc""
- **描述**：哪些OAS 文档将用于bare `oas_url_prefix`端点；当`None`时，该位置将没有文档。

### `oas_ui_redoc`

- **类型**: `bool`
- **默认**: `True`
- **描述**：是否启用 Redoc 界面

### `oas_ui_swagger`

- **类型**: `bool`
- **默认**: `True`
- **描述**：是否启用 Swagger 界面

### `oas_ui_swagger_version`

- **类型**: `str`
- **默认**: `"4.1.0"`
- **描述**：要使用哪个Swagger版本

### `oas_uri_to_config`

- **类型**: `str`
- **Default**: `"/swagger-config"`
- **描述**：为 Swagger 配置服务的路径

### `oas_uri_to_json`

- **类型**: `str`
- **Default**: `"/openapi.json"`
- **描述**：提供 OpenAPI JSON 的路径

### `oas_uri_to_redoc`

- **类型**: `str`
- **默认**: \`"/redoc""
- **描述**：Redoc 路径

### `oas_uri_to_swagger`

- **类型**: `str`
- **Default**: `"/swagger"`
- **描述**：到 Swagger 的路径

### `oas_url_prefix`

- **类型**: `str`
- **Default**: `"/docs"`
- **描述**：所有OA文档都有意附加的蓝图的 URL 前缀

### `swagger_ui_configuration`

- **Type**: `Dict[str, Any]`
- **默认**: "{"apisSorter": "alph", "operationsSorter": "alpha", "docExpassion": "full"}"
- **描述**: 即将服务到前端的 Swagger 文档

### `templating_enable_async`

- **类型**: `bool`
- **默认**: `True`
- **描述**：是否在 Jinja `Environment` 中设置 `enable_async`

### `templating_path_to_templates`

- **Type**: \`Union[str, os.PathLike, Sequence[Union[str, os.PathLie]]]
- **默认**: `templates`
- **描述**：单一路径，或多个路径到您的模板文件所在位置

### `Trace_excluded_headers`

- **Type**: `序列[str]`
- **默认**: `("authorization", "cookie")`
- **描述**：哪个头应该从对 `TRACE` 请求的响应中停止
