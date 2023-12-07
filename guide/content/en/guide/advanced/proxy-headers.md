# Proxy configuration

When you use a reverse proxy server (e.g. nginx), the value of `request.ip` will contain the IP of a proxy, typically `127.0.0.1`. Almost always, this is **not** what you will want.

Sanic may be configured to use proxy headers for determining the true client IP, available as `request.remote_addr`. The full external URL is also constructed from header fields _if available_.


.. tip:: Heads up

    Without proper precautions, a malicious client may use proxy headers to spoof its own IP. To avoid such issues, Sanic does not use any proxy headers unless explicitly enabled.



.. column::

    Services behind reverse proxies must configure one or more of the following [configuration values](/guide/deployment/configuration.md):

    - `FORWARDED_SECRET`
    - `REAL_IP_HEADER`
    - `PROXIES_COUNT`

.. column::

    ```python
    app.config.FORWARDED_SECRET = "super-duper-secret"
    app.config.REAL_IP_HEADER = "CF-Connecting-IP"
    app.config.PROXIES_COUNT = 2
    ```

## Forwarded header

In order to use the `Forwarded` header, you should set `app.config.FORWARDED_SECRET` to a value known to the trusted proxy server. The secret is used to securely identify a specific proxy server.

Sanic ignores any elements without the secret key, and will not even parse the header if no secret is set.

All other proxy headers are ignored once a trusted forwarded element is found, as it already carries complete information about the client.

To learn more about the `Forwarded` header, read the related [MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Forwarded) and [Nginx](https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/) articles.

## Traditional proxy headers

### IP Headers

When your proxy forwards you the IP address in a known header, you can tell Sanic what that is with the `REAL_IP_HEADER` config value.

### X-Forwarded-For

This header typically contains a chain of IP addresses through each layer of a proxy. Setting `PROXIES_COUNT` tells Sanic how deep to look to get an actual IP address for the client. This value should equal the _expected_ number of IP addresses in the chain.

### Other X-headers

If a client IP is found by one of these methods, Sanic uses the following headers for URL parts:

- x-forwarded-proto
- x-forwarded-host
- x-forwarded-port
- x-forwarded-path
- x-scheme

## Examples

In the following examples, all requests will assume that the endpoint looks like this:
```python
@app.route("/fwd")
async def forwarded(request):
    return json(
        {
            "remote_addr": request.remote_addr,
            "scheme": request.scheme,
            "server_name": request.server_name,
            "server_port": request.server_port,
            "forwarded": request.forwarded,
        }
    )
```

---

##### Example 1

Without configured FORWARDED_SECRET, x-headers should be respected

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=1.1.1.1, for=injected;host=", for="[::2]";proto=https;host=me.tld;path="/app/";secret=mySecret,for=broken;;secret=b0rked, for=127.0.0.3;scheme=http;port=1234' \
	-H "X-Real-IP: 127.0.0.2" \
	-H "X-Forwarded-For: 127.0.1.1" \
	-H "X-Scheme: ws" \
	-H "Host: local.site" | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "127.0.0.2",
      "scheme": "ws",
      "server_name": "local.site",
      "server_port": 80,
      "forwarded": {
        "for": "127.0.0.2",
        "proto": "ws"
      }
    }
    ```

---

##### Example 2

FORWARDED_SECRET now configured

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=1.1.1.1, for=injected;host=", for="[::2]";proto=https;host=me.tld;path="/app/";secret=mySecret,for=broken;;secret=b0rked, for=127.0.0.3;scheme=http;port=1234' \
	-H "X-Real-IP: 127.0.0.2" \
	-H "X-Forwarded-For: 127.0.1.1" \
	-H "X-Scheme: ws" \
	-H "Host: local.site" | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "mySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "[::2]",
      "scheme": "https",
      "server_name": "me.tld",
      "server_port": 443,
      "forwarded": {
        "for": "[::2]",
        "proto": "https",
        "host": "me.tld",
        "path": "/app/",
        "secret": "mySecret"
      }
    }
    ```

---

##### Example 3

Empty Forwarded header -> use X-headers

```sh
curl localhost:8000/fwd \
	-H "X-Real-IP: 127.0.0.2" \
	-H "X-Forwarded-For: 127.0.1.1" \
	-H "X-Scheme: ws" \
	-H "Host: local.site" | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "mySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "127.0.0.2",
      "scheme": "ws",
      "server_name": "local.site",
      "server_port": 80,
      "forwarded": {
        "for": "127.0.0.2",
        "proto": "ws"
      }
    }
    ```

---

##### Example 4

Header present but not matching anything

```sh
curl localhost:8000/fwd \
	-H "Forwarded: nomatch" | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "mySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "",
      "scheme": "http",
      "server_name": "localhost",
      "server_port": 8000,
      "forwarded": {}
    }

    ```

---

##### Example 5

Forwarded header present but no matching secret -> use X-headers

```sh
curl localhost:8000/fwd \
	-H "Forwarded: for=1.1.1.1;secret=x, for=127.0.0.1" \
	-H "X-Real-IP: 127.0.0.2" | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "mySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "127.0.0.2",
      "scheme": "http",
      "server_name": "localhost",
      "server_port": 8000,
      "forwarded": {
        "for": "127.0.0.2"
      }
    }
    ```

---

##### Example 6

Different formatting and hitting both ends of the header

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: Secret="mySecret";For=127.0.0.4;Port=1234' | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "mySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "127.0.0.4",
      "scheme": "http",
      "server_name": "localhost",
      "server_port": 1234,
      "forwarded": {
        "secret": "mySecret",
        "for": "127.0.0.4",
        "port": 1234
      }
    }
    ```

---

##### Example 7

Test escapes (modify this if you see anyone implementing quoted-pairs)

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=test;quoted="\,x=x;y=\";secret=mySecret' | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "mySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "test",
      "scheme": "http",
      "server_name": "localhost",
      "server_port": 8000,
      "forwarded": {
        "for": "test",
        "quoted": "\\,x=x;y=\\",
        "secret": "mySecret"
      }
    }
    ```

---

##### Example 8

Secret insulated by malformed field #1

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=test;secret=mySecret;b0rked;proto=wss;' | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "mySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "test",
      "scheme": "http",
      "server_name": "localhost",
      "server_port": 8000,
      "forwarded": {
        "for": "test",
        "secret": "mySecret"
      }
    }
    ```

---

##### Example 9

Secret insulated by malformed field #2

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=test;b0rked;secret=mySecret;proto=wss' | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "mySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "",
      "scheme": "wss",
      "server_name": "localhost",
      "server_port": 8000,
      "forwarded": {
        "secret": "mySecret",
        "proto": "wss"
      }
    }
    ```

---

##### Example 10

Unexpected termination should not lose existing acceptable values

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: b0rked;secret=mySecret;proto=wss' | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "mySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "",
      "scheme": "wss",
      "server_name": "localhost",
      "server_port": 8000,
      "forwarded": {
        "secret": "mySecret",
        "proto": "wss"
      }
    }
    ```

---

##### Example 11

Field normalization

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: PROTO=WSS;BY="CAFE::8000";FOR=unknown;PORT=X;HOST="A:2";PATH="/With%20Spaces%22Quoted%22/sanicApp?key=val";SECRET=mySecret' | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "mySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "",
      "scheme": "wss",
      "server_name": "a",
      "server_port": 2,
      "forwarded": {
        "proto": "wss",
        "by": "[cafe::8000]",
        "host": "a:2",
        "path": "/With Spaces\"Quoted\"/sanicApp?key=val",
        "secret": "mySecret"
      }
    }
    ```

---

##### Example 12

Using "by" field as secret

```sh
curl localhost:8000/fwd \
	-H 'Forwarded: for=1.2.3.4; by=_proxySecret' | jq
```

.. column::

    ```python
    # Sanic application config
    app.config.PROXIES_COUNT = 1
    app.config.REAL_IP_HEADER = "x-real-ip"
    app.config.FORWARDED_SECRET = "_proxySecret"
    ```

.. column::

    ```bash
    # curl response
    {
      "remote_addr": "1.2.3.4",
      "scheme": "http",
      "server_name": "localhost",
      "server_port": 8000,
      "forwarded": {
        "for": "1.2.3.4",
        "by": "_proxySecret"
      }
    }

    ```

