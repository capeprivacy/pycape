import base64
import json
from unittest.mock import patch

from absl.testing import parameterized

from cape_encrypt import cape_encrypt


class TestCapeEncrypt(parameterized.TestCase):
    @patch("socket.socket")
    def test_encrypt(self, mock_socket):
        ciphertext = b"Cape:so_much_cipher"
        plaintext = b"plaintext"

        mock_socket.return_value.recv.return_value = json.dumps(
            {"error": None, "result": ciphertext.decode("utf-8")}
        )
        result = cape_encrypt.encrypt(plaintext)

        want_req = json.dumps(
            {
                "id": 1,
                "method": "CapeEncryptRPC.Encrypt",
                "params": [base64.standard_b64encode(plaintext).decode("utf-8")],
            }
        ).encode()

        mock_socket.return_value.sendall.assert_called_with(want_req)
        self.assertEqual(result, ciphertext)

    @parameterized.parameters({"x": x} for x in ["String", None])
    def test_encrypt_invalid_input(self, x):
        self.assertRaises(TypeError, cape_encrypt.encrypt, x)

    def test_encrypt_empty_input(self):
        self.assertRaises(ValueError, cape_encrypt.encrypt, b"")

    @patch("socket.socket")
    def test_encrypt_err(self, mock_socket):
        mock_socket.return_value.recv.return_value = json.dumps(
            {"error": "invalid key", "result": None}
        )
        self.assertRaises(
            cape_encrypt.ExecutionError, cape_encrypt.encrypt, b"plaintext"
        )

    @patch("socket.socket")
    def test_encrypt_socket_err(self, mock_socket):
        mock_socket.return_value.recv.return_value = ""

        self.assertRaises(
            cape_encrypt.ConnectionError, cape_encrypt.encrypt, b"plaintext"
        )

    @patch("socket.socket")
    def test_decrypt(self, mock_socket):
        ciphertext = b"cape:so_much_cipher"
        plaintext = b"plaintext"

        mock_socket.return_value.recv.return_value = json.dumps(
            {
                "error": None,
                "result": base64.standard_b64encode(plaintext).decode("utf-8"),
            }
        )

        result = cape_encrypt.decrypt(ciphertext)

        want_req = json.dumps(
            {
                "id": 1,
                "method": "CapeEncryptRPC.Decrypt",
                "params": [ciphertext.decode("utf-8")],
            }
        ).encode()
        mock_socket.return_value.sendall.assert_called_with(want_req)
        self.assertEqual(result, plaintext)

    @parameterized.parameters({"x": x} for x in ["String", None])
    def test_decrypt_invalid_type(self, x):
        self.assertRaises(TypeError, cape_encrypt.decrypt, x)

    @parameterized.parameters({"x": x} for x in [b"", b"cape:", b"so_much_cipher"])
    def test_decrypt_invalid_input(self, x):
        self.assertRaises(ValueError, cape_encrypt.decrypt, x)

    @patch("socket.socket")
    def test_decrypt_err(self, mock_socket):
        mock_socket.return_value.recv.return_value = json.dumps(
            {"error": "invalid key", "result": None}
        )
        self.assertRaises(
            cape_encrypt.ExecutionError, cape_encrypt.decrypt, b"cape:so_much_cipher"
        )

    @patch("socket.socket")
    def test_decrypt_socket_err(self, mock_socket):
        mock_socket.return_value.recv.return_value = ""

        self.assertRaises(
            cape_encrypt.ConnectionError, cape_encrypt.decrypt, b"cape:so_much_cipher"
        )
