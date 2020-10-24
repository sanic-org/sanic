Configuration
=============

Any reasonably complex application will need configuration that is not baked into the actual code. Settings might be different for different environments or installations.

Basics
------

Sanic holds the configuration in the `config` attribute of the application object. The configuration object is merely an object that can be modified either using dot-notation or like a dictionary:

.. code-block:: python

    app = Sanic('myapp')
    app.config.DB_NAME = 'appdb'
    app.config['DB_USER'] = 'appuser'

Since the config object has a type that inherits from dictionary, you can use its ``update`` method in order to set several values at once:

.. code-block:: python

    db_settings = {
        'DB_HOST': 'localhost',
        'DB_NAME': 'appdb',
        'DB_USER': 'appuser'
    }
    app.config.update(db_settings)

In general the convention is to only have UPPERCASE configuration parameters. The methods described below for loading configuration only look for such uppercase parameters.

Loading Configuration
---------------------

There are several ways how to load configuration.

From Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~

Any variables defined with the `SANIC_` prefix will be applied to the sanic config. For example, setting `SANIC_REQUEST_TIMEOUT` will be loaded by the application automatically and fed into the `REQUEST_TIMEOUT` config variable. You can pass a different prefix to Sanic:

.. code-block:: python

    app = Sanic(__name__, load_env='MYAPP_')

Then the above variable would be `MYAPP_REQUEST_TIMEOUT`. If you want to disable loading from environment variables you can set it to `False` instead:

.. code-block:: python

    app = Sanic(__name__, load_env=False)   

From file, dict, or any object (having __dict__ attribute).
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can store app configurations in: (1) a Python file, (2) a dictionary, or (3) in some other type of custom object.

In order to load configuration from ove of those, you can use ``app.upload_config()``.

**1) From file**


Let's say you have ``my_config.py`` file that looks like this:

.. code-block:: python

    # my_config.py
    A = 1
    B = 2

Loading config from this file is as easy as:

.. code-block:: python

    app.update_config("/path/to/my_config.py")
 
You can also use environment variables in the path name here.

Let's say you have an environment variable like this:

.. code-block:: shell

    $ export my_path="/path/to"
    
Then you can use it like this:

.. code-block:: python

    app.update_config("${my_path}/my_config.py")

.. note::

    Just remember that you have to provide environment variables in the format ${environment_variable} and that $environment_variable is not expanded (is treated as "plain" text).

**2) From dict**

You can also set your app config by providing a ``dict``:

.. code-block:: python

    d = {"A": 1, "B": 2}
    
    app.update_config(d)
 
**3) From _any_ object**

App config can be taken from an object. Internally, it uses ``__dict__`` to retrieve keys and values.

For example, pass the class:

.. code-block:: python

    class C:
        A = 1
        B = 2
        
    app.update_config(C)

or, it can be instantiated:

.. code-block:: python

    c = C()
    
    app.update_config(c)
    
- From an object (having __dict__ attribute)


From an Object
~~~~~~~~~~~~~~

.. note::

     Deprecated, will be removed in version 21.3.

If there are a lot of configuration values and they have sensible defaults it might be helpful to put them into a module:

.. code-block:: python

    import myapp.default_settings

    app = Sanic('myapp')
    app.config.from_object(myapp.default_settings)

or also by path to config:

.. code-block:: python

    app = Sanic('myapp')
    app.config.from_object('config.path.config.Class')

You could use a class or any other object as well.

From a File
~~~~~~~~~~~

.. note::

     Deprecated, will be removed in version 21.3.

Usually you will want to load configuration from a file that is not part of the distributed application. You can load configuration from a file using `from_pyfile(/path/to/config_file)`. However, that requires the program to know the path to the config file. So instead you can specify the location of the config file in an environment variable and tell Sanic to use that to find the config file:

.. code-block:: python

    app = Sanic('myapp')
    app.config.from_envvar('MYAPP_SETTINGS')

Then you can run your application with the `MYAPP_SETTINGS` environment variable set:

.. code-block:: python

    #$ MYAPP_SETTINGS=/path/to/config_file python3 myapp.py
    #INFO: Goin' Fast @ http://0.0.0.0:8000


The config files are regular Python files which are executed in order to load them. This allows you to use arbitrary logic for constructing the right configuration. Only uppercase variables are added to the configuration. Most commonly the configuration consists of simple key value pairs:

.. code-block:: python

    # config_file
    DB_HOST = 'localhost'
    DB_NAME = 'appdb'
    DB_USER = 'appuser'

Builtin Configuration Values
----------------------------

Out of the box there are just a few predefined values which can be overwritten when creating the application. Note that websocket configuration values will have no impact if running in ASGI mode.

+---------------------------+-------------------+-----------------------------------------------------------------------------+
| Variable                  | Default           | Description                                                                 |
+===========================+===================+=============================================================================+
| REQUEST_MAX_SIZE          | 100000000         | How big a request may be (bytes)                                            |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| REQUEST_BUFFER_QUEUE_SIZE | 100               | Request streaming buffer queue size                                         |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| REQUEST_TIMEOUT           | 60                | How long a request can take to arrive (sec)                                 |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| RESPONSE_TIMEOUT          | 60                | How long a response can take to process (sec)                               |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| KEEP_ALIVE                | True              | Disables keep-alive when False                                              |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| KEEP_ALIVE_TIMEOUT        | 5                 | How long to hold a TCP connection open (sec)                                |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| WEBSOCKET_MAX_SIZE        | 2^20              | Maximum size for incoming messages (bytes)                                  |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| WEBSOCKET_MAX_QUEUE       | 32                | Maximum length of the queue that holds incoming messages                    |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| WEBSOCKET_READ_LIMIT      | 2^16              | High-water limit of the buffer for incoming bytes                           |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| WEBSOCKET_WRITE_LIMIT     | 2^16              | High-water limit of the buffer for outgoing bytes                           |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| WEBSOCKET_PING_INTERVAL   | 20                | A Ping frame is sent every ping_interval seconds.                           |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| WEBSOCKET_PING_TIMEOUT    | 20                | Connection is closed when Pong is not received after ping_timeout seconds   |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| GRACEFUL_SHUTDOWN_TIMEOUT | 15.0              | How long to wait to force close non-idle connection (sec)                   |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| ACCESS_LOG                | True              | Disable or enable access log                                                |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| FORWARDED_SECRET          | None              | Used to securely identify a specific proxy server (see below)               |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| PROXIES_COUNT             | None              | The number of proxy servers in front of the app (e.g. nginx; see below)     |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| FORWARDED_FOR_HEADER      | "X-Forwarded-For" | The name of "X-Forwarded-For" HTTP header that contains client and proxy ip |
+---------------------------+-------------------+-----------------------------------------------------------------------------+
| REAL_IP_HEADER            |  None             | The name of "X-Real-IP" HTTP header that contains real client ip            |
+---------------------------+-------------------+-----------------------------------------------------------------------------+

The different Timeout variables:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`REQUEST_TIMEOUT`
#################

A request timeout measures the duration of time between the instant when a new open TCP connection is passed to the
Sanic backend server, and the instant when the whole HTTP request is received. If the time taken exceeds the
`REQUEST_TIMEOUT` value (in seconds), this is considered a Client Error so Sanic generates an `HTTP 408` response
and sends that to the client. Set this parameter's value higher if your clients routinely pass very large request payloads
or upload requests very slowly.

`RESPONSE_TIMEOUT`
##################

A response timeout measures the duration of time between the instant the Sanic server passes the HTTP request to the
Sanic App, and the instant a HTTP response is sent to the client. If the time taken exceeds the `RESPONSE_TIMEOUT`
value (in seconds), this is considered a Server Error so Sanic generates an `HTTP 503` response and sends that to the
client. Set this parameter's value higher if your application is likely to have long-running process that delay the
generation of a response.

`KEEP_ALIVE_TIMEOUT`
####################

What is Keep Alive? And what does the Keep Alive Timeout value do?
******************************************************************

`Keep-Alive` is a HTTP feature introduced in `HTTP 1.1`. When sending a HTTP request, the client (usually a web browser application)
can set a `Keep-Alive` header to indicate the http server (Sanic) to not close the TCP connection after it has send the response.
This allows the client to reuse the existing TCP connection to send subsequent HTTP requests, and ensures more efficient
network traffic for both the client and the server.

The `KEEP_ALIVE` config variable is set to `True` in Sanic by default. If you don't need this feature in your application,
set it to `False` to cause all client connections to close immediately after a response is sent, regardless of
the `Keep-Alive` header on the request.

The amount of time the server holds the TCP connection open is decided by the server itself.
In Sanic, that value is configured using the `KEEP_ALIVE_TIMEOUT` value. By default, it is set to 5 seconds.
This is the same default setting as the Apache HTTP server and is a good balance between allowing enough time for
the client to send a new request, and not holding open too many connections at once. Do not exceed 75 seconds unless
you know your clients are using a browser which supports TCP connections held open for that long.

For reference:

* Apache httpd server default keepalive timeout = 5 seconds
* Nginx server default keepalive timeout = 75 seconds
* Nginx performance tuning guidelines uses keepalive = 15 seconds
* IE (5-9) client hard keepalive limit = 60 seconds
* Firefox client hard keepalive limit = 115 seconds
* Opera 11 client hard keepalive limit = 120 seconds
* Chrome 13+ client keepalive limit > 300+ seconds


Proxy configuration
~~~~~~~~~~~~~~~~~~~

When you use a reverse proxy server (e.g. nginx), the value of `request.ip` will contain ip of a proxy,
typically `127.0.0.1`. Sanic may be configured to use proxy headers for determining the true client IP,
available as `request.remote_addr`. The full external URL is also constructed from header fields if available.

Without proper precautions, a malicious client may use proxy headers to spoof its own IP. To avoid such issues, Sanic does not use any proxy headers unless explicitly enabled.

Services behind reverse proxies must configure `FORWARDED_SECRET`, `REAL_IP_HEADER` and/or `PROXIES_COUNT`.

Forwarded header
################

.. Forwarded: for="1.2.3.4"; proto="https"; host="yoursite.com"; secret="Pr0xy", for="10.0.0.1"; proto="http"; host="proxy.internal"; by="_1234proxy"

* Set `FORWARDED_SECRET` to an identifier used by the proxy of interest.

The secret is used to securely identify a specific proxy server. Given the above header, secret `Pr0xy` would use the
information on the first line and secret `_1234proxy` would use the second line. The secret must exactly match the value
of `secret` or `by`. A secret in `by` must begin with an underscore and use only characters specified in
`RFC 7239 section 6.3 <https://tools.ietf.org/html/rfc7239#section-6.3>`_, while `secret` has no such restrictions.

Sanic ignores any elements without the secret key, and will not even parse the header if no secret is set.

All other proxy headers are ignored once a trusted forwarded element is found, as it already carries complete information about the client.

Traditional proxy headers
#########################

..  X-Real-IP: 1.2.3.4
    X-Forwarded-For: 1.2.3.4, 10.0.0.1
    X-Forwarded-Proto: https
    X-Forwarded-Host: yoursite.com


* Set `REAL_IP_HEADER` to `x-real-ip`, `true-client-ip`, `cf-connecting-ip` or other name of such header.
* Set `PROXIES_COUNT` to the number of entries expected in `x-forwarded-for` (name configurable via `FORWARDED_FOR_HEADER`).

If client IP is found by one of these methods, Sanic uses the following headers for URL parts:

* `x-forwarded-proto`, `x-forwarded-host`, `x-forwarded-port`, `x-forwarded-path` and if necessary, `x-scheme`.

Proxy config if using ...
#########################

* a proxy that supports `forwarded`: set `FORWARDED_SECRET` to the value that the proxy inserts in the header
    * Apache Traffic Server: `CONFIG proxy.config.http.insert_forwarded STRING for|proto|host|by=_secret`
    * NGHTTPX: `nghttpx --add-forwarded=for,proto,host,by --forwarded-for=ip --forwarded-by=_secret`
    * NGINX: :ref:`nginx`.

* a custom header with client IP: set `REAL_IP_HEADER` to the name of that header
* `x-forwarded-for`: set `PROXIES_COUNT` to `1` for a single proxy, or a greater number to allow Sanic to select the correct IP
* no proxies: no configuration required!

Changes in Sanic 19.9
#####################

Earlier Sanic versions had unsafe default settings. From 19.9 onwards proxy settings must be set manually, and support for negative PROXIES_COUNT has been removed.
