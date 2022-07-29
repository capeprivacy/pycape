import msgpack
from absl.testing import absltest
from absl.testing import parameterized

from pycape import serde


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
    def test_serialize(self, x):
        x_bytes = serde.serialize(x)
        x_deser = serde.deserialize(x_bytes)
        assert x == x_deser


if __name__ == "__main__":
    absltest.main()
