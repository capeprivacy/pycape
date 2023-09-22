import json
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa

from pycape.llms.crypto import aes_decrypt
from pycape.llms.crypto import aes_encrypt
from pycape.llms.crypto import envelope_encrypt

KEY_PREFIX_LENGTH = 512


def _envelope_decrypt(ciphertext: bytes, priv_key: rsa.RSAPrivateKey):
    enc_data_key, encrypted_data = (
        ciphertext[:KEY_PREFIX_LENGTH],
        ciphertext[KEY_PREFIX_LENGTH:],
    )

    data_key = priv_key.decrypt(
        enc_data_key,
        padding=padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return json.loads(aes_decrypt(encrypted_data, data_key))


def test_encrypt_decrypt():
    expected = b"hi there"

    key = os.urandom(32)
    ciphertext = aes_encrypt(expected, key)

    assert expected == aes_decrypt(ciphertext, key)


def test_envelope_encrypt():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    expected = {"hi": "hello"}

    ciphertext = envelope_encrypt(pem, expected)

    assert expected == _envelope_decrypt(ciphertext, private_key)
