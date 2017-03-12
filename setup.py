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

setup_kwargs =  {
    'name': 'sanic',
    'version': version,
    'url': 'http://github.com/channelcat/sanic/',
    'license': 'MIT',
    'author': 'Channel Cat',
    'author_email': 'channelcat@gmail.com',
    'description': (
        'A microframework based on uvloop, httptools, and learnings of flask'),
    'packages': ['sanic'],
    'platforms': 'any',
    'classifiers': [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
}

try:
    normal_requirements = [
        'httptools>=0.0.9',
        'uvloop>=0.5.3',
        'ujson>=1.35',
        'aiofiles>=0.3.0',
        'websockets>=3.2',
    ]
    setup_kwargs['install_requires'] = normal_requirements
    setup(**setup_kwargs)
except DistutilsPlatformError as exception:
    windows_requirements = [
        'httptools>=0.0.9',
        'aiofiles>=0.3.0',
        'websockets>=3.2',
    ]
    setup_kwargs['install_requires'] = windows_requirements
    setup(**setup_kwargs)
    # No exceptions occcured
    print(u"\n\n\U0001F680    "
          "Sanic version {} installation suceeded.\n".format(version))
else:
    print(u"\n\n\U0001F680    "
          "Sanic version {} installation suceeded.\n".format(version))
