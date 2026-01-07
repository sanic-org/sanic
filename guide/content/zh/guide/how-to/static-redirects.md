# “静态”重定向

> 如何配置静态重定向？

## `app.py`

```python
### 设置 ###
import typing
import sanic, sanic.response

# 创建 Sanic app
app = sanic.Sanic(__name__)

# 该目录代表你的 "static" 目录重定向。
# 举个例子，这些值可以从配置文件中提取。
REDIRECTS = {
    '/':'/hello_world',                     # 重定向 '/' 到 '/hello_world'
    '/hello_world':'/hello_world.html'      #重定向 '/hello_world' 到 'hello_world.html'
}

# 这个函数会返回另一个（已配置值）的函数，而且不受已传参数的限制。
def get_static_function(value:typing.Any) -> typing.Callable[..., typing.Any]:
    return lambda *_, **__: value

### 路由 ###
# 遍历重定向
for src, dest in REDIRECTS.items():                            
    # 创建重定向响应对象         
    response:sanic.HTTPResponse = sanic.response.redirect(dest)

    # 创建处理函数，通常，仅将 sanic.Request 对象传递给该函数。 该对象将被忽略。
    handler = get_static_function(response)

    # 路由src到处理函数
    app.route(src)(handler)

# 随便路由一些文件和client资源
app.static('/files/', 'files')
app.static('/', 'client')

### 运行 ###
if __name__ == '__main__':
    app.run(
        '127.0.0.1',
        10000
    )
```

## `client/hello_world.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hello World</title>
</head>
<link rel="stylesheet" href="/hello_world.css">
<body>
    <div id='hello_world'>
        Hello world!
    </div>
</body>
</html>
```

## `client/hello_world.css`

```css
#hello_world {
    width: 1000px;
    margin-left: auto;
    margin-right: auto;
    margin-top: 100px;

    padding: 100px;
    color: aqua;
    text-align: center;
    font-size: 100px;
    font-family: monospace;

    background-color: rgba(0, 0, 0, 0.75);

    border-radius: 10px;
    box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.75);
}

body {
    background-image: url("/files/grottoes.jpg");
    background-repeat: no-repeat;
    background-size: cover;
}
```

## `files/grottoes.jpg`

![lake](/assets/images/grottoes.jpg)

---

此外，结算社区的一些资源：

- [静态路由示例](https://github.com/Perzan/sanic-static-routing-example)
