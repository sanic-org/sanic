# Getting Started

Make sure you have pip and python 3.5 before starting

## Benchmarks
 * Install Sanic
 * `python3 -m pip install git+https://github.com/channelcat/sanic/`
 * Edit main.py to include:
```python
from sanic import Sanic
from sanic.response import json

app = Sanic(__name__)

@app.route("/")
async def test(request):
    return json({ "hello": "world" })

app.run(host="0.0.0.0", port=8000, debug=True)
```
 * Run `python3 main.py`

You now have a working sanic server!  To continue on, check out:
 * [Request Data](request_data.md)
 * [Routing](routing.md)