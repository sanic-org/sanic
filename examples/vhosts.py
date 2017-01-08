from sanic.response import text
from sanic import Sanic

# Usage
# curl -H "Host: example.com" localhost:8000
# curl -H "Host: sub.example.com" localhost:8000

app = Sanic()

@app.route('/', host="example.com")
async def hello(request):
    return text("Answer")
@app.route('/', host="sub.example.com")
async def hello(request):
    return text("42")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
