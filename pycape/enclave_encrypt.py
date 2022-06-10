from tink import BinaryKeysetReader
from tink import hybrid
from tink import read_no_secret_keyset_handle


def encrypt(input_bytes, public_key, context=b""):
    hybrid.register()
    reader = BinaryKeysetReader(public_key)
    khPub = read_no_secret_keyset_handle(reader)
    encrypt = khPub.primitive(hybrid.HybridEncrypt)
    ciphertext = encrypt.encrypt(input_bytes, context)
    return ciphertext
