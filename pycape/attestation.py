import io
import logging
import math
import zipfile

import cbor2
import requests
from cose.keys import EC2Key
from cose.keys.curves import P384
from cose.messages import Sign1Message
from cryptography.x509 import load_der_x509_certificate
from OpenSSL import crypto

_AWS_ROOT_CERT_ARCHIVE = (
    "https://aws-nitro-enclaves.amazonaws.com/AWS_NitroEnclaves_Root-G1.zip"
)

logger = logging.getLogger("pycape")


def download_root_cert():
    logger.debug(
        f"* Downloading AWS root cert for attestation from {_AWS_ROOT_CERT_ARCHIVE}..."
    )
    r = requests.get(_AWS_ROOT_CERT_ARCHIVE)
    f = zipfile.ZipFile(io.BytesIO(r.content))
    with f.open("root.pem") as p:
        root_cert = p.read()
    logger.debug("AWS root cert received.")
    return root_cert


def parse_attestation(attestation, root_cert):
    logger.debug("* Parsing attestation document...")
    # TODO verifies the PCRs
    payload = cbor2.loads(attestation)
    doc = cbor2.loads(payload[2])
    _check_wellformed_attestation(
        doc,
        expected_keys=["certificate", "cabundle", "public_key"],
    )
    doc_cert = doc["certificate"]
    cabundle = doc["cabundle"]
    public_key = doc["public_key"]
    logger.debug("* Attestation document parsed.")

    verify_attestation_signature(attestation, doc_cert)
    verify_cert_chain(root_cert, cabundle, doc_cert)
    # Send back optional parameter user_data
    user_data = doc.get("user_data")
    return public_key, user_data


def verify_cert_chain(root_cert, cabundle, cert):
    logger.debug("* Verifying attestation certificate chain...")
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
    logger.debug("* Attestation certificate chain verified.")


def verify_attestation_signature(payload, cert):
    logger.debug("* Verifying attestation certificate signature...")
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
    verified = msg.verify_signature()
    if not verified:
        errmsg = "Malformed attestation doc: incorrect certificate signature."
        logger.error(errmsg)
        raise RuntimeError(errmsg)
    logger.debug("* Attestation certificate signature verified.")


def _long_to_bytes(x: int):
    bytesize = math.ceil(x.bit_length() / 8.0)
    return x.to_bytes(bytesize, byteorder="big")


def _check_wellformed_attestation(doc, expected_keys):
    for doc_key in expected_keys:
        if doc_key not in doc:
            errmsg = (
                "Malformed attestation doc: missing attestation "
                f"document field {doc_key}."
            )
            logger.error(errmsg)
            raise RuntimeError(errmsg)
