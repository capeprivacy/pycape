"""
Cape Encrypt functionality for use within functions deployed to run in a Cape Enclave. 

This provides the ability to be able to encrypt or decrypt information solely within a 
Cape Enclave using the Cape Key associated with the function owner. Functions can then encrypt 
data generated during the execution of the function or have fine grained control over decrypting
inputs. 
"""
import socket
import json
import random

def connect() -> socket.socket:
    """Connect to unix socket on Cape Enclave to request operations with the Cape Key"""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect('../rpc.sock')
    return sock


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext with a Cape Key within a Cape Enclave.

    This function is intended only for use within a function deployed in a Cape Enclave. 
    It uses envelope encryption. The plaintext is first AES-encrypted with anephemeral AES key, 
    and then this key is itself encrypted with the Cape Key associated with the Cape account 
    that owns the function.

    Args:
    plaintext: string to encrypt.

    Returns:
        String represeting the base64 encoded encryption of the ``plaintext``. The bytes are a concatenation
        of the AES-ciphertext of the ``plaintext``, an AES nonce, and the RSA-ciphertext of
        the AES key prefixed by ``Cape:``.

    Raises:
        Exception: if an error is reported from the socket connection
    """
    sock = connect()
    sock.sendall(json.dumps({"id": 1, "method": "CapeEncryptRPC.Encrypt", "params": [plaintext]}).encode())
    response = json.loads(sock.recv(4096))
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def decrypt(b64ciphertext: str) -> str:
    """Decrypt a plaintext with a Cape Key within a Cape Enclave.

    This function is intended only for use within a function deployed in a Cape Enclave. 
    This function utilizes the Cape Key associated to the function's owner to decrypt
    previously Cape Encrypted input.

    Args:
    b64ciphertext: A base64 encoded string of a previously Cape Encrypted plaintext

    Returns:
        String represeting the plaintext result of the decrypted base64 encoded ciphertext 

    Raises:
        Exception: if an error is reported from the socket connection
    """
    sock = connect()
    sock.sendall(json.dumps(({"id": 1, "method": "CapeEncryptRPC.Decrypt", "params": [b64ciphertext]})).encode())
    response = json.loads(sock.recv(4096))
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']

