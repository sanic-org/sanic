.PHONY: help test test-coverage install docker-test

.DEFAULT: help

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "test"
	@echo "		Run Sanic Unit Tests"
	@echo "test-coverage"
	@echo "		Run Sanic Unit Tests with Coverage"
	@echo "install"
	@echo "		Install Sanic"
	@echo "docker-test"
	@echo "		Run Sanic Unit Tests using Docker"
	@echo ""

clean:
	find . ! -path "./.eggs/*" -name "*.pyc" -exec rm {} \;
	find . ! -path "./.eggs/*" -name "*.pyo" -exec rm {} \;
	rm -rf build/* > /dev/null 2>&1
	rm -rf dist/* > /dev/null 2>&1

test: clean
	python setup.py test

test-coverage: clean
	python setup.py test --pytest-args="--cov sanic --cov-report term --cov-append "

install:
	python setup.py install

docker-test: clean
	docker build -t sanic/test-image -f docker/Dockerfile .
	docker run -t sanic/test-image tox
