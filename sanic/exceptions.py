from .response import text
from .log import log
from traceback import format_exc


class SanicException(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class NotFound(SanicException):
    status_code = 404


class InvalidUsage(SanicException):
    status_code = 400


class ServerError(SanicException):
    status_code = 500


class FileNotFound(NotFound):
    status_code = 404

    def __init__(self, message, path, relative_url):
        super().__init__(message)
        self.path = path
        self.relative_url = relative_url


class RequestTimeout(SanicException):
    status_code = 408


class PayloadTooLarge(SanicException):
    status_code = 413


class Handler:
    handlers = None

    def __init__(self, sanic):
        self.handlers = {}
        self.sanic = sanic

    def add(self, exception, handler):
        self.handlers[exception] = handler

    def response(self, request, exception):
        """
        Fetches and executes an exception handler and returns a response object
        :param request: Request
        :param exception: Exception to handle
        :return: Response object
        """
        handler = self.handlers.get(type(exception), self.default)
        try:
            response = handler(request=request, exception=exception)
        except:
            if self.sanic.debug:
                response_message = (
                    'Exception raised in exception handler "{}" '
                    'for uri: "{}"\n{}').format(
                        handler.__name__, request.url, format_exc())
                log.error(response_message)
                return text(response_message, 500)
            else:
                return text('An error occurred while handling an error', 500)
        return response

    def default(self, request, exception):
        if issubclass(type(exception), SanicException):
            return text(
                'Error: {}'.format(exception),
                status=getattr(exception, 'status_code', 500))
        elif self.sanic.debug:
            response_message = (
                'Exception occurred while handling uri: "{}"\n{}'.format(
                    request.url, format_exc()))
            log.error(response_message)
            return text(response_message, status=500)
        else:
            return text(
                'An error occurred while generating the response', status=500)
