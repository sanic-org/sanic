from datetime import datetime
import re
import string

# ------------------------------------------------------------ #
#  SimpleCookie
# ------------------------------------------------------------ #

# Straight up copied this section of dark magic from SimpleCookie

_LegalChars = string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~:"
_UnescapedChars = _LegalChars + ' ()/<=>?@[]{}'

_Translator = {n: '\\%03o' % n
               for n in set(range(256)) - set(map(ord, _UnescapedChars))}
_Translator.update({
    ord('"'): '\\"',
    ord('\\'): '\\\\',
})


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


_is_legal_key = re.compile('[%s]+' % re.escape(_LegalChars)).fullmatch

# ------------------------------------------------------------ #
#  Custom SimpleCookie
# ------------------------------------------------------------ #


class CookieJar(dict):
    """
    CookieJar dynamically writes headers as cookies are added and removed
    It gets around the limitation of one header per name by using the
    MultiHeader class to provide a unique key that encodes to Set-Cookie
    """
    def __init__(self, headers):
        super().__init__()
        self.headers = headers
        self.cookie_headers = {}

    def __setitem__(self, key, value):
        # If this cookie doesn't exist, add it to the header keys
        cookie_header = self.cookie_headers.get(key)
        if not cookie_header:
            cookie = Cookie(key, value)
            cookie_header = MultiHeader("Set-Cookie")
            self.cookie_headers[key] = cookie_header
            self.headers[cookie_header] = cookie
            return super().__setitem__(key, cookie)
        else:
            self[key].value = value

    def __delitem__(self, key):
        del self.cookie_headers[key]
        return super().__delitem__(key)


class Cookie(dict):
    """
    This is a stripped down version of Morsel from SimpleCookie #gottagofast
    """
    _keys = {
        "expires": "expires",
        "path": "Path",
        "comment": "Comment",
        "domain": "Domain",
        "max-age": "Max-Age",
        "secure": "Secure",
        "httponly": "HttpOnly",
        "version": "Version",
    }
    _flags = {'secure', 'httponly'}

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
        return super().__setitem__(key, value)

    def encode(self, encoding):
        output = ['%s=%s' % (self.key, _quote(self.value))]
        for key, value in self.items():
            if key == 'max-age' and isinstance(value, int):
                output.append('%s=%d' % (self._keys[key], value))
            elif key == 'expires' and isinstance(value, datetime):
                output.append('%s=%s' % (
                    self._keys[key],
                    value.strftime("%a, %d-%b-%Y %T GMT")
                ))
            elif key in self._flags:
                output.append(self._keys[key])
            else:
                output.append('%s=%s' % (self._keys[key], value))

        return "; ".join(output).encode(encoding)

# ------------------------------------------------------------ #
#  Header Trickery
# ------------------------------------------------------------ #


class MultiHeader:
    """
    Allows us to set a header within response that has a unique key,
    but may contain duplicate header names
    """
    def __init__(self, name):
        self.name = name

    def encode(self):
        return self.name.encode()
