import hpke_spec


def encrypt(public_key, input_bytes):
    ciphertext = hpke_spec.hpke_seal(public_key, input_bytes)
    return ciphertext
