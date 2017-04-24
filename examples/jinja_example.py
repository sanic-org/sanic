# Render templates in a Flask like way from a "template" directory in the project

from sanic import Sanic
from sanic import response
from jinja2 import Evironment, PackageLoader, select_autoescape

app = Sanic(__name__)

# Load the template environment with async support
template_env = Environment(
    loader=jinja2.PackageLoader('yourapplication', 'templates'),
    autoescape=jinja2.select_autoescape(['html', 'xml']),
    enable_async=True
)

# Load the template from file
template = template_env.get_template("example_template.html")


@app.route('/')
async def test(request):
    data = request.json
    rendered_template = await template.render_async(**data)
    return response.html(rendered_template)


app.run(host="0.0.0.0", port=8080, debug=True)