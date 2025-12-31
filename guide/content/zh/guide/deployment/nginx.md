# Nginx 部署

## 一. 导言

虽然Sanic可以直接在互联网上运行，但在互联网前使用代理
服务器可能是有用的，例如Nginx。 这对于运行同一IP上的
多个虚拟主机特别有用， 服务于NodeJS或除了
单个Sanic应用之外的其他服务，并且它还允许有效地服务于静态文件。
TLS和HTTP-2也很容易在这种代理上执行。

我们正在设置 Sanic 应用程序仅在本地服务为127.0.0。 :8001，
Nginx 安装负责为域示例.com上的公共互联网
提供服务。 静态文件将由Nginx提供最大
性能。

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

由于这是一个系统服务，将您的代码保存到
`/srv/sanicservice/proxied_example.py`。

为测试，使用你保存文件的文件夹中的 `sanic` CLI 在终端中运行你的应用程序。

```bash
SANIC_FORWARDED_SECRET=_hostname sanic proxied_example --端口 8001
```

We provide Sanic config `FORWARDED_SECRET` to identify which proxy it gets
the remote addresses from. 请注意本地主机名前面的`_` 。
这提供了基本的保护，免受那些假冒头头并传真到
他们的IP地址等用户的伤害。

## SSL 证书

安装 Certbot 并获得您所有域的节拍。 这将会在80端口上增加它自己的web服务器，以验证您控制给定的域名。

```bash
certbot -d example.com -d www.example.com
```

## Nginx 配置

需要很多配置才能快速透明的代理， 但
大部分情况下不需要修改这些内容，所以与我休戚与共。

.. 提示：备注

```
HTTP keep-live需要分隔上游部分，而不是像大多数教程中那样只是在"proxy_pass"
之后添加IP。 我们还启用了串流，
WebSockets 和 Nginx 服务于静态文件。
```

以下配置在 `nginx 的 `http` 部分内。 开启或如果您的
系统使用多个配置文件，`/etc/nginx/sites-available/default` 或
您自己的文件(肯定要将它们与`sites-enabled\`链接)：

```nginx
# Files managed by Certbot
ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

# Sanic service
upstream example.com {
  keepalive 100;
  server 127.0.0.1:8001;
  #server unix:/tmp//sanic.sock;
}

server {
  server_name example.com;
  listen 443 ssl http2 default_server;
  listen [::]:443 ssl http2 default_server;
  # Serve static files if found, otherwise proxy to Sanic
  location / {
    root /srv/sanicexample/static;
    try_files $uri @sanic;
  }
  location @sanic {
    proxy_pass http://$server_name;
    # Allow fast streaming HTTP/1.1 pipes (keep-alive, unbuffered)
    proxy_http_version 1.1;
    proxy_request_buffering off;
    proxy_buffering off;
    proxy_set_header forwarded 'by=\"_$hostname\";$for_addr;proto=$scheme;host=\"$http_host\"';
    # Allow websockets and keep-alive (avoid connection: close)
    proxy_set_header connection "upgrade";
    proxy_set_header upgrade $http_upgrade;
  }
}

# Redirect WWW to no-WWW
server {
  listen 443 ssl http2;
  listen [::]:443 ssl http2;
  server_name ~^www\.(.*)$;
  return 308 $scheme://$1$request_uri;
}

# Redirect all HTTP to HTTPS with no-WWW
server {
  listen 80 default_server;
  listen [::]:80 default_server;
  server_name ~^(?:www\.)?(.*)$;
  return 308 https://$1$request_uri;
}

# Forwarded for= client IP address formatting
map $remote_addr $for_addr {
  ~^[0-9.]+$          "for=$remote_addr";        # IPv4 client address
  ~^[0-9A-Fa-f:.]+$   "for=\"[$remote_addr]\"";  # IPv6 bracketed and quoted
  default             "for=unknown";             # Unix socket
}
```

启动或重启 Nginx 以使更改生效。 例如：

```bash
systemctl 重启 nginx
```

您应该能够在 `https://example.com` 上连接您的应用程序。 任何 404
错误将通过 Sanic's 错误页面处理， 并且当静态
文件存在于给定路径时，它将由Nginx提供服务。

## 作为服务运行

本部分是基于 `systemd` 的 Linux 发行版。 创建一个单位文件
`/etc/systemd/system/sanicexample.service`

```
[Unit]
描述=Sanic 示例

[Service]
动态用户=是
WorkingDirectory=/srv/sanicservice
Environment=SANIC_PROXY_SECRET=_hostname
ExecStart=sanic proxied_example --porter 8001 --fast
Restart=始终

[Install]
WantedBy=multi-user.target。
```

然后重新加载服务文件，启动您的服务并在启动时启用它：

```bash
systemctl daemon-reload
systemctl start sanicexample
systemctl 启用sanicexample
```

.. 提示：备注

```
为简洁起见，我们跳过了设置一个单独的用户帐户和 Python 虚拟环境或将您的应用程序安装为 Python 模块。 其他地方也有很好的关于这些题目的教程，很容易应用于萨尼克。 动态用户设置创建了一个强大的沙盒，基本上意味着您的应用程序不能将其数据存储在文件中， 所以，如果您需要，您可以考虑设置 `User=sanicexplle` 。
```

