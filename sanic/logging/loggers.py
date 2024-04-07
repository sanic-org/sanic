import logging

from sanic.logging.filter import VerbosityFilter


_verbosity_filter = VerbosityFilter()

logger = logging.getLogger("sanic.root")  # no cov
"""
General Sanic logger
"""
logger.addFilter(_verbosity_filter)

error_logger = logging.getLogger("sanic.error")  # no cov
"""
Logger used by Sanic for error logging
"""
error_logger.addFilter(_verbosity_filter)

access_logger = logging.getLogger("sanic.access")  # no cov
"""
Logger used by Sanic for access logging
"""
access_logger.addFilter(_verbosity_filter)

server_logger = logging.getLogger("sanic.server")  # no cov
"""
Logger used by Sanic for server related messages
"""
server_logger.addFilter(_verbosity_filter)

websockets_logger = logging.getLogger("sanic.websockets")  # no cov
"""
Logger used by Sanic for websockets module and protocol related messages
"""
websockets_logger.addFilter(_verbosity_filter)
websockets_logger.setLevel(logging.WARNING)  # Too noisy on debug/info
