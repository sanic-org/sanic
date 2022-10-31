from __future__ import annotations

import ssl
import subprocess
import sys

from abc import ABC, abstractmethod
from contextlib import suppress
from pathlib import Path
from tempfile import mkdtemp
from types import ModuleType
from typing import TYPE_CHECKING, Optional, Tuple, Type, Union, cast

from sanic.application.constants import Mode
from sanic.application.spinner import loading
from sanic.constants import (
    DEFAULT_LOCAL_TLS_CERT,
    DEFAULT_LOCAL_TLS_KEY,
    LocalCertCreator,
)
from sanic.exceptions import SanicException
from sanic.helpers import Default
from sanic.http.tls.context import CertSimple, SanicSSLContext


try:
    import trustme

    TRUSTME_INSTALLED = True
except (ImportError, ModuleNotFoundError):
    trustme = ModuleType("trustme")
    TRUSTME_INSTALLED = False

if TYPE_CHECKING:
    from sanic import Sanic


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


def _make_path(maybe_path: Union[Path, str], tmpdir: Optional[Path]) -> Path:
    if isinstance(maybe_path, Path):
        return maybe_path
    else:
        path = Path(maybe_path)
        if not path.exists():
            if not tmpdir:
                raise RuntimeError("Reached an unknown state. No tmpdir.")
            return tmpdir / maybe_path

    return path


def get_ssl_context(
    app: Sanic, ssl: Optional[ssl.SSLContext]
) -> ssl.SSLContext:
    if ssl:
        return ssl

    if app.state.mode is Mode.PRODUCTION:
        raise SanicException(
            "Cannot run Sanic as an HTTPS server in PRODUCTION mode "
            "without passing a TLS certificate. If you are developing "
            "locally, please enable DEVELOPMENT mode and Sanic will "
            "generate a localhost TLS certificate. For more information "
            "please see: https://sanic.dev/en/guide/deployment/development."
            "html#automatic-tls-certificate."
        )

    creator = CertCreator.select(
        app,
        cast(LocalCertCreator, app.config.LOCAL_CERT_CREATOR),
        app.config.LOCAL_TLS_KEY,
        app.config.LOCAL_TLS_CERT,
    )
    context = creator.generate_cert(app.config.LOCALHOST)
    return context


class CertCreator(ABC):
    def __init__(self, app, key, cert) -> None:
        self.app = app
        self.key = key
        self.cert = cert
        self.tmpdir = None

        if isinstance(self.key, Default) or isinstance(self.cert, Default):
            self.tmpdir = Path(mkdtemp())

        key = (
            DEFAULT_LOCAL_TLS_KEY
            if isinstance(self.key, Default)
            else self.key
        )
        cert = (
            DEFAULT_LOCAL_TLS_CERT
            if isinstance(self.cert, Default)
            else self.cert
        )

        self.key_path = _make_path(key, self.tmpdir)
        self.cert_path = _make_path(cert, self.tmpdir)

    @abstractmethod
    def check_supported(self) -> None:  # no cov
        ...

    @abstractmethod
    def generate_cert(self, localhost: str) -> ssl.SSLContext:  # no cov
        ...

    @classmethod
    def select(
        cls,
        app: Sanic,
        cert_creator: LocalCertCreator,
        local_tls_key,
        local_tls_cert,
    ) -> CertCreator:

        creator: Optional[CertCreator] = None

        cert_creator_options: Tuple[
            Tuple[Type[CertCreator], LocalCertCreator], ...
        ] = (
            (MkcertCreator, LocalCertCreator.MKCERT),
            (TrustmeCreator, LocalCertCreator.TRUSTME),
        )
        for creator_class, local_creator in cert_creator_options:
            creator = cls._try_select(
                app,
                creator,
                creator_class,
                local_creator,
                cert_creator,
                local_tls_key,
                local_tls_cert,
            )
            if creator:
                break

        if not creator:
            raise SanicException(
                "Sanic could not find package to create a TLS certificate. "
                "You must have either mkcert or trustme installed. See "
                "https://sanic.dev/en/guide/deployment/development.html"
                "#automatic-tls-certificate for more details."
            )

        return creator

    @staticmethod
    def _try_select(
        app: Sanic,
        creator: Optional[CertCreator],
        creator_class: Type[CertCreator],
        creator_requirement: LocalCertCreator,
        creator_requested: LocalCertCreator,
        local_tls_key,
        local_tls_cert,
    ):
        if creator or (
            creator_requested is not LocalCertCreator.AUTO
            and creator_requested is not creator_requirement
        ):
            return creator

        instance = creator_class(app, local_tls_key, local_tls_cert)
        try:
            instance.check_supported()
        except SanicException:
            if creator_requested is creator_requirement:
                raise
            else:
                return None

        return instance


class MkcertCreator(CertCreator):
    def check_supported(self) -> None:
        try:
            subprocess.run(  # nosec B603 B607
                ["mkcert", "-help"],
                check=True,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
            )
        except Exception as e:
            raise SanicException(
                "Sanic is attempting to use mkcert to generate local TLS "
                "certificates since you did not supply a certificate, but "
                "one is required. Sanic cannot proceed since mkcert does not "
                "appear to be installed. Alternatively, you can use trustme. "
                "Please install mkcert, trustme, or supply TLS certificates "
                "to proceed. Installation instructions can be found here: "
                "https://github.com/FiloSottile/mkcert.\n"
                "Find out more information about your options here: "
                "https://sanic.dev/en/guide/deployment/development.html#"
                "automatic-tls-certificate"
            ) from e

    def generate_cert(self, localhost: str) -> ssl.SSLContext:
        try:
            if not self.cert_path.exists():
                message = "Generating TLS certificate"
                # TODO: Validate input for security
                with loading(message):
                    cmd = [
                        "mkcert",
                        "-key-file",
                        str(self.key_path),
                        "-cert-file",
                        str(self.cert_path),
                        localhost,
                    ]
                    resp = subprocess.run(  # nosec B603
                        cmd,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )
                sys.stdout.write("\r" + " " * (len(message) + 4))
                sys.stdout.flush()
                sys.stdout.write(resp.stdout)
        finally:

            @self.app.main_process_stop
            async def cleanup(*_):  # no cov
                if self.tmpdir:
                    with suppress(FileNotFoundError):
                        self.key_path.unlink()
                        self.cert_path.unlink()
                    self.tmpdir.rmdir()

        context = CertSimple(self.cert_path, self.key_path)
        context.sanic["creator"] = "mkcert"
        context.sanic["localhost"] = localhost
        SanicSSLContext.create_from_ssl_context(context)

        return context


class TrustmeCreator(CertCreator):
    def check_supported(self) -> None:
        if not TRUSTME_INSTALLED:
            raise SanicException(
                "Sanic is attempting to use trustme to generate local TLS "
                "certificates since you did not supply a certificate, but "
                "one is required. Sanic cannot proceed since trustme does not "
                "appear to be installed. Alternatively, you can use mkcert. "
                "Please install mkcert, trustme, or supply TLS certificates "
                "to proceed. Installation instructions can be found here: "
                "https://github.com/python-trio/trustme.\n"
                "Find out more information about your options here: "
                "https://sanic.dev/en/guide/deployment/development.html#"
                "automatic-tls-certificate"
            )

    def generate_cert(self, localhost: str) -> ssl.SSLContext:
        context = SanicSSLContext.create_from_ssl_context(
            ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        )
        context.sanic = {
            "cert": self.cert_path.absolute(),
            "key": self.key_path.absolute(),
        }
        ca = trustme.CA()
        server_cert = ca.issue_cert(localhost)
        server_cert.configure_cert(context)
        ca.configure_trust(context)

        ca.cert_pem.write_to_path(str(self.cert_path.absolute()))
        server_cert.private_key_and_cert_chain_pem.write_to_path(
            str(self.key_path.absolute())
        )
        context.sanic["creator"] = "trustme"
        context.sanic["localhost"] = localhost

        return context
