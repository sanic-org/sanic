"""
Sanic
"""
import codecs
import os
import re
from setuptools import setup


with codecs.open(os.path.join(os.path.abspath(os.path.dirname(
        __file__)), 'sanic', '__init__.py'), 'r', 'latin1') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

install_requires = [
    'httptools>=0.0.9',
    'aiofiles>=0.3.0',
]

ujson = [
    'ujson>=1.35',
]

uvloop = [
    'uvloop>=0.5.3',
]

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
    extras_require={
        "all": install_requires + ujson + uvloop,
        "ujson": install_requires + ujson,
        "uvloop": install_requires + uvloop,
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
