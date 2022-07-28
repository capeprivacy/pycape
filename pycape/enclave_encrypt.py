import logging

import hpke_spec

logger = logging.getLogger("pycape")


def encrypt(public_key, input_bytes):
    logger.debug("* Encrypting inputs with Hybrid Public Key Encryption (HPKE)")
    ciphertext = hpke_spec.hpke_seal(public_key, input_bytes)
    return ciphertext
