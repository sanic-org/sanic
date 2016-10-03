from .response import text
from traceback import format_exc

class SanicException(Exception):
	pass

class NotFound(SanicException):
	status_code = 404
class InvalidUsage(SanicException):
	status_code = 400
class ServerError(SanicException):
	status_code = 500

class Handler:
	handlers = None
	debug = False
	def __init__(self):
		self.handlers = {}

	def add(self, exception_type, handler):
		self.handlers[exception_type] = handler

	def response(self, request, exception):
		handler = self.handlers.get(type(exception))
		if handler:
			response = handler(request, exception)
		else:
			response = Handler.default(request, exception, self.debug)
		return response

	@staticmethod
	def default(request, exception, debug):
		if issubclass(type(exception), SanicException):
			return text("Error: {}".format(exception), status=getattr(exception, 'status_code', 500))
		elif debug:
			return text("Error: {}\nException: {}".format(exception, format_exc()), status=500)
		else:
			return text("An error occurred while generating the request", status=500)