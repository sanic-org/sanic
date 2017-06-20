from sanic import Sanic
from sanic import response

app = Sanic(__name__)

    
@app.route('/')
def handle_request(request):
    return response.redirect('/redirect')


@app.route('/redirect')
async def test(request):
    return response.json({"Redirected": True})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)