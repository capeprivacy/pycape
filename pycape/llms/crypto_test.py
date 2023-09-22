import os

from pycape.llms.crypto import aes_decrypt
from pycape.llms.crypto import aes_encrypt


def test_encrypt_decrypt():
    expected = b"hi there"

    key = os.urandom(32)
    ciphertext = aes_encrypt(expected, key)

    assert expected == aes_decrypt(ciphertext, key)


def test_envelope_encrypt():
    pass
