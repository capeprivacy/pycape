import base64
import datetime
import io
import json
import time
import zipfile

import cbor2
import requests
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

from pycape import attestation as attest


class TestAttestation:
    def test_parse_attestation(self):
        crv = P384
        root_private_key = ec.generate_private_key(
            crv.curve_obj, backend=default_backend()
        )
        private_key = ec.generate_private_key(crv.curve_obj, backend=default_backend())

        root_cert, cert = create_certs(root_private_key, private_key)
        doc_bytes = create_attestation_doc(root_cert, cert)
        attestation = create_cose_1_sign_msg(doc_bytes, private_key)

        public_key, user_data = attest.parse_attestation(
            attestation, root_cert.public_bytes(Encoding.PEM)
        )
        expected_user_data = json.dumps({"func_hash": "stuff"})
        assert user_data == expected_user_data
        assert len(public_key) == 32

    def test_verify_attestation_signature(self):
        crv = P384
        root_private_key = ec.generate_private_key(
            crv.curve_obj, backend=default_backend()
        )
        private_key = ec.generate_private_key(crv.curve_obj, backend=default_backend())

        root_cert, cert = create_certs(root_private_key, private_key)
        doc_bytes = create_attestation_doc(root_cert, cert)
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

        root_cert, cert = create_certs(root_private_key, private_key)
        doc_bytes = create_attestation_doc(root_cert, cert)
        attestation = create_cose_1_sign_msg(doc_bytes, private_key)

        payload = cbor2.loads(attestation)
        doc = cbor2.loads(payload[2])

        url = "https://aws-nitro-enclaves.amazonaws.com/AWS_NitroEnclaves_Root-G1.zip"
        r = requests.get(url)

        f = zipfile.ZipFile(io.BytesIO(r.content))
        with f.open("root.pem") as p:
            root_cert = p.read()

        attest.verify_cert_chain(root_cert, doc["cabundle"], doc["certificate"])


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


def create_attestation_doc(root_cert, cert):
    cert = cert.public_bytes(Encoding.DER)
    root_cert = root_cert.public_bytes(Encoding.DER)
    user_data = json.dumps({"func_hash": "stuff"})
    public_key = base64.b64decode("d4Y4fxNr/hga+d86m2Lw+SXu+QO6Uuk3yrtrS9CoVgI=")
    obj = {
        "module_id": "my-module",
        "timestamp": time.gmtime(),
        "digest": "abcd",
        "pcrs": {0: b"pcrpcrpcr"},
        "certificate": cert,
        "cabundle": [root_cert],
        "public_key": public_key,
        "user_data": user_data,
    }

    return cbor2.encoder.dumps(obj)


def create_certs(root_key, cert_key):
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Texas"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Austin"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Company"),
            x509.NameAttribute(NameOID.COMMON_NAME, "My CA"),
        ]
    )
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

    new_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Texas"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Austin"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "New Org Name!"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(new_subject)
        .issuer_name(root_cert.issuer)
        .public_key(cert_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=30))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("somedomain.com")]),
            critical=False,
        )
        .sign(root_key, hashes.SHA256(), default_backend())
    )

    return root_cert, cert
