# -*- encoding: utf-8 -*-

import hashlib

from itsdangerous import URLSafeTimedSerializer
from datetime import datetime

import ujson as json
from sanic.exceptions import BadSignature


def total_seconds(td):
    """Returns the total seconds from a timedelta object.
    :param timedelta td: the timedelta to be converted in seconds
    :returns: number of seconds
    :rtype: int
    """
    return td.days * 60 * 60 * 24 + td.seconds


class SessionMixin(object):
    """Expands a basic dictionary with an accessors that are expected
    by Flask extensions and users for the session.
    """

    def _get_permanent(self):
        return self.get('_permanent', False)

    def _set_permanent(self, value):
        self['_permanent'] = bool(value)

    #: this reflects the ``'_permanent'`` key in the dict.
    permanent = property(_get_permanent, _set_permanent)
    del _get_permanent, _set_permanent

    #: some session backends can tell you if a session is new, but that is
    #: not necessarily guaranteed.  Use with caution.  The default mixin
    #: implementation just hardcodes ``False`` in.
    new = False

    #: for some backends this will always be ``True``, but some backends will
    #: default this to false and detect changes in the dictionary for as
    #: long as changes do not happen on mutable structures in the session.
    #: The default mixin implementation just hardcodes ``True`` in.
    modified = True

    #: the accessed variable indicates whether or not the session object has
    #: been accessed in that request. This allows flask to append a `Vary:
    #: Cookie` header to the response if the session is being accessed. This
    #: allows caching proxy servers, like Varnish, to use both the URL and the
    #: session cookie as keys when caching pages, preventing multiple users
    #: from being served the same cache.
    accessed = True


class SecureCookieSession(dict, SessionMixin):
    """Base class for sessions based on signed cookies."""

    def __init__(self, initial=None):
        if initial is None:
            super(SecureCookieSession, self).__init__()
        else:
            super(SecureCookieSession, self).__init__(initial)
        self.modified = False
        self.accessed = False

    def __getitem__(self, key):
        self.accessed = True
        return super(SecureCookieSession, self).__getitem__(key)

    def __setitem__(self, key, value):
        self.modified = True
        return super(SecureCookieSession, self).__setitem__(key, value)

    def get(self, key, default=None):
        self.accessed = True
        return super(SecureCookieSession, self).get(key, default)

    def setdefault(self, key, default=None):
        self.accessed = True
        return super(SecureCookieSession, self).setdefault(key, default)


class NullSession(SecureCookieSession):
    """Class used to generate nicer error messages if sessions are not
    available.  Will still allow read-only access to the empty session
    but fail on setting.
    """

    def _fail(self, *args, **kwargs):
        raise RuntimeError('The session is unavailable because no secret '
                           'key was set.  Set the secret_key on the '
                           'application to something unique and secret.')
    __setitem__ = __delitem__ = clear = pop = popitem = \
        update = setdefault = _fail
    del _fail


class SessionInterface(object):
    null_session_class = NullSession
    pickle_based = False

    def make_null_session(self, app):
        """Creates a null session which acts as a replacement object if the
        real session support could not be loaded due to a configuration
        error.  This mainly aids the user experience because the job of the
        null session is to still support lookup without complaining but
        modifications are answered with a helpful error message of what
        failed.
        This creates an instance of :attr:`null_session_class` by default.
        """
        return self.null_session_class()

    def is_null_session(self, obj):
        """Checks if a given object is a null session.  Null sessions are
        not asked to be saved.
        This checks if the object is an instance of :attr:`null_session_class`
        by default.
        """
        return isinstance(obj, self.null_session_class)

    def get_cookie_domain(self, app):
        """Returns the domain that should be set for the session cookie.
        Uses ``SESSION_COOKIE_DOMAIN`` if it is configured, otherwise
        falls back to detecting the domain based on ``SERVER_NAME``.
        Once detected (or if not set at all), ``SESSION_COOKIE_DOMAIN`` is
        updated to avoid re-running the logic.
        """

        rv = app.config.get('SESSION_COOKIE_DOMAIN')

        # set explicitly, or cached from SERVER_NAME detection
        # if False, return None
        if rv is not None:
            return rv if rv else None

        rv = app.config.get('SERVER_NAME')

        # server name not set, cache False to return none next time
        if not rv:
            app.config['SESSION_COOKIE_DOMAIN'] = False
            return None

        # chop off the port which is usually not supported by browsers
        # remove any leading '.' since we'll add that later
        rv = rv.rsplit(':', 1)[0].lstrip('.')

        if '.' not in rv:
            # Chrome doesn't allow names without a '.'
            # this should only come up with localhost
            # hack around this by not setting the name, and show a warning
            app.config['SESSION_COOKIE_DOMAIN'] = False
            return None

        # if this is not an ip and app is mounted at the root, allow subdomain
        # matching by adding a '.' prefix
        if self.get_cookie_path(app) == '/':
            rv = '.' + rv

        app.config['SESSION_COOKIE_DOMAIN'] = rv
        return rv

    def get_cookie_path(self, app):
        """Returns the path for which the cookie should be valid.  The
        default implementation uses the value from the ``SESSION_COOKIE_PATH``
        config var if it's set, and falls back to ``APPLICATION_ROOT`` or
        uses ``/`` if it's ``None``.
        """
        return app.config.get('SESSION_COOKIE_PATH') \
            or app.config.get('APPLICATION_ROOT', '/')

    def get_cookie_httponly(self, app):
        """Returns True if the session cookie should be httponly.  This
        currently just returns the value of the ``SESSION_COOKIE_HTTPONLY``
        config var.
        """
        return app.config.get('SESSION_COOKIE_HTTPONLY', True)

    def get_cookie_secure(self, app):
        """Returns True if the cookie should be secure.  This currently
        just returns the value of the ``SESSION_COOKIE_SECURE`` setting.
        """
        return app.config.get('SESSION_COOKIE_SECURE', True)

    def get_expiration_time(self, app, session):
        """A helper method that returns an expiration date for the session
        or ``None`` if the session is linked to the browser session.  The
        default implementation returns now + the permanent session
        lifetime configured on the application.
        """
        if session.permanent:
            return datetime.utcnow() + app.config.PERMANENT_SESSION_LIFETIME

    def should_set_cookie(self, app, session):
        """Used by session backends to determine if a ``Set-Cookie`` header
        should be set for this session cookie for this response. If the session
        has been modified, the cookie is set. If the session is permanent and
        the ``SESSION_REFRESH_EACH_REQUEST`` config is true, the cookie is
        always set.
        This check is usually skipped if the session was deleted.
        .. versionadded:: 0.11
        """

        return session.modified or (
            session.permanent and app.config.get(
                'SESSION_REFRESH_EACH_REQUEST', False)
        )

    def open_session(self, app, request):
        """This method has to be implemented and must either return ``None``
        in case the loading failed because of a configuration error or an
        instance of a session object which implements a dictionary like
        interface + the methods and attributes on :class:`SessionMixin`.
        """
        raise NotImplementedError()

    def save_session(self, app, session, response):
        """This is called for actual sessions returned by :meth:`open_session`
        at the end of the request.  This is still called during a request
        context so if you absolutely need access to the request you can do
        that.
        """
        raise NotImplementedError()


session_json_serializer = json


class SecureCookieSessionInterface(SessionInterface):
    """The default session interface that stores sessions in signed cookies
    through the :mod:`itsdangerous` module.
    """
    #: the salt that should be applied on top of the secret key for the
    #: signing of cookie based sessions.
    salt = 'cookie-session'
    #: the hash function to use for the signature.  The default is sha1
    digest_method = staticmethod(hashlib.sha1)
    #: the name of the itsdangerous supported key derivation.  The default
    #: is hmac.
    key_derivation = 'hmac'
    #: A python serializer for the payload.  The default is a compact
    #: JSON derived serializer with support for some extra Python types
    #: such as datetime objects or tuples.
    serializer = session_json_serializer
    session_class = SecureCookieSession

    def get_signing_serializer(self, app):
        if not app.config.SECRET_KEY:
            return None
        signer_kwargs = dict(
            key_derivation=self.key_derivation,
            digest_method=self.digest_method
        )

        return URLSafeTimedSerializer(app.config.SECRET_KEY, salt=self.salt,
                                      serializer=self.serializer,
                                      signer_kwargs=signer_kwargs)

    def open_session(self, app, request):
        s = self.get_signing_serializer(app)
        if s is None:
            return None
        val = request.cookies.get(app.config.SESSION_COOKIE_NAME)
        if not val:
            return self.session_class()
        max_age = total_seconds(app.config.PERMANENT_SESSION_LIFETIME)
        try:
            data = s.loads(val, max_age=max_age)
            return self.session_class(data)
        except BadSignature:
            return self.session_class()

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)

        # If the session is modified to be empty, remove the cookie.
        # If the session is empty, return without setting the cookie.
        if not session:
            if session.modified:
                response.delete_cookie(
                    app.config.SESSION_COOKIE_NAME,
                    domain=domain,
                    path=path
                )

            return

        if not self.should_set_cookie(app, session):
            return
        httponly = self.get_cookie_httponly(app)
        # secure = self.get_cookie_secure(app)
        expires = self.get_expiration_time(app, session)
        val = self.get_signing_serializer(app).dumps(dict(session))
        session_cookie_name = app.config.SESSION_COOKIE_NAME
        response.cookies[session_cookie_name] = val
        if expires:
            response.cookies[session_cookie_name]["expires"] = expires
        response.cookies[session_cookie_name]["httponly"] = httponly
        if domain:
            response.cookies[session_cookie_name]["domain"] = domain
        response.cookies[session_cookie_name]["path"] = path
        # response.cookies[session_cookie_name]["secure"] = secure
