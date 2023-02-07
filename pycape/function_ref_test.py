import json
import tempfile
import unittest

from pycape import function_ref as fref


class TestFunctionRef(unittest.TestCase):
    def test_from_to_json_string(self):
        exp_function_json = json.dumps(
            {"function_id": "foo", "function_token": "bar", "function_checksum": "yo"}
        )
        function_ref = fref.FunctionRef.from_json(exp_function_json)
        act_function_json = function_ref.to_json()
        assert exp_function_json == act_function_json

    def test_from_to_json_file(self):
        exp_function_ref = fref.FunctionRef("foo", "bar", "yo")
        with tempfile.NamedTemporaryFile() as f:
            exp_function_ref.to_json(f.name)
            act_function_ref = fref.FunctionRef.from_json(f.name)

        assert exp_function_ref.id == act_function_ref.id
        assert exp_function_ref.token == act_function_ref.token
        assert exp_function_ref.checksum == act_function_ref.checksum
