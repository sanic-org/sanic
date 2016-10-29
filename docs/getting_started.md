# Getting Started

Make sure you have pip and python 3.5 before continuing.

## Installation

 Install `sanic` by using the following command:

 `python3 -m pip install sanic`

It is as easy as that!

## Hello World!

 Create a file called `main.py` and paste the following code into.
```python
from sanic import Sanic
from sanic.response import text

app = Sanic(__name__)

@app.route("/")
async def test(request):
    return text("Hello World!")

app.run(host="0.0.0.0", port=8000, debug=True)
```
 Run it by using `python3 main.py`

You now have a working Sanic server! To learn more about Sanic, read the following:
 * [Request Data](request_data.md)
 * [Routing](routing.md)
 * [Serving static files](static_files.md)
