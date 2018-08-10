from sanic import response
from sanic import Sanic
from sanic.blueprints import Blueprint

# Usage
# curl -H "Host: example.com" localhost:8000
# curl -H "Host: sub.example.com" localhost:8000
# curl -H "Host: bp.example.com" localhost:8000/question
# curl -H "Host: bp.example.com" localhost:8000/answer

app = Sanic()
bp = Blueprint("bp", host="bp.example.com")


@app.route('/', host=["example.com",
                      "somethingelse.com",
                      "therestofyourdomains.com"])
async def hello(request):
    return response.text("Some defaults")


@app.route('/', host="sub.example.com")
async def hello(request):
    return response.text("42")


@bp.route("/question")
async def hello(request):
    return response.text("What is the meaning of life?")


@bp.route("/answer")
async def hello(request):
    return response.text("42")

app.blueprint(bp)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)