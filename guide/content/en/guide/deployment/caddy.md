# Caddy Deployment

## Introduction

Caddy is a state-of-the-art web server and proxy that supports up to HTTP/3. Its simplicity lies in its minimalistic configuration and the inbuilt ability to automatically procure TLS certificates for your domains from Let's Encrypt. In this setup, we will configure the Sanic application to serve locally at 127.0.0.1:8001, with Caddy playing the role of the public-facing server for the domain example.com.

You may install Caddy from your favorite package menager on Windows, Linux and Mac. The package is named `caddy`.

## Proxied Sanic app

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

To run this application, save as `proxied_example.py`, and use the sanic command-line interface as follows:

```bash
SANIC_PROXIES_COUNT=1 sanic proxied_example --port 8001
```

Setting the SANIC_PROXIES_COUNT environment variable instructs Sanic to trust the X-Forwarded-* headers sent by Caddy, allowing it to correctly identify the client's IP address and other information.

## Caddy is simple

If you have no other web servers running, you can simply run Caddy CLI (needs `sudo` on Linux):

```bash
caddy reverse-proxy --from example.com --to :8001
```

This is a complete server that includes a certificate for your domain, http-to-https redirect, proxy headers, streaming and WebSockets. Your Sanic application should now be available on the domain you specified by HTTP versions 1, 2 and 3. Remember to open up UDP/443 on your firewall to enable H3 communications.

All done?

Soon enough you'll be needing more than one server, or more control over details, which is where the configuration files come in. The above command is equivalent to this `Caddyfile`, serving as a good starting point for your install:

```
example.com {
    reverse_proxy localhost:8001
}
```

Some Linux distributions install Caddy such that it reads configuration from `/etc/caddy/Caddyfile`, which `import /etc/caddy/conf.d/*` for each site you are running. If not, you'll need to manually run `caddy run` as a system service, pointing it at the proper config file. Alternatively, use Caddy API mode with `caddy run --resume` for persistent config changes. Note that any Caddyfile loading will replace all prior configuration and thus `caddy-api` is not configurable in this traditional manner.

## Advanced configuration

At times, you might need to mix static files and handlers at the site root for cleaner URLs. In Sanic, you'd use `app.static("/", "static", index="index.html")` to achieve this. However, for improved performance, you can offload serving static files to Caddy:

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

Please refer to [Caddy documentation](https://caddyserver.com/docs/) for more options.
