# Nginx Deployment

## Introduction

Although Sanic can be run directly on Internet, it may be useful to use a proxy
server such as Nginx in front of it. This is particularly useful for running
multiple virtual hosts on the same IP, serving NodeJS or other services beside
a single Sanic app, and it also allows for efficient serving of static files.
TLS and HTTP/2 are also easily implemented on such proxy.

We are setting the Sanic app to serve only locally at 127.0.0.1:8001, while the
Nginx installation is responsible for providing the service to public Internet
on domain example.com. Static files will be served by Nginx for maximal
performance.

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

Since this is going to be a system service, save your code to
`/srv/sanicservice/proxied_example.py`.

For testing, run your app in a terminal using the `sanic` CLI in the folder where you saved the file.

```bash
SANIC_FORWARDED_SECRET=_hostname sanic proxied_example --port 8001
```

We provide Sanic config `FORWARDED_SECRET` to identify which proxy it gets
the remote addresses from. Note the `_` in front of the local hostname.
This gives basic protection against users spoofing these headers and faking
their IP addresses and more.

## SSL certificates

Install Certbot and obtain a certicate for all your domains. This will spin up its own webserver on port 80 for a moment to verify you control the given domain names.

```bash
certbot -d example.com -d www.example.com
```

## Nginx configuration

Quite much configuration is required to allow fast transparent proxying, but
for the most part these don't need to be modified, so bear with me.


.. tip:: Note

    Separate upstream section, rather than simply adding the IP after `proxy_pass`
    as in most tutorials, is needed for HTTP keep-alive. We also enable streaming,
    WebSockets and Nginx serving static files.


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

Start or restart Nginx for changes to take effect. E.g.

```bash
systemctl restart nginx
```

You should be able to connect your app on `https://example.com`. Any 404
errors and such will be handled by Sanic's error pages, and whenever a static
file is present at a given path, it will be served by Nginx.

## Running as a service

This part is for Linux distributions based on `systemd`. Create a unit file
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

Then reload service files, start your service and enable it on boot:

```bash
systemctl daemon-reload
systemctl start sanicexample
systemctl enable sanicexample
```


.. tip:: Note

    For brevity we skipped setting up a separate user account and a Python virtual environment or installing your app as a Python module. There are good tutorials on those topics elsewhere that easily apply to Sanic as well. The DynamicUser setting creates a strong sandbox which basically means your application cannot store its data in files, so you may consider setting `User=sanicexample` instead if you need that.

