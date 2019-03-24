# Configuration

Any reasonably complex application will need configuration that is not baked into the actual code. Settings might be different for different environments or installations.

## Basics

Sanic holds the configuration in the `config` attribute of the application object. The configuration object is merely an object that can be modified either using dot-notation or like a dictionary:

```
app = Sanic('myapp')
app.config.DB_NAME = 'appdb'
app.config.DB_USER = 'appuser'
```

Since the config object actually is a dictionary, you can use its `update` method in order to set several values at once:

```
db_settings = {
    'DB_HOST': 'localhost',
    'DB_NAME': 'appdb',
    'DB_USER': 'appuser'
}
app.config.update(db_settings)
```

In general the convention is to only have UPPERCASE configuration parameters. The methods described below for loading configuration only look for such uppercase parameters.

## Loading Configuration

There are several ways how to load configuration.

### From Environment Variables

Any variables defined with the `SANIC_` prefix will be applied to the sanic config. For example, setting `SANIC_REQUEST_TIMEOUT` will be loaded by the application automatically and fed into the `REQUEST_TIMEOUT` config variable. You can pass a different prefix to Sanic:

```python
app = Sanic(load_env='MYAPP_')
```

Then the above variable would be `MYAPP_REQUEST_TIMEOUT`. If you want to disable loading from environment variables you can set it to `False` instead:

```python
app = Sanic(load_env=False)
```

### From an Object

If there are a lot of configuration values and they have sensible defaults it might be helpful to put them into a module:

```
import myapp.default_settings

app = Sanic('myapp')
app.config.from_object(myapp.default_settings)
```

You could use a class or any other object as well.

### From a File

Usually you will want to load configuration from a file that is not part of the distributed application. You can load configuration from a file using `from_pyfile(/path/to/config_file)`. However, that requires the program to know the path to the config file. So instead you can specify the location of the config file in an environment variable and tell Sanic to use that to find the config file:

```
app = Sanic('myapp')
app.config.from_envvar('MYAPP_SETTINGS')
```

Then you can run your application with the `MYAPP_SETTINGS` environment variable set:

```
$ MYAPP_SETTINGS=/path/to/config_file python3 myapp.py
INFO: Goin' Fast @ http://0.0.0.0:8000
```

The config files are regular Python files which are executed in order to load them. This allows you to use arbitrary logic for constructing the right configuration. Only uppercase variables are added to the configuration. Most commonly the configuration consists of simple key value pairs:

```
# config_file
DB_HOST = 'localhost'
DB_NAME = 'appdb'
DB_USER = 'appuser'
```

## Builtin Configuration Values

Out of the box there are just a few predefined values which can be overwritten when creating the application.

    | Variable                  | Default   | Description                                               |
    | ------------------------- | --------- | --------------------------------------------------------- |
    | REQUEST_MAX_SIZE          | 100000000 | How big a request may be (bytes)                          |
    | REQUEST_BUFFER_QUEUE_SIZE | 100       | Request streaming buffer queue size                    |
    | REQUEST_TIMEOUT           | 60        | How long a request can take to arrive (sec)               |
    | RESPONSE_TIMEOUT          | 60        | How long a response can take to process (sec)             |
    | KEEP_ALIVE                | True      | Disables keep-alive when False                            |
    | KEEP_ALIVE_TIMEOUT        | 5         | How long to hold a TCP connection open (sec)              |
    | GRACEFUL_SHUTDOWN_TIMEOUT | 15.0      | How long to wait to force close non-idle connection (sec) |
    | ACCESS_LOG                | True      | Disable or enable access log                              |

### The different Timeout variables:

#### `REQUEST_TIMEOUT`

A request timeout measures the duration of time between the instant when a new open TCP connection is passed to the 
Sanic backend server, and the instant when the whole HTTP request is received. If the time taken exceeds the 
`REQUEST_TIMEOUT` value (in seconds), this is considered a Client Error so Sanic generates an `HTTP 408` response 
and sends that to the client. Set this parameter's value higher if your clients routinely pass very large request payloads 
or upload requests very slowly.

#### `RESPONSE_TIMEOUT`

A response timeout measures the duration of time between the instant the Sanic server passes the HTTP request to the 
Sanic App, and the instant a HTTP response is sent to the client. If the time taken exceeds the `RESPONSE_TIMEOUT` 
value (in seconds), this is considered a Server Error so Sanic generates an `HTTP 503` response and sends that to the 
client. Set this parameter's value higher if your application is likely to have long-running process that delay the 
generation of a response.

#### `KEEP_ALIVE_TIMEOUT`

##### What is Keep Alive? And what does the Keep Alive Timeout value do?

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
```
Apache httpd server default keepalive timeout = 5 seconds
Nginx server default keepalive timeout = 75 seconds
Nginx performance tuning guidelines uses keepalive = 15 seconds
IE (5-9) client hard keepalive limit = 60 seconds
Firefox client hard keepalive limit = 115 seconds
Opera 11 client hard keepalive limit = 120 seconds
Chrome 13+ client keepalive limit > 300+ seconds
```
