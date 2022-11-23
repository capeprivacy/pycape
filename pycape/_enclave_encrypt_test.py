import base64

from pycape._enclave_encrypt import encrypt


class TestEnclaveEncryption:
    def test_data_encryption(self):
        plaintext = b"private_data"

        public_key = base64.b64decode("d4Y4fxNr/hga+d86m2Lw+SXu+QO6Uuk3yrtrS9CoVgI=")

        _ = encrypt(public_key, plaintext)
