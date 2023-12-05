.DEFAULT: help

.PHONY: help
help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "install"
	@echo "		Install Sanic"
	@echo "docker-test"
	@echo "		Run Sanic Unit Tests using Docker"
	@echo "fix"
	@echo "		Analyze and fix linting issues using ruff"
	@echo "format"
	@echo "		Analyze and format using ruff"
	@echo "pretty"
	@echo "		Analyze and fix linting and format using ruff"
	@echo ""
	@echo "docs"
	@echo "		Generate Sanic documentation"
	@echo ""
	@echo "clean-docs"
	@echo "		Clean Sanic documentation"
	@echo ""
	@echo "docs-test"
	@echo "		Test Sanic Documentation for errors"
	@echo ""
	@echo "changelog"
	@echo "		Generate changelog for Sanic to prepare for new release"
	@echo ""
	@echo "release"
	@echo "		Prepare Sanic for a new changes by version bump and changelog"
	@echo ""

.PHONY: clean
clean:
	find . ! -path "./.eggs/*" -name "*.pyc" -exec rm {} \;
	find . ! -path "./.eggs/*" -name "*.pyo" -exec rm {} \;
	find . ! -path "./.eggs/*" -name ".coverage" -exec rm {} \;
	rm -rf build/* > /dev/null 2>&1
	rm -rf dist/* > /dev/null 2>&1

.PHONY: view-coverage
view-coverage:
	sanic ./coverage --simple

.PHONY: install
install:
	python -m pip install .

.PHONY: docker-test
docker-test: clean
	docker build -t sanic/test-image -f docker/Dockerfile .
	docker run -t sanic/test-image tox

.PHONY: fix
fix:
	ruff check sanic --fix

.PHONY: format
format:
	ruff format sanic

.PHONY: pretty
pretty: fix format

.PHONY: docs-clean
docs-clean:
	cd docs && make clean

.PHONY: docs
docs: docs-clean
	cd docs && make html

.PHONY: docs-test
docs-test: docs-clean
	cd docs && make dummy

.PHONY: docs-serve
docs-serve:
	sphinx-autobuild docs docs/_build/html --port 9999 --watch ./

.PHONY: changelog
changelog:
	python scripts/changelog.py

.PHONY: guide-serve
guide-serve:
	cd guide && sanic server:app -r -R ./content -R ./style

.PHONY: release
release:
ifdef version
	python scripts/release.py --release-version ${version} --generate-changelog
else
	python scripts/release.py --generate-changelog
endif

