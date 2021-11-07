from sanic import Sanic
from sanic.blueprints import Blueprint
from sanic.response import json


app = Sanic(name="blue-print-group-version-example")

bp1 = Blueprint(name="ultron", url_prefix="/ultron")
bp2 = Blueprint(name="vision", url_prefix="/vision", strict_slashes=None)

bpg = Blueprint.group(
    bp1, bp2, url_prefix="/sentient/robot", version=1, strict_slashes=True
)


@bp1.get("/name")
async def bp1_name(request):
    """This will expose an Endpoint GET /v1/sentient/robot/ultron/name"""
    return json({"name": "Ultron"})


@bp2.get("/name")
async def bp2_name(request):
    """This will expose an Endpoint GET /v1/sentient/robot/vision/name"""
    return json({"name": "vision"})


@bp2.get("/name", version=2)
async def bp2_revised_name(request):
    """This will expose an Endpoint GET /v2/sentient/robot/vision/name"""
    return json({"name": "new vision"})


app.blueprint(bpg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
