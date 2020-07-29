from asyncio import sleep

from sanic import Sanic, response

app = Sanic(__name__, strict_slashes=True)

@app.get("/")
async def handler(request):
    return response.redirect("/sleep/3")

@app.get("/sleep/<t:number>")
async def handler2(request, t=0.3):
    await sleep(t)
    return response.text(f"Slept {t:.1f} seconds.\n")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
