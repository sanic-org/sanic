import warnings

from sanic.testing import SanicTestClient


def sanic_endpoint_test(app, method='get', uri='/', gather_request=True,
                        debug=False, server_kwargs={},
                        *request_args, **request_kwargs):
    warnings.warn(
        "Use of sanic_endpoint_test will be deprecated in"
        "the next major version after 0.4.0.  Please use the `test_client` "
        "available on the app object.", DeprecationWarning)

    test_client = SanicTestClient(app)
    return test_client._sanic_endpoint_test(
        method, uri, gather_request, debug, server_kwargs,
        *request_args, **request_kwargs)
