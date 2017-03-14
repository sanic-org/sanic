"""
Sanic
"""
import codecs
import os
import re
from setuptools import setup
from distutils.util import strtobool

with codecs.open(os.path.join(os.path.abspath(os.path.dirname(
        __file__)), 'sanic', '__init__.py'), 'r', 'latin1') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

uvloop = 'uvloop>=0.5.3'
ujson = 'ujson>=1.35'

install_requires = [
    'httptools>=0.0.9',
    'aiofiles>=0.3.0',
    ujson,
    uvloop
]

if strtobool(os.environ.get("SANIC_NO_UVLOOP", "false")):
    install_requires.remove(uvloop)

if strtobool(os.environ.get("SANIC_NO_UJSON", "false")):
    install_requires.remove(ujson)


def run_setup():
    setup(
        name='sanic',
        version=version,
        url='http://github.com/channelcat/sanic/',
        license='MIT',
        author='Channel Cat',
        author_email='channelcat@gmail.com',
        description=(
            'A microframework based on uvloop, httptools, and learnings of flask'),
        packages=['sanic'],
        platforms='any',
        install_requires=install_requires,
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Environment :: Web Environment',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
        ],
    )


try:
    run_setup()
except:
    install_requires.remove(uvloop)
    install_requires.remove(ujson)
    run_setup()
