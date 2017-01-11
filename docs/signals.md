# Signals

Signals allow you to send notifications to multiple subscribers when the specific event occured.
Signaling is provided by [Blinker](http://pythonhosted.org/blinker/) library and
Sanic has few built-in signals:

* `request_started`: Sent when the request processing has started.
* `request_finished`: Sent when the request processing has finished.

## Examples

```python
from sanic.signals import request_started
import my_realtime_stat

app = Sanic(__name__)

@request_started.connect
def collect_stats(request):
    my_realtime_stat.incoming_requests.incr(request.url)


@request_finished.connect
def count_errors(response):
    if response.status != 200:
        my_realtime_stat.error_responses.incr(response.status)
```
