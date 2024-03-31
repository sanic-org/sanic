from warnings import warn

from sanic.helpers import is_atty
from sanic.logging.color import Colors


def deprecation(message: str, version: float):  # no cov
    """
    Add a deprecation notice

    Example when a feature is being removed. In this case, version
    should be AT LEAST next version + 2

        deprecation("Helpful message", 99.9)

    Example when a feature is deprecated but not being removed:

        deprecation("Helpful message", 0)

    :param message: The message of the notice
    :type message: str
    :param version: The version when the feature will be removed. If it is
      not being removed, then set version=0.
    :type version: float
    """
    version_display = f" v{version}" if version else ""
    version_info = f"[DEPRECATION{version_display}] "
    if is_atty():
        version_info = f"{Colors.RED}{version_info}"
        message = f"{Colors.YELLOW}{message}{Colors.END}"
    warn(version_info + message, DeprecationWarning)
