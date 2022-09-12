import os
from typing import Tuple

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import aead


def encrypt(message: bytes, key: bytes) -> bytes:
    # cape key is DEM-encoded RSA key
    rsa_key = _parse_rsa_key(key)
    # create ephemeral AES key
    aes_key = _aes_keygen(32)
    # encrypt message w/ AES
    data_ctxt, nonce = _aes_encrypt(message)
    # encrypt the ephemeral AES key w/ RSA
    key_ctxt = _rsa_encrypt(aes_key, rsa_key)
    # concatenate everything into a single bytes obj
    final_ctxt = key_ctxt + nonce + data_ctxt
    return final_ctxt


def _aes_encrypt(inputs: bytes, key: bytes) -> Tuple[bytes, bytes]:
    encryptor = aead.AESGCM(key)
    nonce = os.urandom(12)  # AESGCM nonce size is 12
    ctxt = encryptor.encrypt(nonce, inputs, None)
    return ctxt, nonce


def _aes_keygen(bitlength: int) -> bytes:
    return aead.AESGCM.generate_aes_key(bitlength)


def _parse_rsa_key(key: bytes) -> rsa.RSAPublicKey:
    return x509.load_der_x609_certificate(key).public_key()


def _rsa_encrypt(inputs: bytes, public_key: rsa.RSAPublicKey) -> bytes:
    return public_key.encrypt(
        inputs,
        padding=padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
