# Caddy 部署

## 一. 导言

Caddy 是一个最先进的网络服务器和代理服务器，最多支持 HTTP/3。 它的简单性在于它的最小化配置以及从我们加密中自动获取您的域名的 TLS 证书的内置能力。 在这个设置中，我们将配置Sanic应用程序在 127.0.0.0 本地服务。 :8001, 与 Caddy 在域example.com中扮演公共对口服务器的角色。

您可以在 Windows、Linux 和 Mac 上从您最喜欢的软件包菜单中安装Caddy。 包名为`caddy`。

## Proxied Sanic 应用

```python
from sanic import Sanic
from sanic.response import text

app = Sanic("proxied_example")

@app.get("/")
def index(request):
    # This should display external (public) addresses:
    return text(
        f"{request.remote_addr} connected to {request.url_for('index')}\n"
        f"Forwarded: {request.forwarded}\n"
    )
```

要运行此应用程序，请另存为 `proxied_example.py`，并使用符合条件的命令行接口如下：

```bash
SANIC_PROXIES_COUNT=1 sanic proxied_example --porter 8001
```

设置SANIC_PROXIES_COUNT 环境变量指示Sanic信任Caddy发送的 X-Forwarded-\* 头部。 允许它正确识别客户端的 IP 地址和其他信息。

## Caddy 是简单的

如果你没有其他网络服务器运行，你可以简单地运行 Caddy CLI (Linux需要`sudo`)：

```bash
caddy reverse-proxy --from example.com --to :8001
```

这是一个完整的服务器，包括您的域名、 httpto https 重定向、 代理头、 流媒体和 WebSockets的证书。 您的 Sanic 应用程序现在应该可以在 HTTP 版本 1, 2 和 3 指定的域上使用。 记住要在您的防火墙上打开 UDP/443 以启用 H3 通信。

完成了所有任务吗？

很快，您将需要多个服务器，或者更多的细节控制，这是配置文件的位置。 上述命令相当于此 `Caddyfile` ，作为您安装的一个良好起点：

```
example.com {
    reverse_proxy localhost:8001
}
```

一些Linux 发行版安装Caddy，它会读取`/etc/caddy/Caddyfile`的配置，它会为您正在运行的每个网站导入/etc/caddy/conf.d/\*。 如果没有，你需要手动运行 "caddy run" 作为系统服务，指向正确的配置文件。 或者，使用 caddy 运行 --resume` 来进行持续性配置更改的 Caddy API 模式。 请注意，任何Caddyfile 加载都将替换所有先前的配置，因此`caddy-api\`无法按照这种传统方式进行配置。

## 高级配置

有时，您可能需要在站点根目录混合静态文件和处理程序以获取更干净的 URL。 在 Sanic, 您使用 `app.static("/", "static", index="index.html")` 来实现这一点。 然而，为了提高性能，您可以卸载静态文件到 Cadd：

```
app.example.com {
    # Look for static files first, proxy to Sanic if not found
    route {
        file_server {
            root /srv/sanicexample/static
            precompress br                     # brotli your large scripts and styles
            pass_thru
        }
        reverse_proxy unix//tmp/sanic.socket   # sanic --unix /tmp/sanic.socket
    }
}
```

更多选项请参阅[Caddy documentation](https://caddyserver.com/docs/)。
