"""
Sanic
"""
from setuptools import setup

setup(
    name='Sanic',
    version="0.0.2",
    url='http://github.com/channelcat/sanic/',
    license='BSD',
    author='Channel Cat',
    author_email='channelcat@gmail.com',
    description='A microframework based on uvloop and httptools',
    #long_description=,
    packages=['sanic'],
    #include_package_data=True,
    #zip_safe=False,
    platforms='any',
    install_requires=[
        'uvloop>=0.5.3',
        'httptools>=0.0.9',
        'ujson>=1.35',
    ],
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Environment :: Web Environment',
    ],
)