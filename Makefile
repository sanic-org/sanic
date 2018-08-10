test:
	find . -name "*.pyc" -delete
	docker build -t sanic/test-image -f docker/Dockerfile .
	docker run -t sanic/test-image tox
