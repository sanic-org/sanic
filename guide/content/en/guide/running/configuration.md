# Configuration

## Basics


.. column::

    Sanic holds the configuration in the config attribute of the application object. The configuration object is merely an object that can be modified either using dot-notation or like a dictionary.

.. column::

    ```python
    app = Sanic("myapp")
    app.config.DB_NAME = "appdb"
    app.config["DB_USER"] = "appuser"
    ```


.. column::

    You can also use the `update()` method like on regular dictionaries.

.. column::

    ```python
    db_settings = {
        'DB_HOST': 'localhost',
        'DB_NAME': 'appdb',
        'DB_USER': 'appuser'
    }
    app.config.update(db_settings)
    ```



.. note:: 

    It is standard practice in Sanic to name your config values in **uppercase letters**. Indeed, you may experience weird behaviors if you start mixing uppercase and lowercase names.



## Loading

### Environment variables

.. column::

    Any environment variables defined with the `SANIC_` prefix will be applied to the Sanic config. For example, setting `SANIC_REQUEST_TIMEOUT` will be loaded by the application automatically and fed into the `REQUEST_TIMEOUT` config variable.

.. column::

    ```bash
    $ export SANIC_REQUEST_TIMEOUT=10
    ```
    ```python
    >>> print(app.config.REQUEST_TIMEOUT)
    10
    ```


.. column::

    You can change the prefix that Sanic is expecting at startup.

.. column::

    ```bash
    $ export MYAPP_REQUEST_TIMEOUT=10
    ```
    ```python
    >>> app = Sanic(__name__, env_prefix='MYAPP_')
    >>> print(app.config.REQUEST_TIMEOUT)
    10
    ```


.. column::

    You can also disable environment variable loading completely.

.. column::

    ```python
    app = Sanic(__name__, load_env=False)
    ```

### Using Sanic.update_config

The `Sanic` instance has a _very_ versatile method for loading config: `app.update_config`. You can feed it a path to a file, a dictionary, a class, or just about any other sort of object.

#### From a file

.. column::

    Let's say you have `my_config.py` file that looks like this.

.. column::

    ```python
    # my_config.py
    A = 1
    B = 2
    ```


.. column::

    You can load this as config values by passing its path to `app.update_config`.

.. column::

    ```python
    >>> app.update_config("/path/to/my_config.py")
    >>> print(app.config.A)
    1
    ```


.. column::

    This path also accepts bash style environment variables.

.. column::

    ```bash
    $ export my_path="/path/to"
    ```
    ```python
    app.update_config("${my_path}/my_config.py")
    ```



.. note:: 
    
    Just remember that you have to provide environment variables in the format `${environment_variable}` and that `$environment_variable` is not expanded (is treated as "plain" text).



#### From a dict

.. column::

    The `app.update_config` method also works on plain dictionaries.

.. column::

    ```python
    app.update_config({"A": 1, "B": 2})
    ```

#### From a class or object

.. column::

    You can define your own config class, and pass it to `app.update_config`

.. column::

    ```python
    class MyConfig:
        A = 1
        B = 2

    app.update_config(MyConfig)
    ```


.. column::

    It even could be instantiated.

.. column::

    ```python
    app.update_config(MyConfig())
    ```

### Type casting

When loading from environment variables, Sanic will attempt to cast the values to expected Python types. This particularly applies to:

- `int`
- `float`
- `bool`

In regards to `bool`, the following _case insensitive_ values are allowed:

- **`True`**: `y`, `yes`, `yep`, `yup`, `t`, `true`, `on`, `enable`, `enabled`, `1`
- **`False`**: `n`, `no`, `f`, `false`, `off`, `disable`, `disabled`, `0`

If a value cannot be cast, it will default to a `str`.

.. column::

    Additionally, Sanic can be configured to cast additional types using additional type converters. This should be any callable that returns the value or raises a `ValueError`.

    *Added in v21.12*

.. column::

    ```python
    app = Sanic(..., config=Config(converters=[UUID]))
    ```

## Builtin values

| **Variable**              | **Default**      | **Description**                                                                                                                       |
|---------------------------|------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| ACCESS_LOG                | True             | Disable or enable access log                                                                                                          |
| AUTO_EXTEND               | True             | Control whether [Sanic Extensions](../../plugins/sanic-ext/getting-started.md) will load if it is in the existing virtual environment |
| AUTO_RELOAD               | True             | Control whether the application will automatically reload when a file changes                                                         |
| EVENT_AUTOREGISTER        | True             | When `True` using the `app.event()` method on a non-existing signal will automatically create it and not raise an exception           |
| FALLBACK_ERROR_FORMAT     | html             | Format of error response if an exception is not caught and handled                                                                    |
| FORWARDED_FOR_HEADER      | X-Forwarded-For  | The name of "X-Forwarded-For" HTTP header that contains client and proxy ip                                                           |
| FORWARDED_SECRET          | None             | Used to securely identify a specific proxy server (see below)                                                                         |
| GRACEFUL_SHUTDOWN_TIMEOUT | 15.0             | How long to wait to force close non-idle connection (sec)                                                                             |
| INSPECTOR                 | False            | Whether to enable the Inspector                                                                                                       |
| INSPECTOR_HOST            | localhost        | The host for the Inspector                                                                                                            |
| INSPECTOR_PORT            | 6457             | The port for the Inspector                                                                                                            |
| INSPECTOR_TLS_KEY         | -                | The TLS key for the Inspector                                                                                                         |
| INSPECTOR_TLS_CERT        | -                | The TLS certificate for the Inspector                                                                                                 |
| INSPECTOR_API_KEY         | -                | The API key for the Inspector                                                                                                         |
| KEEP_ALIVE_TIMEOUT        | 120              | How long to hold a TCP connection open (sec)                                                                                          |
| KEEP_ALIVE                | True             | Disables keep-alive when False                                                                                                        |
| MOTD                      | True             | Whether to display the MOTD (message of the day) at startup                                                                           |
| MOTD_DISPLAY              | {}               | Key/value pairs to display additional, arbitrary data in the MOTD                                                                     |
| NOISY_EXCEPTIONS          | False            | Force all `quiet` exceptions to be logged                                                                                             |
| PROXIES_COUNT             | None             | The number of proxy servers in front of the app (e.g. nginx; see below)                                                               |
| REAL_IP_HEADER            | None             | The name of "X-Real-IP" HTTP header that contains real client ip                                                                      |
| REGISTER                  | True             | Whether the app registry should be enabled                                                                                            |
| REQUEST_BUFFER_SIZE       | 65536            | Request buffer size before request is paused, default is 64 Kib                                                                       |
| REQUEST_ID_HEADER         | X-Request-ID     | The name of "X-Request-ID" HTTP header that contains request/correlation ID                                                           |
| REQUEST_MAX_SIZE          | 100000000        | How big a request may be (bytes), default is 100 megabytes                                                                            |
| REQUEST_MAX_HEADER_SIZE   | 8192            | How big a request header may be (bytes), default is 8192 bytes                                                                         |
| REQUEST_TIMEOUT           | 60               | How long a request can take to arrive (sec)                                                                                           |
| RESPONSE_TIMEOUT          | 60               | How long a response can take to process (sec)                                                                                         |
| USE_UVLOOP                | True             | Whether to override the loop policy to use `uvloop`. Supported only with `app.run`.                                                   |
| WEBSOCKET_MAX_SIZE        | 2^20             | Maximum size for incoming messages (bytes)                                                                                            |
| WEBSOCKET_PING_INTERVAL   | 20               | A Ping frame is sent every ping_interval seconds.                                                                                     |
| WEBSOCKET_PING_TIMEOUT    | 20               | Connection is closed when Pong is not received after ping_timeout seconds                                                             |


.. tip:: FYI

    - The `USE_UVLOOP` value will be ignored if running with Gunicorn. Defaults to `False` on non-supported platforms (Windows).
    - The `WEBSOCKET_` values will be ignored if in ASGI mode.
    - v21.12 added: `AUTO_EXTEND`, `MOTD`, `MOTD_DISPLAY`, `NOISY_EXCEPTIONS`
    - v22.9 added: `INSPECTOR`
    - v22.12 added: `INSPECTOR_HOST`, `INSPECTOR_PORT`, `INSPECTOR_TLS_KEY`, `INSPECTOR_TLS_CERT`, `INSPECTOR_API_KEY`


## Timeouts

### REQUEST_TIMEOUT

A request timeout measures the duration of time between the instant when a new open TCP connection is passed to the
Sanic backend server, and the instant when the whole HTTP request is received. If the time taken exceeds the
`REQUEST_TIMEOUT` value (in seconds), this is considered a Client Error so Sanic generates an `HTTP 408` response
and sends that to the client. Set this parameter's value higher if your clients routinely pass very large request payloads
or upload requests very slowly.

### RESPONSE_TIMEOUT

A response timeout measures the duration of time between the instant the Sanic server passes the HTTP request to the Sanic App, and the instant a HTTP response is sent to the client. If the time taken exceeds the `RESPONSE_TIMEOUT` value (in seconds), this is considered a Server Error so Sanic generates an `HTTP 503` response and sends that to the client. Set this parameter's value higher if your application is likely to have long-running process that delay the
generation of a response.

### KEEP_ALIVE_TIMEOUT

#### What is Keep Alive? And what does the Keep Alive Timeout value do?

`Keep-Alive` is a HTTP feature introduced in `HTTP 1.1`. When sending a HTTP request, the client (usually a web browser application) can set a `Keep-Alive` header to indicate the http server (Sanic) to not close the TCP connection after it has send the response. This allows the client to reuse the existing TCP connection to send subsequent HTTP requests, and ensures more efficient network traffic for both the client and the server.

The `KEEP_ALIVE` config variable is set to `True` in Sanic by default. If you don't need this feature in your application, set it to `False` to cause all client connections to close immediately after a response is sent, regardless of the `Keep-Alive` header on the request.

The amount of time the server holds the TCP connection open is decided by the server itself. In Sanic, that value is configured using the `KEEP_ALIVE_TIMEOUT` value. By default, **it is set to 120 seconds**. This means that if the client sends a `Keep-Alive` header, the server will hold the TCP connection open for 120 seconds after sending the response, and the client can reuse the connection to send another HTTP request within that time.

For reference:

* Apache httpd server default keepalive timeout = 5 seconds
* Nginx server default keepalive timeout = 75 seconds
* Nginx performance tuning guidelines uses keepalive = 15 seconds
* Caddy server default keepalive timeout = 120 seconds
* IE (5-9) client hard keepalive limit = 60 seconds
* Firefox client hard keepalive limit = 115 seconds
* Opera 11 client hard keepalive limit = 120 seconds
* Chrome 13+ client keepalive limit > 300+ seconds

## Proxy configuration

See [proxy configuration section](/guide/advanced/proxy-headers.md)
