import json
import unittest
from unittest.mock import Mock

import pycape
from pycape.cape import _convert_to_function_ref
from pycape.cape import _create_connection_request
from pycape.cape import _generate_nonce


class TestCape(unittest.TestCase):
    def test_convert_to_function_ref(self):
        CAPE_FUNCTION_ID = "mHwsZ9Bh5cK4Bz8utHjdhy"
        fun_ref = _convert_to_function_ref(CAPE_FUNCTION_ID)
        self.assertTrue(isinstance(fun_ref, pycape.function_ref.FunctionRef))

    def test_generate_nonce(self):
        length = 8
        nonce = _generate_nonce(length=length)
        self.assertTrue(isinstance(nonce, str))
        self.assertTrue(len(nonce), length)

    def test_create_connection_request(self):
        nonce = "90444145"
        conn_req = _create_connection_request(nonce)
        self.assertEqual(conn_req, json.dumps({"message": {"nonce": "90444145"}}))

    def test_connect(self):
        Cape = Mock()
        client = Cape()
        CAPE_FUNCTION_ID = "mHwsZ9Bh5cK4Bz8utHjdhy"
        function_ref = _convert_to_function_ref(CAPE_FUNCTION_ID)
        client.connect(function_ref)
        client.connect.assert_called_with(function_ref)


if __name__ == "__main__":
    unittest.main()
