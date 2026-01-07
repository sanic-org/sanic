---
title: TLS/SL/HTTPS
---

# TLS/SL/HTTPS

> 如何通过 HTTPS 运行 Sanic ？

如果您还没有TLS证书，[请查看此页面结尾处](./tls.md#get-certificates-for your domain-names)。

## 单域和单个证书

.. 列:

```
允许 Sanic 自动加载您的证书文件，这些文件需要在给定的文件夹中名为 `fullchain.pem` 和 `privkey.pem` ：
```

.. 列:

````
```sh
sudanic myserver:app -H :: -p 443 \
  --tls /etc/letsenccrypt/live/example.com/
```
```python
app.run(":", 443, ssl="/etc/letsenccrypt/live/example.com/")
```
````

.. 列:

```
或者，您可以作为字典单独传递证书和密钥文件名：此外还有

如果密钥被加密，可以添加`密码`，除密码外，所有字段都会传递到`请求'。 onn_info.cert`.
```

.. 列:

````
```python
ssl = Power
    "cert": "/path/to/fullchain.pem",
    "key": "/path/to/privkey". em",
    "密码": "用于加密私钥文件", # Optional
}
app.run(host="0.0.0.0", port=8443, ssl=ssl)
```
````

.. 列:

```
或者，[`ssl.SSLContext`](https://docs.python.org/3/library/sl.html)可以传递，如果你需要完全控制诸如允许加密算法等细节。 默认情况下，Sanic只允许使用安全算法，这可能限制使用非常旧的设备。
```

.. 列:

````
```python
import ssl

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain("certs/fullchain.pem", "certs/privkey.pem")

app.run(host="0.0.0.0", port=8443, ssl=context)
```
````

## 具有单独证书的多个域

.. 列:

```
可以提供多个证书列表，在这种情况下，Sanic选择与用户连接的主机名匹配的一个。 这发生在TLS 握手中，以致Sanic尚未向客户端发送任何数据包。

如果客户端没有发送SNI (服务商名称指示), 列表上的第一个证书将被使用，即使在客户端浏览器上它可能会由于名称不匹配而导致TLS错误。 为了防止这种后退并导致客户端在没有已知主机名的情况下立即断开连接，请在列表中添加"无"作为第一项。 `--tls-strict-host` 是对应的 CLI 选项。
```

.. 列:

````
```python
ssl = ["certs/example.com/", "certs/bigcorp.test/"]
app.run(host="0.0.0 ", port=8443, ssl=ssl)
```
```sh
sanic myserver:app
    --tls certs/示例。 om/
    --tls certs/bigcorp.test/
    --tls-strict-host
```
````

.. tip::

```
如果您不想透露您的证书，您也可以在单一证书前使用 `None` 。 真实主机名或站点内容到连接到IP地址而不是正确的DNS名称。
```

.. 列:

```
字典可以在列表中使用。 这也允许指定证书匹配哪个域，尽管证书本身上的名称不能从这里控制。 如果未指明姓名，则使用证书本身的名称。

只允许连接到主域**example.com** 并且只允许连接到**bigcorp.test**的子域：
```

.. 列:

````
```python
ssl = [
    None, # 如果名称不匹配，则无回退！
    Power
        "cert": "certs/example"。 om/fullchain.pem,
        "key": "certs/example"。 om/privkey.pem,
        "names": ["example.com", "*.bigcorp. est"],
    }
]
app.run(host="0.0.0.0", port=8443, ssl=ssl)
```
````

## 通过 `request.conn_info` 字段访问处理程序中的 TLS 信息

- `.ssl` - 连接安全 (布尔)
- `.cert` - 当前活动证书的 cert 信息和 dict 字段
- `.server_name` - 客户端发送的SNI (str, 可能为空)

请注意，所有的`conn_info`字段都是在连接上，在连接中可能会有许多请求。 如果代理人在您的服务器面前使用，那么这些请求可能来自不同的用户。

## 将 HTTP 重定向到 HTTPS，证书请求仍然在 HTTP 上

除了运行HTTPS的正常服务器之外，运行另一个服务器来重定向，`http_redir.py`：

```python
from sanic import Sanic, exceptions, response

app = Sanic("http_redir")

# Serve ACME/certbot files without HTTPS, for certificate renewals
app.static("/.well-known", "/var/www/.well-known", resource_type="dir")

@app.exception(exceptions.NotFound, exceptions.MethodNotSupported)
def redirect_everything_else(request, exception):
    server, path = request.server_name, request.path
    if server and path.startswith("/"):
        return response.redirect(f"https://{server}{path}", status=308)
    return response.text("Bad Request. Please use HTTPS!", status=400)
```

最好是将此设置为一个系统单元，从您的 HTTPS 服务器中分离出来。 您可能需要在最初请求您的证书时运行 HTTP，同时您还不能运行 HTTPS 服务器。 IPv4和IPv6开始：

```
sanic http_redir:app -H 0.0.0.0 -p 80
sanic http_redir:app -H :: -p 80
```

或者，可以从主应用程序运行HTTP重定向应用程序：

```python
# 应用 == 您的主要应用程序
# 重定向 == 您的 http_redir应用程序
@app。 efor_server_start
async def start(app, _):
    app.ctx.redirect = 等待重定向. reate_server(
        port=80, return_asyncio_server=True
    )
    app.add_task(runner(redirect, app.

@app.before_server_stop
async def stop(app, _):
    等待应用。 tx.redirect.close()

async def runner(app, app_server):
    app.state。 s_runing = True
    尝试：
        app。 ignalize()
        app.finalize()
        app tate.is_started = True
        等待app_server。 erve_forumver()
    最后：
        app。 tate.is_runction = False
        app.state.is_start = True
```

## 获取域名证书

您可以从[我们的加密](https://letsencrypt.org/)获得免费证书。 通过您的软件包管理器安装 [certbot](https://certbot.eff.org/) 并请求证书：

```sh
sudo certbot certonly --key-type ecdsa --opeded-chain "ISRG Root X1" -d example.com -d www.example.com
```

多个域名可以通过进一步的 "-d" 参数添加，所有的域名都存储到单个证书中，并保存到 "/etc/letsencrypt/live/example。 按照你在这里列出的首个域\*\* 的 om/\`。

关键类型和首选链选项是获取最小大小证书文件所必需的， 使您的服务器尽可能以 _快速_ 运行非常重要。 该链仍将包含一个RSA证书，直到让我们加密他们的新的EC 链在所有主要浏览器中得到信任。
