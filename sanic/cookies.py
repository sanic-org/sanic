import re
import string

from datetime import datetime
from typing import Dict


DEFAULT_MAX_AGE = 0

# ------------------------------------------------------------ #
#  SimpleCookie
# ------------------------------------------------------------ #

# Straight up copied this section of dark magic from SimpleCookie

_LegalChars = string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~:"
_UnescapedChars = _LegalChars + " ()/<=>?@[]{}"

_Translator = {
    n: "\\%03o" % n for n in set(range(256)) - set(map(ord, _UnescapedChars))
}
_Translator.update({ord('"'): '\\"', ord("\\"): "\\\\"})


def _quote(str):
    r"""Quote a string for use in a cookie header.
    If the string does not need to be double-quoted, then just return the
    string.  Otherwise, surround the string in doublequotes and quote
    (with a \) special characters.
    """
    if str is None or _is_legal_key(str):
        return str
    else:
        return '"' + str.translate(_Translator) + '"'


_is_legal_key = re.compile("[%s]+" % re.escape(_LegalChars)).fullmatch

# ------------------------------------------------------------ #
#  Custom SimpleCookie
# ------------------------------------------------------------ #


class CookieJar(dict):
    """
    CookieJar dynamically writes headers as cookies are added and removed
    It gets around the limitation of one header per name by using the
    MultiHeader class to provide a unique key that encodes to Set-Cookie.
    """

    def __init__(self, headers):
        super().__init__()
        self.headers: Dict[str, str] = headers
        self.cookie_headers: Dict[str, str] = {}
        self.header_key: str = "Set-Cookie"

    def __setitem__(self, key, value):
        # If this cookie doesn't exist, add it to the header keys
        if not self.cookie_headers.get(key):
            cookie = Cookie(key, value)
            cookie["path"] = "/"
            self.cookie_headers[key] = self.header_key
            self.headers.add(self.header_key, cookie)
            return super().__setitem__(key, cookie)
        else:
            self[key].value = value

    def __delitem__(self, key):
        if key not in self.cookie_headers:
            self[key] = ""
            self[key]["max-age"] = 0
        else:
            cookie_header = self.cookie_headers[key]
            # remove it from header
            cookies = self.headers.popall(cookie_header)
            for cookie in cookies:
                if cookie.key != key:
                    self.headers.add(cookie_header, cookie)
            del self.cookie_headers[key]
            return super().__delitem__(key)


class Cookie(dict):
    """A stripped down version of Morsel from SimpleCookie #gottagofast"""

    _keys = {
        "expires": "expires",
        "path": "Path",
        "comment": "Comment",
        "domain": "Domain",
        "max-age": "Max-Age",
        "secure": "Secure",
        "httponly": "HttpOnly",
        "version": "Version",
        "samesite": "SameSite",
    }
    _flags = {"secure", "httponly"}

    def __init__(self, key, value):
        if key in self._keys:
            raise KeyError("Cookie name is a reserved word")
        if not _is_legal_key(key):
            raise KeyError("Cookie key contains illegal characters")
        self.key = key
        self.value = value
        super().__init__()

    def __setitem__(self, key, value):
        if key not in self._keys:
            raise KeyError("Unknown cookie property")
        if value is not False:
            if key.lower() == "max-age":
                if not str(value).isdigit():
                    raise ValueError("Cookie max-age must be an integer")
            elif key.lower() == "expires":
                if not isinstance(value, datetime):
                    raise TypeError(
                        "Cookie 'expires' property must be a datetime"
                    )
            return super().__setitem__(key, value)

    def encode(self, encoding):
        """
        Encode the cookie content in a specific type of encoding instructed
        by the developer. Leverages the :func:`str.encode` method provided
        by python.

        This method can be used to encode and embed ``utf-8`` content into
        the cookies.

        :param encoding: Encoding to be used with the cookie
        :return: Cookie encoded in a codec of choosing.
        :except: UnicodeEncodeError
        """
        return str(self).encode(encoding)

    def __str__(self):
        """Format as a Set-Cookie header value."""
        output = ["%s=%s" % (self.key, _quote(self.value))]
        for key, value in self.items():
            if key == "max-age":
                try:
                    output.append("%s=%d" % (self._keys[key], value))
                except TypeError:
                    output.append("%s=%s" % (self._keys[key], value))
            elif key == "expires":
                output.append(
                    "%s=%s"
                    % (self._keys[key], value.strftime("%a, %d-%b-%Y %T GMT"))
                )
            elif key in self._flags and self[key]:
                output.append(self._keys[key])
            else:
                output.append("%s=%s" % (self._keys[key], value))

        return "; ".join(output)
