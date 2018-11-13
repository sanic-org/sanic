"""
Sanic
"""
import codecs
import os
import re
from distutils.errors import DistutilsPlatformError
from distutils.util import strtobool

from setuptools import setup


def open_local(paths, mode='r', encoding='utf8'):
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        *paths
    )

    return codecs.open(path, mode, encoding)


with open_local(['sanic', '__init__.py'], encoding='latin1') as fp:
    try:
        version = re.findall(r"^__version__ = \"([^']+)\"\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


with open_local(['README.rst']) as rm:
    long_description = rm.read()

setup_kwargs = {
    'name': 'sanic',
    'version': version,
    'url': 'http://github.com/channelcat/sanic/',
    'license': 'MIT',
    'author': 'Channel Cat',
    'author_email': 'channelcat@gmail.com',
    'description': (
        'A microframework based on uvloop, httptools, and learnings of flask'),
    'long_description': long_description,
    'packages': ['sanic'],
    'platforms': 'any',
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
}

env_dependency = '; sys_platform != "win32" and implementation_name == "cpython"'
ujson = 'ujson>=1.35' + env_dependency
uvloop = 'uvloop>=0.5.3' + env_dependency

requirements = [
    'httptools>=0.0.10',
    uvloop,
    ujson,
    'aiofiles>=0.3.0',
    'websockets>=6.0,<7.0',
    'multidict>=4.0,<5.0',
]
if strtobool(os.environ.get("SANIC_NO_UJSON", "no")):
    print("Installing without uJSON")
    requirements.remove(ujson)

# 'nt' means windows OS
if strtobool(os.environ.get("SANIC_NO_UVLOOP", "no")):
    print("Installing without uvLoop")
    requirements.remove(uvloop)

setup_kwargs['install_requires'] = requirements
setup(**setup_kwargs)
