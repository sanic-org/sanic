---
title: Sanic Extensions - Jinja
---

# 模板

Sanic 扩展可以轻松地帮助您将模板整合到您的路由处理器中。

## 依赖关系

**目前，我们只支持 [Jinja](https://github.com/pallets/jinja/)。**

[如果你不熟悉如何创建模板，请先阅读Jinja 文档](https://jinja.palletsprojects.com/en/3.1.x/)。

Sanic 扩展如果安装在您的环境中，它将自动为您设置并加载Jinja。 因此，您需要做的唯一设置是安装 Jinja：

```
pip install Jinja2
```

## 从文件渲染模板

您有三(3)种方式：

1. 使用装饰器预加载模板文件
2. 返回渲染`HTTPResponse`对象
3. 混合模式创建一个 `LazyResponse`

让我们想象你有一个叫做`./templates/foo.html`的文件：

```html
<!DOCTYPE html>
<html lang="en">

    <head>
        <title>My Webpage</title>
    </head>

    <body>
        <h1>Hello, world!!!!</h1>
        <ul>
            {% for item in seq %}
            <li>{{ item }}</li>
            {% endfor %}
        </ul>
    </body>

</html>
```

让我们看看你如何用 Sanic + Jinja来渲染它。

### 备选案文1 - 装饰符

.. 列:

```
这种方法的好处是，可以在启动时预定义模板。 这将意味着较少需要在处理器中进行获取，因此应该是最快的选择。
```

.. 列:

````
```python
@app.get("/")
@app.ext.template("foo.html")
async def handler(request: Request):
    return {"seq": ["one", "two"]}
```
````

### 备选案文2 - 作为退货对象

.. 列:

```
这意在模仿核心Sanic的“文本”、“json”、“html”、“file”等模式。 它将允许对响应对象进行最直接的自定义，因为它可以直接控制它。 就像在其他 `HTTPResponse` 对象一样，你可以控制头、 cookie 等。
```

.. 列:

````
```python
来自sanic_ext import render

@app。 et("/alt")
异步处理器(请求: 请求):
    正在等待渲染(
        "foo". tml, context={"seq": ["the", "four"]}, status=400

```
````

### 备选案文3 - 混合的 lazy

.. 列:

```
在这个方法中，模板是先定义的，而不是在处理程序内(用于性能)。 然后，`render` 函数返回一个 `LazyResponse` ，该函数可以用于在装配器内构建一个 `HTTPResponse` 。
```

.. 列:

````
```python
from sanic_ext importing render

@app.get("/")
@app.ext.template("foo.html")
async def handler(request: Request):
    returning render(context={"seq": ["fir", "six"]}, status=400)
```
````

## 从字符串渲染模板

.. 列:

```
有时，您可能想要在 Python 代码中写入(或生成) 您的模板和 _not_ 从 HTML 文件中读取。 在这种情况下，你仍然可以使用 `render` 函数。只需使用 `template_source` 。
```

.. 列:

````
```python
from sanic_ext import render
from textwrap import dedent

@app.get("/")
async def handler(request):
    template = dedent("""
        <!DOCTYPE html>
        <html lang="en">

            <head>
                <title>My Webpage</title>
            </head>

            <body>
                <h1>Hello, world!!!!</h1>
                <ul>
                    {% for item in seq %}
                    <li>{{ item }}</li>
                    {% endfor %}
                </ul>
            </body>

        </html>
    """)
    return await render(
        template_source=template,
        context={"seq": ["three", "four"]},
        app=app,
    )
```
````

.. 注：

```
在这个示例中，我们使用 `texttwrap.dedent` 来删除多行字符串开始处的空格。 它是不必要的，而只是一个很好的触摸来保持代码和生成的源代码的清理。
```

## 开发和自动重载

如果启用自动重新加载，则更改您的模板文件会触发服务器的重新加载。

## 配置

See `templating_enable_async` and `templating_path_to_templates` in [settings](./configuration.md#settings).
