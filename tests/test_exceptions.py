from json import loads as json_loads, dumps as json_dumps
from sanic import Sanic
from sanic.response import json, text
from sanic.exceptions import InvalidUsage, ServerError, NotFound
from helpers import sanic_endpoint_test

# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_exception_response():
	app = Sanic('test_text')

	@app.route('/')
	def handler(request):
		return text('OK')

	@app.route('/error')
	def handler_error(request):
		raise ServerError("OK")

	@app.route('/404')
	def handler_404(request):
		raise NotFound("OK")

	@app.route('/invalid')
	def handler_invalid(request):
		raise InvalidUsage("OK")

	request, response = sanic_endpoint_test(app)
	assert response.status == 200
	assert response.text == 'OK'

	request, response = sanic_endpoint_test(app, uri='/error')
	assert response.status == 500

	request, response = sanic_endpoint_test(app, uri='/invalid')
	assert response.status == 400

	request, response = sanic_endpoint_test(app, uri='/404')
	assert response.status == 404

def test_exception_handler():
	app = Sanic('test_text')

	@app.route('/1')
	def handler_1(request):
		raise InvalidUsage("OK")
	@app.route('/2')
	def handler_2(request):
		raise ServerError("OK")
	@app.route('/3')
	def handler_3(request):
		raise NotFound("OK")

	@app.exception(NotFound, ServerError)
	def handler_exception(request, exception):
		return text("OK")

	request, response = sanic_endpoint_test(app, uri='/1')
	assert response.status == 400

	request, response = sanic_endpoint_test(app, uri='/2')
	assert response.status == 200
	assert response.text == 'OK'

	request, response = sanic_endpoint_test(app, uri='/3')
	assert response.status == 200

	request, response = sanic_endpoint_test(app, uri='/random')
	assert response.status == 200
	assert response.text == 'OK'