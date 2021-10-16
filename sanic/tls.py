import os
import ssl

from sanic.log import logger


# Only allow secure ciphers, notably leaving out AES-CBC mode
# OpenSSL chooses ECDSA or RSA depending on the cert in use
CIPHERS_TLS12 = [
    "ECDHE-ECDSA-CHACHA20-POLY1305",
    "ECDHE-ECDSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-AES128-GCM-SHA256",
    "ECDHE-RSA-CHACHA20-POLY1305",
    "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-RSA-AES128-GCM-SHA256",
]


def create_context(certfile=None, keyfile=None):
    """Create a context with secure crypto and HTTP/1.1 in protocols."""
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.set_ciphers(":".join(CIPHERS_TLS12))
    context.set_alpn_protocols(["http/1.1"])
    if certfile and keyfile:
        context.load_cert_chain(certfile, keyfile)
    return context


def process_to_context(context):
    """Process app.run ssl argument from easy formats to full SSLContext."""
    if context is None:
        return None
    if isinstance(context, ssl.SSLContext):
        return context
    if isinstance(context, dict):
        # try common aliaseses
        certfile = context.get("cert") or context.get("certificate")
        keyfile = context.get("key") or context.get("keyfile")
        if not certfile or not keyfile:
            raise ValueError("SSL dict needs filenames for cert and key.")
        return create_context(certfile, keyfile)
    if isinstance(context, (list, tuple)):
        return SSLSelector(*context).context
    raise ValueError(
        f"Invalid ssl argument type {type(context)}."
        " Expecting a list of certdirs, a dict or an SSLContext."
    )


def load_cert_dir(p):
    if os.path.isfile(p):
        raise ValueError(f"Certificate folder expected but {p} is a file.")
    keyfile = os.path.join(p, "privkey.pem")
    certfile = os.path.join(p, "fullchain.pem")
    if not os.access(keyfile, os.R_OK):
        raise Exception(
            f"Certificate not found or permission denied {keyfile}"
        )
    if not os.access(certfile, os.R_OK):
        raise Exception(
            f"Certificate not found or permission denied {certfile}"
        )
    cert = ssl._ssl._test_decode_cert(certfile)
    return cert, create_context(certfile, keyfile)


class SSLSelector:
    def __init__(self, *paths):
        """Automatically select SSL certificate based on the hostname that the
        client is trying to access, via SSL SNI. Paths to certificate folders
        with privkey.pem and fullchain.pem in them should be provided, and
        will be matched in the order given whenever there is a new connection.
        """
        self.context = create_context()
        self.context.sni_callback = self._sni_callback
        self.names = []
        self.certs = []
        for p in paths:
            cert, ctx = load_cert_dir(p)
            self.names += [
                name
                for t, name in cert["subjectAltName"]
                if t in ["DNS", "IP Address"]
            ]
            self.certs.append((cert, ctx))
        logger.debug(f"Certificate vhosts: {', '.join(self.names)}")

    def find(self, hostname):
        """Find the first certificate that matches the given hostname.

        :raises ssl.CertificateError: No matching certificate found.
        :return: A matching ssl.SSLContext object if found."""
        if not hostname:
            raise ssl.CertificateError(
                "The client provided no SNI to match for certificate."
            )
        for cert, ctx in self.certs:
            try:
                ssl.match_hostname(cert, hostname)
                return ctx
            except ssl.CertificateError:
                pass
        raise ssl.CertificateError(
            f"No certificate found matching hostname {hostname!r}"
        )

    def _sni_callback(self, sslobj, server_name, ctx):
        sslobj.server_name = server_name
        try:
            sslobj.context = self.find(server_name)
        except ssl.CertificateError:
            logger.debug(
                f"Rejecting TLS connection to unrecognized SNI {server_name!r}"
            )
            # This would show ERR_SSL_UNRECOGNIZED_NAME_ALERT on client side if
            # asyncio/uvloop did proper SSL shutdown. They don't.
            return ssl.ALERT_DESCRIPTION_UNRECOGNIZED_NAME
