import logging

import hybrid_pke

logger = logging.getLogger("pycape")


def encrypt(public_key, input_bytes):
    logger.debug("* Encrypting inputs with Hybrid Public Key Encryption (HPKE)")
    hpke = hybrid_pke.default()
    info = b""
    aad = b""
    encap, ciphertext = hpke.seal(public_key, info, aad, input_bytes)
    return encap + ciphertext
