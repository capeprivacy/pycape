import logging
import math

import cbor2
from cose.keys import EC2Key
from cose.keys.curves import P384
from cose.messages import Sign1Message
from cryptography.x509 import load_der_x509_certificate
from OpenSSL import crypto

logger = logging.getLogger("pycape")


def parse_attestation(attestation, root_cert):
    logger.debug("\n* Verifying attestation document")
    # TODO verifies the PCRs
    payload = cbor2.loads(attestation)
    doc = cbor2.loads(payload[2])

    logger.debug("* Verifying signature")
    if not verify_signature(attestation, doc["certificate"]):
        raise ValueError("wrong signature")

    logger.debug("* Verifying certificate chain")
    verify_cert_chain(root_cert, doc["cabundle"], doc["certificate"])

    public_key = doc.get("public_key")
    if public_key is None:
        raise ValueError("The public key is missing in the attestation document.")

    return public_key


def verify_signature(payload, cert) -> bool:
    cert = load_der_x509_certificate(cert)
    cert_public_numbers = cert.public_key().public_numbers()
    x = cert_public_numbers.x
    y = cert_public_numbers.y

    x = _long_to_bytes(x)
    y = _long_to_bytes(y)

    # Create the EC2 key from public key parameters
    key = EC2Key(x=x, y=y, crv=P384)

    cose_obj = cbor2.loads(payload)
    msg = Sign1Message.from_cose_obj(cose_obj, allow_unknown_attributes=True)
    msg.key = key

    # Verify the signature using the EC2 key
    return msg.verify_signature()


def verify_cert_chain(root_cert, cabundle, cert):
    cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert)

    # Create an X509Store object for the CA bundles
    store = crypto.X509Store()

    # Create the CA cert object from PEM string, and store into X509Store
    _cert = crypto.load_certificate(crypto.FILETYPE_PEM, root_cert)
    store.add_cert(_cert)

    # Get the CA bundle from attestation document and store into X509Store
    # Except the first certificate, which is the root certificate
    for _cert_binary in cabundle:
        _cert = crypto.load_certificate(crypto.FILETYPE_ASN1, _cert_binary)
        store.add_cert(_cert)

    # Get the X509Store context
    store_ctx = crypto.X509StoreContext(store, cert)

    # Validate the certificate
    # If the cert is invalid, it will raise exception
    store_ctx.verify_certificate()


def _long_to_bytes(x: int):
    bytesize = math.ceil(x.bit_length() / 8.0)
    return x.to_bytes(bytesize, byteorder="big")
