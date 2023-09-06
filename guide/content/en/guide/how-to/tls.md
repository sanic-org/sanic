# TLS/SSL/HTTPS

> How do I run Sanic via HTTPS? 

If you do not have TLS certificates yet, [see the end of this page](./tls.md#get-certificates-for-your-domain-names).

## Single domain and single certificate

.. column::

    Let Sanic automatically load your certificate files, which need to be named `fullchain.pem` and `privkey.pem` in the given folder:

.. column::

    ```sh
    sudo sanic myserver:app -H :: -p 443 \
      --tls /etc/letsencrypt/live/example.com/
    ```
    ```python
    app.run("::", 443, ssl="/etc/letsencrypt/live/example.com/")
    ```


.. column::

    Or, you can pass cert and key filenames separately as a dictionary:

    Additionally, `password` may be added if the key is encrypted, all fields except for the password are passed to `request.conn_info.cert`.

.. column::

    ```python
    ssl = {
        "cert": "/path/to/fullchain.pem",
        "key": "/path/to/privkey.pem",
        "password": "for encrypted privkey file",   # Optional
    }
    app.run(host="0.0.0.0", port=8443, ssl=ssl)
    ```


.. column::

    Alternatively, [`ssl.SSLContext`](https://docs.python.org/3/library/ssl.html) may be passed, if you need full control over details such as which crypto algorithms are permitted. By default Sanic only allows secure algorithms, which may restrict access from very old devices.

.. column::

    ```python
    import ssl

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain("certs/fullchain.pem", "certs/privkey.pem")

    app.run(host="0.0.0.0", port=8443, ssl=context)
    ```


## Multiple domains with separate certificates

.. column::

    A list of multiple certificates may be provided, in which case Sanic chooses the one matching the hostname the user is connecting to. This occurs so early in the TLS handshake that Sanic has not sent any packets to the client yet.

    If the client sends no SNI (Server Name Indication), the first certificate on the list will be used even though on the client browser it will likely fail with a TLS error due to name mismatch. To prevent this fallback and to cause immediate disconnection of clients without a known hostname, add `None` as the first entry on the list. `--tls-strict-host` is the equivalent CLI option.

.. column::

    ```python
    ssl = ["certs/example.com/", "certs/bigcorp.test/"]
    app.run(host="0.0.0.0", port=8443, ssl=ssl)
    ```
    ```sh
    sanic myserver:app
        --tls certs/example.com/
        --tls certs/bigcorp.test/
        --tls-strict-host
    ```

.. tip:: 

    You may also use `None` in front of a single certificate if you do not wish to reveal your certificate, true hostname or site content to anyone connecting to the IP address instead of the proper DNS name.

.. column::

    Dictionaries can be used on the list. This allows also specifying which domains a certificate matches to, although the names present on the certificate itself cannot be controlled from here. If names are not specified, the names from the certificate itself are used.

    To only allow connections to the main domain **example.com** and only to subdomains of **bigcorp.test**:

.. column::

    ```python
    ssl = [
        None,  # No fallback if names do not match!
        {
            "cert": "certs/example.com/fullchain.pem",
            "key": "certs/example.com/privkey.pem",
            "names": ["example.com", "*.bigcorp.test"],
        }
    ]
    app.run(host="0.0.0.0", port=8443, ssl=ssl)
    ```

## Accessing TLS information in handlers via `request.conn_info` fields

* `.ssl` - is the connection secure (bool)
* `.cert` - certificate info and dict fields of the currently active cert (dict)
* `.server_name` - the SNI sent by the client (str, may be empty)

Do note that all `conn_info` fields are per connection, where there may be many requests over time. If a proxy is used in front of your server, these requests on the same pipe may even come from different users.

## Redirect HTTP to HTTPS, with certificate requests still over HTTP

In addition to your normal server(s) running HTTPS, run another server for redirection, `http_redir.py`:

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

It is best to setup this as a systemd unit separate of your HTTPS servers. You may need to run HTTP while initially requesting your certificates, while you cannot run the HTTPS server yet. Start for IPv4 and IPv6:

```
sanic http_redir:app -H 0.0.0.0 -p 80
sanic http_redir:app -H :: -p 80
```

Alternatively, it is possible to run the HTTP redirect application from the main application:

```python
# app == Your main application
# redirect == Your http_redir application
@app.before_server_start
async def start(app, _):
    app.ctx.redirect = await redirect.create_server(
        port=80, return_asyncio_server=True
    )
    app.add_task(runner(redirect, app.ctx.redirect))

@app.before_server_stop
async def stop(app, _):
    await app.ctx.redirect.close()

async def runner(app, app_server):
    app.is_running = True
    try:
        app.signalize()
        app.finalize()
        app.state.is_started = True
        await app_server.serve_forever()
    finally:
        app.is_running = False
        app.is_stopping = True
```

## Get certificates for your domain names

You can get free certificates from [Let's Encrypt](https://letsencrypt.org/). Install [certbot](https://certbot.eff.org/) via your package manager, and request a certificate:

```sh
sudo certbot certonly --key-type ecdsa --preferred-chain "ISRG Root X1" -d example.com -d www.example.com
```

Multiple domain names may be added by further `-d` arguments, all stored into a single certificate which gets saved to `/etc/letsencrypt/live/example.com/` as per **the first domain** that you list here.

The key type and preferred chain options are necessary for getting a minimal size certificate file, essential for making your server run as *fast* as possible. The chain will still contain one RSA certificate until when Let's Encrypt gets their new EC chain trusted in all major browsers.
