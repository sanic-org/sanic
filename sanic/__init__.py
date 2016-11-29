from .sanic import Sanic
from .blueprints import Blueprint

sanic = Sanic()

__version__ = '0.1.7'

__all__ = ['Sanic', 'Blueprint']
