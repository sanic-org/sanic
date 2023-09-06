# Application Mounting

> How do I mount my application at some path above the root?

```python
# server.py
from sanic import Sanic, text

app = Sanic("app")
app.config.SERVER_NAME = "example.com/api"

@app.route("/foo")
def handler(request):
    url = app.url_for("handler", _external=True)
    return text(f"URL: {url}")
```

```yaml
# docker-compose.yml
version: "3.7"
services:
  app:
    image: nginx:alpine
    ports:
      - 80:80
    volumes:
      - type: bind
        source: ./conf
        target: /etc/nginx/conf.d/default.conf
```

```nginx
# conf
server {
    listen 80;

    # Computed data service
    location /api/ {
        proxy_pass http://<YOUR IP ADDRESS>:9999/;
        proxy_set_header Host example.com;
    }
}
```
```bash
$ docker-compose up -d
$ sanic server.app --port=9999 --host=0.0.0.0
```
```bash
$ curl localhost/api/foo
URL: http://example.com/api/foo
```
