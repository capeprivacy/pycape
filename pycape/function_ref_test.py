import json
import tempfile

from absl.testing import absltest

from pycape import function_ref as fref


class TestFunctionRef(absltest.TestCase):
    def test_from_to_json_string(self):
        exp_function_json = json.dumps(
            {
                "function_id": "foo",
                "function_name": "foo/bar",
                "function_checksum": "yo",
            }
        )
        function_ref = fref.FunctionRef.from_json(exp_function_json)
        act_function_json = function_ref.to_json()
        assert exp_function_json == act_function_json

    def test_from_to_json_file(self):
        exp_function_ref = fref.FunctionRef("foo", "foo/bar", "yo")
        with tempfile.NamedTemporaryFile() as f:
            exp_function_ref.to_json(f.name)
            act_function_ref = fref.FunctionRef.from_json(f.name)

        assert exp_function_ref.id == act_function_ref.id
        assert exp_function_ref.user == act_function_ref.user
        assert exp_function_ref.name == act_function_ref.name
        assert exp_function_ref.checksum == act_function_ref.checksum

    def test_build_without_id(self):
        f = fref.FunctionRef(name="foo/bar", checksum="yo")
        exp_function_json = json.dumps(
            {"function_name": "foo/bar", "function_checksum": "yo"}
        )
        assert f.to_json() == exp_function_json

    def test_build_without_name(self):
        f = fref.FunctionRef(id="foo", checksum="yo")
        exp_function_json = json.dumps(
            {"function_id": "foo", "function_checksum": "yo"}
        )
        assert f.to_json() == exp_function_json

    def test_no_id_or_name_raises(self):
        with self.assertRaises(ValueError):
            fref.FunctionRef(checksum="yo")

    def test_wrong_name_raises(self):
        with self.assertRaises(ValueError):
            fref.FunctionRef(id="foo", name="bar", checksum="yo")
