from typing import Dict
import json
import os
from typing import Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import aead
from cryptography.hazmat.primitives.asymmetric import padding



def aes_encrypt(aes_key: bytes, ptxt: bytes):
    encryptor = aead.AESGCM(aes_key)
    nonce = os.urandom(12)  # AESGCM nonce size is 12
    ctxt = encryptor.encrypt(nonce, ptxt, None)
    return nonce + ctxt


def envelope_encrypt(public_key: bytes, data: Dict[str, Any]):
    aes_key = os.urandom(32)
    s = json.dumps(data)

    enc_data = aes_encrypt(aes_key, s.encode())

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
