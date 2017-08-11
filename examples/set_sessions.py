# -*- encoding: utf-8 -*-

from sanic import Sanic
from sanic.response import json

app = Sanic()


@app.route("/")
async def test(request):
    if request.session.get('key') is None:
        request.session['key'] = 'value'
        return json(dict(ok=True))
    else:
        return json(dict(key=request.session['key']))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
