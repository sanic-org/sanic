import logging


LOGGING_CONFIG_DEFAULTS = dict(
        version=1,
        disable_existing_loggers=False,

        loggers={
            "root": {
                "level": "INFO",
                "handlers": ["console"]},
            "sanic.error": {
                "level": "INFO",
                "handlers": ["error_console"],
                "propagate": True,
                "qualname": "sanic.error"
            },

            "sanic.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": True,
                "qualname": "sanic.access"
            }
        },
        handlers={
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "generic",
                "stream": "sys.stdout"
            },
            "error_console": {
                "class": "logging.StreamHandler",
                "formatter": "generic",
                "stream": "sys.stderr"
            },
        },
        formatters={
            "generic": {
                "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
                "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
                "class": "logging.Formatter"
            }
        }
)


class AccessLogger:

    def __init__(self, logger, access_log_format=None):
        pass


log = logging.getLogger('sanic')
error_logger = logging.getLogger('sanic.error')
access_logger = logging.getLogger('sanic.access')
