import base64
import datetime
import json
import time

import cbor2
import pytest
from cose.algorithms import Es384
from cose.keys import EC2Key
from cose.keys.curves import P384
from cose.messages import Sign1Message
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID
from OpenSSL import crypto

from pycape import _attestation as attest

root_subject = issuer = x509.Name(
    [
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Texas"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Austin"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, "My CA"),
    ]
)

intermediate_subject = issuer = x509.Name(
    [
        x509.NameAttribute(NameOID.COUNTRY_NAME, "JP"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Tokyo"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Tokyo"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Cool Comp"),
        x509.NameAttribute(NameOID.COMMON_NAME, "COOL"),
    ]
)

cert_subject = x509.Name(
    [
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CA"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Nova Scotia"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Halifax"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "New Org Name!"),
    ]
)


class TestAttestation:
    def test_parse_attestation(self):
        crv = P384
        root_private_key = ec.generate_private_key(
            crv.curve_obj, backend=default_backend()
        )
        private_key = ec.generate_private_key(crv.curve_obj, backend=default_backend())

        root_cert = create_root_cert(root_private_key, root_subject)
        intermediate_cert = create_child_cert(
            root_cert, root_private_key, root_private_key, intermediate_subject, ca=True
        )
        cert = create_child_cert(
            intermediate_cert, root_private_key, private_key, cert_subject, ca=False
        )
        doc_bytes = create_attestation_doc(intermediate_cert, cert)
        attestation = create_cose_1_sign_msg(doc_bytes, private_key)

        attestation_doc = attest.parse_attestation(
            attestation, root_cert.public_bytes(Encoding.PEM)
        )
        public_key = attestation_doc["public_key"]
        user_data = attestation_doc.get("user_data")
        expected_user_data = json.dumps({"func_hash": "stuff"})
        assert user_data == expected_user_data
        assert len(public_key) == 32

    def test_verify_attestation_signature(self):
        crv = P384
        root_private_key = ec.generate_private_key(
            crv.curve_obj, backend=default_backend()
        )
        private_key = ec.generate_private_key(crv.curve_obj, backend=default_backend())

        root_cert = create_root_cert(root_private_key, root_subject)
        intermediate_cert = create_child_cert(
            root_cert, root_private_key, root_private_key, intermediate_subject, ca=True
        )
        cert = create_child_cert(
            intermediate_cert, root_private_key, private_key, cert_subject, ca=False
        )
        doc_bytes = create_attestation_doc(intermediate_cert, cert)
        attestation = create_cose_1_sign_msg(doc_bytes, private_key)

        payload = cbor2.loads(attestation)
        doc = cbor2.loads(payload[2])

        attest.verify_attestation_signature(attestation, doc["certificate"])

    def test_verify_cert_chain(self):
        crv = P384
        root_private_key = ec.generate_private_key(
            crv.curve_obj, backend=default_backend()
        )
        private_key = ec.generate_private_key(crv.curve_obj, backend=default_backend())

        root_cert = create_root_cert(root_private_key, root_subject)
        intermediate_cert = create_child_cert(
            root_cert, root_private_key, root_private_key, intermediate_subject, ca=True
        )
        cert = create_child_cert(
            intermediate_cert, root_private_key, private_key, cert_subject
        )

        doc_bytes = create_attestation_doc(intermediate_cert, cert)
        attestation = create_cose_1_sign_msg(doc_bytes, private_key)

        payload = cbor2.loads(attestation)
        doc = cbor2.loads(payload[2])

        root_cert_pem = root_cert.public_bytes(Encoding.PEM)

        attest.verify_cert_chain(root_cert_pem, doc["cabundle"], doc["certificate"])

    def test_verify_cert_chain_fails_if_bad_intermediate(self):
        crv = P384
        root_private_key = ec.generate_private_key(
            crv.curve_obj, backend=default_backend()
        )
        intermediate_private_key = ec.generate_private_key(
            crv.curve_obj, backend=default_backend()
        )

        private_key = ec.generate_private_key(crv.curve_obj, backend=default_backend())

        root_cert = create_root_cert(root_private_key, root_subject)
        intermediate_cert = create_root_cert(
            intermediate_private_key, intermediate_subject
        )
        cert = create_child_cert(
            intermediate_cert, root_private_key, private_key, cert_subject, ca=False
        )

        doc_bytes = create_attestation_doc(intermediate_cert, cert)
        attestation = create_cose_1_sign_msg(doc_bytes, private_key)

        payload = cbor2.loads(attestation)
        doc = cbor2.loads(payload[2])

        root_cert_pem = root_cert.public_bytes(Encoding.PEM)

        with pytest.raises(crypto.X509StoreContextError):
            attest.verify_cert_chain(root_cert_pem, doc["cabundle"], doc["certificate"])

    def test_verify_pcrs(self):
        crv = P384
        root_private_key = ec.generate_private_key(
            crv.curve_obj, backend=default_backend()
        )
        private_key = ec.generate_private_key(crv.curve_obj, backend=default_backend())

        root_cert = create_root_cert(root_private_key, root_subject)
        intermediate_cert = create_child_cert(
            root_cert, root_private_key, root_private_key, intermediate_subject, ca=True
        )
        cert = create_child_cert(
            intermediate_cert, root_private_key, private_key, cert_subject, ca=False
        )
        doc_bytes = create_attestation_doc(intermediate_cert, cert)
        attestation = create_cose_1_sign_msg(doc_bytes, private_key)

        attestation_doc = attest.parse_attestation(
            attestation, root_cert.public_bytes(Encoding.PEM)
        )

        attest.verify_pcrs({"0": [b"pcrpcrpcr".hex()]}, attestation_doc)

    def test_verify_pcrs_fail(self):
        crv = P384
        root_private_key = ec.generate_private_key(
            crv.curve_obj, backend=default_backend()
        )
        private_key = ec.generate_private_key(crv.curve_obj, backend=default_backend())

        root_cert = create_root_cert(root_private_key, root_subject)
        intermediate_cert = create_child_cert(
            root_cert, root_private_key, root_private_key, intermediate_subject, ca=True
        )
        cert = create_child_cert(
            intermediate_cert, root_private_key, private_key, cert_subject, ca=False
        )
        doc_bytes = create_attestation_doc(intermediate_cert, cert)
        attestation = create_cose_1_sign_msg(doc_bytes, private_key)

        attestation_doc = attest.parse_attestation(
            attestation, root_cert.public_bytes(Encoding.PEM)
        )

        with pytest.raises(Exception):
            attest.verify_pcrs({"0": [b"pcrpcr".hex()]}, attestation_doc)


def create_cose_1_sign_msg(payload, private_key):
    crv = P384
    d_value = private_key.private_numbers().private_value
    x_coor = private_key.public_key().public_numbers().x
    y_coor = private_key.public_key().public_numbers().y

    key = EC2Key(
        crv=crv,
        d=d_value.to_bytes(crv.size, "big"),
        x=x_coor.to_bytes(crv.size, "big"),
        y=y_coor.to_bytes(crv.size, "big"),
    )

    phdr = {1: Es384}
    msg = Sign1Message(phdr=phdr, payload=payload, key=key)

    sig = msg.compute_signature()
    msg._signature = sig

    return msg.encode(tag=False)


def create_attestation_doc(intermediate_cert, cert):
    cert = cert.public_bytes(Encoding.DER)
    intermediate_cert = intermediate_cert.public_bytes(Encoding.DER)
    user_data = json.dumps({"func_hash": "stuff"})
    public_key = base64.b64decode("d4Y4fxNr/hga+d86m2Lw+SXu+QO6Uuk3yrtrS9CoVgI=")
    obj = {
        "module_id": "my-module",
        "timestamp": time.gmtime(),
        "digest": "abcd",
        "pcrs": {0: b"pcrpcrpcr"},
        "certificate": cert,
        "cabundle": [intermediate_cert],
        "public_key": public_key,
        "user_data": user_data,
    }

    return cbor2.encoder.dumps(obj)


def create_root_cert(root_key, subject):
    issuer = subject
    root_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(root_key.public_key())
        .serial_number(x509.random_serial_number())
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .sign(root_key, hashes.SHA256(), default_backend())
    )

    return root_cert


def create_child_cert(parent_cert, parent_key, cert_key, subject, ca=False):
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(parent_cert.issuer)
        .public_key(cert_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=30))
    )

    if ca:
        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        )

    cert = builder.sign(parent_key, hashes.SHA256(), default_backend())

    return cert
