from os import getenv

from raygun4py.raygunprovider import RaygunSender

from sanic import Sanic
from sanic.exceptions import SanicException
from sanic.handlers import ErrorHandler


class RaygunExceptionReporter(ErrorHandler):
    def __init__(self, raygun_api_key=None):
        super().__init__()
        if raygun_api_key is None:
            raygun_api_key = getenv("RAYGUN_API_KEY")

        self.sender = RaygunSender(raygun_api_key)

    def default(self, request, exception):
        self.sender.send_exception(exception=exception)
        return super().default(request, exception)


raygun_error_reporter = RaygunExceptionReporter()
app = Sanic("Example", error_handler=raygun_error_reporter)


@app.route("/raise")
async def test(request):
    raise SanicException("You Broke It!")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=getenv("PORT", 8080))
