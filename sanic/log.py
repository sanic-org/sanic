import logging


class DefaultFilter(logging.Filter):

    def __init__(self, param=None):
        self.param = param

    def filter(self, record):
        if self.param is None:
            return True
        if record.levelno in self.param:
            return True
        return False


log = logging.getLogger('sanic')
netlog = logging.getLogger('network')
