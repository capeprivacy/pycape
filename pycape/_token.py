import pathlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from pycape import _config as cape_config

_FUNCTION_TOKEN_PUBLIC_KEY_FILE = "token.pub.pem"
_FUNCTION_TOKEN_PRIVATE_KEY_FILE = "token.pem"


def get_function_token_public_key_pem():
    pubic_pem_file = (
        pathlib.Path(cape_config.LOCAL_CONFIG_DIR) / _FUNCTION_TOKEN_PUBLIC_KEY_FILE
    )

    if not pubic_pem_file.is_file():
        _ = _generate_rsa_key_pair()

    with open(pubic_pem_file, "r") as f:
        public_key_pem = f.read()

    return public_key_pem


def _generate_rsa_key_pair():
    # Generate key pair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Convert private key to PKCS#1
    pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    # Convert public key to SubjectPublicKeyInfo
    pem_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    pem_folder = pathlib.Path(cape_config.LOCAL_CONFIG_DIR)
    with open(pem_folder / _FUNCTION_TOKEN_PRIVATE_KEY_FILE, "wb") as f:
        f.write(pem_private_key)

    with open(pem_folder / _FUNCTION_TOKEN_PUBLIC_KEY_FILE, "wb") as f:
        f.write(pem_public_key)
