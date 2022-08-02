from cose.keys.curves import P384
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding

from pycape.attestation import parse_attestation
from pycape.attestation_test import create_attestation_doc
from pycape.attestation_test import create_certs
from pycape.attestation_test import create_cose_1_sign_msg
from pycape.enclave_encrypt import encrypt


class TestEnclaveEncryption:
    def test_data_encryption(self):
        plaintext = b"private_data"

        crv = P384
        root_private_key = ec.generate_private_key(
            crv.curve_obj, backend=default_backend()
        )
        private_key = ec.generate_private_key(crv.curve_obj, backend=default_backend())

        root_cert, cert = create_certs(root_private_key, private_key)
        doc_bytes = create_attestation_doc(root_cert, cert)
        attestation = create_cose_1_sign_msg(doc_bytes, private_key)

        public_key, _ = parse_attestation(
            attestation, root_cert.public_bytes(Encoding.PEM)
        )
        _ = encrypt(public_key, plaintext)
