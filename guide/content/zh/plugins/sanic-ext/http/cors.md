---
title: Sanic Extensions - CORS 保护
---

# CORS 保护

跨源资源共享（又称核心资源共享）本身就是一个_大量_的主题。 这里的文档无法详细了解_它是什么_。 我们非常鼓励你自己进行一些研究，以了解它所提出的安全问题以及解决办法背后的理论。 [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)是很好的第一步。

以超简短的措辞， CORS 保护是一个浏览器用来方便网页如何和何时可以从另一个域访问信息的框架。 这与任何人建立单页应用程序都是极其相关的。 您的前端常常可能位于一个域名上，例如`https://portal.myapp.com`，但它需要访问`https://api.myapp.com`的后端。

此处的执行受到[`sanic-cors`](https://github.com/ashleysommer/sanic-cors)的大力启发，而这又是基于[`flask-cors`](https://github.com/corydolphin/flask-cors)。 因此，你很可能会用`sanic-ext`来取代\`sanic-cors'。

## 基本执行

.. 列:

```
如[自动端点示例](方法)中的示例所示。 d#options), Sanic Extensions 会自动使CORS 保护无需采取进一步行动, 但它不会提供太多的箱子.

在 *bare minimum * 上，**强烈** 建议您将 `config.CORS_ORIGINS` 设置为将访问应用程序的原始(s)。
```

.. 列:

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

## 配置

然而，一旦你开始配置CORS 保护的真正功效。 这是所有选项的一个表。

| 关键字                         | 类型                               | 默认设置    | 描述                                                                                                                                                      |
| --------------------------- | -------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CORS_ALLOW_HEADERS`        | `str` 或 `list[str]`              | `"*"`   | 显示在"访问控制-允许-headers"中的标题列表。                                                                                                                             |
| `CORS_ALWAYS_SEND`          | `bool`                           | `True`  | 当`True`时，总是会设置`access-control-allow-origin`的值。 当`False`时，只有在存在`原始`标题时才会设置它。                                                                             |
| `CORS_AUTOMATIC_OPTIONS`    | `bool`                           | `True`  | 当收到传入的飞行前请求时，是否为`access-controll-allow-headers`、`access-control-max-age`和`access-control-allow-methods`设置自动设置值。 如果`False`，则这些值将只设在使用 `@cors` 装饰器装饰的路径上。 |
| `CORS_EXPOSE_HEADERS`       | `str` 或 `list[str]`              | `""`    | 要在 `access-controll-expose-headers` 标题中设置的特殊标题列表。                                                                                                       |
| `CORS_MAX_AGE`              | `str`, `int`, `timedelta`        | `0`     | 飞行前响应的最大秒数可以使用 'access-control-max-age' 头缓存。 falsey 值将导致页眉不被设置。                                                                                         |
| `CORS_METHODS`              | `str` 或 `list[str]`              | `""`    | 允许的源代码访问的 HTTP 方法，设置在 `access-control-allow-methods` 标题上。                                                                                               |
| `CORS_ORIGINS`              | `str`, `List[str]`, `re.Pattern` | `"*"`   | 允许访问资源的来源，如在 `access-control-allow-origin` 标题上设定。                                                                                                       |
| `CORS_SEND_WILDCARD`        | `bool`                           | `False` | 如果`True`，将发送通配符`*`而不是\`orig'请求标题。                                                                                                                       |
| `CORS_SUPPORTS_CREDENTIALS` | `bool`                           | `False` | 是否设置 `access-control-allow-credentials` 标题。                                                                                                             |
| `CORS_VARY_HEADER`          | `bool`                           | `True`  | 是否在适当时添加 `vary` 标题。                                                                                                                                     |

_For the sake of brevity, where the above says `List[str]` any instance of a `list`, `set`, `frozenset`, or `tuple` will be acceptable. 或者，如果值是 `str`，它可以是逗号分隔的列表。_

## 路由级别覆盖

.. 列:

```
有时可能需要覆盖特定路由的应用程序设置。 为了允许这一点，您可以使用 `@sanic_ext.cors()` 装饰符来设置不同的路径特定值。

此装饰符可以覆盖的值是：

- `origins`
- `expose_headers'
- `allow_headers`
- `allow_methods`
- `supports_credentials`
- `max_age`
```

.. 列:

````
```python
from sanic_ext import cors

app.config.CORS_ORIGINS = "https://foo.com"

@app.get("/", host="bar.com")
@cors(origins="https://bar.com")
async def hello_world(request):
    return text("Hello, world.")
```
````
