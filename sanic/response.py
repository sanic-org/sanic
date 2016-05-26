import ujson

from .server import Response

def json(input):
	return Response(ujson.dumps(input), content_type="application/json")