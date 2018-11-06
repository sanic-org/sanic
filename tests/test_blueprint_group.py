from sanic.app import Sanic
from sanic.blueprints import Blueprint
from sanic.response import text

MIDDLEWARE_INVOKE_COUNTER = {
        'request': 0,
        'response': 0
    }


def test_bp_group(app: Sanic):
    blueprint_1 = Blueprint('blueprint_1', url_prefix="/bp1")
    blueprint_2 = Blueprint('blueprint_2', url_prefix='/bp2')

    @blueprint_1.route('/')
    def blueprint_1_default_route(request):
        return text("BP1_OK")

    @blueprint_2.route("/")
    def blueprint_2_default_route(request):
        return text("BP2_OK")

    blueprint_group_1 = Blueprint.group(
        blueprint_1, blueprint_2, url_prefix="/bp")

    blueprint_3 = Blueprint('blueprint_3', url_prefix="/bp3")

    @blueprint_group_1.middleware('request')
    def blueprint_group_1_middleware(request):
        global MIDDLEWARE_INVOKE_COUNTER
        MIDDLEWARE_INVOKE_COUNTER['request'] += 1

    @blueprint_3.route("/")
    def blueprint_3_default_route(request):
        return text("BP3_OK")

    blueprint_group_2 = Blueprint.group(blueprint_group_1, blueprint_3, url_prefix="/api")

    @blueprint_group_2.middleware('response')
    def blueprint_group_2_middleware(request, response):
        global MIDDLEWARE_INVOKE_COUNTER
        MIDDLEWARE_INVOKE_COUNTER['response'] += 1

    app.blueprint(blueprint_group_2)

    @app.route("/")
    def app_default_route(request):
        return text("APP_OK")

    _, response = app.test_client.get("/")
    assert response.text == 'APP_OK'

    _, response = app.test_client.get("/api/bp/bp1")
    assert response.text == 'BP1_OK'

    _, response = app.test_client.get("/api/bp/bp2")
    assert response.text == 'BP2_OK'

    _, response = app.test_client.get('/api/bp3')
    assert response.text == 'BP3_OK'

    assert MIDDLEWARE_INVOKE_COUNTER['response'] == 4
    assert MIDDLEWARE_INVOKE_COUNTER['request'] == 4
