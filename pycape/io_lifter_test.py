import numpy as np
from absl.testing import parameterized

from pycape.io_lifter import io_serialize
from pycape.serialize import deserialize
from pycape.serialize import serialize


@io_serialize
def identity(x):
    return x


class TestIoLifter(parameterized.TestCase):
    @parameterized.parameters({"x": x} for x in [1, "foo", np.array([1, 2, 3, 4])])
    def test_iolifter(self, x):
        x_ser = serialize(x)
        result = identity(x_ser)
        result_deser = deserialize(result)
        if isinstance(x, np.ndarray):
            np.testing.assert_array_equal(x, result_deser)
        else:
            assert x == result_deser
