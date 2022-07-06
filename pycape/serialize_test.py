import numpy as np
from absl.testing import absltest
from absl.testing import parameterized

from pycape.serialize import deserialize
from pycape.serialize import serialize


class SerializeTest(parameterized.TestCase):
    @parameterized.parameters(
        {"x": x}
        for x in [
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
            np.array([1, 2]),
        ]
    )
    def test_serialize(self, x):
        x_bytes = serialize(x)
        x_deser = deserialize(x_bytes)
        if isinstance(x, np.ndarray):
            np.testing.assert_array_equal(x, x_deser)
        else:
            assert x == x_deser


if __name__ == "__main__":
    absltest.main()
