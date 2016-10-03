from .response import html

class NotFound(Exception):
	status_code = 404
class InvalidUsage(Exception):
	status_code = 400
class ServerError(Exception):
	status_code = 500

class Handler:
	handlers = None
	def __init__(self):
		self.handlers = {}

	def add(self, exception_type, handler):
		self.handlers[exception_type] = handler

	def response(self, request, exception):
		handler = self.handlers.get(type(exception))
		if handler:
			response = handler(request, exception)
		else:
			response = Handler.default(request, exception)
		return response

	@staticmethod
	def default(request, exception):
		return html("Error: {}".format(exception), status=getattr(exception, 'status_code', 500))