import base64
import json
import os
import pathlib
import tempfile
import unittest
import zipfile
from unittest.mock import Mock

import pycape
from pycape.cape import _convert_to_function_ref
from pycape.cape import _create_connection_request
from pycape.cape import _generate_nonce
from pycape.cape import _handle_expected_field
from pycape.cape import _make_zipfile
from pycape.cape import _parse_wss_response


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

    def test_connect(self):
        Cape = Mock()
        client = Cape()
        CAPE_FUNCTION_ID = "mHwsZ9Bh5cK4Bz8utHjdhy"
        function_ref = _convert_to_function_ref(CAPE_FUNCTION_ID)
        client.connect(function_ref)
        client.connect.assert_called_with(function_ref)

    def test_run(self):
        Cape = Mock()
        client = Cape()
        CAPE_FUNCTION_ID = "mHwsZ9Bh5cK4Bz8utHjdhy"
        function_ref = _convert_to_function_ref(CAPE_FUNCTION_ID)
        input = "Welcome to Cape"
        result = client.run(
            function_ref, input.encode()
        ).return_value = b"Welcome to Cape"
        self.assertEqual(result.decode(), input)


class TestZip(unittest.TestCase):
    def test_make_zip(self):
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_dir_path = pathlib.Path(tmp_dir.name)
        app_file_path = tmp_dir_path / "app.py"
        dependency_folder_path = tmp_dir_path / "dependency"
        dependency_file_path = dependency_folder_path / "numpy.py"
        zipped_folder_path = tmp_dir_path / "function.zip"

        with open(app_file_path, "w"):
            pass

        os.mkdir(dependency_folder_path)
        with open(dependency_file_path, "w"):
            pass

        zipped_folder, _ = _make_zipfile(tmp_dir_path)

        with open(zipped_folder_path, "wb") as z:
            z.write(zipped_folder)

        with zipfile.ZipFile(zipped_folder_path, "r") as archive:
            assert str(app_file_path)[1:] in archive.namelist()
            assert str(dependency_file_path)[1:] in archive.namelist()


if __name__ == "__main__":
    unittest.main()
