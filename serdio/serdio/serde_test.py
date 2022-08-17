import msgpack
from absl.testing import absltest
from absl.testing import parameterized

from serdio import _test_utils as ut
from serdio import serde


class SerializeTest(parameterized.TestCase):
    @parameterized.parameters(
        {"x": x}
        for x in [
            msgpack.packb("foo"),
            "foo",
            1,
            1.0,
            [1, 2],
            (1, 2),
            {"a": 1, "b": 2},
            set([1, 2]),
            frozenset([1, 2]),
            True,
            bytes("foo", "utf-8"),
            bytearray([1]),
        ]
    )
    def test_serde(self, x):
        x_bytes = serde.serialize(x)
        x_deser = serde.deserialize(x_bytes)
        assert x == x_deser

    @parameterized.parameters(
        {"x": x}
        for x in [
            ut.MyCoolClass(2, 3.0),
            ut.MyCoolResult(6.0),
            (ut.MyCoolClass(2, 3.0), ut.MyCoolResult(6.0)),
            {
                "classes": (ut.MyCoolClass(2, 3.0), ut.MyCoolClass(4, 6.0)),
                "results": (ut.MyCoolResult(6.0), ut.MyCoolResult(24.0)),
            },
        ]
    )
    def test_custom_types(self, x):
        x_bytes = serde.serialize(x, encoder=ut.my_cool_encoder)
        x_deser = serde.deserialize(x_bytes, decoder=ut.my_cool_decoder)
        assert x == x_deser


if __name__ == "__main__":
    absltest.main()
