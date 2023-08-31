# Health monitor

The health monitor requires both `sanic>=22.9` and `sanic-ext>=22.9`.

You can setup Sanic Extensions to monitor the health of your worker processes. This requires that you not be in [single process mode](../../guide/deployment/manager.md#single-process-mode).

## Setup

.. column::

    Out of the box, the health monitor is disabled. You will need to opt-in if you would like to use it.

.. column::

    ```python
    app.config.HEALTH = True
    ```

## How does it work

The monitor sets up a new background process that will periodically receive acknowledgements of liveliness from each worker process. If a worker process misses a report too many times, then the monitor will restart that one worker.

## Diagnostics endpoint

.. column::

    The health monitor will also enable a diagnostics endpoint that outputs the [worker state](../../guide/deployment/manager.md#worker-state). By default is id disabled.

    .. danger:: 

        The diagnostics endpoint is not secured. If you are deploying it in a production environment, you should take steps to protect it with a proxy server if you are using one. If not, you may want to consider disabling this feature in production since it will leak details about your server state.

.. column::

    ```
    $ curl http://localhost:8000/__health__
    {
        'Sanic-Main': {'pid': 99997},
        'Sanic-Server-0-0': {
            'server': True,
            'state': 'ACKED',
            'pid': 9999,
            'start_at': datetime.datetime(2022, 10, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc),
            'starts': 2,
            'restart_at': datetime.datetime(2022, 10, 1, 0, 0, 12, 861332, tzinfo=datetime.timezone.utc)
        },
        'Sanic-Reloader-0': {
            'server': False,
            'state': 'STARTED',
            'pid': 99998,
            'start_at': datetime.datetime(2022, 10, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc),
            'starts': 1
        }
    }
    ```


## Configuration

| Key | Type | Default| Description |
|--|--|--|--|
| HEALTH | `bool` | `False` | Whether to enable this extension. |
| HEALTH_ENDPOINT | `bool` | `False` | Whether to enable the diagnostics endpoint. |
| HEALTH_MAX_MISSES | `int` | `3` | The number of consecutive misses before a worker process is restarted. |
| HEALTH_MISSED_THRESHHOLD | `int` | `10` | The number of seconds the monitor checks for worker process health. |
| HEALTH_MONITOR | `bool` | `True` | Whether to enable the health monitor. |
| HEALTH_REPORT_INTERVAL | `int` | `5` | The number of seconds between reporting each acknowledgement of liveliness. |
| HEALTH_URI_TO_INFO | `str` | `""` | The URI path of the diagnostics endpoint. |
| HEALTH_URL_PREFIX | `str` | `"/__health__"` | The URI prefix of the diagnostics blueprint. |
