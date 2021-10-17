from datetime import datetime, timedelta
from ipaddress import ip_address
from os import path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509 import (
    BasicConstraints,
    CertificateBuilder,
    DNSName,
    ExtendedKeyUsage,
    IPAddress,
    KeyUsage,
    Name,
    NameAttribute,
    SubjectAlternativeName,
    random_serial_number,
)
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def writefiles(key, cert):
    cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    folder = path.join(path.dirname(__file__), cn)
    with open(path.join(folder, "fullchain.pem"), "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    with open(path.join(folder, "privkey.pem"), "wb") as f:
        f.write(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )


def selfsigned(key, common_name, san):
    subject = issuer = Name(
        [
            NameAttribute(NameOID.COMMON_NAME, common_name),
            NameAttribute(NameOID.ORGANIZATION_NAME, "Sanic Org"),
        ]
    )
    cert = (
        CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365.25 * 8))
        .add_extension(
            KeyUsage(
                True, False, False, False, False, False, False, False, False
            ),
            critical=True,
        )
        .add_extension(
            ExtendedKeyUsage(
                [
                    ExtendedKeyUsageOID.SERVER_AUTH,
                    ExtendedKeyUsageOID.CLIENT_AUTH,
                ]
            ),
            critical=False,
        )
        .add_extension(
            BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            SubjectAlternativeName(
                [
                    IPAddress(ip_address(n))
                    if n[0].isdigit() or ":" in n
                    else DNSName(n)
                    for n in san
                ]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    return cert


# Sanic example/test self-signed cert RSA
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
cert = selfsigned(
    key,
    "sanic.example",
    [
        "sanic.example",
        "www.sanic.example",
        "*.sanic.test",
        "2001:db8::541c",
        "localhost",
    ],
)
writefiles(key, cert)

# Sanic localhost self-signed cert ECDSA
key = ec.generate_private_key(ec.SECP256R1)
cert = selfsigned(
    key,
    "localhost",
    [
        "localhost",
        "127.0.0.1",
        "::1",
    ],
)
writefiles(key, cert)
