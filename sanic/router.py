from .log import log
from .exceptions import NotFound

class Router():
	routes = None

	def __init__(self):
		self.routes = {}

	def add(self, uri, handler):
		self.routes[uri] = handler

	def get(self, request):
		handler = self.routes.get(request.url)
		if handler:
			return handler
		else:
			raise NotFound("Requested URL {} not found".format(request.url))