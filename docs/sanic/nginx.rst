
.. _nginx:

Nginx Deployment
================

Introduction
~~~~~~~~~~~~

Although Sanic can be run directly on Internet, it may be useful to use a proxy
server such as Nginx in front of it. This is particularly useful for running
multiple virtual hosts on the same IP, serving NodeJS or other services beside
a single Sanic app, and it also allows for efficient serving of static files.
SSL and HTTP/2 are also easily implemented on such proxy.

We are setting the Sanic app to serve only locally at `127.0.0.1:8000`, while the
Nginx installation is responsible for providing the service to public Internet
on domain `example.com`. Static files will be served from `/var/www/`.


Proxied Sanic app
~~~~~~~~~~~~~~~~~

The app needs to be setup with a secret key used to identify a trusted proxy,
so that real client IP and other information can be identified. This protects
against anyone on the Internet sending fake headers to spoof their IP addresses
and other details. Choose any random string and configure it both on the app
and in Nginx config.

.. code-block:: python

    from sanic import Sanic
    from sanic.response import text

    app = Sanic("proxied_example")
    app.config.FORWARDED_SECRET = "YOUR SECRET"

    @app.get("/")
    def index(request):
        # This should display external (public) addresses:
        return text(
            f"{request.remote_addr} connected to {request.url_for('index')}\n"
            f"Forwarded: {request.forwarded}\n"
        )

    if __name__ == '__main__':
        app.run(host='127.0.0.1', port=8000, workers=8, access_log=False)

Since this is going to be a system service, save your code to
`/srv/sanicexample/sanicexample.py`.

For testing, run your app in a terminal.


Nginx configuration
~~~~~~~~~~~~~~~~~~~

Quite much configuration is required to allow fast transparent proxying, but
for the most part these don't need to be modified, so bear with me.

Upstream servers need to be configured in a separate `upstream` block to enable
HTTP keep-alive, which can drastically improve performance, so we use this
instead of directly providing an upstream address in `proxy_pass` directive. In
this example, the upstream section is named by `server_name`, i.e. the public
domain name, which then also gets passed to Sanic in the `Host` header. You may
change the naming as you see fit. Multiple servers may also be provided for
load balancing and failover.

Change the two occurrences of `example.com` to your true domain name, and
instead of `YOUR SECRET` use the secret you chose for your app.

::

    upstream example.com {
      keepalive 100;
      server 127.0.0.1:8000;
      #server unix:/tmp/sanic.sock;
    }

    server {
      server_name example.com;
      listen 443 ssl http2 default_server;
      listen [::]:443 ssl http2 default_server;
      # Serve static files if found, otherwise proxy to Sanic
      location / {
        root /var/www;
        try_files $uri @sanic;
      }
      location @sanic {
        proxy_pass http://$server_name;
        # Allow fast streaming HTTP/1.1 pipes (keep-alive, unbuffered)
        proxy_http_version 1.1;
        proxy_request_buffering off;
        proxy_buffering off;
        # Proxy forwarding (password configured in app.config.FORWARDED_SECRET)
        proxy_set_header forwarded "$proxy_forwarded;secret=\"YOUR SECRET\"";
        # Allow websockets
        proxy_set_header connection "upgrade";
        proxy_set_header upgrade $http_upgrade;
      }
    }

To avoid cookie visibility issues and inconsistent addresses on search engines,
it is a good idea to redirect all visitors to one true domain, always using
HTTPS:

::

    # Redirect all HTTP to HTTPS with no-WWW
    server {
      listen 80 default_server;
      listen [::]:80 default_server;
      server_name ~^(?:www\.)?(.*)$;
      return 301 https://$1$request_uri;
    }

    # Redirect WWW to no-WWW
    server {
      listen 443 ssl http2;
      listen [::]:443 ssl http2;
      server_name ~^www\.(.*)$;
      return 301 $scheme://$1$request_uri;
    }

The above config sections may be placed in `/etc/nginx/sites-available/default`
or in other site configs (be sure to symlink them to `sites-enabled` if you
create new ones).

Make sure that your SSL certificates are configured in the main config, or
add the `ssl_certificate` and `ssl_certificate_key` directives to each
`server` section that listens on SSL.

Additionally, copy&paste all of this into `nginx/conf.d/forwarded.conf`:

::

    # RFC 7239 Forwarded header for Nginx proxy_pass

    # Add within your server or location block:
    #    proxy_set_header forwarded "$proxy_forwarded;secret=\"YOUR SECRET\"";

    # Configure your upstream web server to identify this proxy by that password
    # because otherwise anyone on the Internet could spoof these headers and fake
    # their real IP address and other information to your service.


    # Provide the full proxy chain in $proxy_forwarded
    map $proxy_add_forwarded $proxy_forwarded {
      default "$proxy_add_forwarded;by=\"_$hostname\";proto=$scheme;host=\"$http_host\";path=\"$request_uri\"";
    }

    # The following mappings are based on
    # https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/

    map $remote_addr $proxy_forwarded_elem {
      # IPv4 addresses can be sent as-is
      ~^[0-9.]+$          "for=$remote_addr";

      # IPv6 addresses need to be bracketed and quoted
      ~^[0-9A-Fa-f:.]+$   "for=\"[$remote_addr]\"";

      # Unix domain socket names cannot be represented in RFC 7239 syntax
      default             "for=unknown";
    }

    map $http_forwarded $proxy_add_forwarded {
      # If the incoming Forwarded header is syntactically valid, append to it
      "~^(,[ \\t]*)*([!#$%&'*+.^_`|~0-9A-Za-z-]+=([!#$%&'*+.^_`|~0-9A-Za-z-]+|\"([\\t \\x21\\x23-\\x5B\\x5D-\\x7E\\x80-\\xFF]|\\\\[\\t \\x21-\\x7E\\x80-\\xFF])*\"))?(;([!#$%&'*+.^_`|~0-9A-Za-z-]+=([!#$%&'*+.^_`|~0-9A-Za-z-]+|\"([\\t \\x21\\x23-\\x5B\\x5D-\\x7E\\x80-\\xFF]|\\\\[\\t \\x21-\\x7E\\x80-\\xFF])*\"))?)*([ \\t]*,([ \\t]*([!#$%&'*+.^_`|~0-9A-Za-z-]+=([!#$%&'*+.^_`|~0-9A-Za-z-]+|\"([\\t \\x21\\x23-\\x5B\\x5D-\\x7E\\x80-\\xFF]|\\\\[\\t \\x21-\\x7E\\x80-\\xFF])*\"))?(;([!#$%&'*+.^_`|~0-9A-Za-z-]+=([!#$%&'*+.^_`|~0-9A-Za-z-]+|\"([\\t \\x21\\x23-\\x5B\\x5D-\\x7E\\x80-\\xFF]|\\\\[\\t \\x21-\\x7E\\x80-\\xFF])*\"))?)*)?)*$" "$http_forwarded, $proxy_forwarded_elem";

      # Otherwise, replace it
      default "$proxy_forwarded_elem";
    }

For installs that don't use `conf.d` and `sites-available`, all of the above
configs may also be placed inside the `http` section of the main `nginx.conf`.

Reload Nginx config after changes:

::

    sudo nginx -s reload

Now you should be able to connect your app on `https://example.com/`. Any 404
errors and such will be handled by Sanic's error pages, and whenever a static
file is present at a given path, it will be served by Nginx.


SSL certificates
~~~~~~~~~~~~~~~~

If you haven't already configured valid certificates on your server, now is a
good time to do so. Install `certbot` and `python3-certbot-nginx`, then run

::

    certbot --nginx -d example.com -d www.example.com

`<https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/>`_

Running as a service
~~~~~~~~~~~~~~~~~~~~

This part is for Linux distributions based on `systemd`. Create a unit file
`/etc/systemd/system/sanicexample.service`::

    [Unit]
    Description=Sanic Example

    [Service]
    User=nobody
    WorkingDirectory=/srv/sanicexample
    ExecStart=/usr/bin/env python3 sanicexample.py
    Restart=always

    [Install]
    WantedBy=multi-user.target

Then reload service files, start your service and enable it on boot::

    sudo systemctl daemon-reload
    sudo systemctl start sanicexample
    sudo systemctl enable sanicexample
