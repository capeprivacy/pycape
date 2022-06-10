import io

import tink
from tink import cleartext_keyset_handle

from pycape.enclave_encrypt import encrypt


class TestEnclaveEncryption:
    def test_data_encryption(self):
        plaintext = b"private_data"
        context = b""

        tink.hybrid.register()
        private_keyset_handle = tink.new_keyset_handle(
            tink.hybrid.hybrid_key_templates.ECIES_P256_HKDF_HMAC_SHA256_AES128_GCM
        )
        public_keyset_handle = private_keyset_handle.public_keyset_handle()
        public_key_stream = io.BytesIO()
        writer = tink.BinaryKeysetWriter(public_key_stream)
        cleartext_keyset_handle.write(writer, public_keyset_handle)
        ciphertext = encrypt(plaintext, public_key_stream.getvalue(), context)
        decrypt = private_keyset_handle.primitive(tink.hybrid.HybridDecrypt)
        decrypted_data = decrypt.decrypt(ciphertext, context)

        assert plaintext == decrypted_data
