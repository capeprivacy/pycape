import json
import os
from typing import Any
from typing import Dict

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import aead

NONCE_SIZE = 12


def aes_decrypt(ctxt: bytes, key: bytes) -> bytes:
    nonce, ctxt = ctxt[:NONCE_SIZE], ctxt[NONCE_SIZE:]
    encryptor = aead.AESGCM(key)
    ptxt = encryptor.decrypt(nonce, ctxt, None)
    return ptxt


def aes_encrypt(ptxt: bytes, key: bytes):
    encryptor = aead.AESGCM(key)
    nonce = os.urandom(NONCE_SIZE)
    ctxt = encryptor.encrypt(nonce, ptxt, None)
    return nonce + ctxt


def envelope_encrypt(public_key: bytes, data: Dict[str, Any]):
    aes_key = os.urandom(32)
    s = json.dumps(data)

    enc_data = aes_encrypt(s.encode(), aes_key)

    pub = serialization.load_pem_public_key(public_key)

    enc_data_key = pub.encrypt(
        aes_key,
        padding=padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return enc_data_key + enc_data
