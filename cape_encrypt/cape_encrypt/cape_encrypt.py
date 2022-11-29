"""
Cape Encrypt functionality for use within functions deployed to run in a Cape Enclave.

This provides the ability to be able to encrypt or decrypt information solely within a
Cape Enclave using the Cape Key associated with the function owner. Functions can then
encrypt data generated during the execution of the function or have fine grained
control over decrypting inputs.
"""
import base64
import json
import socket


class ExecutionError(Exception):
    """Server reports an error."""


class ConnectionError(Exception):
    """An issue arose in the communication with the server."""


def _call(req: str) -> bytes:
    """RPC through unix domain socket to Cape Enclave to request operations with the Cape
    Key.
    """
    buffer_size = 10485760

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect("../rpc.sock")
    sock.sendall(req)
    response = sock.recv(buffer_size)
    if response == "":
        raise ConnectionError("unexpected connection error, invalid response")
    return response


def encrypt(plaintext: bytes) -> bytes:
    """Encrypt a plaintext with a Cape Key within a Cape Enclave.

    This function is intended only for use within a function deployed in a Cape
    Enclave. It uses envelope encryption. The plaintext is first AES-encrypted with
    anephemeral AES key, and then this key is itself encrypted with the Cape Key
    associated with the Cape account that owns the function.

    Args:
        plaintext: bytes to encrypt.

    Returns:
        Bytes representing the base64 encoded encryption of the ``plaintext``. The
        bytes are a concatenation of the AES-ciphertext of the ``plaintext``, an AES
        nonce, and the RSA-ciphertext of the AES key prefixed by ``cape:``.

    Raises:
        TypeError: if the input is not of the correct type
        ValueError: if the input is empty
        ConnectionError: if an error is thrown from the socket connection
        ExecutionError: if a server error is reported during the remote encryption
        process
    """
    if not isinstance(plaintext, (bytes, bytearray)):
        raise TypeError("input is required to be valid bytes")
    if plaintext == b"":
        raise ValueError("input is empty")

    b64plaintext = base64.standard_b64encode(plaintext).decode("utf-8")
    response = _call(
        json.dumps(
            {"id": 1, "method": "CapeEncryptRPC.Encrypt", "params": [b64plaintext]}
        ).encode()
    )
    payload = json.loads(response)
    if payload["error"] is not None:
        raise ExecutionError(payload["error"])
    return bytes(payload["result"], "utf-8")


def decrypt(ciphertext: bytes) -> bytes:
    """Decrypt a plaintext with a Cape Key within a Cape Enclave.

    This function is intended only for use within a function deployed in a Cape Enclave.
    This function utilizes the Cape Key associated to the function's owner to decrypt
    previously Cape Encrypted input.

    Args:
        b64ciphertext: Base64 encoded bytes of a previously Cape Encrypted plaintext,
        prefixed with Cape:

    Returns:
        Bytes represeting the plaintext result of the decrypted ciphertext

    Raises:
        TypeError: if the input is not of the correct type
        ValueError: if the input is formatted incorrectly or empty
        ConnectionError: if an error is thrown from the socket connection
        ExecutionError: if a server error is reported during the remote encryption
        process
    """
    prefix = b"cape:"
    if not isinstance(ciphertext, (bytes, bytearray)):
        raise TypeError("input is required to be valid bytes")
    if not bytes.startswith(ciphertext, prefix):
        raise ValueError(
            "input must be a valid Cape encrypted value prefixed with 'cape:'"
        )
    if len(bytes.removeprefix(ciphertext, prefix)) == 0:
        raise ValueError("input is empty")

    response = _call(
        json.dumps(
            {
                "id": 1,
                "method": "CapeEncryptRPC.Decrypt",
                "params": [ciphertext.decode("utf-8")],
            }
        ).encode()
    )

    payload = json.loads(response)
    if payload["error"] is not None:
        raise ExecutionError(payload["error"])
    return base64.standard_b64decode(payload["result"])
