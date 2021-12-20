from sanic import Blueprint, Sanic
from sanic.response import text


"""
Demonstrates that blueprint request middleware are executed in the order they
are added. And blueprint response middleware are executed in _reverse_ order.
On a valid request, it should print "1 2 3 6 5 4" to terminal
"""

app = Sanic(__name__)

bp = Blueprint("bp_" + __name__)


@bp.on_request
def request_middleware_1(request):
    print("1")


@bp.on_request
def request_middleware_2(request):
    print("2")


@bp.on_request
def request_middleware_3(request):
    print("3")


@bp.on_response
def resp_middleware_4(request, response):
    print("4")


@bp.on_response
def resp_middleware_5(request, response):
    print("5")


@bp.on_response
def resp_middleware_6(request, response):
    print("6")


@bp.route("/")
def pop_handler(request):
    return text("hello world")


app.blueprint(bp, url_prefix="/bp")

app.run(host="0.0.0.0", port=8000, debug=True, auto_reload=False)
