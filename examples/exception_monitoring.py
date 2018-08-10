"""
Example intercepting uncaught exceptions using Sanic's error handler framework.
This may be useful for developers wishing to use Sentry, Airbrake, etc.
or a custom system to log and monitor unexpected errors in production.
First we create our own class inheriting from Handler in sanic.exceptions,
and pass in an instance of it when we create our Sanic instance. Inside this
class' default handler, we can do anything including sending exceptions to
an external service.
"""
from sanic.handlers import ErrorHandler
from sanic.exceptions import SanicException
"""
Imports and code relevant for our CustomHandler class
(Ordinarily this would be in a separate file)
"""


class CustomHandler(ErrorHandler):

    def default(self, request, exception):
        # Here, we have access to the exception object
        # and can do anything with it (log, send to external service, etc)

        # Some exceptions are trivial and built into Sanic (404s, etc)
        if not isinstance(exception, SanicException):
            print(exception)

        # Then, we must finish handling the exception by returning
        # our response to the client
        # For this we can just call the super class' default handler
        return super().default(request, exception)


"""
This is an ordinary Sanic server, with the exception that we set the
server's error_handler to an instance of our CustomHandler
"""

from sanic import Sanic

app = Sanic(__name__)

handler = CustomHandler()
app.error_handler = handler


@app.route("/")
async def test(request):
    # Here, something occurs which causes an unexpected exception
    # This exception will flow to our custom handler.
    raise SanicException('You Broke It!')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
