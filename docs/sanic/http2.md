# HTTP/2

HTTP/2 support is experimental and requires SSL be enabled, and OpenSSL be version 1.0.2 or greater.

```python
import ssl

from sanic import Sanic
app = Sanic(__name__)

context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain("/path/to/cert", keyfile="/path/to/keyfile")

app.run(host="0.0.0.0", port=8443, ssl=context, http2=True)
```
