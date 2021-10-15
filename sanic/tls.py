import os
import ssl

from sanic.log import logger


def process_to_context(context):
    """Process app.run ssl argument from easy formats to full SSLContext."""
    if isinstance(context, dict):
        # try common aliaseses
        cert = context.get("cert") or context.get("certificate")
        key = context.get("key") or context.get("keyfile")
        if cert is None or key is None:
            raise ValueError("SSLContext or certificate and key required.")
        context = create_context()
        context.load_cert_chain(cert, keyfile=key)
    elif isinstance(context, list):
        context = SSLSelector(*context).context
    return context


def create_context():
    """Create a context with secure crypto and HTTP/1.1 in protocols."""
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.set_alpn_protocols(["http/1.1"])
    context.set_ciphers(
        "ECDHE-ECDSA-AES256-GCM-SHA384:"
        "ECDHE-ECDSA-CHACHA20-POLY1305:"
        "ECDHE-ECDSA-AES128-GCM-SHA256"
    )
    return context


def load_cert_dir(p):
    if os.path.isfile(p):
        raise ValueError(f"Certificate directory expected but {p} is a file.")
    pub = os.path.join(p, "fullchain.pem")
    pub2 = os.path.join(p, "chain.pem")
    key = os.path.join(p, "privkey.pem")
    if not os.access(key, os.R_OK):
        raise Exception(f"Certificate not found or permission denied {key}")
    if not os.access(pub, os.R_OK):
        if os.access(pub2, os.R_OK):
            pub = pub2
        else:
            raise Exception(
                f"Certificate {pub} (alternatively, chain.pem) cannot be read."
            )
    try:
        ctx = create_context()
        ctx.load_cert_chain(pub, keyfile=key)
        cert = ssl._ssl._test_decode_cert(pub)
    except Exception as e:
        raise Exception(f"Error reading {pub}: {e}")
    return cert, ctx


class SSLSelector:
    def __init__(self, *paths):
        """Automatically select SSL certificate based on the hostname that the
        client is trying to access, via SSL SNI. Paths to certificate folders
        with privkey.pem and fullchain.pem in them should be provided, and
        will be matched in the order given whenever there is a new connection.
        """
        self.context = create_context()
        self.context.sni_callback = self._callback
        self.names = []
        self.certs = []
        for p in paths:
            cert, ctx = load_cert_dir(p)
            self.names += [
                name
                for t, name in cert["subjectAltName"]
                if t in ["DNS", "IP"]
            ]
            self.certs.append((cert, ctx))
        logger.info(f"Loaded certificates for {', '.join(self.names)}")

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

    def _callback(self, ssock, hostname, ctx):
        try:
            ssock.context = self.find(hostname)
        except ssl.CertificateError:
            # I think this is supposed to raise ERR_SSL_UNRECOGNIZED_NAME_ALERT
            # on the client side but I am only getting ERR_CONNECTION_CLOSED.
            return ssl.ALERT_DESCRIPTION_UNRECOGNIZED_NAME
