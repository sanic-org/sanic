# How to contribute to Sanic

Thank you for your interest!

## Setting up the dev environment

It is ideal to create a virtual environment whenever you want to work on
a python project. **Note:** This is not a necessity to work on sanic.

Create a a new virtual environment if you dont have one, using:

`python3 -m venv <any name>`

Enable it using:

`. <any name>/bin/activate`

Get the source of sanic:

`git clone https://github.com/channelcat/sanic`

`cd sanic`

Install sanic :

`python setup.py install develop`

OR

`pip install -e .`

Install the dev dependencies:

`pip install -r requirements-dev.txt`

Create a new branch for your bugfix or feature:

`git checkout -b <branch name>`

Now you can start working on sanic.

## Tests

Install pytest and flake8 or tox:

`pip install pytest`

`pip install flake8` or `pip install tox`

Run the tests:

 `pytest tests`

 Ensure your code is properly linted using flake8:

 `flake8 sanic/`

 ## Pull request

 Once all tests have passed send out a PR.

## Warning
One of the main goals of Sanic is speed.  Sanic uses `wrk` tool for benchmarking purposes. Code that lowers the performance of Sanic without significant gains in usability, security, or features may not be merged.
