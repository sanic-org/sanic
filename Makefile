test:
	find . -name "*.pyc" -delete
	docker build -t sanic/test-image .
	docker run -t sanic/test-image tox
