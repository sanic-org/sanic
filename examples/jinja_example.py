## To use this example:
# curl -d '{"name": "John Doe"}' localhost:8000

from sanic import Sanic
from sanic.response import html
from jinja2 import Template

template = Template('Hello {{ name }}!')

app = Sanic(__name__)

@app.route('/')
async def test(request):
    data = request.json
    return html(template.render(**data))


app.run(host="0.0.0.0", port=8000)
