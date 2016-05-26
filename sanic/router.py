from .log import log

class Router():
	routes = None
	default = None

	def __init__(self, default=None):
		self.routes = {}
		self.default=default

	def add(self, route, handler):
		self.routes[route] = handler

	def get(self, uri):
		return self.routes.get(uri.decode('utf-8'), self.default)