from .log import log
from .exceptions import NotFound

class Router():
	routes = None

	def __init__(self):
		self.routes = {}

	def add(self, uri, handler):
		self.routes[uri] = handler

	def get(self, request):
		uri_string = request.url.decode('utf-8')
		handler = self.routes.get(uri_string)
		if handler:
			return handler
		else:
			raise NotFound("Requested URL {} not found".format(uri_string))