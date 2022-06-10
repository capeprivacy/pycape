import base64

from tink import BinaryKeysetReader
from tink import hybrid
from tink import read_no_secret_keyset_handle


def encrypt(public_key, input_bytes):
    hybrid.register()
    reader = BinaryKeysetReader(public_key)
    khPub = read_no_secret_keyset_handle(reader)
    encrypt = khPub.primitive(hybrid.HybridEncrypt)
    ciphertext = encrypt.encrypt(input_bytes, b"")
    encoded = base64.b64encode(ciphertext).decode("utf-8")
    return encoded
