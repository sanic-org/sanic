# Nginx デプロイ

## はじめに

Sanicはインターネット上で直接実行することができますが、Nginxなどのプロキシ
サーバーをその前に使用すると便利です。 This is particularly useful for running
multiple virtual hosts on the same IP, serving NodeJS or other services beside
a single Sanic app, and it also allows for efficient serving of static files.
TLS と HTTP/2 は、このようなプロキシでも容易に実装されています。

Sanicアプリは127.0.0でローカルでのみ動作するように設定しています。 :8001, 一方、
Nginx のインストールは、ドメインの example.com 上のパブリック インターネット
にサービスを提供する責任があります。 スタティックファイルは最大
パフォーマンスのためにNginxによって提供されます。

## プロキシされたサニックアプリ

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

これはシステムサービスになりますので、コードを
`/srv/sanicservice/proxied_example.py`に保存してください。

テストのために、ファイルを保存したフォルダにある `sanic` CLI を使用して、アプリをターミナルで実行します。

```bash
SANIC_FORWARDED_SECRET=_hostname sanic proxied_example --port 8001
```

Sanic config `FORWARDED_SECRET`を用意して、リモートアドレスから
取得するプロキシを特定します。 ローカルホスト名の前にある `_` に注意してください。
This gives basic protection against users spoofing these headers and faking
their IP addresses and more.

## SSL 証明書

Certbotをインストールし、すべてのドメインの証明書を取得してください。 これは、指定されたドメイン名を制御することを確認するために、しばらくの間、ポート80上で独自のWebサーバーを起動します。

```bash
certbot -d example.com -d www.example.com
```

## Nginx 設定

高速な透過プロキシを許可するには、非常に多くの構成が必要です しかし、ほとんどの場合、
は修正する必要はありません。

.. tip:: メモ

```
Separate upstream section, rather than simply adding the IP after `proxy_pass`
as in most tutorials, is needed for HTTP keep-alive. We also enable streaming,
WebSockets and Nginx serving static files.
```

The following config goes inside the `http` section of `nginx.conf` or if your
system uses multiple config files, `/etc/nginx/sites-available/default` or
your own files (be sure to symlink them to `sites-enabled`):

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

変更を有効にするためにNginxを起動または再起動します。 例えば、

```bash
systemctl restart nginx
```

`https://example.com`でアプリを接続できます。 Any 404
errors and such will be handled by Sanic's error pages, and whenever a static
file is present at a given path, it will be served by Nginx.

## サービスとして実行中

この部分は `systemd` に基づいたLinuxディストリビューション用です。 Create a unit file
`/etc/systemd/system/sanicexample.service`

```
[Unit]
Description=Sanic Example

[Service]
DynamicUser=Yes
WorkingDirectory=/srv/sanicservice
Environment=SANIC_PROXY_SECRET=_hostname
ExecStart=sanic proxied_example --port 8001 --fast
Restart=always

[Install]
WantedBy=multi-user.target
```

次に、サービスファイルを再読み込みし、サービスを開始し、起動時に有効にします:

```bash
systemctl daemon-reload
systemctl start sanicexample
systemctl enable sanicexample
```

.. tip:: メモ

```
簡潔さのために、別のユーザアカウントとPython仮想環境のセットアップをスキップしたり、アプリケーションをPythonモジュールとしてインストールしたりしました。 Sanicにも簡単に適用できる他のトピックについても良いチュートリアルがあります。 DynamicUser設定は強力なサンドボックスを作成します。これは、アプリケーションがファイルにデータを保存できないことを意味します。 その代わりに、`User=sanicexample` を設定することを考えてみましょう。
```

