import base64
import json
import unittest

from pycape.cape import _create_connection_request
from pycape.cape import _generate_nonce
from pycape.cape import _handle_expected_field
from pycape.cape import _parse_wss_response


class TestCape(unittest.TestCase):
    def test_generate_nonce(self):
        length = 8
        nonce = _generate_nonce(length=length)
        self.assertTrue(isinstance(nonce, str))
        self.assertTrue(len(nonce), length)

    def test_create_connection_request(self):
        nonce = "90444145"
        conn_req = _create_connection_request(nonce)
        self.assertEqual(conn_req, json.dumps({"message": {"nonce": "90444145"}}))

    def test_handle_expected_field(self):
        response = '{"message": "connected"}'
        response = json.loads(response)
        response_msg = _handle_expected_field(
            response,
            "message",
            fallback_err="Missing 'message' field in websocket response.",
        )
        self.assertEqual(response_msg, "connected")

    def test_parse_wss_response(self):
        response = json.dumps({"message": {"message": "conn"}})
        inner_msg = _parse_wss_response(response)
        self.assertEqual(inner_msg, base64.b64decode("conn"))


if __name__ == "__main__":
    unittest.main()
